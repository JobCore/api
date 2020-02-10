FROM python:3.7.4-buster
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
COPY Pipfile /code/
RUN pip install "pipenv==2018.05.18"
RUN pip install pytest
RUN pipenv install --python /usr/local/bin/python
COPY . /code/