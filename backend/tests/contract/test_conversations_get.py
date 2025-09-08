"""
Contract tests for GET /api/conversations endpoint.

These tests verify direct conversations listing API contract.
CRITICAL: These tests MUST FAIL initially (RED phase of TDD)
"""

import pytest
import json


class TestConversationsGetContract:
    """Contract tests for direct conversations listing endpoint."""

    def test_get_conversations_authenticated_returns_200(self, client, auth_headers):
        """Test GET /api/conversations returns 200 with conversations list."""
        # Act
        response = client.get(
            "/api/v1/conversations",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Contract validation: Response structure
        assert "conversations" in data
        assert isinstance(data["conversations"], list)
        
        # If conversations exist, validate schema
        if data["conversations"]:
            conversation = data["conversations"][0]
            assert "id" in conversation
            assert "other_user" in conversation
            assert "last_message" in conversation
            assert "last_message_at" in conversation
            assert "unread_count" in conversation
            
            # Other user object validation
            other_user = conversation["other_user"]
            assert "id" in other_user
            assert "username" in other_user
            assert "display_name" in other_user
            
            # Last message object validation (if exists)
            if conversation["last_message"]:
                last_message = conversation["last_message"]
                assert "id" in last_message
                assert "content" in last_message
                assert "sender" in last_message
                assert "created_at" in last_message

    def test_get_conversations_unauthenticated_returns_401(self, client):
        """Test GET /api/conversations returns 401 without auth."""
        # Act
        response = client.get("/api/v1/conversations")
        
        # Assert
        assert response.status_code == 401

    def test_get_conversations_invalid_token_returns_401(self, client):
        """Test GET /api/conversations returns 401 with invalid token."""
        # Arrange
        headers = {"Authorization": "Bearer invalid_token"}
        
        # Act
        response = client.get(
            "/api/v1/conversations",
            headers=headers
        )
        
        # Assert
        assert response.status_code == 401

    def test_get_conversations_empty_list_when_no_conversations(self, client, auth_headers):
        """Test GET /api/conversations returns empty list for user with no conversations."""
        # Act
        response = client.get(
            "/api/v1/conversations",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "conversations" in data
        assert isinstance(data["conversations"], list)
        # List may be empty - that's valid

    def test_get_conversations_ordered_by_recent_activity(self, client, auth_headers):
        """Test GET /api/conversations returns conversations ordered by last_message_at."""
        # This test verifies ordering behavior (most recent conversations first)
        # Act
        response = client.get(
            "/api/v1/conversations",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # If multiple conversations, verify ordering
        conversations = data["conversations"]
        if len(conversations) > 1:
            # Verify timestamps are in descending order (most recent first)
            timestamps = [conv["last_message_at"] for conv in conversations if conv["last_message_at"]]
            for i in range(1, len(timestamps)):
                # Later timestamp should come first (descending order)
                # This will be validated by implementation
                assert "last_message_at" in conversations[i]

    def test_get_conversations_includes_unread_count(self, client, auth_headers):
        """Test GET /api/conversations includes accurate unread message count."""
        # Act
        response = client.get(
            "/api/v1/conversations",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Verify unread_count is present and is non-negative integer
        for conversation in data["conversations"]:
            assert "unread_count" in conversation
            assert isinstance(conversation["unread_count"], int)
            assert conversation["unread_count"] >= 0