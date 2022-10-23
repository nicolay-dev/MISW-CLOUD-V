#!/bin/bash

set -o errexit
set -o nounset

rm -f './celerybeat.pid'
cd ./tasks
celery -A tasks beat -l info