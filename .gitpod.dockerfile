FROM gitpod/workspace-postgres

USER root

# install heroku
RUN sudo apt install snapd \
 && sudo snap install --classic heroku
