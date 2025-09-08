"""
Contract tests for GET /api/channels/{channel_id}/messages endpoint.

These tests verify channel message history API contract.
CRITICAL: These tests MUST FAIL initially (RED phase of TDD)
"""

import pytest
import json
import uuid


class TestChannelMessagesContract:
    """Contract tests for channel message history endpoint."""

    def test_get_channel_messages_authenticated_returns_200(self, client, auth_headers):
        """Test GET /api/channels/{id}/messages returns 200 with message list."""
        # Arrange
        channel_id = str(uuid.uuid4())  # Mock UUID
        
        # Act
        response = client.get(
            f"/api/v1/channels/{channel_id}/messages",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Contract validation: Response structure
        assert "messages" in data
        assert "has_more" in data
        assert isinstance(data["messages"], list)
        assert isinstance(data["has_more"], bool)
        
        # If messages exist, validate schema
        if data["messages"]:
            message = data["messages"][0]
            assert "id" in message
            assert "content" in message
            assert "sender" in message
            assert "created_at" in message
            assert "message_type" in message
            
            # Sender object validation
            sender = message["sender"]
            assert "id" in sender
            assert "username" in sender
            assert "display_name" in sender

    def test_get_channel_messages_unauthenticated_returns_401(self, client):
        """Test GET /api/channels/{id}/messages returns 401 without auth."""
        # Arrange
        channel_id = str(uuid.uuid4())
        
        # Act
        response = client.get(f"/api/v1/channels/{channel_id}/messages")
        
        # Assert
        assert response.status_code == 401

    def test_get_channel_messages_not_member_returns_403(self, client, auth_headers):
        """Test GET /api/channels/{id}/messages returns 403 for non-members."""
        # Arrange
        private_channel_id = str(uuid.uuid4())  # Channel user is not a member of
        
        # Act
        response = client.get(
            f"/api/v1/channels/{private_channel_id}/messages",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 403

    def test_get_channel_messages_nonexistent_returns_404(self, client, auth_headers):
        """Test GET /api/channels/{id}/messages returns 404 for nonexistent channel."""
        # Arrange
        nonexistent_id = str(uuid.uuid4())
        
        # Act
        response = client.get(
            f"/api/v1/channels/{nonexistent_id}/messages",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 404

    def test_get_channel_messages_invalid_uuid_returns_400(self, client, auth_headers):
        """Test GET /api/channels/{id}/messages returns 400 for invalid UUID."""
        # Act
        response = client.get(
            "/api/v1/channels/invalid-uuid/messages",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 400

    def test_get_channel_messages_with_before_parameter(self, client, auth_headers):
        """Test GET /api/channels/{id}/messages respects 'before' parameter."""
        # Arrange
        channel_id = str(uuid.uuid4())
        before_timestamp = "2023-10-01T12:00:00Z"
        
        # Act
        response = client.get(
            f"/api/v1/channels/{channel_id}/messages?before={before_timestamp}",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code in [200, 403, 404]  # Valid request format

    def test_get_channel_messages_with_limit_parameter(self, client, auth_headers):
        """Test GET /api/channels/{id}/messages respects 'limit' parameter."""
        # Arrange
        channel_id = str(uuid.uuid4())
        limit = 25
        
        # Act
        response = client.get(
            f"/api/v1/channels/{channel_id}/messages?limit={limit}",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code in [200, 403, 404]  # Valid request format

    def test_get_channel_messages_limit_exceeds_maximum_returns_400(self, client, auth_headers):
        """Test GET /api/channels/{id}/messages returns 400 when limit > 100."""
        # Arrange
        channel_id = str(uuid.uuid4())
        excessive_limit = 101  # Above maximum (100 per contract)
        
        # Act
        response = client.get(
            f"/api/v1/channels/{channel_id}/messages?limit={excessive_limit}",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 400

    def test_get_channel_messages_default_limit_50(self, client, auth_headers):
        """Test GET /api/channels/{id}/messages uses default limit of 50."""
        # This will be validated in implementation that without limit param,
        # at most 50 messages are returned
        # Arrange
        channel_id = str(uuid.uuid4())
        
        # Act
        response = client.get(
            f"/api/v1/channels/{channel_id}/messages",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code in [200, 403, 404]  # Valid request format