FROM python:3.8

LABEL maintainer='jelle.prins <jelle.prins@nelen-schuurmans.nl>'
LABEL py_version='3.8'

# Change the date to force rebuilding the whole image.
ENV REFRESHED_AT 2019-02-25

WORKDIR /code
COPY requirements_base.txt requirements_dev.txt /code/
RUN pip install --no-cache-dir -r requirements_dev.txt
