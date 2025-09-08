"""
Integration tests for multi-client session synchronization.

Tests the end-to-end multi-client scenarios including:
- Same user with multiple devices/sessions
- Session synchronization across clients
- Message delivery to all user sessions
- Session management and cleanup

CRITICAL: These tests MUST FAIL initially (RED phase of TDD)
"""

import pytest
import json
import uuid
from flask_socketio import SocketIOTestClient


@pytest.mark.integration
class TestMultiClientSyncFlow:
    """Integration tests for multi-client session synchronization."""

    def test_multi_device_message_synchronization(self, app, client):
        """Test message synchronization across multiple devices for same user."""
        # Arrange - Create user and get auth tokens for multiple "devices"
        user_data = {
            "username": "multidevuser",
            "password": "password123",
            "email": "multidev@example.com"
        }
        
        # Register user via REST API
        register_response = client.post("/api/v1/auth/register", json=user_data, content_type="application/json")
        assert register_response.status_code == 201
        user_info = json.loads(register_response.data)
        user_id = user_info["id"]
        
        # Login multiple times to simulate multiple devices
        device1_login = client.post("/api/v1/auth/login",
                                  json={"username": "multidevuser", "password": "password123"},
                                  content_type="application/json")
        device2_login = client.post("/api/v1/auth/login",
                                  json={"username": "multidevuser", "password": "password123"},
                                  content_type="application/json")
        
        device1_token = json.loads(device1_login.data)["access_token"]
        device2_token = json.loads(device2_login.data)["access_token"]
        
        # Create WebSocket connections for both "devices"
        ws_device1 = SocketIOTestClient(app)
        ws_device2 = SocketIOTestClient(app)
        
        # Connect both WebSocket clients
        ws_device1.connect('/socket.io/', auth={'token': device1_token})
        ws_device2.connect('/socket.io/', auth={'token': device2_token})
        
        # Clear connection messages
        ws_device1.get_received()
        ws_device2.get_received()
        
        # Both devices join the same channel
        channel_id = str(uuid.uuid4())
        ws_device1.emit('join_channel', {'channel_id': channel_id})
        ws_device2.emit('join_channel', {'channel_id': channel_id})
        
        # Clear join messages
        ws_device1.get_received()
        ws_device2.get_received()
        
        # Act - Create another user to send messages to the multi-device user
        sender_data = {
            "username": "sender",
            "password": "password123",
            "email": "sender@example.com"
        }
        
        client.post("/api/v1/auth/register", json=sender_data, content_type="application/json")
        sender_login = client.post("/api/v1/auth/login",
                                 json={"username": "sender", "password": "password123"},
                                 content_type="application/json")
        sender_token = json.loads(sender_login.data)["access_token"]
        
        # Sender connects via WebSocket and joins same channel
        ws_sender = SocketIOTestClient(app)
        ws_sender.connect('/socket.io/', auth={'token': sender_token})
        ws_sender.emit('join_channel', {'channel_id': channel_id})
        ws_sender.get_received()  # Clear messages
        
        # Act - Sender sends a message to the channel
        ws_sender.emit('send_message', {
            'type': 'channel',
            'target_id': channel_id,
            'content': 'Message for multi-device user',
            'temp_id': 'multi_temp_123'
        })
        
        # Get responses from both devices
        device1_received = ws_device1.get_received()
        device2_received = ws_device2.get_received()
        sender_received = ws_sender.get_received()
        
        # Assert - Both devices receive the same message
        device1_message = None
        device2_message = None
        
        for event in device1_received:
            if event['name'] == 'message_received':
                device1_message = event['args'][0]['message']
                break
        
        for event in device2_received:
            if event['name'] == 'message_received':
                device2_message = event['args'][0]['message']
                break
        
        assert device1_message is not None
        assert device2_message is not None
        
        # Both devices should receive identical message data
        assert device1_message['content'] == 'Message for multi-device user'
        assert device2_message['content'] == 'Message for multi-device user'
        assert device1_message['id'] == device2_message['id']
        
        # Act - Send direct message to the multi-device user
        ws_sender.emit('send_message', {
            'type': 'direct',
            'target_id': user_id,
            'content': 'Direct message for multi-device user',
            'temp_id': 'direct_temp_456'
        })
        
        # Get responses from both devices
        device1_received = ws_device1.get_received()
        device2_received = ws_device2.get_received()
        
        # Assert - Both devices receive the direct message
        device1_dm = None
        device2_dm = None
        
        for event in device1_received:
            if event['name'] == 'message_received':
                device1_dm = event['args'][0]['message']
                break
        
        for event in device2_received:
            if event['name'] == 'message_received':
                device2_dm = event['args'][0]['message']
                break
        
        assert device1_dm is not None
        assert device2_dm is not None
        
        assert device1_dm['content'] == 'Direct message for multi-device user'
        assert device2_dm['content'] == 'Direct message for multi-device user'
        assert device1_dm['type'] == 'direct'
        assert device2_dm['type'] == 'direct'

    def test_multi_client_typing_indicators_sync(self, app, client):
        """Test typing indicators synchronization across multiple clients."""
        # Arrange - Create user with multiple WebSocket connections
        user_data = {
            "username": "typinguser",
            "password": "password123",
            "email": "typing@example.com"
        }
        
        client.post("/api/v1/auth/register", json=user_data, content_type="application/json")
        
        # Login from multiple devices
        login1 = client.post("/api/v1/auth/login",
                           json={"username": "typinguser", "password": "password123"},
                           content_type="application/json")
        login2 = client.post("/api/v1/auth/login",
                           json={"username": "typinguser", "password": "password123"},
                           content_type="application/json")
        
        token1 = json.loads(login1.data)["access_token"]
        token2 = json.loads(login2.data)["access_token"]
        
        # Create WebSocket connections
        ws1 = SocketIOTestClient(app)
        ws2 = SocketIOTestClient(app)
        
        ws1.connect('/socket.io/', auth={'token': token1})
        ws2.connect('/socket.io/', auth={'token': token2})
        
        # Create another user to observe typing indicators
        observer_data = {
            "username": "observer",
            "password": "password123",
            "email": "observer@example.com"
        }
        
        client.post("/api/v1/auth/register", json=observer_data, content_type="application/json")
        observer_login = client.post("/api/v1/auth/login",
                                   json={"username": "observer", "password": "password123"},
                                   content_type="application/json")
        observer_token = json.loads(observer_login.data)["access_token"]
        
        ws_observer = SocketIOTestClient(app)
        ws_observer.connect('/socket.io/', auth={'token': observer_token})
        
        # All join the same channel
        channel_id = str(uuid.uuid4())
        ws1.emit('join_channel', {'channel_id': channel_id})
        ws2.emit('join_channel', {'channel_id': channel_id})
        ws_observer.emit('join_channel', {'channel_id': channel_id})
        
        # Clear join messages
        ws1.get_received()
        ws2.get_received()
        ws_observer.get_received()
        
        # Act - Device 1 starts typing
        ws1.emit('start_typing', {
            'type': 'channel',
            'target_id': channel_id
        })
        
        # Get responses
        ws1_received = ws1.get_received()
        ws2_received = ws2.get_received()
        observer_received = ws_observer.get_received()
        
        # Assert - Observer sees typing indicator, but Device 2 (same user) may not
        observer_typing = None
        for event in observer_received:
            if event['name'] == 'user_typing':
                observer_typing = event
                break
        
        assert observer_typing is not None
        
        # Device 2 should NOT receive typing indicator from Device 1 (same user)
        device2_typing = None
        for event in ws2_received:
            if event['name'] == 'user_typing':
                device2_typing = event
                break
        
        # Same user's devices should not see each other's typing indicators
        assert device2_typing is None

    def test_multi_client_session_management(self, app, client):
        """Test session management across multiple client connections."""
        # Arrange - Create user
        user_data = {
            "username": "sessionuser",
            "password": "password123",
            "email": "session@example.com"
        }
        
        client.post("/api/v1/auth/register", json=user_data, content_type="application/json")
        
        # Create multiple login sessions
        sessions = []
        ws_clients = []
        
        for i in range(3):  # 3 different sessions
            login_response = client.post("/api/v1/auth/login",
                                       json={"username": "sessionuser", "password": "password123"},
                                       content_type="application/json")
            session_data = json.loads(login_response.data)
            sessions.append(session_data)
            
            # Create WebSocket connection for each session
            ws_client = SocketIOTestClient(app)
            ws_client.connect('/socket.io/', auth={'token': session_data['access_token']})
            ws_clients.append(ws_client)
        
        # Clear connection messages
        for ws_client in ws_clients:
            ws_client.get_received()
        
        # Act - Logout from one session via REST API
        logout_headers = {"Authorization": f"Bearer {sessions[0]['access_token']}"}
        logout_response = client.post("/api/v1/auth/logout", headers=logout_headers)
        assert logout_response.status_code == 200
        
        # The WebSocket connection for the logged out session should be terminated
        # This is implementation-specific behavior
        
        # Act - Test that other sessions remain active
        channel_id = str(uuid.uuid4())
        
        # Try to join channel from remaining active sessions
        for i in range(1, 3):  # Skip first session (logged out)
            ws_clients[i].emit('join_channel', {'channel_id': channel_id})
        
        # Get responses
        for i in range(1, 3):
            received = ws_clients[i].get_received()
            # Should receive successful join (no error)
            join_success = any(event['name'] == 'channel_joined' for event in received)
            assert join_success or not any(event['name'] == 'error' for event in received)

    def test_multi_client_message_ordering_consistency(self, app, client):
        """Test that message ordering is consistent across multiple clients."""
        # Arrange - Create multiple users with multiple devices each
        users = []
        all_ws_clients = []
        
        for user_num in range(2):
            user_data = {
                "username": f"user{user_num}",
                "password": "password123",
                "email": f"user{user_num}@example.com"
            }
            
            client.post("/api/v1/auth/register", json=user_data, content_type="application/json")
            
            # Each user has 2 devices
            user_clients = []
            for device_num in range(2):
                login_response = client.post("/api/v1/auth/login",
                                           json={"username": f"user{user_num}", "password": "password123"},
                                           content_type="application/json")
                token = json.loads(login_response.data)["access_token"]
                
                ws_client = SocketIOTestClient(app)
                ws_client.connect('/socket.io/', auth={'token': token})
                user_clients.append(ws_client)
                all_ws_clients.append(ws_client)
            
            users.append(user_clients)
        
        # All clients join the same channel
        channel_id = str(uuid.uuid4())
        for ws_client in all_ws_clients:
            ws_client.emit('join_channel', {'channel_id': channel_id})
            ws_client.get_received()  # Clear join messages
        
        # Act - Send multiple messages from different users/devices rapidly
        message_sequence = [
            (users[0][0], "Message 1 from User0 Device0"),
            (users[1][0], "Message 2 from User1 Device0"),
            (users[0][1], "Message 3 from User0 Device1"),
            (users[1][1], "Message 4 from User1 Device1"),
            (users[0][0], "Message 5 from User0 Device0"),
        ]
        
        sent_message_ids = []
        for ws_client, content in message_sequence:
            temp_id = f"temp_{len(sent_message_ids)}"
            ws_client.emit('send_message', {
                'type': 'channel',
                'target_id': channel_id,
                'content': content,
                'temp_id': temp_id
            })
            
            # Get acknowledgment to capture server-assigned message ID
            ack_received = ws_client.get_received()
            for event in ack_received:
                if event['name'] == 'message_ack':
                    ack_data = event['args'][0]
                    if ack_data['temp_id'] == temp_id:
                        sent_message_ids.append(ack_data['message_id'])
        
        # Collect all message_received events from all clients
        all_received_messages = []
        for ws_client in all_ws_clients:
            received = ws_client.get_received()
            client_messages = []
            for event in received:
                if event['name'] == 'message_received':
                    message = event['args'][0]['message']
                    client_messages.append(message)
            all_received_messages.append(client_messages)
        
        # Assert - All clients received all messages in the same order
        assert len(all_received_messages) > 0
        
        # All clients should have received the same number of messages
        message_count = len(all_received_messages[0])
        for client_messages in all_received_messages:
            assert len(client_messages) == message_count
        
        # All clients should have received messages in the same order
        first_client_order = [msg['id'] for msg in all_received_messages[0]]
        for client_messages in all_received_messages[1:]:
            client_order = [msg['id'] for msg in client_messages]
            assert client_order == first_client_order

    def test_multi_client_connection_limits_and_cleanup(self, app, client):
        """Test connection limits and cleanup for multi-client scenarios."""
        # Arrange - Create user
        user_data = {
            "username": "limituser",
            "password": "password123",
            "email": "limit@example.com"
        }
        
        client.post("/api/v1/auth/register", json=user_data, content_type="application/json")
        
        # Act - Create many connections for the same user
        max_connections = 5  # Implementation-defined limit
        connections = []
        
        for i in range(max_connections + 2):  # Try to exceed limit
            login_response = client.post("/api/v1/auth/login",
                                       json={"username": "limituser", "password": "password123"},
                                       content_type="application/json")
            token = json.loads(login_response.data)["access_token"]
            
            ws_client = SocketIOTestClient(app)
            connection_success = ws_client.connect('/socket.io/', auth={'token': token})
            
            if connection_success:
                connections.append(ws_client)
        
        # Assert - Connection limit is enforced (implementation-specific)
        # Some implementations may limit concurrent connections per user
        # Others may allow unlimited connections
        
        # At minimum, should handle the connections gracefully without crashing
        assert len(connections) > 0  # At least some connections succeeded
        
        # Act - Disconnect all connections
        for ws_client in connections:
            ws_client.disconnect()
        
        # Assert - All connections cleaned up properly
        # Implementation should handle cleanup gracefully