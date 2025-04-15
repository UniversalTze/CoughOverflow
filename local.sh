#!/bin/bash

docker compose up --build -d
#HEALTH_URL="http://localhost:8080/api/v1/health"
#echo "Health URL: $HEALTH_URL"
#echo "Waiting for service to be healthy"
#until curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" | grep -q "200"; do
#  echo -n "."
#  sleep 1
#done
#echo "service healthy"