#!/usr/bin/env bash

REV=$(git describe --always HEAD)
NAME=tweetdeck-scraper:$REV

docker build -t $NAME .


