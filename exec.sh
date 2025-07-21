#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd && echo x)"
DIR="${DIR%x}"
cd ${DIR}
echo "Hello ${DIR}"
export PYTHONPATH=${DIR}
BOKEH_ALLOW_WS_ORIGIN=*.*.*.*:5006 /usr/bin/poetry run -vvv python kalpanactl/kalpanactld.py > /tmp/kalpana-log
