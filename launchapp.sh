#!/bin/bash
set -e  # stop on error

# Run DB init
python -m app_cough.models.initdb

# Start app
gunicorn app_cough.main:app -k uvicorn.workers.UvicornWorker -w 2 -b 0.0.0.0:6400