FROM python:3.8.6-slim-buster

LABEL maintainer='jelle.prins <jelle.prins@nelen-schuurmans.nl>'
LABEL py_version='3.8.6'

# Change the date to force rebuilding the whole image.
ENV REFRESHED_AT 2020-01-27

WORKDIR /code
COPY requirements_base.txt requirements_dev.txt /code/

#RUN apt-get update && apt-get install -y --no-install-recommends \
#    build-essential \
#	&& pip3 install -r requirements_dev.txt\
#    && apt-get remove -y\
#    build-essential \
#	&& rm -rf /root/.cache/pip \
#    && apt-get autoremove -y\
#    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements_dev.txt
