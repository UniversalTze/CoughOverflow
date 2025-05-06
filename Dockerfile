FROM python:3.12-slim

# Install basic dependencies and Python-related dependencies
# Install dependencies.
RUN apt-get update && apt-get install -y wget pip steghide && pip install pipx && rm -rf /var/lib/apt/lists/*

# Install pipx and poetry
RUN pipx ensurepath && \
    pipx install poetry

# Set the working directory
WORKDIR /app

# Install poetry dependencies
COPY pyproject.toml ./

# Create virual env inside project directory /app/.venv (instead of default global cache)
RUN poetry config virtualenvs.in-project true

# Temp pipx managed poetry instance that installs all dependencies into a persistent virtual env (/app/.venv/) due to above command
RUN poetry install --no-root

# Copy the application code
COPY app_cough app_cough

# Add .venv to PATH for runtime
ENV PATH="/app/.venv/bin:/root/.local/bin:/usr/bin:$PATH"

ENV PYTHONPATH=/app

# Define the container's command to run the app, exposing port 6400
# CMD ["pipx", "run", "poetry", "run", "uvicorn", "app_cough.main:app", "--host", "0.0.0.0", "--port", "6400"] 
CMD ["python3", "-m", "uvicorn", "app_cough.main:app", "--host", "0.0.0.0", "--port", "6400"]