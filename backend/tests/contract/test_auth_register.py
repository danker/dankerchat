"""
Contract tests for POST /api/auth/register endpoint.

These tests verify user registration API contract.
CRITICAL: These tests MUST FAIL initially (RED phase of TDD)
"""

import pytest
import json


class TestAuthRegisterContract:
    """Contract tests for user registration endpoint."""

    def test_register_successful_with_valid_data(self, client):
        """Test POST /api/auth/register creates user and returns 201."""
        # Arrange
        payload = {
            "username": "newuser",
            "password": "newpassword123",
            "email": "newuser@example.com",
            "display_name": "New User"
        }
        
        # Act
        response = client.post(
            "/api/v1/auth/register",
            json=payload,
            content_type="application/json"
        )
        
        # Assert
        assert response.status_code == 201
        data = json.loads(response.data)
        
        # Contract validation: Response should contain user object
        assert "id" in data
        assert "username" in data
        assert data["username"] == "newuser"
        assert "display_name" in data
        assert "email" in data
        assert "is_active" in data
        assert "created_at" in data

    def test_register_username_already_exists_returns_409(self, client):
        """Test POST /api/auth/register returns 409 for duplicate username."""
        # Arrange
        payload = {
            "username": "existinguser",
            "password": "password123",
            "email": "user@example.com"
        }
        
        # Create user first
        client.post("/api/v1/auth/register", json=payload)
        
        # Try to create same username again
        duplicate_payload = {
            "username": "existinguser",  # Same username
            "password": "differentpass123",
            "email": "different@example.com"
        }
        
        # Act
        response = client.post(
            "/api/v1/auth/register",
            json=duplicate_payload,
            content_type="application/json"
        )
        
        # Assert
        assert response.status_code == 409

    def test_register_missing_username_returns_400(self, client):
        """Test POST /api/auth/register returns 400 when username missing."""
        # Arrange
        payload = {
            "password": "password123",
            "email": "user@example.com"
        }
        
        # Act
        response = client.post(
            "/api/v1/auth/register",
            json=payload,
            content_type="application/json"
        )
        
        # Assert
        assert response.status_code == 400

    def test_register_missing_password_returns_400(self, client):
        """Test POST /api/auth/register returns 400 when password missing."""
        # Arrange
        payload = {
            "username": "newuser",
            "email": "user@example.com"
        }
        
        # Act
        response = client.post(
            "/api/v1/auth/register",
            json=payload,
            content_type="application/json"
        )
        
        # Assert
        assert response.status_code == 400

    def test_register_password_too_short_returns_400(self, client):
        """Test POST /api/auth/register returns 400 when password < 8 chars."""
        # Arrange
        payload = {
            "username": "newuser",
            "password": "short",  # Too short (min 8 per contract)
            "email": "user@example.com"
        }
        
        # Act
        response = client.post(
            "/api/v1/auth/register",
            json=payload,
            content_type="application/json"
        )
        
        # Assert
        assert response.status_code == 400

    def test_register_invalid_email_returns_400(self, client):
        """Test POST /api/auth/register returns 400 with invalid email format."""
        # Arrange
        payload = {
            "username": "newuser",
            "password": "password123",
            "email": "invalid-email"  # Invalid format
        }
        
        # Act
        response = client.post(
            "/api/v1/auth/register",
            json=payload,
            content_type="application/json"
        )
        
        # Assert
        assert response.status_code == 400