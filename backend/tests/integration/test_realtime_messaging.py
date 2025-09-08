"""
Integration tests for real-time WebSocket messaging flow.

Tests the end-to-end real-time messaging workflow including:
- WebSocket connection and authentication
- Real-time message broadcasting
- Channel joining and leaving
- Typing indicators
- Multi-client synchronization

CRITICAL: These tests MUST FAIL initially (RED phase of TDD)
"""

import pytest
import json
import uuid
from flask_socketio import SocketIOTestClient


@pytest.mark.integration
class TestRealtimeMessagingFlow:
    """Integration tests for real-time WebSocket messaging workflow."""

    def test_complete_realtime_channel_messaging_flow(self, app):
        """Test complete real-time channel messaging between multiple clients."""
        # Arrange - Create two users and authenticate them
        # Note: In a real test, you'd create actual users through the API
        user1_token = "mock_user1_jwt_token"
        user2_token = "mock_user2_jwt_token"
        
        # Create WebSocket clients for both users
        client1 = SocketIOTestClient(app)
        client2 = SocketIOTestClient(app)
        
        # Both clients connect with authentication
        success1 = client1.connect('/socket.io/', auth={'token': user1_token})
        success2 = client2.connect('/socket.io/', auth={'token': user2_token})
        
        # Assert - Both connections successful
        assert success1 is True
        assert success2 is True
        
        # Clear any connection acknowledgment messages
        client1.get_received()
        client2.get_received()
        
        # Act - Step 1: Both users join the same channel
        channel_id = str(uuid.uuid4())
        
        client1.emit('join_channel', {'channel_id': channel_id})
        client2.emit('join_channel', {'channel_id': channel_id})
        
        # Both should receive channel_joined events
        received1 = client1.get_received()
        received2 = client2.get_received()
        
        # Assert - Both users successfully joined
        assert any(event['name'] == 'channel_joined' for event in received1)
        assert any(event['name'] == 'channel_joined' for event in received2)
        
        # Act - Step 2: User1 sends a message to the channel
        temp_id = "temp_message_123"
        client1.emit('send_message', {
            'type': 'channel',
            'target_id': channel_id,
            'content': 'Hello everyone in real-time!',
            'temp_id': temp_id
        })
        
        # Get responses
        client1_received = client1.get_received()
        client2_received = client2.get_received()
        
        # Assert - User1 gets message acknowledgment
        message_ack = None
        for event in client1_received:
            if event['name'] == 'message_ack':
                message_ack = event
                break
        
        assert message_ack is not None
        ack_data = message_ack['args'][0]
        assert ack_data['temp_id'] == temp_id
        assert 'message_id' in ack_data
        
        # Assert - User2 receives the real-time message
        message_received = None
        for event in client2_received:
            if event['name'] == 'message_received':
                message_received = event
                break
        
        assert message_received is not None
        received_data = message_received['args'][0]
        message = received_data['message']
        
        assert message['content'] == 'Hello everyone in real-time!'
        assert message['type'] == 'channel'
        assert message['target_id'] == channel_id
        
        # Act - Step 3: User2 replies in real-time
        client2.emit('send_message', {
            'type': 'channel',
            'target_id': channel_id,
            'content': 'Got your message instantly!',
            'temp_id': 'temp_reply_456'
        })
        
        # Get responses
        client1_received = client1.get_received()
        client2_received = client2.get_received()
        
        # Assert - User1 receives User2's reply in real-time
        reply_received = None
        for event in client1_received:
            if event['name'] == 'message_received':
                reply_received = event
                break
        
        assert reply_received is not None
        reply_data = reply_received['args'][0]
        reply_message = reply_data['message']
        
        assert reply_message['content'] == 'Got your message instantly!'

    def test_realtime_direct_messaging_flow(self, app):
        """Test real-time direct messaging between two users."""
        # Arrange - Create WebSocket clients for two users
        user1_token = "mock_user1_jwt_token"
        user2_token = "mock_user2_jwt_token"
        
        client1 = SocketIOTestClient(app)
        client2 = SocketIOTestClient(app)
        
        client1.connect('/socket.io/', auth={'token': user1_token})
        client2.connect('/socket.io/', auth={'token': user2_token})
        
        # Clear connection messages
        client1.get_received()
        client2.get_received()
        
        # Act - Step 1: User1 sends direct message to User2
        user2_id = str(uuid.uuid4())  # Mock User2's ID
        
        client1.emit('send_message', {
            'type': 'direct',
            'target_id': user2_id,
            'content': 'Private message for you!',
            'temp_id': 'dm_temp_123'
        })
        
        # Get responses
        client1_received = client1.get_received()
        client2_received = client2.get_received()
        
        # Assert - User1 gets acknowledgment
        ack_found = any(event['name'] == 'message_ack' for event in client1_received)
        assert ack_found
        
        # Assert - User2 receives the direct message
        dm_received = None
        for event in client2_received:
            if event['name'] == 'message_received':
                dm_received = event
                break
        
        assert dm_received is not None
        dm_data = dm_received['args'][0]
        dm_message = dm_data['message']
        
        assert dm_message['content'] == 'Private message for you!'
        assert dm_message['type'] == 'direct'
        assert dm_message['target_id'] == user2_id

    def test_typing_indicators_realtime_flow(self, app):
        """Test real-time typing indicators between users."""
        # Arrange - Create WebSocket clients
        user1_token = "mock_user1_jwt_token"
        user2_token = "mock_user2_jwt_token"
        
        client1 = SocketIOTestClient(app)
        client2 = SocketIOTestClient(app)
        
        client1.connect('/socket.io/', auth={'token': user1_token})
        client2.connect('/socket.io/', auth={'token': user2_token})
        
        # Both join the same channel
        channel_id = str(uuid.uuid4())
        client1.emit('join_channel', {'channel_id': channel_id})
        client2.emit('join_channel', {'channel_id': channel_id})
        
        # Clear setup messages
        client1.get_received()
        client2.get_received()
        
        # Act - Step 1: User1 starts typing
        client1.emit('start_typing', {
            'type': 'channel',
            'target_id': channel_id
        })
        
        # Get responses
        client1_received = client1.get_received()
        client2_received = client2.get_received()
        
        # Assert - User2 receives typing indicator
        typing_event = None
        for event in client2_received:
            if event['name'] == 'user_typing':
                typing_event = event
                break
        
        assert typing_event is not None
        typing_data = typing_event['args'][0]
        
        assert typing_data['type'] == 'channel'
        assert typing_data['target_id'] == channel_id
        assert 'user' in typing_data
        
        # Act - Step 2: User1 stops typing
        client1.emit('stop_typing', {
            'type': 'channel',
            'target_id': channel_id
        })
        
        # Get responses
        client1_received = client1.get_received()
        client2_received = client2.get_received()
        
        # Assert - User2 receives stop typing indicator
        stop_typing_event = None
        for event in client2_received:
            if event['name'] == 'user_stopped_typing':
                stop_typing_event = event
                break
        
        assert stop_typing_event is not None
        stop_typing_data = stop_typing_event['args'][0]
        
        assert stop_typing_data['type'] == 'channel'
        assert stop_typing_data['target_id'] == channel_id

    def test_channel_member_join_leave_notifications(self, app):
        """Test real-time notifications when users join/leave channels."""
        # Arrange - Create WebSocket clients
        user1_token = "mock_user1_jwt_token"
        user2_token = "mock_user2_jwt_token"
        
        client1 = SocketIOTestClient(app)
        client2 = SocketIOTestClient(app)
        
        client1.connect('/socket.io/', auth={'token': user1_token})
        client2.connect('/socket.io/', auth={'token': user2_token})
        
        # User1 joins channel first
        channel_id = str(uuid.uuid4())
        client1.emit('join_channel', {'channel_id': channel_id})
        
        # Clear setup messages
        client1.get_received()
        client2.get_received()
        
        # Act - User2 joins the same channel
        client2.emit('join_channel', {'channel_id': channel_id})
        
        # Get responses
        client1_received = client1.get_received()
        client2_received = client2.get_received()
        
        # Assert - User1 receives notification about User2 joining
        user_joined_event = None
        for event in client1_received:
            if event['name'] == 'user_joined_channel':
                user_joined_event = event
                break
        
        assert user_joined_event is not None
        join_data = user_joined_event['args'][0]
        
        assert join_data['channel_id'] == channel_id
        assert 'user' in join_data
        assert 'joined_at' in join_data
        
        # Act - User2 leaves the channel
        client2.emit('leave_channel', {'channel_id': channel_id})
        
        # Get responses
        client1_received = client1.get_received()
        client2_received = client2.get_received()
        
        # Assert - User1 receives notification about User2 leaving
        user_left_event = None
        for event in client1_received:
            if event['name'] == 'user_left_channel':
                user_left_event = event
                break
        
        assert user_left_event is not None
        leave_data = user_left_event['args'][0]
        
        assert leave_data['channel_id'] == channel_id
        assert 'user' in leave_data
        assert 'left_at' in leave_data

    def test_websocket_authentication_flow(self, app):
        """Test WebSocket authentication and connection flow."""
        # Act - Step 1: Try to connect without authentication
        unauthenticated_client = SocketIOTestClient(app)
        unauthenticated_success = unauthenticated_client.connect('/socket.io/')
        
        # Assert - Unauthenticated connection fails
        assert unauthenticated_success is False
        
        # Act - Step 2: Connect with valid token
        authenticated_client = SocketIOTestClient(app)
        valid_token = "valid_jwt_token"
        authenticated_success = authenticated_client.connect('/socket.io/', auth={'token': valid_token})
        
        # Assert - Authenticated connection succeeds
        assert authenticated_success is True
        
        # Should receive connection acknowledgment
        received = authenticated_client.get_received()
        connect_ack = None
        for event in received:
            if event['name'] == 'connect_ack':
                connect_ack = event
                break
        
        assert connect_ack is not None
        ack_data = connect_ack['args'][0]
        
        # Connection ack should include user info and session
        assert 'user' in ack_data
        assert 'session_id' in ack_data
        
        user_info = ack_data['user']
        assert 'id' in user_info
        assert 'username' in user_info
        assert 'display_name' in user_info
        assert 'role' in user_info
        
        # Act - Step 3: Try to connect with invalid token
        invalid_client = SocketIOTestClient(app)
        invalid_success = invalid_client.connect('/socket.io/', auth={'token': 'invalid_token'})
        
        # Assert - Invalid token connection fails
        assert invalid_success is False

    def test_websocket_error_handling_flow(self, app):
        """Test WebSocket error handling for various scenarios."""
        # Arrange - Create authenticated client
        client = SocketIOTestClient(app)
        client.connect('/socket.io/', auth={'token': 'valid_jwt_token'})
        client.get_received()  # Clear connection messages
        
        # Act - Step 1: Try to join nonexistent channel
        fake_channel_id = str(uuid.uuid4())
        client.emit('join_channel', {'channel_id': fake_channel_id})
        
        received = client.get_received()
        
        # Assert - Receive error for nonexistent channel
        error_event = None
        for event in received:
            if event['name'] == 'error':
                error_event = event
                break
        
        assert error_event is not None
        error_data = error_event['args'][0]
        
        assert 'code' in error_data
        assert 'message' in error_data
        assert error_data['code'] in ['CHANNEL_NOT_FOUND', 'NOT_AUTHORIZED']
        
        # Act - Step 2: Try to send message with invalid data
        client.emit('send_message', {
            'type': 'invalid_type',  # Invalid type
            'target_id': str(uuid.uuid4()),
            'content': 'This should fail'
        })
        
        received = client.get_received()
        
        # Assert - Receive error for invalid message data
        error_event = None
        for event in received:
            if event['name'] == 'error':
                error_event = event
                break
        
        assert error_event is not None
        
        # Act - Step 3: Try to send message without required fields
        client.emit('send_message', {
            'type': 'channel'
            # Missing target_id and content
        })
        
        received = client.get_received()
        
        # Assert - Receive error for missing required fields
        error_event = None
        for event in received:
            if event['name'] == 'error':
                error_event = event
                break
        
        assert error_event is not None

    def test_websocket_reconnection_and_state_recovery(self, app):
        """Test WebSocket reconnection and state recovery."""
        # Arrange - Create client and join channel
        client = SocketIOTestClient(app)
        client.connect('/socket.io/', auth={'token': 'valid_jwt_token'})
        client.get_received()  # Clear connection messages
        
        channel_id = str(uuid.uuid4())
        client.emit('join_channel', {'channel_id': channel_id})
        client.get_received()  # Clear join messages
        
        # Act - Step 1: Simulate disconnect
        client.disconnect()
        
        # Act - Step 2: Reconnect
        reconnect_success = client.connect('/socket.io/', auth={'token': 'valid_jwt_token'})
        assert reconnect_success is True
        
        # Clear reconnection messages
        client.get_received()
        
        # Act - Step 3: Rejoin channel with last message timestamp to get missed messages
        last_message_timestamp = '2025-09-07T10:30:00Z'
        client.emit('join_channel', {
            'channel_id': channel_id,
            'last_message_timestamp': last_message_timestamp
        })
        
        received = client.get_received()
        
        # Assert - Should receive channel_joined with missed messages
        channel_joined = None
        for event in received:
            if event['name'] == 'channel_joined':
                channel_joined = event
                break
        
        assert channel_joined is not None
        join_data = channel_joined['args'][0]
        
        assert 'channel' in join_data
        assert 'recent_messages' in join_data
        assert 'members_online' in join_data
        
        # Recent messages should include any messages since the timestamp
        recent_messages = join_data['recent_messages']
        assert isinstance(recent_messages, list)