# Use an official Python runtime as a parent image
FROM python:3.6


# I would like to have access to the most up to date utilities, vim and psql to wait on postgres
RUN apt-get update && apt-get install -y \
  coreutils \
  vim \
  postgresql-client \
  dos2unix
  # redis-tools \

# Create the group and user to be used in this container
RUN groupadd flaskgroup && useradd -m -g flaskgroup -s /bin/bash flask

# Set the working directory of the application
RUN mkdir -p /home/flask/app/web
WORKDIR /home/flask/app/web

# Install package dependencies as this is recommended best practice
# https://docs.docker.com/engine/userguide/eng-image/dockerfile_best-practices/#add-or-copy
# This helps to avoid re-installing python packages if source code is changed
COPY requirements.txt /home/flask/app/web
RUN dos2unix /home/flask/app/web/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# A .dockerignore file needs to be present to ignore .git etc
# Copy the source code into the container
COPY . /home/flask/app/web
RUN find /home/flask/app/web -type f -print0 | xargs -0 dos2unix

# Change owner of the directory for security reasons
RUN chown -R flask:flaskgroup /home/flask

# Change the user to flask so that root attacks are prevented
USER flask

# RUN ./docker_setup.sh





