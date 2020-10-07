#! /bin/bash

# Script to run zoom from anywhere

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

cd $DIR

/usr/local/bin/pipenv run python ./zoom.py
