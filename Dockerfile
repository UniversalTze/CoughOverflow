FROM ubuntu:24.04

# Install basic dependencies and Python-related dependencies
# Install dependencies.
RUN apt-get update && apt-get install -y wget python3.12 pipx steghide && rm -rf /var/lib/apt/lists/*

# Install pipx and poetry
RUN pipx ensurepath && \
    pipx install poetry

# Set the working directory
WORKDIR /app

# Install poetry dependencies
COPY pyproject.toml ./
RUN pipx run poetry install --no-root

# Copy the application code
COPY app_cough app_cough

# Updated computer architecture selection of the OverflowEngine binary.
# This appears to work on Windows, Macs, and EC2 AMD64 and ARM64 instances.
RUN ARCH=$(dpkg --print-architecture) && \
    if [ "$ARCH" = "amd64" ]; then \
        wget https://github.com/CSSE6400/CoughOverflow-Engine/releases/download/v1.0/overflowengine-amd64 -O overflowengine; \
    else \
        wget https://github.com/CSSE6400/CoughOverflow-Engine/releases/download/v1.0/overflowengine-arm64 -O overflowengine; \
    fi && \
    chmod +x overflowengine

# Define the container's command to run the app
CMD ["pipx", "run", "poetry", "run", "uvicorn", "app_cough.main:app", "--host", "0.0.0.0", "--port", "6400"]

# Use the same Ubuntu base for the final image to ensure library compatibility
#FROM python:latest

 #path for project and pipx for additional package managers. 
#RUN apt-get update && apt-get install -y pipx && \
#    pipx ensurepath && pipx install poetry

# Setting the working directory
# It changes the default directory where commands run inside the container.
# If the directory does not exist, Docker creates it.
#WORKDIR /app

# Install poetry dependencies
#COPY pyproject.toml ./
#RUN pipx run poetry install --no-root

#COPY --from=builder /overflowengine ./
# Copying our application into the container
#COPY app_cough app_cough

#ENV LD_LIBRARY_PATH=/lib/aarch64-linux-gnu:/usr/lib/aarch64-linux-gnu:$LD_LIBRARY_PATH

#CMD ["pipx", "run", "poetry", "run", "uvicorn", "app_cough.main:app", \
#    "--host", "0.0.0.0", "--port", "6400"]

