from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager
import os
import logging

from app.api import auth as auth_router
from app.database import Base, engine
from app.models import *
from app.services.user_store import create_test_user

logger = logging.getLogger(__name__)
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables
    Base.metadata.create_all(bind=engine)
    try:
        # create_test_user is a convenience helper for local/dev only
        create_test_user()
    except Exception as e:
        logger.warning(f"Could not create test user: {e}")
    yield
    # Shutdown: Nothing to do


app = FastAPI(title="Auth Service", lifespan=lifespan)

# Configure CORS origins via environment variable ALLOWED_ORIGINS (comma-separated)
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*")
if allowed_origins.strip() == "*":
    cors_origins = ["*"]
else:
    cors_origins = [u.strip() for u in allowed_origins.split(",") if u.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,  # In production, set this to your frontend's URL(s)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Use an environment-configured session secret; change in production
session_secret = os.getenv("SESSION_SECRET", "CHANGE_THIS_TO_A_RANDOM_SECRET")
app.add_middleware(
    SessionMiddleware,
    secret_key=session_secret,
)
app.include_router(auth_router.router, prefix="/auth", tags=["auth"])


@app.get("/")
async def root():
    return {"message": "Auth service is running"}
