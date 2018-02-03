# BACKEND STACK DOCKER README #

### Backend Framework Stack###

### Limitations of Docker, Compose and Swarm ###
Building images

* Swarm can build an image from a Dockerfile just like a single-host Docker instance can, but the resulting image will only live on a single node and won’t be distributed to other nodes.

* If you want to use Compose to scale the service in question to multiple nodes, you’ll have to build it yourself, push it to a registry (e.g. the Docker Hub) and reference it from docker-compose.yml

* See also: https://docs.docker.com/compose/swarm/#limitations

### Docker Compose File References v3 ###
* See https://docs.docker.com/compose/compose-file/

### Environment variables and file ###
* https://docs.docker.com/compose/env-file/#syntax-rules
* https://docs.docker.com/compose/environment-variables/
* Do not version control sensitive values

### Secrets ###
* Requires use of Docker Swarm
* Do not version control sensitive values
* Only specific people with clearance can access production servers/resources

### Networking in Compose ###
* https://docs.docker.com/compose/networking/
* 

### Compose in Production ###
* Different configuration files can be used as follows:
    - `docker-compose -f docker-compose.yml -f production.yml up -d`
    - This causes production to apply over the original docker-compose

### Compose files and use of docker stack ###
* https://docs.docker.com/compose/bundles/#overview
* Version 3 is supported

### Using compose in non swarm configuration ###
* Docker compose version 3.x can be used in non swarm config with the following
    - `docker-compose build`
    - `docker-compose up`
    - `docker-compose down`

### Docker compose using swarm configruation ###
* A single node docker swarm can be configured and run as follows:
    - `docker swarm init`
    - `docker stack deploy -c docker-compose.yml --with-registry-auth ${DOCKER_STACK}`
* NOTE since we have private registries we need to add the flag at the end


* To see a list of the containers launched:
    - `docker stack ps ${DOCKER_STACK}`
* To take down the app:
    - `docker stack rm ${DOCKER_STACK}`
* To take down the swarm:
    - `docker swarm leave --force`

### Docker Stack Cheat Sheet ###
`docker stack ls              # List all running applications on this Docker host`
`docker stack deploy -c <composefile> <appname>  # Run the specified Compose file`
`docker stack services <appname>       # List the services associated with an app`
`docker stack ps <appname>   # List the running containers associated with an app`
`docker stack rm <appname>                             # Tear down an application`

### Interested in multiple nodes? Read this about swarms on Mac, Linux, Windows ###
* See also: https://docs.docker.com/get-started/part4/#set-up-your-swarm

### Docker Machine/Swarm Cheat Sheet ###
`docker-machine create --driver virtualbox myvm1 # Create a VM (Mac, Win7, Linux)`
`docker-machine create -d hyperv --hyperv-virtual-switch "myswitch" myvm1 # Win10`
`docker-machine env myvm1                # View basic information about your node`
`docker-machine ssh myvm1 "docker node ls"         # List the nodes in your swarm`
`docker-machine ssh myvm1 "docker node inspect <node ID>"        # Inspect a node`
`docker-machine ssh myvm1 "docker swarm join-token -q worker"   # View join token`
`docker-machine ssh myvm1   # Open an SSH session with the VM; type "exit" to end`
`docker-machine ssh myvm2 "docker swarm leave"  # Make the worker leave the swarm`
`docker-machine ssh myvm1 "docker swarm leave -f" # Make master leave, kill swarm`
`docker-machine start myvm1            # Start a VM that is currently not running`
`docker-machine stop $(docker-machine ls -q)               # Stop all running VMs`
`docker-machine rm $(docker-machine ls -q) # Delete all VMs and their disk images`
`docker-machine scp docker-compose.yml myvm1:~     # Copy file to node's home dir`
`docker-machine ssh myvm1 "docker stack deploy -c <file> <app>"   # Deploy an app`

### Further Hacks ###
`docker volume rm $(docker volume ls -f dangling=true) -f; #Remove volumes to clean up docker, dangerous in production`

`docker cp ${DOCKER_STACK}_web.1.pbveu5798yu46yr99birq0tb6:/home/flask/app/web/migrations \
~/bitbucket/<repo>/sw/backend/web/migrations # copy migrations out of container`

`docker service logs ${DOCKER_STACK}_web -f # tail -f logs from a service`

`docker exec -it ${DOCKER_STACK}_web.1.<hash> /bin/bash # open a shell inside a container`



### More about scaling stacks ###
* See also: https://docs.docker.com/get-started/part5/

### Deploying apps to cloud ###
* See also: https://docs.docker.com/get-started/part6/#introduction
* Deploy to Docker Cloud in Standard Mode: https://docs.docker.com/docker-cloud/infrastructure/
* Deploy to Docker Cloud in Swarm Mode (Beta): https://docs.docker.com/docker-cloud/cloud-swarm/

### Managing Sensitive Data with Docker Secrets ### 
* See also: https://docs.docker.com/engine/swarm/secrets/#examples

### Cloud stack file yaml reference (extension of docker-compose.yml) ###
* See also: https://docs.docker.com/docker-cloud/apps/stack-yaml-reference/

### Docker Swarm Tutorial ###
* See also: https://github.com/docker/labs/blob/master/swarm-mode/beginner-tutorial/README.md

### Contacts ###

* Repo owner:
    - Aarya Shahsavar
* Team contacts:
    - Backend: Connor Schentag
    - Documentation: Arthur Loucks
