"""
Contract tests for POST /api/channels endpoint.

These tests verify channel creation API contract.
CRITICAL: These tests MUST FAIL initially (RED phase of TDD)
"""

import pytest
import json


class TestChannelsPostContract:
    """Contract tests for channel creation endpoint."""

    def test_create_channel_successful_returns_201(self, client, auth_headers):
        """Test POST /api/channels creates channel and returns 201."""
        # Arrange
        payload = {
            "name": "general-chat",
            "display_name": "General Chat",
            "description": "General discussion channel",
            "is_private": False,
            "max_members": 100
        }
        
        # Act
        response = client.post(
            "/api/v1/channels",
            json=payload,
            headers=auth_headers,
            content_type="application/json"
        )
        
        # Assert
        assert response.status_code == 201
        data = json.loads(response.data)
        
        # Contract validation: Channel object schema
        assert "id" in data
        assert "name" in data
        assert data["name"] == "general-chat"
        assert "display_name" in data
        assert "description" in data
        assert "is_private" in data
        assert "is_archived" in data
        assert "max_members" in data
        assert "member_count" in data
        assert "created_at" in data
        assert "created_by" in data

    def test_create_channel_missing_name_returns_400(self, client, auth_headers):
        """Test POST /api/channels returns 400 when name missing."""
        # Arrange
        payload = {
            "display_name": "Test Channel",
            "description": "A test channel"
        }
        
        # Act
        response = client.post(
            "/api/v1/channels",
            json=payload,
            headers=auth_headers,
            content_type="application/json"
        )
        
        # Assert
        assert response.status_code == 400

    def test_create_channel_invalid_name_pattern_returns_400(self, client, auth_headers):
        """Test POST /api/channels returns 400 for invalid name pattern."""
        # Arrange
        payload = {
            "name": "Invalid Name!",  # Contains invalid chars (contract: ^[a-z0-9-]+$)
            "display_name": "Invalid Channel"
        }
        
        # Act
        response = client.post(
            "/api/v1/channels",
            json=payload,
            headers=auth_headers,
            content_type="application/json"
        )
        
        # Assert
        assert response.status_code == 400

    def test_create_channel_name_too_short_returns_400(self, client, auth_headers):
        """Test POST /api/channels returns 400 when name < 3 chars."""
        # Arrange
        payload = {
            "name": "ab",  # Too short (min 3 per contract)
            "display_name": "Short Channel"
        }
        
        # Act
        response = client.post(
            "/api/v1/channels",
            json=payload,
            headers=auth_headers,
            content_type="application/json"
        )
        
        # Assert
        assert response.status_code == 400

    def test_create_channel_name_too_long_returns_400(self, client, auth_headers):
        """Test POST /api/channels returns 400 when name > 50 chars."""
        # Arrange
        payload = {
            "name": "a" * 51,  # Too long (max 50 per contract)
            "display_name": "Long Channel"
        }
        
        # Act
        response = client.post(
            "/api/v1/channels",
            json=payload,
            headers=auth_headers,
            content_type="application/json"
        )
        
        # Assert
        assert response.status_code == 400

    def test_create_channel_duplicate_name_returns_409(self, client, auth_headers):
        """Test POST /api/channels returns 409 for duplicate channel name."""
        # Arrange
        payload = {
            "name": "duplicate-channel",
            "display_name": "Duplicate Channel"
        }
        
        # Create channel first
        client.post("/api/v1/channels", json=payload, headers=auth_headers)
        
        # Try to create same name again
        # Act
        response = client.post(
            "/api/v1/channels",
            json=payload,
            headers=auth_headers,
            content_type="application/json"
        )
        
        # Assert
        assert response.status_code == 409

    def test_create_channel_unauthenticated_returns_401(self, client):
        """Test POST /api/channels returns 401 without auth."""
        # Arrange
        payload = {
            "name": "test-channel",
            "display_name": "Test Channel"
        }
        
        # Act
        response = client.post(
            "/api/v1/channels",
            json=payload,
            content_type="application/json"
        )
        
        # Assert
        assert response.status_code == 401

    def test_create_channel_max_members_below_minimum_returns_400(self, client, auth_headers):
        """Test POST /api/channels returns 400 when max_members < 2."""
        # Arrange
        payload = {
            "name": "small-channel",
            "display_name": "Small Channel",
            "max_members": 1  # Below minimum (2 per contract)
        }
        
        # Act
        response = client.post(
            "/api/v1/channels",
            json=payload,
            headers=auth_headers,
            content_type="application/json"
        )
        
        # Assert
        assert response.status_code == 400

    def test_create_channel_max_members_above_maximum_returns_400(self, client, auth_headers):
        """Test POST /api/channels returns 400 when max_members > 200."""
        # Arrange
        payload = {
            "name": "huge-channel",
            "display_name": "Huge Channel",
            "max_members": 201  # Above maximum (200 per contract)
        }
        
        # Act
        response = client.post(
            "/api/v1/channels",
            json=payload,
            headers=auth_headers,
            content_type="application/json"
        )
        
        # Assert
        assert response.status_code == 400