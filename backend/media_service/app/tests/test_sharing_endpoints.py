import asyncio
import json
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app import database
from app.database import get_db
from app.utils.security import get_current_user_id
from app.models.share import Share, ShareLink


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def test_db_engine(tmp_path):
    # Use a file-backed SQLite database for tests and allow cross-thread access
    db_file = tmp_path / "test_db.sqlite"
    url = f"sqlite:///{db_file}"
    engine = create_engine(url, echo=False, future=True, connect_args={"check_same_thread": False})
    # Bind the application's Base to this engine
    database.engine = engine
    database.SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    # Create tables
    database.Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def override_get_db(test_db_engine):
    def _override():
        db = database.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def override_current_user():
    # Fixed user id for tests
    user_id = str(uuid.uuid4())

    async def _fake_current_user_id():
        return user_id

    app.dependency_overrides[get_current_user_id] = _fake_current_user_id
    yield user_id
    app.dependency_overrides.pop(get_current_user_id, None)


@pytest.mark.anyio
async def test_shared_with_and_by_me(override_get_db, override_current_user):
    # `override_current_user` fixture yields a string user_id (not a coroutine)
    user_id = override_current_user
    # Create some shares in DB
    db = database.SessionLocal()
    try:
        share = Share(
            file_id="file123",
            shared_by_user_id=uuid.UUID(user_id),
            shared_with_user_id=uuid.UUID(user_id),
            permission="read",
        )
        db.add(share)
        db.commit()

        # Test shared-with-me
        async with AsyncClient(app=app, base_url="http://testserver") as ac:
            r = await ac.get(f"/media/users/{user_id}/files/shared-with-me")
            assert r.status_code == 200
            data = r.json()
            assert isinstance(data, list)
            assert any(item.get("file_id") == "file123" for item in data)

        # Test shared-by-me
        async with AsyncClient(app=app, base_url="http://testserver") as ac:
            r = await ac.get(f"/media/users/{user_id}/files/shared-by-me")
            assert r.status_code == 200
            data = r.json()
            assert isinstance(data, list)
            assert any(item.get("file_id") == "file123" for item in data)
    finally:
        db.close()


@pytest.mark.anyio
async def test_share_links_and_access(override_get_db, override_current_user):
    # `override_current_user` fixture yields a string user_id (not a coroutine)
    user_id = override_current_user
    db = database.SessionLocal()
    try:
        token = "tokentest123"
        link = ShareLink(
            file_id="file_link_1",
            created_by_user_id=uuid.UUID(user_id),
            token=token,
            max_downloads=0,
            downloads_used=0,
            active=True,
        )
        db.add(link)
        db.commit()

        async with AsyncClient(app=app, base_url="http://testserver") as ac:
            # debug endpoint
            r = await ac.get(f"/media/s/{token}/debug")
            assert r.status_code == 200
            data = r.json()
            assert data.get("token") == token

            # access (GET) should redirect to download URL
            r = await ac.get(f"/media/s/{token}/access", follow_redirects=False)
            assert r.status_code in (307, 302)
    finally:
        db.close()
