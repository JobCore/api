FROM gitpod/workspace-postgres

USER root

RUN apt-get remove --purge postgresql-9.1 \
  && sudo apt-get install postgresql-9.1