FROM python:3.10

LABEL maintainer='jelle.prins <jelle.prins@nelen-schuurmans.nl>'
LABEL py_version='3.10'

# Change the date to force rebuilding the whole image.
ENV REFRESHED_AT 2025-04-11

WORKDIR /code
COPY requirements.txt /code/
RUN pip install --no-cache-dir -r requirements.txt
