"""
Contract tests for POST /api/auth/login endpoint.

These tests verify the API contract defined in specs/001-chat-application/contracts/rest-api.yml
CRITICAL: These tests MUST FAIL initially (RED phase of TDD)
"""

import pytest
import json
from flask import Flask


class TestAuthLoginContract:
    """Contract tests for authentication login endpoint."""

    def test_login_successful_with_valid_credentials(self, client):
        """Test POST /api/auth/login returns 200 with valid credentials."""
        # Arrange
        payload = {
            "username": "testuser",
            "password": "testpassword123"
        }
        
        # Act
        response = client.post(
            "/api/v1/auth/login",
            json=payload,
            content_type="application/json"
        )
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Contract validation: Response must contain required fields
        assert "access_token" in data
        assert "refresh_token" in data
        assert "user" in data
        assert isinstance(data["access_token"], str)
        assert isinstance(data["refresh_token"], str)
        
        # User object validation (per contract schema)
        user = data["user"]
        assert "id" in user
        assert "username" in user
        assert "display_name" in user
        assert "email" in user
        assert "is_active" in user
        assert "created_at" in user
        assert "role" in user

    def test_login_invalid_credentials_returns_401(self, client):
        """Test POST /api/auth/login returns 401 with invalid credentials."""
        # Arrange
        payload = {
            "username": "testuser",
            "password": "wrongpassword"
        }
        
        # Act
        response = client.post(
            "/api/v1/auth/login",
            json=payload,
            content_type="application/json"
        )
        
        # Assert
        assert response.status_code == 401

    def test_login_missing_username_returns_400(self, client):
        """Test POST /api/auth/login returns 400 when username missing."""
        # Arrange
        payload = {
            "password": "testpassword123"
        }
        
        # Act
        response = client.post(
            "/api/v1/auth/login",
            json=payload,
            content_type="application/json"
        )
        
        # Assert
        assert response.status_code == 400

    def test_login_missing_password_returns_400(self, client):
        """Test POST /api/auth/login returns 400 when password missing."""
        # Arrange
        payload = {
            "username": "testuser"
        }
        
        # Act
        response = client.post(
            "/api/v1/auth/login",
            json=payload,
            content_type="application/json"
        )
        
        # Assert
        assert response.status_code == 400

    def test_login_username_too_short_returns_400(self, client):
        """Test POST /api/auth/login returns 400 when username < 3 chars."""
        # Arrange
        payload = {
            "username": "ab",  # Too short (min 3 per contract)
            "password": "testpassword123"
        }
        
        # Act
        response = client.post(
            "/api/v1/auth/login",
            json=payload,
            content_type="application/json"
        )
        
        # Assert
        assert response.status_code == 400

    def test_login_username_too_long_returns_400(self, client):
        """Test POST /api/auth/login returns 400 when username > 30 chars."""
        # Arrange
        payload = {
            "username": "a" * 31,  # Too long (max 30 per contract)
            "password": "testpassword123"
        }
        
        # Act
        response = client.post(
            "/api/v1/auth/login",
            json=payload,
            content_type="application/json"
        )
        
        # Assert
        assert response.status_code == 400

    def test_login_password_too_short_returns_400(self, client):
        """Test POST /api/auth/login returns 400 when password < 8 chars."""
        # Arrange
        payload = {
            "username": "testuser",
            "password": "short"  # Too short (min 8 per contract)
        }
        
        # Act
        response = client.post(
            "/api/v1/auth/login",
            json=payload,
            content_type="application/json"
        )
        
        # Assert
        assert response.status_code == 400

    def test_login_invalid_json_returns_400(self, client):
        """Test POST /api/auth/login returns 400 with malformed JSON."""
        # Act
        response = client.post(
            "/api/v1/auth/login",
            data="invalid json",
            content_type="application/json"
        )
        
        # Assert
        assert response.status_code == 400

    def test_login_no_authentication_required(self, client):
        """Test POST /api/auth/login doesn't require authentication."""
        # This endpoint should work without Bearer token (security: [] in contract)
        # Arrange
        payload = {
            "username": "testuser",
            "password": "testpassword123"
        }
        
        # Act - No Authorization header should be fine
        response = client.post(
            "/api/v1/auth/login",
            json=payload,
            content_type="application/json"
        )
        
        # Assert - Should not return 401 due to missing auth
        # (Will return 401 only for wrong credentials)
        assert response.status_code in [200, 401, 400]  # Not 403 (forbidden)