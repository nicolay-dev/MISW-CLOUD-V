#!/bin/bash

set -o errexit
set -o nounset

cd ./tasks
celery -A tasks worker -l info --logfile=../logs/celery.log