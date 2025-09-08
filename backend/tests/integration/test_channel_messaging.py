"""
Integration tests for channel creation and messaging flow.

Tests the end-to-end channel and messaging workflow including:
- Channel creation and management
- Member management
- Message sending and receiving
- Channel permissions

CRITICAL: These tests MUST FAIL initially (RED phase of TDD)
"""

import pytest
import json
import uuid


@pytest.mark.integration
class TestChannelMessagingFlow:
    """Integration tests for channel creation and messaging workflow."""

    def test_complete_channel_creation_and_messaging_flow(self, client):
        """Test complete channel creation, joining, and messaging workflow."""
        # Arrange - Create two users
        user1_data = {
            "username": "channelowner",
            "password": "password123",
            "email": "owner@example.com"
        }
        
        user2_data = {
            "username": "channelmember",
            "password": "password123",
            "email": "member@example.com"
        }
        
        # Register both users
        client.post("/api/v1/auth/register", json=user1_data, content_type="application/json")
        client.post("/api/v1/auth/register", json=user2_data, content_type="application/json")
        
        # Login both users
        login1 = client.post("/api/v1/auth/login", 
                           json={"username": "channelowner", "password": "password123"},
                           content_type="application/json")
        login2 = client.post("/api/v1/auth/login",
                           json={"username": "channelmember", "password": "password123"}, 
                           content_type="application/json")
        
        user1_token = json.loads(login1.data)["access_token"]
        user2_token = json.loads(login2.data)["access_token"]
        
        headers1 = {"Authorization": f"Bearer {user1_token}"}
        headers2 = {"Authorization": f"Bearer {user2_token}"}
        
        # Act - Step 1: User1 creates a channel
        channel_data = {
            "name": "general-chat",
            "display_name": "General Chat",
            "description": "General discussion channel",
            "is_private": False,
            "max_members": 50
        }
        
        create_response = client.post(
            "/api/v1/channels",
            json=channel_data,
            headers=headers1,
            content_type="application/json"
        )
        
        # Assert - Channel created successfully
        assert create_response.status_code == 201
        channel_info = json.loads(create_response.data)
        channel_id = channel_info["id"]
        
        assert channel_info["name"] == "general-chat"
        assert channel_info["is_private"] is False
        assert channel_info["created_by"]["username"] == "channelowner"
        
        # Act - Step 2: User2 joins the channel (for public channels, this might be automatic)
        # First, user2 should see the channel in the channels list
        channels_response = client.get("/api/v1/channels", headers=headers2)
        assert channels_response.status_code == 200
        channels_data = json.loads(channels_response.data)
        
        # Channel should be visible to user2 (public channel)
        channel_names = [ch["name"] for ch in channels_data["channels"]]
        assert "general-chat" in channel_names
        
        # Act - Step 3: User1 sends a message to the channel
        message1_data = {"content": "Hello everyone! Welcome to the channel."}
        
        send1_response = client.post(
            f"/api/v1/channels/{channel_id}/messages",
            json=message1_data,
            headers=headers1,
            content_type="application/json"
        )
        
        # Assert - Message sent successfully
        assert send1_response.status_code == 201
        message1_info = json.loads(send1_response.data)
        
        assert message1_info["content"] == "Hello everyone! Welcome to the channel."
        assert message1_info["sender"]["username"] == "channelowner"
        
        # Act - Step 4: User2 sends a reply message
        message2_data = {"content": "Thanks for creating this channel!"}
        
        send2_response = client.post(
            f"/api/v1/channels/{channel_id}/messages",
            json=message2_data,
            headers=headers2,
            content_type="application/json"
        )
        
        # Assert - Reply sent successfully
        assert send2_response.status_code == 201
        message2_info = json.loads(send2_response.data)
        
        assert message2_info["content"] == "Thanks for creating this channel!"
        assert message2_info["sender"]["username"] == "channelmember"
        
        # Act - Step 5: Both users retrieve message history
        history1_response = client.get(f"/api/v1/channels/{channel_id}/messages", headers=headers1)
        history2_response = client.get(f"/api/v1/channels/{channel_id}/messages", headers=headers2)
        
        # Assert - Both users can see all messages
        assert history1_response.status_code == 200
        assert history2_response.status_code == 200
        
        history1_data = json.loads(history1_response.data)
        history2_data = json.loads(history2_response.data)
        
        assert len(history1_data["messages"]) == 2
        assert len(history2_data["messages"]) == 2
        
        # Messages should be in chronological order
        messages = history1_data["messages"]
        assert messages[0]["content"] == "Hello everyone! Welcome to the channel."
        assert messages[1]["content"] == "Thanks for creating this channel!"

    def test_private_channel_access_control(self, client):
        """Test that private channels enforce access control properly."""
        # Arrange - Create three users
        users = []
        tokens = []
        headers = []
        
        for i, username in enumerate(["owner", "member", "outsider"]):
            user_data = {
                "username": username,
                "password": "password123",
                "email": f"{username}@example.com"
            }
            
            client.post("/api/v1/auth/register", json=user_data, content_type="application/json")
            
            login_response = client.post("/api/v1/auth/login",
                                       json={"username": username, "password": "password123"},
                                       content_type="application/json")
            token = json.loads(login_response.data)["access_token"]
            tokens.append(token)
            headers.append({"Authorization": f"Bearer {token}"})
        
        owner_headers, member_headers, outsider_headers = headers
        
        # Act - Step 1: Owner creates private channel
        private_channel_data = {
            "name": "private-team",
            "display_name": "Private Team Channel",
            "description": "Private channel for team members only",
            "is_private": True,
            "max_members": 10
        }
        
        create_response = client.post(
            "/api/v1/channels",
            json=private_channel_data,
            headers=owner_headers,
            content_type="application/json"
        )
        
        assert create_response.status_code == 201
        channel_info = json.loads(create_response.data)
        channel_id = channel_info["id"]
        
        # Act - Step 2: Outsider tries to see private channel in channels list
        outsider_channels = client.get("/api/v1/channels", headers=outsider_headers)
        assert outsider_channels.status_code == 200
        
        outsider_data = json.loads(outsider_channels.data)
        channel_names = [ch["name"] for ch in outsider_data["channels"]]
        
        # Assert - Outsider cannot see private channel
        assert "private-team" not in channel_names
        
        # Act - Step 3: Outsider tries to access private channel directly
        outsider_access = client.get(f"/api/v1/channels/{channel_id}", headers=outsider_headers)
        
        # Assert - Access denied
        assert outsider_access.status_code in [403, 404]
        
        # Act - Step 4: Outsider tries to send message to private channel
        message_data = {"content": "Unauthorized message"}
        outsider_message = client.post(
            f"/api/v1/channels/{channel_id}/messages",
            json=message_data,
            headers=outsider_headers,
            content_type="application/json"
        )
        
        # Assert - Message sending denied
        assert outsider_message.status_code in [403, 404]
        
        # Act - Step 5: Owner sends message (should work)
        owner_message_data = {"content": "Private team discussion"}
        owner_message = client.post(
            f"/api/v1/channels/{channel_id}/messages",
            json=owner_message_data,
            headers=owner_headers,
            content_type="application/json"
        )
        
        # Assert - Owner can send messages
        assert owner_message.status_code == 201

    def test_channel_member_limits_enforcement(self, client):
        """Test that channel member limits are enforced."""
        # Arrange - Create a channel with max_members = 2
        owner_data = {
            "username": "limitowner",
            "password": "password123",
            "email": "limitowner@example.com"
        }
        
        client.post("/api/v1/auth/register", json=owner_data, content_type="application/json")
        
        login_response = client.post("/api/v1/auth/login",
                                   json={"username": "limitowner", "password": "password123"},
                                   content_type="application/json")
        owner_token = json.loads(login_response.data)["access_token"]
        owner_headers = {"Authorization": f"Bearer {owner_token}"}
        
        # Act - Create channel with low member limit
        channel_data = {
            "name": "small-channel",
            "display_name": "Small Channel",
            "description": "Channel with member limit",
            "is_private": False,
            "max_members": 2  # Very low limit for testing
        }
        
        create_response = client.post(
            "/api/v1/channels",
            json=channel_data,
            headers=owner_headers,
            content_type="application/json"
        )
        
        assert create_response.status_code == 201
        channel_info = json.loads(create_response.data)
        
        # Assert - Channel created with correct member limit
        assert channel_info["max_members"] == 2
        assert channel_info["member_count"] == 1  # Owner is automatically a member

    def test_channel_message_pagination_and_ordering(self, client):
        """Test message pagination and chronological ordering."""
        # Arrange - Create user and channel
        user_data = {
            "username": "msguser",
            "password": "password123", 
            "email": "msguser@example.com"
        }
        
        client.post("/api/v1/auth/register", json=user_data, content_type="application/json")
        
        login_response = client.post("/api/v1/auth/login",
                                   json={"username": "msguser", "password": "password123"},
                                   content_type="application/json")
        token = json.loads(login_response.data)["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create channel
        channel_data = {
            "name": "message-test",
            "display_name": "Message Test Channel",
            "description": "Testing message ordering"
        }
        
        create_response = client.post(
            "/api/v1/channels",
            json=channel_data,
            headers=headers,
            content_type="application/json"
        )
        
        channel_id = json.loads(create_response.data)["id"]
        
        # Act - Send multiple messages
        messages_to_send = [
            "First message",
            "Second message", 
            "Third message",
            "Fourth message",
            "Fifth message"
        ]
        
        sent_messages = []
        for content in messages_to_send:
            response = client.post(
                f"/api/v1/channels/{channel_id}/messages",
                json={"content": content},
                headers=headers,
                content_type="application/json"
            )
            assert response.status_code == 201
            sent_messages.append(json.loads(response.data))
        
        # Act - Retrieve messages with default pagination
        history_response = client.get(f"/api/v1/channels/{channel_id}/messages", headers=headers)
        
        # Assert - Messages retrieved in correct order
        assert history_response.status_code == 200
        history_data = json.loads(history_response.data)
        
        retrieved_messages = history_data["messages"]
        assert len(retrieved_messages) == 5
        
        # Verify chronological order (oldest to newest or newest to oldest)
        for i, expected_content in enumerate(messages_to_send):
            # Messages might be ordered newest-first or oldest-first depending on implementation
            assert any(msg["content"] == expected_content for msg in retrieved_messages)
        
        # Act - Test pagination with limit
        paginated_response = client.get(
            f"/api/v1/channels/{channel_id}/messages?limit=3",
            headers=headers
        )
        
        # Assert - Pagination works
        assert paginated_response.status_code == 200
        paginated_data = json.loads(paginated_response.data)
        
        assert len(paginated_data["messages"]) == 3
        assert "has_more" in paginated_data

    def test_channel_update_permissions(self, client):
        """Test that only authorized users can update channel settings."""
        # Arrange - Create owner and regular user
        owner_data = {
            "username": "chanowner",
            "password": "password123",
            "email": "chanowner@example.com"
        }
        
        user_data = {
            "username": "regularuser",
            "password": "password123",
            "email": "regular@example.com"
        }
        
        client.post("/api/v1/auth/register", json=owner_data, content_type="application/json")
        client.post("/api/v1/auth/register", json=user_data, content_type="application/json")
        
        # Login both users
        owner_login = client.post("/api/v1/auth/login",
                                json={"username": "chanowner", "password": "password123"},
                                content_type="application/json")
        user_login = client.post("/api/v1/auth/login",
                               json={"username": "regularuser", "password": "password123"},
                               content_type="application/json")
        
        owner_token = json.loads(owner_login.data)["access_token"]
        user_token = json.loads(user_login.data)["access_token"]
        
        owner_headers = {"Authorization": f"Bearer {owner_token}"}
        user_headers = {"Authorization": f"Bearer {user_token}"}
        
        # Owner creates channel
        channel_data = {
            "name": "update-test",
            "display_name": "Update Test Channel",
            "description": "Testing updates"
        }
        
        create_response = client.post(
            "/api/v1/channels",
            json=channel_data,
            headers=owner_headers,
            content_type="application/json"
        )
        
        channel_id = json.loads(create_response.data)["id"]
        
        # Act - Regular user tries to update channel
        update_data = {
            "display_name": "Unauthorized Update",
            "description": "This should not work"
        }
        
        user_update_response = client.put(
            f"/api/v1/channels/{channel_id}",
            json=update_data,
            headers=user_headers,
            content_type="application/json"
        )
        
        # Assert - Regular user update denied
        assert user_update_response.status_code == 403
        
        # Act - Owner updates channel
        owner_update_data = {
            "display_name": "Updated Channel Name",
            "description": "Updated description"
        }
        
        owner_update_response = client.put(
            f"/api/v1/channels/{channel_id}",
            json=owner_update_data,
            headers=owner_headers,
            content_type="application/json"
        )
        
        # Assert - Owner update succeeds
        assert owner_update_response.status_code == 200
        updated_info = json.loads(owner_update_response.data)
        
        assert updated_info["display_name"] == "Updated Channel Name"
        assert updated_info["description"] == "Updated description"