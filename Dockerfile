FROM python:3.8

LABEL maintainer='jelle.prins <jelle.prins@nelen-schuurmans.nl>'
LABEL py_version='3.8'

# Change the date to force rebuilding the whole image.
ENV REFRESHED_AT 2023-12-19

WORKDIR /code
COPY requirements.txt /code/
RUN pip install --no-cache-dir -r requirements.txt
