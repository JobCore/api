FROM gitpod/workspace-postgres

USER root

RUN apt-get -y remove --purge postgresql-10 \
  && apt-get -y install postgresql-10
