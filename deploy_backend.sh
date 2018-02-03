#!/bin/bash

set +o nounset
#conditionally assign variables if they aren't passed from command line
ARG1=${1:-"foo"}
ARG2=${2:-"bar"}
ARG3=${3:-"baz"}

set -o nounset
set -e
set -u
set -o pipefail
shopt -s extglob

# Stack locations and names
export DOCKER_REPO='your_registry'
export DOCKER_STACK='your_stackname'

# Directory this script should be in
current_dir=${PWD##*/}
proper_dir='PyIoT'

export GIT_REV_SHORT=$(git rev-parse --short HEAD)

#For Linux these libraries must be installed sudo apt-get install python3 and associated 

if [[ $current_dir != $proper_dir ]]; then
        echo "Script is not located in $proper_dir, aborting."
        exit -1
fi

# This usage function is formatted to properly display on a terminal
usage(){
cat <<EOF
Usage: $0 COMMAND [OPTIONS]

A solution for deploying docker stacks for $DOCKER_STACK

Commands:
    build
	    images		Build Dockerfile containers for this stack and push to repository
            docs		Build Sphinx documentation, copies to ./docs	
    deploy
    	    test		Deploy a swarm in testing configuration
	    local		Deploy a swarm in development configuration locally
    clean
    	    images		Clean local machine of all docker images
	    volumes		DANGER - Cleans all local machine volumes, including dbs (requires -f)
	    venv		Cleans any venv files and py cache
	    all			DANGER - Cleans all local machine images and volumes, including dbs (requires -f)
    stop			Stops a swarm
    login			Login to your docker cloud account
    bash
    	    web			Creates a bash shell into web container
    logs
    	    web			Shows logs for the web service
	    nginx		Shows logs for nginx
	    redis		Shows logs for redis
	    postgres		Shows logs for postgres development db
	    postgres_test	Shows logs for postgres testing db
    migrate			Migrates db and copies the migrations folder from the docker web container to the git repo
    				(requires -f)
    help			Prints this message

Options:
    -f	    force		Force flag to delete volumes and clean

EOF
}

docker_build_images(){
	echo "Building ${DOCKER_STACK}_redis"
	cd ./redis && ./docker_build_redis_image.sh $GIT_REV_SHORT && cd ..
	echo "Building ${DOCKER_STACK}_nginx"
	cd ./nginx && ./docker_build_nginx_image.sh $GIT_REV_SHORT && cd ..
	echo "Building ${DOCKER_STACK}_web"
	cd ./web && ./docker_build_web_image.sh $GIT_REV_SHORT && cd ..
}

docker_deploy_swarm(){
	echo "Building and deploying on commit: $GIT_REV_SHORT"
	docker_build_images
	echo "Initializing swarm"
	# use a random port on the local net for swarm so that if multiple interfaces work we are good. 
	docker swarm init --advertise-addr lo
	echo "Deploying $DOCKER_STACK stack"
	case "$1" in
		test)
			echo "Deploying swarm in testing mode"
			docker stack deploy -c docker-compose.yml --with-registry-auth $DOCKER_STACK
		;;
		local)
			echo "Deploying swarm in local mode"
			docker stack deploy -c docker-compose.yml --with-registry-auth $DOCKER_STACK
		;;
		*)
			exit -1
		;;
	esac
}

clean_venv(){
	echo "Cleaning virtual environments and py cache"
	find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf
	find . -name "venv" | xargs rm -rf
}

setup_venv(){
	echo "Setting up local venv"
	python3 -m venv ./web/venv
	set +o nounset #bug with virtual environrments
	source ./web/venv/bin/activate
	set -o nounset
	pip install -r ./web/requirements.txt
}

build_sphinx_docs(){
	echo "Building Sphinx Docs"
	echo "Executing build docs on web"
	until [[ -n $(docker ps -f name=${DOCKER_STACK}_web -q) ]]; do
		>&2 echo "Waiting on web"
		sleep 1
	done
	docker exec -t -e SPHINX_GIT_REV_SHORT=$GIT_REV_SHORT \
			$(docker ps -f name=${DOCKER_STACK}_web -q) \
		/bin/bash -c 'echo "We are building on rev: $SPHINX_GIT_REV_SHORT"; \
			cd sphinx_docs; \
			./build_html.sh; \
			exit'
	echo "Cleaning Sphinx Documents"
	rm -rf ./docs/sphinx
	echo "Copying Sphinx Docs out of container to docs"
	docker cp $(docker ps -f name=${DOCKER_STACK}_web -q):/home/flask/app/web/sphinx_docs/_build \
		./docs/sphinx	
}

docker_clean_images(){
	echo "Cleaning images"
	docker rmi $(docker images -q) -f
}

docker_clean_volumes(){
	echo "Cleaning volumes"
	docker volume rm $(docker volume ls -f dangling=true) -f
}

docker_stop(){
	echo "Stopping swarm"
	docker stack rm $DOCKER_STACK
	docker swarm leave -f
}

docker_exec_shell_web(){
	echo "Creating a bash shell into web"
	docker exec -it $(docker ps -f name=${DOCKER_STACK}_web -q ) /bin/bash
}

run_unit_tests_web(){
	echo "Cleaning Coverage Reports"
	rm -rf ./docs/coverage
	echo "Executing unit tests on web"
	until [[ -n $(docker ps -f name=${DOCKER_STACK}_web -q) ]]; do
		>&2 echo "Waiting on web"
		sleep 1
	done
	echo "Entering web to run coverage test"
	docker exec -t $(docker ps -f name=${DOCKER_STACK}_web -q) \
		/bin/bash -c 'python3 manage.py test --coverage; exit'
	echo "Copying unit test Coverage Reports out of container to docs"
	docker cp $(docker ps -f name=${DOCKER_STACK}_web -q):/home/flask/app/web/tmp/coverage \
		./docs/coverage	
}

docker_service_logs(){
	case "$1" in
		web)
			docker service logs $(docker service ls -f name=${DOCKER_STACK}_web -q) -f -t
		;;
		nginx)
			docker service logs $(docker service ls -f name=${DOCKER_STACK}_nginx -q) -f -t
		;;
		redis)
			docker service logs $(docker service ls -f name=${DOCKER_STACK}_redis -q) -f -t
		;;
		postgres)
			docker service logs $(docker service ls \
				--filter name=${DOCKER_STACK}_postgres.1 -q) -f -t 
		;;
		postgres_test)
			docker service logs $(docker service ls \
				--filter name=${DOCKER_STACK}_postgres_test.1 -q) -f -t 
		;;
		*)
			usage
		;;
	esac
}

docker_migrate_db(){
	echo "Cleaning current migrations."
	rm -rf ./web/migrations
	docker exec -t -e SPHINX_GIT_REV_SHORT=$GIT_REV_SHORT \
			$(docker ps -f name=${DOCKER_STACK}_web -q) \
		/bin/bash -c 'echo "We are migrating db on rev: $SPHINX_GIT_REV_SHORT"; \
			python3 /home/flask/app/web/manage.py db migrate; \
			exit'
	echo "Copying over new migrations."
	docker cp $(docker ps -f name=${DOCKER_STACK}_web -q):/home/flask/app/web/migrations \
		./web/migrations
}

case "$ARG1" in 
	build) 
		case "$ARG2" in
			images) 
				docker_build_images
			;;
			docs) 
				docker_deploy_swarm "local"
				build_sphinx_docs
                                docker_stop
			;;
			*) 
				usage
			;;
		esac
	;;
	deploy) 
		case "$ARG2" in
			test) 
				echo "Setting up stack for test"
				docker_deploy_swarm "test"
				echo "Stack up. Running Unit Tests."
				run_unit_tests_web
				docker_stop
			;;
			local) 
				echo "Deploying locally"
				docker_deploy_swarm "local"
			;;
			*) 
				usage
			;;
		esac
	;;
	clean) 
		case "$ARG2" in
			images) 
				docker_clean_images
			;;
			volumes) 
				case "$ARG3" in 
					-f)
						docker_clean_volumes
					;;
					*)
						echo -e "\n"
        					echo "WARNING:	Cleaning volumes requires -f flag"
        					echo -e "\n"
        					usage
					;;
				esac
			;;
			venv) 
				clean_venv

			;;
			all) echo "Cleaning all"
				case "$ARG3" in 
					-f)
						echo "Cleaning all"
						docker_clean_images
						docker_clean_volumes
						clean_venv
					;;
					*)
						echo -e "\n"
        					echo "WARNING:	Cleaning all requires -f flag"
        					echo -e "\n"
        					usage
					;;
				esac
			;;
			*) 
				usage
			;;
		esac
	;;
	stop) 
		docker_stop
	;;
	login) 
		echo "Logging in to Docker Cloud"
		docker login
	;;
	bash)
		docker_exec_shell_web
	;;
	logs)
		docker_service_logs $ARG2
	;;
	migrate)
		docker_migrate_db
	;;
	help) 
		usage
	;;
	*) 
		usage
	
	;;
esac

if [[ $? != 0 ]]; then
    echo "An error has occurred."
else
    exit 0
fi
