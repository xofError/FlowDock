"""
Tests for application services
"""
import pytest
from unittest.mock import MagicMock, patch


class TestStorageQuotaService:
    """Test storage quota service"""

    @patch('app.application.quota_service.StorageQuotaService')
    def test_deduct_quota_success(self, mock_quota_service):
        """Test deducting quota"""
        mock_service = MagicMock()
        mock_service.deduct_quota.return_value = True
        mock_quota_service.return_value = mock_service
        
        result = mock_service.deduct_quota("test-user-1", 100 * 1024 * 1024)
        assert result is True

    @patch('app.application.quota_service.StorageQuotaService')
    def test_deduct_quota_exceeds_limit(self, mock_quota_service):
        """Test deducting quota fails when exceeding limit"""
        mock_service = MagicMock()
        mock_service.deduct_quota.return_value = False
        mock_quota_service.return_value = mock_service
        
        result = mock_service.deduct_quota("test-user-2", 200 * 1024 * 1024)
        assert result is False

    @patch('app.application.quota_service.StorageQuotaService')
    def test_add_quota(self, mock_quota_service):
        """Test adding back quota"""
        mock_service = MagicMock()
        mock_service.add_quota.return_value = None
        mock_quota_service.return_value = mock_service
        
        mock_service.add_quota("test-user-3", 50 * 1024 * 1024)
        mock_service.add_quota.assert_called_once()

    @patch('app.application.quota_service.StorageQuotaService')
    def test_get_quota_info(self, mock_quota_service):
        """Test getting quota info"""
        mock_service = MagicMock()
        mock_service.get_quota_info.return_value = {
            "total": 1024 * 1024 * 1024,
            "used": 250 * 1024 * 1024,
            "available": 774 * 1024 * 1024,
            "percentage": 25.0
        }
        mock_quota_service.return_value = mock_service
        
        info = mock_service.get_quota_info("test-user-4")
        assert info["total"] == 1024 * 1024 * 1024
        assert info["percentage"] == 25.0


class TestAuthService:
    """Test auth service"""

    @patch('app.application.services.AuthService')
    def test_register_user(self, mock_auth_service):
        """Test user registration"""
        mock_service = MagicMock()
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_service.register_user.return_value = mock_user
        mock_auth_service.return_value = mock_service
        
        from app.application.dtos import RegisterRequestDTO
        data = RegisterRequestDTO(
            email="test@example.com",
            password="TestPassword123!",
            full_name="Test User"
        )
        user = mock_service.register_user(data)
        assert user.email == "test@example.com"

    @patch('app.application.services.AuthService')
    def test_authenticate_user(self, mock_auth_service):
        """Test user authentication"""
        mock_service = MagicMock()
        mock_user = MagicMock()
        mock_user.id = "user-123"
        mock_user.verified = True
        mock_service.authenticate_user.return_value = mock_user
        mock_auth_service.return_value = mock_service
        
        user = mock_service.authenticate_user("test@example.com", "password")
        assert user.id == "user-123"
        assert user.verified is True

    @patch('app.application.services.AuthService')
    def test_authenticate_user_fails(self, mock_auth_service):
        """Test authentication fails with wrong credentials"""
        mock_service = MagicMock()
        mock_service.authenticate_user.side_effect = ValueError("Invalid credentials")
        mock_auth_service.return_value = mock_service
        
        with pytest.raises(ValueError):
            mock_service.authenticate_user("test@example.com", "wrong_password")

