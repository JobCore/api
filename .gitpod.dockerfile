FROM heroku/heroku:18

USER root

RUN apt-get update \
 && apt-get install -y heroku