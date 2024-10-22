#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd && echo x)"
DIR="${DIR%x}"
echo ${DIR} > /tmp/curie-log
cd ${DIR}
BOKEH_ALLOW_WS_ORIGIN=*.*.*.*:5006 /usr/bin/poetry run python curiectl/curiectld.py > /tmp/curie-log
