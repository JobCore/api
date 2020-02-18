FROM python:3.7.4-buster
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/
RUN pip install pytest
RUN pip install -r requirements.txt
COPY . /code/