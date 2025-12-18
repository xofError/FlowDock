import os
import sys
from pathlib import Path
import pytest

# Ensure minimal environment variables are set at import time so modules that
# build DB URLs at import (like `database.py`) do not fail during test
# collection. These are safe defaults for a local test run.
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("POSTGRES_DB", "test_db")
os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("MONGO_DB_NAME", "test_media")
os.environ.setdefault("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
os.environ.setdefault("RABBITMQ_QUEUE", "file_events")

# Ensure the package `app` (backend/media_service/app) is importable when tests
# are executed from the tests directory. We insert the parent directory of
# `app` (i.e. backend/media_service) onto sys.path.
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def set_env_vars(monkeypatch):
    """Allow tests to override env vars if needed via monkeypatch while
    still providing the defaults above."""
    monkeypatch.setenv("MONGO_URL", os.environ["MONGO_URL"])
    monkeypatch.setenv("MONGO_DB_NAME", os.environ["MONGO_DB_NAME"])
    monkeypatch.setenv("RABBITMQ_URL", os.environ["RABBITMQ_URL"])
    monkeypatch.setenv("RABBITMQ_QUEUE", os.environ["RABBITMQ_QUEUE"])
    monkeypatch.setenv("POSTGRES_USER", os.environ["POSTGRES_USER"])
    monkeypatch.setenv("POSTGRES_PASSWORD", os.environ["POSTGRES_PASSWORD"])
    monkeypatch.setenv("POSTGRES_HOST", os.environ["POSTGRES_HOST"])
    monkeypatch.setenv("POSTGRES_PORT", os.environ["POSTGRES_PORT"])
    monkeypatch.setenv("POSTGRES_DB", os.environ["POSTGRES_DB"])
    yield
