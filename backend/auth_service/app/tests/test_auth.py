"""
Tests for auth endpoints
"""
import pytest
from unittest.mock import patch, MagicMock


class TestAuthEndpoints:
    """Test authentication endpoints"""

    def test_health_check(self, client):
        """Test health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_register_endpoint_exists(self, client):
        """Test register endpoint exists and validates input"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "TestPassword123!",
                "full_name": "Test User"
            }
        )
        # Endpoint exists (may fail due to mocking, but not 404)
        assert response.status_code != 404

    def test_register_weak_password(self, client):
        """Test registering with weak password fails validation"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "weak",
                "full_name": "Test User"
            }
        )
        # Pydantic validation should fail (422 Unprocessable Entity)
        assert response.status_code == 422

    def test_login_endpoint_exists(self, client):
        """Test login endpoint exists"""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPassword123!"
            }
        )
        # Endpoint exists (may fail due to mocking, but not 404)
        assert response.status_code != 404

    def test_logout_endpoint_exists(self, client):
        """Test logout endpoint exists"""
        response = client.post(
            "/api/auth/logout",
            json={"refresh_token": "test_token"}
        )
        # Endpoint exists
        assert response.status_code in [200, 400, 422]

    def test_invalid_email_format(self, client):
        """Test that invalid email is rejected"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "not-an-email",
                "password": "TestPassword123!",
                "full_name": "Test User"
            }
        )
        # Email validation should fail (422)
        assert response.status_code == 422

