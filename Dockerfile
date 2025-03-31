FROM python:latest

# path for project and pipx for additional package managers. 
RUN apt-get update && apt-get install -y pipx
RUN pipx ensurepath 
# Install poetry
RUN pipx install poetry

# Setting the working directory
# It changes the default directory where commands run inside the container.
# If the directory does not exist, Docker creates it.
WORKDIR /app

# Install poetry dependencies
COPY pyproject.toml ./
RUN pipx run poetry install --no-root

# Copying our application into the container
COPY app_cough app_cough

CMD ["pipx", "run", "poetry", "run", "uvicorn", "app_cough.main:app", \
    "--host", "0.0.0.0", "--port", "6400"]

