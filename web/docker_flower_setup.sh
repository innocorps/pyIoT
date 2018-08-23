#!/bin/bash
set +o nounset
ARG1=${1:-false}
ARG2=${2:-"local"}
set -o nounset
set -e
set -u
set -o pipefail

# from https://medium.com/@basi/docker-environment-variables-expanded-from-secrets-8fa70617b3bc

# secret file has username:password
: ${ENV_SECRETS_FILE:=/run/secrets/flower_secrets}

current_dir=${PWD##*/}
proper_dir='web'

ENV_SECRETS_DEBUG=$ARG1

if [[ $current_dir != $proper_dir ]]; then
        echo "Script is not located in $proper_dir, aborting."
        exit -1
fi

env_secret_debug()
{
    	if [ "$ENV_SECRETS_DEBUG" = true ]; then
		echo "Running in debug mode"
        	echo -e "\033[1m$@\033[0m"
   	fi
}

# usage: env_secret_expand VAR
#    ie: env_secret_expand 'XYZ_DB_PASSWORD'
# (will check for "$XYZ_DB_PASSWORD" variable value for a placeholder that defines the
#  name of the docker secret to use instead of the original value. For example:
# XYZ_DB_PASSWORD={{DOCKER-SECRET:my-db.secret}}
env_secret_expand() {
    var="$1"
    eval val=\$$var
    if secret_name=$(expr match "$val" "{{DOCKER-SECRET:\([^}]\+\)}}$"); then
        secret="${ENV_SECRETS_FILE}"
        env_secret_debug "Secret file for $var: $secret"
        if [ -f "$secret" ]; then
            val=$(cat "${secret}")
            export "$var"="$val"
            env_secret_debug "Expanded variable: $var=$val"
        else
            env_secret_debug "Secret file does not exist! $secret"
        fi
    fi
}

env_secrets_expand() {
    	for env_var in $(printenv | cut -f1 -d"=")
    	do
        	env_secret_expand $env_var
    	done
	
    	if [ "$ENV_SECRETS_DEBUG" = true ]; then
        	echo -e "\n\033[1mExpanded environment variables\033[0m"
        	printenv
   	fi
}


echo "Expanding docker secrets to environment"

export FLOWER_CREDENTIALS={{DOCKER-SECRET:FLOWER_CREDENTIALS}}
env_secrets_expand

#USE IF YOU WANT TO SET UP BASIC AUTH
FLOWER_USERNAME=$(echo $FLOWER_CREDENTIALS | cut -f1 -d":")
FLOWER_PASSWORD=$(echo $FLOWER_CREDENTIALS | cut -f2 -d":")
if [ "$ENV_SECRETS_DEBUG" = true ]; then
        echo -e "\n\033[1mFlower credentials\033[0m"
        echo $FLOWER_USERNAME
	echo $FLOWER_PASSWORD
fi

echo "Running flower on port 5555 with authentication"

# USE IF YOU WANT TO SET UP BASIC AUTH
echo "Running basic http authentication"
celery flower --basic_auth=$FLOWER_USERNAME:$FLOWER_PASSWORD -A celery_worker.celery --port=5555

if [[ $? != 0 ]]; then
    echo "An error has occurred."
else
    exit 0
fi
