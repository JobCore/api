FROM gitpod/workspace-postgres

USER root

# install heroku
RUN sudo snap install --classic heroku
