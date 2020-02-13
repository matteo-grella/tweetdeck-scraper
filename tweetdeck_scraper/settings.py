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

import os
# from dotenv import load_dotenv
# load_dotenv()

DEBUG = False
LOG_PATH = '/tmp/tweetdeck-scraper.log'
SCRAPE_INTERVAL = 10.0
COLUMNS = 'ALL'  # 'ALL' or list of xpaths

# twitter
TWITTER_USERNAME = os.getenv("TWITTER_USERNAME")
TWITTER_PASSWORD = os.getenv("TWITTER_PASSWORD")
# Elastic Search
# Properties of the document type used for storage.
ES_HOST = os.getenv('ES_HOST')
ES_PORT = os.getenv('ES_PORT')
ES_CURRENT = os.getenv('ES_CURRENT')
ES_USERNAME = os.getenv('ES_USERNAME')
ES_SECRET = os.getenv('ES_SECRET')
# rabbit mq
RMQ_HOST = os.getenv('RMQ_HOST')
RMQ_PORT = os.getenv('RMQ_PORT')
RMQ_USERNAME = os.getenv('RMQ_USERNAME')
RMQ_PASSWORD = os.getenv('RMQ_PASSWORD')
RMQ_QUEUE = os.getenv('RMQ_QUEUE')

# Caution!
TWEETDECK_LOGIN_URL = 'https://twitter.com/login?hide_message=true&redirect_after_login=https%3A%2F%2Ftweetdeck' \
                      '.twitter.com%2F%3Fvia_twitter_login%3Dtrue '
CHROME_DRIVER_PATH = '/usr/local/bin/chromedriver'

ES_MAPPING = {
    'id': {'type': 'keyword'},
    'date_download': {'type': 'date', 'format': "yyyy-MM-dd HH:mm:ss"},
    'date_publish': {'type': 'date', 'format': "yyyy-MM-dd HH:mm:ss"},
    'author': {'type': 'text'},
    'language': {'type': 'keyword'},
    'body': {'type': 'text'},
    'text': {'type': 'text'},
    'image_url': {'type': 'keyword'},
}
