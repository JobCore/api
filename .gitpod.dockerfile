FROM gitpod/workspace-postgres

USER root

RUN postgres -V \
  && apt-get update \
  && apt-get -y remove --purge postgresql-10.8 \
  && apt-get -y install postgresql-10.8
