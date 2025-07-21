#!/bin/bash
DIR=$(dirname $(realpath "$0")) 
cd ${DIR}
echo "Hello ${DIR}"
export PYTHONPATH=${DIR}
BOKEH_ALLOW_WS_ORIGIN=*.*.*.*:5006 /usr/bin/poetry run -vvv python kalpanactl/kalpanactld.py
