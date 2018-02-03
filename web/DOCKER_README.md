# BACKEND WEB APP DOCKER README #

### Limitations of Docker, Compose and Swarm ###
Building images

* Swarm can build an image from a Dockerfile just like a single-host Docker instance can, but the resulting image will only live on a single node and won’t be distributed to other nodes.

* If you want to use Compose to scale the service in question to multiple nodes, you’ll have to build it yourself, push it to a registry (e.g. the Docker Hub) and reference it from docker-compose.yml

* See also: https://docs.docker.com/compose/swarm/#limitations

### Building and Deploying Docker Image ###

* Run docker build 
    - `docker build -t ${DOCKER_STACK}_web .`
* Login to docker id
    - `docker login`
* Tag the image (tagname is optional, if omitted, will be latest)
    - `docker tag ${DOCKER_STACK}_web ${DOCKER_REPO}/${DOCKER_STACK}_web:tagname`
* Publish the image
    - `docker push ${DOCKER_REPO}/${DOCKER_STACK}_web:tagname`

### Docker container commands ###
* To pull an image
    - `docker pull ${DOCKER_REPO}/${DOCKER_STACK}_web:tagname`
* To run an image (flag -d for detached)
    - `docker run ${DOCKER_REPO}/${DOCKER_STACK}_web:tagname`
* See docker containers running in background
    - `docker ps`
* Stop docker containers
    - `docker stop CONTAINER_ID_FROM_PS`
* See docker images
    - `docker images`

### Dockerfile ###

* See also: https://docs.docker.com/engine/userguide/eng-image/dockerfile_best-practices/

### Docker Cheatsheet ###
`docker build -t friendlyname .  # Create image using this directory's Dockerfile`
`docker run -p 4000:80 friendlyname  # Run "friendlyname" mapping port 4000 to 80`
`docker run -d -p 4000:80 friendlyname         # Same thing, but in detached mode`
`docker ps                                 # See a list of all running containers`
`docker stop <hash>                     # Gracefully stop the specified container`
`docker ps -a           # See a list of all containers, even the ones not running`
`docker kill <hash>                   # Force shutdown of the specified container`
`docker rm <hash>              # Remove the specified container from this machine`
`docker rm $(docker ps -a -q)           # Remove all containers from this machine`
`docker images -a                               # Show all images on this machine`
`docker rmi <imagename>            # Remove the specified image from this machine`
`docker rmi $(docker images -q)             # Remove all images from this machine`
`docker login             # Log in this CLI session using your Docker credentials`
`docker tag <image> username/repository:tag  # Tag <image> for upload to registry`
`docker push username/repository:tag            # Upload tagged image to registry`
`docker run username/repository:tag                   # Run image from a registry`


### Contacts ###

* Repo owner:
    - Aarya Shahsavar
* Team contacts:
    - Backend: Connor Schentag
    - Documentation: Arthur Loucks
