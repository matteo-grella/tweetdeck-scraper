# TweetDeck Scraper Docker Container

A docker container wrapping a tool to continuously scrape [Tweetdeck](https://tweetdeck.twitter.com/) tweets, store them in ElasticSearch and add scraped ids to a RabbitMQ queue.

The extracted information are:

- Id
- Publish date
- Download date
- Author
- Language
- Text
- Full body
- Image url

## Configuration

Sensible settings are configured in a `.env` file, these are exported as env variables when running the container so can be changed even after the container is built:

Twitter account params:

    $ cd tweetdeck-scraper
    $ echo "TWITTER_USERNAME=username" > .env
    $ echo "TWITTER_PASWORD=password" >> .env

Elasticsearch settings:

    $ echo "ES_HOST=localhost" >> .env
    $ echo "ES_PORT=9200" >> .env
    $ echo "ES_CURRENT=index_name" >> .env
    $ echo "ES_USERNAME=username" >> .env
    $ echo "ES_SECRET=password" >> .env

RabbitMQ settings:

    $ echo "RMQ_HOST=localhost" >> .env
    $ echo "RMQ_PORT=5762" >> .env
    $ echo "RMQ_QUEUE=tweetdeck" >> .env
    $ echo "RMQ_USERNAME=username" >> .env
    $ echo "RMQ_PASSWORD=password" >> .env

Additional settings can be found inside `tweetdeck_scraper/settings.py` and should be modified before building the container.

**DEBUG**

When True additional infos are logged.

**LOG_PATH**

The path of the log file.

**SCRAPE_INTERVAL**

Seconds between scraping actions.

**COLUMNS**

Which columns to scrape, value can be 'ALL' or a list of xpaths.

## Usage

Build the container

    $ ./build-docker.sh

Run the container

    $ ./run-docker.sh

Enjoy :)

-----

Legal
=====

It is your responsibility to ensure that your use of tweetdeck-scraper does not violate applicable laws.

Licensing
=====

Tweetdeck Scraper is licensed under the Apache License, Version 2.0. See
[LICENSE](https://github.com/matteo-grella/tweetdeck-scraper/blob/master/LICENSE) for the full
license text.
