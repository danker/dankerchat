"""
Contract tests for GET /api/users/me endpoint.

These tests verify current user profile API contract.
CRITICAL: These tests MUST FAIL initially (RED phase of TDD)
"""

import pytest
import json


class TestUsersMeContract:
    """Contract tests for current user profile endpoint."""

    def test_users_me_authenticated_returns_200(self, client, auth_headers):
        """Test GET /api/users/me returns 200 with valid auth."""
        # Act
        response = client.get(
            "/api/v1/users/me",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Contract validation: User object schema
        assert "id" in data
        assert "username" in data
        assert "display_name" in data
        assert "email" in data
        assert "is_active" in data
        assert "created_at" in data
        assert "last_seen" in data
        assert "role" in data
        
        # Role object validation
        role = data["role"]
        assert "id" in role
        assert "name" in role
        assert "description" in role
        assert "permissions" in role

    def test_users_me_unauthenticated_returns_401(self, client):
        """Test GET /api/users/me returns 401 without auth."""
        # Act
        response = client.get("/api/v1/users/me")
        
        # Assert
        assert response.status_code == 401

    def test_users_me_invalid_token_returns_401(self, client):
        """Test GET /api/users/me returns 401 with invalid token."""
        # Arrange
        headers = {"Authorization": "Bearer invalid_token"}
        
        # Act
        response = client.get(
            "/api/v1/users/me",
            headers=headers
        )
        
        # Assert
        assert response.status_code == 401

    def test_users_me_expired_token_returns_401(self, client, expired_token):
        """Test GET /api/users/me returns 401 with expired token."""
        # Arrange
        headers = {"Authorization": f"Bearer {expired_token}"}
        
        # Act
        response = client.get(
            "/api/v1/users/me",
            headers=headers
        )
        
        # Assert
        assert response.status_code == 401