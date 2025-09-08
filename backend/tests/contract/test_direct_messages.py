"""
Contract tests for POST /api/conversations/{user_id}/messages endpoint.

These tests verify direct messaging API contract.
CRITICAL: These tests MUST FAIL initially (RED phase of TDD)
"""

import pytest
import json
import uuid


class TestDirectMessagesContract:
    """Contract tests for direct message sending endpoint."""

    def test_send_direct_message_successful_returns_201(self, client, auth_headers):
        """Test POST /api/conversations/{user_id}/messages creates message and returns 201."""
        # Arrange
        recipient_id = str(uuid.uuid4())
        payload = {
            "content": "Hello, this is a direct message!"
        }
        
        # Act
        response = client.post(
            f"/api/v1/conversations/{recipient_id}/messages",
            json=payload,
            headers=auth_headers,
            content_type="application/json"
        )
        
        # Assert
        assert response.status_code == 201
        data = json.loads(response.data)
        
        # Contract validation: Message object schema
        assert "id" in data
        assert "content" in data
        assert data["content"] == "Hello, this is a direct message!"
        assert "sender" in data
        assert "created_at" in data
        assert "message_type" in data
        
        # Sender object validation
        sender = data["sender"]
        assert "id" in sender
        assert "username" in sender
        assert "display_name" in sender

    def test_send_direct_message_to_nonexistent_user_returns_404(self, client, auth_headers):
        """Test POST /api/conversations/{user_id}/messages returns 404 for nonexistent user."""
        # Arrange
        nonexistent_user_id = str(uuid.uuid4())
        payload = {
            "content": "Message to nobody"
        }
        
        # Act
        response = client.post(
            f"/api/v1/conversations/{nonexistent_user_id}/messages",
            json=payload,
            headers=auth_headers,
            content_type="application/json"
        )
        
        # Assert
        assert response.status_code == 404

    def test_send_direct_message_missing_content_returns_400(self, client, auth_headers):
        """Test POST /api/conversations/{user_id}/messages returns 400 when content missing."""
        # Arrange
        recipient_id = str(uuid.uuid4())
        payload = {}  # Missing required content field
        
        # Act
        response = client.post(
            f"/api/v1/conversations/{recipient_id}/messages",
            json=payload,
            headers=auth_headers,
            content_type="application/json"
        )
        
        # Assert
        assert response.status_code == 400

    def test_send_direct_message_empty_content_returns_400(self, client, auth_headers):
        """Test POST /api/conversations/{user_id}/messages returns 400 for empty content."""
        # Arrange
        recipient_id = str(uuid.uuid4())
        payload = {
            "content": ""  # Empty content (min 1 char per contract)
        }
        
        # Act
        response = client.post(
            f"/api/v1/conversations/{recipient_id}/messages",
            json=payload,
            headers=auth_headers,
            content_type="application/json"
        )
        
        # Assert
        assert response.status_code == 400

    def test_send_direct_message_content_too_long_returns_400(self, client, auth_headers):
        """Test POST /api/conversations/{user_id}/messages returns 400 for content > 5000 chars."""
        # Arrange
        recipient_id = str(uuid.uuid4())
        payload = {
            "content": "a" * 5001  # Too long (max 5000 per contract)
        }
        
        # Act
        response = client.post(
            f"/api/v1/conversations/{recipient_id}/messages",
            json=payload,
            headers=auth_headers,
            content_type="application/json"
        )
        
        # Assert
        assert response.status_code == 400

    def test_send_direct_message_unauthenticated_returns_401(self, client):
        """Test POST /api/conversations/{user_id}/messages returns 401 without auth."""
        # Arrange
        recipient_id = str(uuid.uuid4())
        payload = {
            "content": "Unauthorized message"
        }
        
        # Act
        response = client.post(
            f"/api/v1/conversations/{recipient_id}/messages",
            json=payload,
            content_type="application/json"
        )
        
        # Assert
        assert response.status_code == 401

    def test_send_direct_message_invalid_user_id_returns_400(self, client, auth_headers):
        """Test POST /api/conversations/{user_id}/messages returns 400 for invalid UUID."""
        # Arrange
        payload = {
            "content": "Message with invalid recipient ID"
        }
        
        # Act
        response = client.post(
            "/api/v1/conversations/invalid-uuid/messages",
            json=payload,
            headers=auth_headers,
            content_type="application/json"
        )
        
        # Assert
        assert response.status_code == 400

    def test_send_direct_message_to_self_allowed(self, client, auth_headers):
        """Test POST /api/conversations/{user_id}/messages allows sending to self."""
        # Note: Some chat systems allow users to send messages to themselves
        # This test verifies the contract allows it (implementation decides behavior)
        # Arrange
        self_user_id = str(uuid.uuid4())  # Would be current user's ID
        payload = {
            "content": "Note to self"
        }
        
        # Act
        response = client.post(
            f"/api/v1/conversations/{self_user_id}/messages",
            json=payload,
            headers=auth_headers,
            content_type="application/json"
        )
        
        # Assert - Should not be forbidden by contract (404 if user not found is fine)
        assert response.status_code in [201, 404]  # Not 403 (forbidden)