# CoughOverflow
Cough Overflow is a backend webserver use to handle request. 

Tech stack includes: 
- Backend built in python using FastAPI framework.
- Docker image has been made for this webserver. (Docker.yml)
- Docker image for analysis engine was alsoc created.
- Deployed on AWS using Terraform. 

## CoughOverflow Pathogen Analysis Service

This repository contains the backend service for CoughOverflow’s Pathogen Analysis Service (PAS). The service exposes a REST API that allows pathology labs and healthcare systems to submit sample images for analysis and later retrieve the results.

The PAS acts as a scalable microservice that:

- Accepts image analysis requests via a specified REST API.
- Uses the provided `overflowengine` tool to detect COVID-19 and H5N1 (avian influenza) markers in pre-processed saliva sample images.
- Persists analysis requests and results to durable storage to prevent data loss, even in the event of service failure or restart.
- Is designed to remain responsive under varying and potentially high load, supporting both individual result queries and batched queries for labs or patients.
- Is deployable to AWS using Terraform, enabling automated provisioning and testing in a fresh cloud environment.

The overall purpose of this system is to provide a reliable, cloud-hosted analysis pipeline that can scale to epidemic-level demand, delivering timely, automated pathogen detection to support clinical decision-making and public health response.

## Repo Structure (Stage#1, Stage#2, Stage#3):
Each branch represents the code at different stages. 
### Stage 1 – Containerised Web Server

Stage 1:
- Dockerfile and associated config for building the web server image.
- Local development and testing using Docker (e.g. `docker run` / `docker-compose`).

### Stage 2 – AWS Deployment

Stage 2 is about deploying the containerised service to AWS:

- Infrastructure-as-code to provision required AWS resources (e.g. ECS/ECR, networking, etc.).
- CI/CD or deployment scripts to push the Docker image and update the running service.
- Configuration to run the web server in the cloud (environment variables, task definitions, etc.).

### Stage 3 – Optimised Deployment with Celery

Stage 3 improves scalability and responsiveness by using asynchronous task processing like queues:

- Celery worker(s) added to offload long-running analysis jobs from the web server.
- A message broker / queue (e.g. Redis or SQS) for distributing jobs to workers.
- Updated deployment so both web and worker components are managed and scaled in AWS.
- Optimised flow: web API enqueues analysis jobs, workers process them, results are stored in a postgress DB and later retrieved using API's.


