"""
Fixtures for testing
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def mock_db():
    """Provide mock database session"""
    return MagicMock()


@pytest.fixture
def client(mock_db):
    """Provide test client with mocked dependencies"""
    # Mock the database before importing app
    with patch('app.database.SessionLocal', return_value=mock_db), \
         patch('app.database.Base.metadata.create_all'), \
         patch('app.database.engine'):
        
        from app.main import app
        from app.presentation.dependencies import get_db
        
        def override_get_db():
            return mock_db
        
        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)
        yield client
        app.dependency_overrides.clear()

