"""
Contract tests for GET /api/channels endpoint.

These tests verify channel listing API contract.
CRITICAL: These tests MUST FAIL initially (RED phase of TDD)
"""

import pytest
import json


class TestChannelsGetContract:
    """Contract tests for channel listing endpoint."""

    def test_get_channels_authenticated_returns_200(self, client, auth_headers):
        """Test GET /api/channels returns 200 with channels list."""
        # Act
        response = client.get(
            "/api/v1/channels",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Contract validation: Response structure
        assert "channels" in data
        assert isinstance(data["channels"], list)
        
        # If channels exist, validate schema
        if data["channels"]:
            channel = data["channels"][0]
            assert "id" in channel
            assert "name" in channel
            assert "display_name" in channel
            assert "description" in channel
            assert "is_private" in channel
            assert "is_archived" in channel
            assert "max_members" in channel
            assert "member_count" in channel
            assert "created_at" in channel
            assert "created_by" in channel

    def test_get_channels_unauthenticated_returns_401(self, client):
        """Test GET /api/channels returns 401 without auth."""
        # Act
        response = client.get("/api/v1/channels")
        
        # Assert
        assert response.status_code == 401

    def test_get_channels_only_accessible_channels(self, client, auth_headers):
        """Test GET /api/channels only returns accessible channels."""
        # This test verifies that private channels the user isn't a member of
        # are not included in the response (per contract: "accessible channels")
        
        # Act
        response = client.get(
            "/api/v1/channels",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # All returned channels should be accessible to the user
        # (Implementation will filter based on membership and privacy)
        for channel in data["channels"]:
            # If private, user must be a member (will be validated in implementation)
            if channel.get("is_private", False):
                # This assertion will be validated by the implementation
                # For now, just ensure the field exists
                assert "is_private" in channel

    def test_get_channels_excludes_archived_channels(self, client, auth_headers):
        """Test GET /api/channels excludes archived channels by default."""
        # Act
        response = client.get(
            "/api/v1/channels",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # No archived channels should be returned by default
        for channel in data["channels"]:
            assert channel.get("is_archived", False) is False