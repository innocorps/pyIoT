#!/bin/bash
set +o nounset
ARG1=${1:-"postgres"}
ARG2=${2:-""}

set -o nounset
set -e
set -u
set -o pipefail

current_dir=${PWD##*/}
proper_dir='web'
virtualenv_dir='venv'

#For Linux these libraries must be installed sudo apt-get install python3 and associated 

if [[ $current_dir != $proper_dir ]]; then
        echo "Script is not located in $proper_dir, aborting."
        exit -1
fi

echo "Wait for Postgres to come online"

host_1="$ARG1"
host_2="$ARG2"

cp /run/secrets/psql_password_secrets ~/.pgpass && chmod 600 ~/.pgpass

case "$ARG1" in
	postgres)
		echo "Connecting to $host_1"
		until psql -w -h "$host_1" -p 5432 -U "postgres" -c '\l'; do
		>&2 echo "Postgres is unavailable - sleeping"
		done
		sleep 1
		>&2 echo "Postgres is up - executing command"
		
		case "$ARG2" in
			postgres_test)
				until psql -w -h "$host_2" -p 5433 -U "postgres" -c '\l'; do
  				>&2 echo "Postgres_test is unavailable - sleeping"
  				sleep 1
				done
				>&2 echo "Postgres_test is up - executing command"
			;;
			*)
				echo "Skipping postgres_test setup"
			;;
		esac
	;;
	postgres_dev)
		echo "Connecting to $host_2"
		until psql -w -h "$host_2" -p 5432 -U "postgres" -c '\l'; do
		>&2 echo "$host_2 postgres is unavailable - sleeping"
		done
		sleep 1
		>&2 echo "Postgres is up - executing command"
	;;
	postgres_prod)
		echo "Connecting to $host_2"
		until psql -w -h "$host_2" -p 5432 -U "postgres" -c '\l'; do
		>&2 echo "$host_2 postgres is unavailable - sleeping"
		done
		sleep 1
		>&2 echo "Postgres is up - executing command"
	;;
	*)
		echo "Error in connecting to postgres db."
		exit -1
	;;

esac

echo "Waiting on redis:6379"
./wait-for-it.sh redis:6379 -s -t 120
echo "redis:6379 is up."


if [[ $(ls -A migrations) ]]; then
	echo "migrations is not empty, already initialized, upgrading"
	python3 manage.py db upgrade
else
	echo "Initiallizing database"
	python3 manage.py db init
	echo "Migrating database"
	python3 manage.py db migrate -m "Initial migration"
	echo "Upgrading database"
	python3 manage.py db upgrade
fi

echo "Running Gunicorn WSGI"
/usr/local/bin/gunicorn --error-logfile ./error.log --log-file ./info.log --enable-stdio-inheritance --timeout 30 -w 1 -b :8000 manage:app


if [[ $? != 0 ]]; then
    echo "An error has occurred."
else
    exit 0
fi


