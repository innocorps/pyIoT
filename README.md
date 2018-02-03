# PyIoT: a Docker deployed Flask microservice framework

PyIoT is a batteries not included microservice framework. A barebones Flask webapp is paired with Redis, Nginx and Postgresql in Docker containers for local development and deployment to cloud services. This project was initially created to integrate and control remote industrial equipment for a IIOT application.  

A simple RESTful API is demonstrated where a sensor and datetime stamp in RFC-3339 format POSTed and stored within the Redis cache and database. 

The motivation for creating this was to have a framework to integrate business logic and data analysis easily into a web app and be able to develop across multiple platforms. Docker allows for much easier deployment, increasing productivity by being lazily efficient engineers. We also wanted to use the latest versions of Docker as they had some interesting new features.


## Getting Started

The framework can be cloned from here: [Git Repository](https://github.com/innocorps/PyIoT.git)

The coding style for this project follows similarly to [Google's Python Style Guide](https://google.github.io/styleguide/pyguide.html).


### Prerequisites

These prequisites are required for getting a local machine up and running. Deployment is covered below.

Before getting started, you will need to get Docker up and running on your development machine: [Install Docker](https://docs.docker.com/install/)

Bash completion should also be installed in order to use the deployment autocomplete script in /etc/: 

[Docker for Mac Bash and Docker completion](https://docs.docker.com/docker-for-mac/#install-shell-completion)

A Docker ID will need to be created, as well as a private cloud registry on Docker Cloud or roll your own. 

After the a personal or corporate registry has been created, the following repositories need to be created:

```
{your_registry}/{your_stack_name}_redis
{your_registry}/{your_stack_name}_nginx
{your_registry}/{your_stack_name}_web
```

If OAuth is to be used for creating accounts, OAuth credentials will need to be generated. A no-reply email at a domain you control will also need to be created in order to authenticate users.



### Installing

Once the git repository is cloned or forked, a couple of secret keys and environment variables will need to be set.

1. Follow the instructions in etc/deploy_backend.bash-completion for how to set up autocompletion
2. Within deploy_backend.sh, the exported variables DOCKER_REPO and DOCKER_STACK should be set as the names created above in your repository. If you have changed the name of the folder the project is checked out in, proper_dir will have to be changed as well:
	```
	DOCKER_REPO='your_registry'
	DOCKER_STACK='your_stack_name'
	```
3. For local deployment, you will need to create 3 secrets files for https locally using self-signed certificates. This can be done by:
	```
	cd nginx
	./generate_certs.sh dhparam
	./generate_certs.sh localhost
	```
The script can be modified with your company info. The first call to the script creates the dhparam.pem.secrets, the second creates nginx.crt.secrets and nginx.key.secrets. 
4. 2 example Docker secrets files are provided for the structure of the app. This is where the configuration of the app can be set, a secret key for Flask is added, OAuth credentials and the mail domain that users must have an account on in order to sign up. Furthermore, the email address used to send messages to new users when they sign up and login information must be added here.

*NOTE* These secret files should never be committed to version control. Both .gitignore and .dockerignore should exclude them and access permissions should be set properly. 

The username, password, port and database information in both secrets files for Postgres must match in order for the app to work properly.

5. Redis and Nginx configuration files can be modified in their respective folders. 

6. The system must be run locally the first time in order to generate the database migration, this is done as follows:
	```
	./deploy_backend.sh deploy local
	./deploy_backend.sh migrate
	git add web/migrations/
	git commit -m "First commit of initial db initialization."
	./deploy_backend.sh stop
	```
Through this, the deploy script will build the docker images for Redis, Nginx and the web app. It will then push this docker image to your cloud registry with the tag GIT_REV_SHORT defined in deploy_backend.sh so that each image in the repository is unique to a commit. 

7. To build Sphinx documentation run the following command:
	```
	./deploy_backend.sh build docs
	```
The Sphinx html docs can be found at ./docs/sphinx/html/index.html

8. Modifications to the web app will be required in order to make it functional to your application. The app follows other similar Flask application structures. ./web/config.py contains general configuration parameters. ./web/app/api_0_1/ contains v0.1 of the RESTful api, ./web/app/models.py contains the database model.


## Tests

1. Unit tests are defined under web/tests/. To run them:
	```
	./deploy_backend.sh deploy test
	```
A coverage report is generate and can be found under ./docs/coverage/index.html.


## Deployment

Further docker-compose.yml files can be created, as well as their respective Docker secrets files, in order to deploy to beta and production servers. Further extensions to deploy_backend.sh hae been implemented in other projects to automate this process further. 

Docker for AWS can be used quite easily by following instructions here:
* [Docker for AWS](https://docs.docker.com/docker-for-aws/)

## Built With

* [Flask](http://flask.pocoo.org/) 
* [Redis](https://redis.io/)
* [Nginx](https://nginx.org/en/docs/)

## Contributing

* Please contact us for more details on contributing

## Versioning

* [SemVer](https://semver.org/) 

## Authors

* [AUTHORS](https://github.com/innocorps/pyIoT/blob/master/AUTHORS)

## License

* [LICENSE](LICENSE) 
* [Third Party Licenses](https://github.com/innocorps/pyIoT/tree/master/licenses)

## Known Issues

* Currently, accounts set up through OAuth cannot set a password and get a token, they can only sign in through the web interface. 
* Periodically, upon deployment, the waits within the docker web container will not start up after Redis and the swarm will have to be cancelled and started up again.
* See also [Issues](https://github.com/innocorps/pyIoT/issues).

## Acknowledgements 

* README.md inspired from [here](https://gist.github.com/PurpleBooth/109311bb0361f32d87a2)
