#!/usr/bin/env bash

REV=$(git describe --always HEAD)

docker run -d --env-file .env tweetdeck-scraper:$REV
