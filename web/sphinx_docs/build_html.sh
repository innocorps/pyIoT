#!/bin/bash

set -e 
set -u
set -o pipefail

current_dir=${PWD##*/}
proper_dir='sphinx_docs'

if [[ $current_dir != $proper_dir ]]; then
	echo "Script is not located in $proper_dir, aborting."
	exit -1
fi

echo "Cleaning sphinxdocs"
make -f Makefile clean
echo "Done"

echo "Creating sphinx apidocs"
sphinx-apidoc -f -o source/ ../app/
echo "Done"

echo "Creating html files"
make -f Makefile html
echo "Done"

if [[ $? != 0 ]]; then
	echo "An error has occurred."
else
	exit 0
fi

