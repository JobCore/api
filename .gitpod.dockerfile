FROM gitpod/workspace-postgres

USER root

RUN apt-get remove --purge postgresql-10 \
  && sudo apt-get install postgresql-10
