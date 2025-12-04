# syntax=docker/dockerfile:1.4
FROM python:3.11-slim

WORKDIR /app

# Install minimal system dependencies (cleanup to keep the image small)
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install with BuildKit cache mount for faster rebuilds
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt

# Copy only the application code
COPY app/ ./app/

# Create a non-root user for better security and lower risk when running containers
RUN addgroup --system app \
    && adduser --system --ingroup app app \
    && chown -R app:app /app

USER app

# Expose the application port
EXPOSE 8000

# Start the service
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
