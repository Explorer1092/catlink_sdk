FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy poetry files
COPY pyproject.toml poetry.lock* ./

# Install poetry and dependencies
RUN pip install --no-cache-dir poetry==1.7.1 && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi

# Copy the application code
COPY catlink_sdk/ ./catlink_sdk/
COPY example/ ./example/

# Create a non-root user
RUN useradd -m -u 1000 catlink && \
    chown -R catlink:catlink /app

USER catlink

# Default command
CMD ["python", "-m", "example.cli", "-c", "example/config.toml", "--monitor"]