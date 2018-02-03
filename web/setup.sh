#!/bin/bash

set -e
set -u
set -o pipefail

current_dir=${PWD##*/}
proper_dir='web'
virtualenv_dir='venv'
pip_libs="requirements.txt"


#For Linux these libraries must be installed sudo apt-get install python3 and associated 

if [[ $current_dir != $proper_dir ]]; then
        echo "Script is not located in $proper_dir, aborting."
        exit -1
fi

echo "This script will setup the $proper_dir app" 
echo "Python 3.6 is used for this project"
echo "Would you like to continue? (y/n): "
echo -n $'\a'
read user_input

if [[ $user_input != 'y' ]]; then
        echo "Aborting."
        exit -1
fi

echo "Cleaning virtual environment"
if [[ $(ls -A $virtualenv_dir) ]]; then
        echo "$virtualenv_dir is not empty, removing. "
        rm -rf $virtualenv_dir
else
        echo "$virtualenv_dir clean"
fi

# setup virtual environment
echo "Setting up and sourcing virtual environment"
python3 -m $virtualenv_dir ./$virtualenv_dir
set +o nounset #BUG toNOTdo virtualenv sourcing has issues
source $virtualenv_dir/bin/activate
set -o nounset #BUG toNOTdo virtualenv sourcing has issues

os_platform='UNKNOWN'
case "$OSTYPE" in
  solaris*) echo "SOLARIS, never going to be supported, exited"; exit -1;;
  darwin*)  echo "I am a Mac OSX"; os_platform='OSX' ;; 
  linux*)   echo "LINUXMasterRace"; os_platform='LINUX' ;;
  bsd*)     echo "BSD, unsupported, exiting"; exit -1 ;;
  msys*)    echo "WINDOWS, currently unsupported, exiting"; exit -1;;
  *)        echo "unknown: $OSTYPE, unsupported, exiting"; exit -1 ;;
esac


echo "Installing virtualenv pip requirements"
pip3 install --upgrade -r $pip_libs

echo "Creating Sphinx Autodocs"
cd sphinx_docs
./build_html.sh
cd ..

if [[ $(ls -A migrations) ]]; then
	echo "migrations is not empty, already initialized, upgrading"
	python3 manage.py db upgrade
else
	echo "Initiallizing databases"
	python3 manage.py db init
	python3 manage.py db migrate -m "Initial migration"
	python3 manage.py db upgrade
fi

if [[ $? != 0 ]]; then
    echo "An error has occurred."
else
    exit 0
fi


