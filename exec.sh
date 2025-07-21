#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd && echo x)"
DIR="${DIR%x}"
echo ${DIR} > /tmp/kalpana-log
cd ${DIR}
echo "Hello"
BOKEH_ALLOW_WS_ORIGIN=*.*.*.*:5006 /usr/bin/poetry run python kalpanactl/kalpanactld.py > /tmp/kalpana-log
