#!/bin/bash

ARG1=${1:-"latest"}

set -o nounset
set -e
set -u
set -o pipefail
shopt -s extglob

current_dir=${PWD##*/}
proper_dir='nginx'

#For Linux these libraries must be installed sudo apt-get install python3 and associated 

if [[ $current_dir != $proper_dir ]]; then
        echo "Script is not located in $proper_dir, aborting."
        exit -1
fi

# docker login
docker build -t ${DOCKER_REPO}/${DOCKER_STACK}_nginx:$ARG1 .
docker push ${DOCKER_REPO}/${DOCKER_STACK}_nginx:$ARG1

if [[ $? != 0 ]]; then
    echo "An error has occurred."
else
    exit 0
fi


