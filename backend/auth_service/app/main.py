from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager
import os
import logging

from app.presentation.api import auth as auth_router
from app.presentation.api import users as users_router
from app.database import Base, engine, SessionLocal
from app.infrastructure.database.models import UserModel, SessionModel, RecoveryTokenModel
from app.application.user_util_service import UserUtilService
from app.infrastructure.database.repositories import PostgresUserRepository
from app.infrastructure.security.security import ArgonPasswordHasher

logger = logging.getLogger(__name__)
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables
    Base.metadata.create_all(bind=engine)
    try:
        # Create test user using clean architecture service
        db = SessionLocal()
        try:
            user_repo = PostgresUserRepository(db)
            password_hasher = ArgonPasswordHasher()
            user_util_service = UserUtilService(user_repo, password_hasher)
            user_util_service.create_test_user()
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Could not create test user: {e}")
    
    yield
    # Shutdown: Nothing to do


app = FastAPI(title="Auth Service", lifespan=lifespan)

# Configure CORS origins via environment variable ALLOWED_ORIGINS (comma-separated)
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
if allowed_origins.strip() == "*":
    # When using wildcard, we can't use credentials=True (browser restriction)
    cors_origins = ["*"]
    allow_credentials = False
else:
    cors_origins = [u.strip() for u in allowed_origins.split(",") if u.strip()]
    allow_credentials = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_credentials,
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
app.include_router(users_router.router, tags=["users"])


@app.get("/")
async def root():
    return {"message": "Auth service is running"}


@app.get("/health")
async def health():
    return {"status": "ok"}