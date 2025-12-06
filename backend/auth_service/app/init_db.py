"""
Database initialization script - Creates tables and test user.

Uses clean architecture services for consistency.
"""

from app.database import Base, engine, SessionLocal
from app.infrastructure.database.models import UserModel, SessionModel, RecoveryTokenModel
from app.application.user_util_service import UserUtilService
from app.infrastructure.database.repositories import PostgresUserRepository
from app.infrastructure.security.security import ArgonPasswordHasher

# Create all tables
Base.metadata.create_all(bind=engine)

# Create test user using clean architecture
db = SessionLocal()
try:
    user_repo = PostgresUserRepository(db)
    password_hasher = ArgonPasswordHasher()
    user_util_service = UserUtilService(user_repo, password_hasher)
    user_util_service.create_test_user()
finally:
    db.close()

