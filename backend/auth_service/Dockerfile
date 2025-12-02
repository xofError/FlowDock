# syntax=docker/dockerfile:1.4
FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install with BuildKit cache mount for faster rebuilds
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt

# Copy only the application folder to keep context small
COPY app/ ./app/

# Create non-root user and give ownership of the app directory
RUN addgroup --system app \
	&& adduser --system --ingroup app app \
	&& chown -R app:app /app

USER app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
