from fastapi import FastAPI
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
app.include_router(auth_router.router, prefix="/auth", tags=["auth"])


@app.get("/")
async def root():
    return {"message": "Auth service is running"}
