#!/bin/bash
set -e #exit script if error (fail fast)

# Defaults in case ENV vars aren't set
NORMAL_QUEUE_NAME=${NORMAL_QUEUE:-"cough-worker-normal-queue"}
NORMAL_QUEUE_MIN=${NORMAL_QUEUE_MIN:-2}
NORMAL_QUEUE_MAX=${NORMAL_QUEUE_MAX:-8}

URGENT_QUEUE_NAME=${URGENT_QUEUE:-"cough-worker-urgent.fifo"}
URGENT_QUEUE_MIN=${URGENT_QUEUE_MIN:-3}
URGENT_QUEUE_MAX=${URGENT_QUEUE_MAX:-28}

pipx run poetry run celery --app app_cough.tasks.analysis:celery worker --loglevel=info  -n worker_urgent@%h \
    -Q "$URGENT_QUEUE_NAME" --autoscale="$URGENT_QUEUE_MAX,$URGENT_QUEUE_MIN" & 

sleep 10

pipx run poetry run celery --app app_cough.tasks.analysis:celery worker --loglevel=info  -n worker_normal@%h \
    -Q "$NORMAL_QUEUE_NAME" --autoscale="$NORMAL_QUEUE_MAX,$NORMAL_QUEUE_MIN" & 

wait