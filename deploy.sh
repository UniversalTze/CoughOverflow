#!/bin/bash

terraform destroy -auto-approve

terraform init

terraform apply -auto-approve
