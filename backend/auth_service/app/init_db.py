from app.database import Base, engine
from app.models import *
from app.services.user_store import create_test_user

Base.metadata.create_all(bind=engine)

# create a default local test user if missing
create_test_user()
