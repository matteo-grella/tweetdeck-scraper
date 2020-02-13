"""
   Copyright 2019 Matteo Grella, Stefano Contini

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

import collections
import logging
import re
import sys
import time
import pika
from datetime import datetime
from dateutil.parser import parse
from elasticsearch import Elasticsearch
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from settings import (CHROME_DRIVER_PATH, COLUMNS, DEBUG, ES_CURRENT, ES_HOST,
                      ES_MAPPING, ES_PORT, ES_SECRET, ES_USERNAME, LOG_PATH,
                      RMQ_HOST, RMQ_PASSWORD, RMQ_PORT, RMQ_QUEUE,
                      RMQ_USERNAME, SCRAPE_INTERVAL, TWEETDECK_LOGIN_URL,
                      TWITTER_PASSWORD, TWITTER_USERNAME)

if sys.version_info[0] < 3:
    ConnectionError = OSError


class Scraper:
    def __init__(self, ):
        # logging
        self.set_logger()
        # registry that stores already inserted items
        self.registry = collections.deque(maxlen=1000)
        # ES
        self.setup_es()
        # rabbitmq
        self.setup_rmq()
        # init web driver
        chrome_options = Options()
        # chrome_options.add_argument("--window-size=1920x1080")
        chrome_options.add_argument("--headless")
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(
            options=chrome_options, executable_path=CHROME_DRIVER_PATH)

    def set_logger(self):
        self.logger = logging.getLogger('scraper')
        self.logger.setLevel(logging.INFO)

        fh = logging.FileHandler(LOG_PATH)
        # fh = logging.StreamHandler(sys.stdout)
        fh.setLevel(logging.INFO)

        formatstr = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        formatter = logging.Formatter(formatstr)

        fh.setFormatter(formatter)

        self.logger.addHandler(fh)

    def setup_es(self):
        self.es = Elasticsearch(
            [ES_HOST],
            http_auth=(str(ES_USERNAME), str(ES_SECRET)),
            port=ES_PORT,
            use_ssl=False,
        )
        self.index_current = ES_CURRENT
        self.mapping = {'properties': ES_MAPPING}

        try:
            # check if server is available
            self.es.ping()

            # check if the necessary indices exist and create them if needed
            if not self.es.indices.exists(self.index_current):
                self.es.indices.create(
                    index=self.index_current, ignore=[400, 404])
                self.es.indices.put_mapping(
                    index=self.index_current,
                    doc_type='article',
                    body=self.mapping)
            self.running = True

        except ConnectionError as error:
            self.running = False
            self.logger.error(
                "Failed to connect to Elasticsearch, exiting: %s" % error)
            sys.exit()

    def setup_rmq(self):
        try:
            if RMQ_USERNAME and RMQ_PASSWORD:
                self.rmq = pika.BlockingConnection(
                    pika.ConnectionParameters(
                        host=RMQ_HOST,
                        port=RMQ_PORT,
                        credentials=pika.credentials.PlainCredentials(
                            RMQ_USERNAME, RMQ_PASSWORD)))
            else:
                self.rmq = pika.BlockingConnection(
                    pika.ConnectionParameters(
                        host=RMQ_HOST,
                        port=RMQ_PORT
                    )
                )
            self.rmq_channel = self.rmq.channel()
            self.rmq_channel.queue_declare(
                queue=RMQ_QUEUE, durable=True)  # idempotent!
        except Exception as error:
            self.logger.error(
                "Failed to connect to RabbitMQ, exiting: %s" % error)

    def login(self):
        self.logger.info('performing login')
        self.driver.get(TWEETDECK_LOGIN_URL)

        username_field = self.driver.find_element_by_class_name(
            "js-username-field")
        password_field = self.driver.find_element_by_class_name(
            "js-password-field")

        username_field.send_keys(TWITTER_USERNAME)
        time.sleep(1)

        password_field.send_keys(TWITTER_PASSWORD)
        time.sleep(1)

        self.driver.find_element_by_class_name("EdgeButtom--medium").click()

    def scrape(self):
        # wait for page to load
        try:
            element_present = EC.presence_of_element_located((By.CLASS_NAME,
                                                              'column'))
            WebDriverWait(self.driver, 10).until(element_present)
        except TimeoutException:
            self.logger.warning("Timed out waiting for page to load")
            return

        self.logger.info('scraping')

        if COLUMNS == 'ALL':
            columns = self.driver.find_elements_by_class_name('column')
        else:
            columns = COLUMNS

        for key, column in enumerate(columns):
            if COLUMNS != 'ALL':
                column = self.driver.find_element_by_xpath(column)
            items = column.find_elements_by_class_name('js-stream-item')
            if DEBUG:
                self.logger.info('column %s, items: %s' % (key, len(items)))
            for item in items:
                id = item.get_attribute('data-tweet-id')
                if id not in self.registry:
                    try:
                        self.registry.append(id)
                        author = item.find_element_by_class_name(
                            'fullname').text
                        dt = parse(
                            item.find_element_by_class_name('tweet-timestamp').
                            get_attribute('datetime'))
                        text_el = item.find_element_by_class_name('tweet-text')
                        text = text_el.get_attribute('innerHTML')
                        body = item.find_element_by_class_name(
                            'tweet-body').get_attribute('innerHTML')
                        language = text_el.get_attribute('lang')
                        image_url = None
                        try:
                            anchor_image = item.find_element_by_class_name(
                                'js-media-image-link')
                            if anchor_image:
                                style = anchor_image.get_attribute('style')
                                match = re.match(
                                    r'background-image:\s*url\("?(.*?)\?',
                                    style)
                                if match:
                                    image_url = match.group(1)
                        except NoSuchElementException:
                            image_url = None
                        # store in elastic search
                        self.store(
                            id,
                            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            dt.strftime('%Y-%m-%d %H:%M:%S'), author, language,
                            text, body, image_url)
                        # enqueue
                        self.enqueue(id)
                    except Exception as e:
                        self.logger.warning('warning: %s' % str(e))

                elif DEBUG:
                    self.logger.info('already added, not adding: %s' % str(id))

    def store(self, id, date_download, date_publish, author, language, text,
              body, image_url):
        if not self.es.exists(
                index=self.index_current, doc_type='article', id=id):
            self.logger.info("Saving to ElasticSearch: %s" % id)
            extracted_info = {'id': id, 'date_download': date_download, 'date_publish': date_publish, 'author': author,
                              'language': language, 'text': text, 'body': body}
            if image_url:
                extracted_info['image_url'] = image_url
            self.es.index(
                index=self.index_current,
                doc_type='article',
                id=id,
                body=extracted_info,
                refresh=True)

    def enqueue(self, id):
        if not self.rmq.is_open:
            self.setup_rmq()

        self.rmq_channel.basic_publish(
            exchange='',
            routing_key=RMQ_QUEUE,
            body=id,
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            ))

    def run(self):
        self.login()
        start_time = time.time()
        while 1:
            try:
                self.scrape()
            except Exception as e:
                self.logger.error('scrape() error: %s' % str(e))
            self.rmq.sleep(SCRAPE_INTERVAL - (
                (time.time() - start_time) % SCRAPE_INTERVAL))


if __name__ == "__main__":
    scraper = Scraper()
    scraper.run()
