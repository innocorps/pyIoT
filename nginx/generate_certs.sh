#!/bin/bash
set +o nounset
ARG1=${1:-"localhost"} #conditionally assign to local host if no IP provided

set -o nounset
set -e 
set -u
set -o pipefail
shopt -s extglob

#current_dir=${PWD##*/}
#proper_dir='nginx'

#if [[ $current_dir != $proper_dir ]]; then
#        echo "Script is not located in $proper_dir, aborting."
#        exit -1
#fi

usage(){
cat <<EOF
Usage: $0 COMMAND [OPTIONS]

A solution for generating self signed certs for TLS for local host or FQDNs

Commands:
	localhost	Generate for localhost (DEFAULT)
    	*		TODO for FQDNs or IPs
	dhparam		Generate a dhparam 2048 cert for perfect forward secrecy
    	help		Print Usage

EOF
}

case "$ARG1" in
	localhost)
		echo "Generating certificates for localhost"
		openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
			-keyout ../nginx.key.secrets \
			-out ../nginx.crt.secrets \
			-subj "/C=CA/ST=Saskatchewan/L=Saskatoon/O=YourCompany/OU=Engineering/CN=localhost"
	;;
	dhparam)
		openssl dhparam -out ../dhparam.pem.secrets 4096
	;;
	help)
		usage
	;;
	*)
		usage
	;;
esac
