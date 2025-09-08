"""
Integration tests for direct messaging flow.

Tests the end-to-end direct messaging workflow including:
- Direct conversation initiation
- Message sending and receiving
- Conversation history
- Unread message tracking

CRITICAL: These tests MUST FAIL initially (RED phase of TDD)
"""

import pytest
import json


@pytest.mark.integration
class TestDirectMessagingFlow:
    """Integration tests for direct messaging workflow."""

    def test_complete_direct_messaging_flow(self, client):
        """Test complete direct messaging conversation between two users."""
        # Arrange - Create two users
        user1_data = {
            "username": "sender",
            "password": "password123",
            "email": "sender@example.com"
        }
        
        user2_data = {
            "username": "receiver",
            "password": "password123",
            "email": "receiver@example.com"
        }
        
        # Register both users
        register1 = client.post("/api/v1/auth/register", json=user1_data, content_type="application/json")
        register2 = client.post("/api/v1/auth/register", json=user2_data, content_type="application/json")
        
        assert register1.status_code == 201
        assert register2.status_code == 201
        
        user1_id = json.loads(register1.data)["id"]
        user2_id = json.loads(register2.data)["id"]
        
        # Login both users
        login1 = client.post("/api/v1/auth/login",
                           json={"username": "sender", "password": "password123"},
                           content_type="application/json")
        login2 = client.post("/api/v1/auth/login",
                           json={"username": "receiver", "password": "password123"},
                           content_type="application/json")
        
        user1_token = json.loads(login1.data)["access_token"]
        user2_token = json.loads(login2.data)["access_token"]
        
        headers1 = {"Authorization": f"Bearer {user1_token}"}
        headers2 = {"Authorization": f"Bearer {user2_token}"}
        
        # Act - Step 1: User1 sends first direct message to User2
        message1_data = {"content": "Hey there! How are you doing?"}
        
        send1_response = client.post(
            f"/api/v1/conversations/{user2_id}/messages",
            json=message1_data,
            headers=headers1,
            content_type="application/json"
        )
        
        # Assert - First message sent successfully
        assert send1_response.status_code == 201
        message1_info = json.loads(send1_response.data)
        
        assert message1_info["content"] == "Hey there! How are you doing?"
        assert message1_info["sender"]["username"] == "sender"
        
        # Act - Step 2: User2 checks their conversations list
        conversations2_response = client.get("/api/v1/conversations", headers=headers2)
        
        # Assert - User2 sees conversation with User1
        assert conversations2_response.status_code == 200
        conversations2_data = json.loads(conversations2_response.data)
        
        conversations = conversations2_data["conversations"]
        assert len(conversations) == 1
        
        conversation = conversations[0]
        assert conversation["other_user"]["username"] == "sender"
        assert conversation["last_message"]["content"] == "Hey there! How are you doing?"
        assert conversation["unread_count"] > 0  # Should have unread messages
        
        # Act - Step 3: User2 replies to the message
        reply_data = {"content": "Hi! I'm doing great, thanks for asking!"}
        
        reply_response = client.post(
            f"/api/v1/conversations/{user1_id}/messages",
            json=reply_data,
            headers=headers2,
            content_type="application/json"
        )
        
        # Assert - Reply sent successfully
        assert reply_response.status_code == 201
        reply_info = json.loads(reply_response.data)
        
        assert reply_info["content"] == "Hi! I'm doing great, thanks for asking!"
        assert reply_info["sender"]["username"] == "receiver"
        
        # Act - Step 4: User1 checks their conversations (should now see the reply)
        conversations1_response = client.get("/api/v1/conversations", headers=headers1)
        
        # Assert - User1 sees updated conversation
        assert conversations1_response.status_code == 200
        conversations1_data = json.loads(conversations1_response.data)
        
        conversations = conversations1_data["conversations"]
        assert len(conversations) == 1
        
        conversation = conversations[0]
        assert conversation["other_user"]["username"] == "receiver"
        assert conversation["last_message"]["content"] == "Hi! I'm doing great, thanks for asking!"
        
        # Act - Step 5: Both users retrieve full message history
        history1_response = client.get(f"/api/v1/conversations/{user2_id}/messages", headers=headers1)
        history2_response = client.get(f"/api/v1/conversations/{user1_id}/messages", headers=headers2)
        
        # Assert - Both users see complete conversation history
        assert history1_response.status_code == 200
        assert history2_response.status_code == 200
        
        history1_data = json.loads(history1_response.data)
        history2_data = json.loads(history2_response.data)
        
        # Both should see the same 2 messages
        assert len(history1_data["messages"]) == 2
        assert len(history2_data["messages"]) == 2
        
        # Messages should be in chronological order
        messages1 = history1_data["messages"]
        assert messages1[0]["content"] == "Hey there! How are you doing?"
        assert messages1[1]["content"] == "Hi! I'm doing great, thanks for asking!"

    def test_direct_message_to_nonexistent_user(self, client):
        """Test that sending direct messages to nonexistent users fails gracefully."""
        # Arrange - Create one user
        user_data = {
            "username": "lonely_user",
            "password": "password123",
            "email": "lonely@example.com"
        }
        
        client.post("/api/v1/auth/register", json=user_data, content_type="application/json")
        
        login_response = client.post("/api/v1/auth/login",
                                   json={"username": "lonely_user", "password": "password123"},
                                   content_type="application/json")
        
        token = json.loads(login_response.data)["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Act - Try to send message to nonexistent user
        fake_user_id = "00000000-0000-0000-0000-000000000000"
        message_data = {"content": "Message to nobody"}
        
        response = client.post(
            f"/api/v1/conversations/{fake_user_id}/messages",
            json=message_data,
            headers=headers,
            content_type="application/json"
        )
        
        # Assert - Request fails appropriately
        assert response.status_code == 404

    def test_direct_message_conversation_privacy(self, client):
        """Test that direct message conversations are private between participants."""
        # Arrange - Create three users
        users = []
        tokens = []
        headers = []
        
        for username in ["user_a", "user_b", "user_c"]:
            user_data = {
                "username": username,
                "password": "password123",
                "email": f"{username}@example.com"
            }
            
            register_response = client.post("/api/v1/auth/register", json=user_data, content_type="application/json")
            user_info = json.loads(register_response.data)
            users.append(user_info)
            
            login_response = client.post("/api/v1/auth/login",
                                       json={"username": username, "password": "password123"},
                                       content_type="application/json")
            token = json.loads(login_response.data)["access_token"]
            tokens.append(token)
            headers.append({"Authorization": f"Bearer {token}"})
        
        user_a, user_b, user_c = users
        headers_a, headers_b, headers_c = headers
        
        # Act - Step 1: User A sends private message to User B
        private_message = {"content": "This is a private message between A and B"}
        
        message_response = client.post(
            f"/api/v1/conversations/{user_b['id']}/messages",
            json=private_message,
            headers=headers_a,
            content_type="application/json"
        )
        
        assert message_response.status_code == 201
        
        # Act - Step 2: User C tries to access the conversation between A and B
        # This should fail as User C is not a participant
        
        # Try to read A's messages with B using C's credentials
        unauthorized_read = client.get(
            f"/api/v1/conversations/{user_a['id']}/messages",
            headers=headers_c
        )
        
        # Assert - User C cannot access A-B conversation
        # This might return 404 (not found) or 403 (forbidden) or empty results
        assert unauthorized_read.status_code in [403, 404] or \
               len(json.loads(unauthorized_read.data).get("messages", [])) == 0
        
        # Act - Step 3: Verify User B can see the message from A
        conversation_history = client.get(
            f"/api/v1/conversations/{user_a['id']}/messages",
            headers=headers_b
        )
        
        # Assert - User B can access their conversation with A
        assert conversation_history.status_code == 200
        history_data = json.loads(conversation_history.data)
        
        messages = history_data["messages"]
        assert len(messages) == 1
        assert messages[0]["content"] == "This is a private message between A and B"
        
        # Act - Step 4: Verify User C's conversations list doesn't include A-B conversation
        c_conversations = client.get("/api/v1/conversations", headers=headers_c)
        assert c_conversations.status_code == 200
        
        c_conversations_data = json.loads(c_conversations.data)
        assert len(c_conversations_data["conversations"]) == 0  # C has no conversations

    def test_direct_message_unread_count_tracking(self, client):
        """Test that unread message counts are tracked correctly."""
        # Arrange - Create two users
        user1_data = {"username": "reader", "password": "password123", "email": "reader@example.com"}
        user2_data = {"username": "writer", "password": "password123", "email": "writer@example.com"}
        
        # Register and login both users
        register1 = client.post("/api/v1/auth/register", json=user1_data, content_type="application/json")
        register2 = client.post("/api/v1/auth/register", json=user2_data, content_type="application/json")
        
        user1_id = json.loads(register1.data)["id"]
        user2_id = json.loads(register2.data)["id"]
        
        login1 = client.post("/api/v1/auth/login", json={"username": "reader", "password": "password123"}, content_type="application/json")
        login2 = client.post("/api/v1/auth/login", json={"username": "writer", "password": "password123"}, content_type="application/json")
        
        reader_token = json.loads(login1.data)["access_token"]
        writer_token = json.loads(login2.data)["access_token"]
        
        reader_headers = {"Authorization": f"Bearer {reader_token}"}
        writer_headers = {"Authorization": f"Bearer {writer_token}"}
        
        # Act - Step 1: Writer sends multiple messages to Reader
        messages = [
            "First unread message",
            "Second unread message", 
            "Third unread message"
        ]
        
        for content in messages:
            response = client.post(
                f"/api/v1/conversations/{user1_id}/messages",
                json={"content": content},
                headers=writer_headers,
                content_type="application/json"
            )
            assert response.status_code == 201
        
        # Act - Step 2: Reader checks conversations list
        conversations_response = client.get("/api/v1/conversations", headers=reader_headers)
        assert conversations_response.status_code == 200
        
        conversations_data = json.loads(conversations_response.data)
        conversation = conversations_data["conversations"][0]
        
        # Assert - Unread count reflects the 3 messages
        assert conversation["unread_count"] == 3
        assert conversation["other_user"]["username"] == "writer"
        
        # Act - Step 3: Reader reads the messages (this should mark them as read)
        read_messages_response = client.get(
            f"/api/v1/conversations/{user2_id}/messages",
            headers=reader_headers
        )
        
        assert read_messages_response.status_code == 200
        
        # Act - Step 4: Reader checks conversations again
        updated_conversations_response = client.get("/api/v1/conversations", headers=reader_headers)
        assert updated_conversations_response.status_code == 200
        
        updated_conversations_data = json.loads(updated_conversations_response.data)
        updated_conversation = updated_conversations_data["conversations"][0]
        
        # Assert - Unread count should be 0 after reading
        assert updated_conversation["unread_count"] == 0

    def test_direct_message_pagination_and_history(self, client):
        """Test direct message history pagination and ordering."""
        # Arrange - Create two users
        user1_data = {"username": "historian", "password": "password123", "email": "historian@example.com"}
        user2_data = {"username": "archivist", "password": "password123", "email": "archivist@example.com"}
        
        register1 = client.post("/api/v1/auth/register", json=user1_data, content_type="application/json")
        register2 = client.post("/api/v1/auth/register", json=user2_data, content_type="application/json")
        
        user1_id = json.loads(register1.data)["id"]
        user2_id = json.loads(register2.data)["id"]
        
        login1 = client.post("/api/v1/auth/login", json={"username": "historian", "password": "password123"}, content_type="application/json")
        login2 = client.post("/api/v1/auth/login", json={"username": "archivist", "password": "password123"}, content_type="application/json")
        
        token1 = json.loads(login1.data)["access_token"]
        token2 = json.loads(login2.data)["access_token"]
        
        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        # Act - Step 1: Send many messages back and forth
        messages_to_send = [
            (headers1, user2_id, "Message 1 from historian"),
            (headers2, user1_id, "Message 2 from archivist"),
            (headers1, user2_id, "Message 3 from historian"),
            (headers2, user1_id, "Message 4 from archivist"),
            (headers1, user2_id, "Message 5 from historian"),
            (headers2, user1_id, "Message 6 from archivist"),
        ]
        
        sent_messages = []
        for headers, recipient_id, content in messages_to_send:
            response = client.post(
                f"/api/v1/conversations/{recipient_id}/messages",
                json={"content": content},
                headers=headers,
                content_type="application/json"
            )
            assert response.status_code == 201
            sent_messages.append(json.loads(response.data))
        
        # Act - Step 2: Retrieve full message history
        full_history_response = client.get(
            f"/api/v1/conversations/{user2_id}/messages",
            headers=headers1
        )
        
        assert full_history_response.status_code == 200
        full_history = json.loads(full_history_response.data)
        
        # Assert - All messages present in correct order
        messages = full_history["messages"]
        assert len(messages) == 6
        
        # Verify chronological order (implementation may be newest-first or oldest-first)
        expected_contents = [content for _, _, content in messages_to_send]
        actual_contents = [msg["content"] for msg in messages]
        
        # Check that all expected messages are present (order may vary by implementation)
        for expected_content in expected_contents:
            assert expected_content in actual_contents
        
        # Act - Step 3: Test pagination
        paginated_response = client.get(
            f"/api/v1/conversations/{user2_id}/messages?limit=3",
            headers=headers1
        )
        
        assert paginated_response.status_code == 200
        paginated_data = json.loads(paginated_response.data)
        
        # Assert - Pagination works correctly
        assert len(paginated_data["messages"]) == 3
        assert "has_more" in paginated_data
        assert paginated_data["has_more"] is True  # Should have more messages available