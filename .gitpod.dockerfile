FROM gitpod/workspace-postgres

USER root

# install heroku
RUN apt-get update \ 
 && apt-get -y install snapd \
 && sudo snap install --classic heroku
