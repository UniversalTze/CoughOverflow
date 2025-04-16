#!/bin/bash

export DOCKER_BUILDKIT=1
terraform init

terraform apply -auto-approve

until curl -s -o /dev/null -w "%{http_code}" "$(cat ./api.txt)/health" | grep -q "200"; 
do echo "waiting for api to be ready..." && sleep 20; done && echo "API active"

# echo "$(cat ./api.txt)/health"
