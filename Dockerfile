# pull official base image
FROM python:3.10.7-slim-buster

# set work directory
WORKDIR /usr/src/cloud-app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install system dependencies
RUN apt-get update && apt-get install -y netcat && apt-get -y install curl

# install dependencies
RUN pip install --upgrade pip
# RUN pip install psycopg2
COPY ./requirements.txt /usr/src/cloud-app/requirements.txt
RUN pip install -r requirements.txt

# copy project
COPY . /usr/src/cloud-app/

# run entrypoint.sh
ENTRYPOINT ["/usr/src/cloud-app/entrypoint.sh"]