from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager

from app.api import auth as auth_router
from app.database import Base, engine
from app.models import *
from app.services.user_store import create_test_user


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables
    Base.metadata.create_all(bind=engine)
    create_test_user()
    yield
    # Shutdown: Nothing to do


app = FastAPI(title="Auth Service", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, set this to your frontend's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    SessionMiddleware,
    secret_key="CHANGE_THIS_TO_A_RANDOM_SECRET",  # Set to a strong random value in production
)
app.include_router(auth_router.router, prefix="/auth", tags=["auth"])


@app.get("/")
async def root():
    return {"message": "Auth service is running"}
