"""
Contract tests for join_channel WebSocket event.

These tests verify channel joining WebSocket contract.
CRITICAL: These tests MUST FAIL initially (RED phase of TDD)
"""

import pytest
import json
import uuid
from flask_socketio import SocketIOTestClient


class TestWebSocketJoinContract:
    """Contract tests for join_channel WebSocket event."""

    def test_join_channel_authenticated_emits_channel_joined(self, app, auth_token):
        """Test join_channel event emits channel_joined with channel info."""
        # Arrange
        socketio_client = SocketIOTestClient(app)
        channel_id = str(uuid.uuid4())
        
        # Connect with authentication
        socketio_client.connect('/socket.io/', auth={'token': auth_token})
        
        # Act
        socketio_client.emit('join_channel', {
            'channel_id': channel_id,
            'last_message_timestamp': '2025-09-07T10:30:00Z'
        })
        
        # Assert
        received = socketio_client.get_received()
        
        # Should receive channel_joined event
        channel_joined_event = None
        for event in received:
            if event['name'] == 'channel_joined':
                channel_joined_event = event
                break
                
        assert channel_joined_event is not None
        data = channel_joined_event['args'][0]
        
        # Contract validation: channel_joined payload
        assert 'channel' in data
        assert 'recent_messages' in data
        assert 'members_online' in data
        
        # Channel object validation
        channel = data['channel']
        assert 'id' in channel
        assert 'name' in channel
        assert 'display_name' in channel
        assert 'member_count' in channel
        
        # Recent messages array validation
        assert isinstance(data['recent_messages'], list)
        
        # Members online array validation  
        assert isinstance(data['members_online'], list)
        for member in data['members_online']:
            assert 'id' in member
            assert 'username' in member
            assert 'display_name' in member

    def test_join_channel_nonexistent_emits_error(self, app, auth_token):
        """Test join_channel for nonexistent channel emits error."""
        # Arrange
        socketio_client = SocketIOTestClient(app)
        nonexistent_channel_id = str(uuid.uuid4())
        
        socketio_client.connect('/socket.io/', auth={'token': auth_token})
        
        # Act
        socketio_client.emit('join_channel', {
            'channel_id': nonexistent_channel_id
        })
        
        # Assert
        received = socketio_client.get_received()
        
        # Should receive error event
        error_event = None
        for event in received:
            if event['name'] == 'error':
                error_event = event
                break
                
        assert error_event is not None
        data = error_event['args'][0]
        
        # Contract validation: error payload
        assert 'code' in data
        assert 'message' in data
        assert data['code'] in ['CHANNEL_NOT_FOUND', 'NOT_AUTHORIZED']

    def test_join_channel_no_permission_emits_error(self, app, auth_token):
        """Test join_channel for private channel without permission emits error."""
        # Arrange  
        socketio_client = SocketIOTestClient(app)
        private_channel_id = str(uuid.uuid4())  # Private channel user isn't member of
        
        socketio_client.connect('/socket.io/', auth={'token': auth_token})
        
        # Act
        socketio_client.emit('join_channel', {
            'channel_id': private_channel_id
        })
        
        # Assert
        received = socketio_client.get_received()
        
        # Should receive error event
        error_event = None
        for event in received:
            if event['name'] == 'error':
                error_event = event
                break
                
        assert error_event is not None
        data = error_event['args'][0]
        
        # Contract validation: error payload
        assert 'code' in data
        assert 'message' in data
        assert data['code'] in ['NOT_AUTHORIZED', 'CHANNEL_NOT_FOUND']

    def test_join_channel_missing_channel_id_emits_error(self, app, auth_token):
        """Test join_channel without channel_id emits error."""
        # Arrange
        socketio_client = SocketIOTestClient(app)
        socketio_client.connect('/socket.io/', auth={'token': auth_token})
        
        # Act
        socketio_client.emit('join_channel', {})  # Missing required channel_id
        
        # Assert
        received = socketio_client.get_received()
        
        # Should receive error event
        error_event = None
        for event in received:
            if event['name'] == 'error':
                error_event = event
                break
                
        assert error_event is not None

    def test_join_channel_invalid_channel_id_emits_error(self, app, auth_token):
        """Test join_channel with invalid channel_id format emits error."""
        # Arrange
        socketio_client = SocketIOTestClient(app)
        socketio_client.connect('/socket.io/', auth={'token': auth_token})
        
        # Act
        socketio_client.emit('join_channel', {
            'channel_id': 'invalid-uuid-format'
        })
        
        # Assert
        received = socketio_client.get_received()
        
        # Should receive error event
        error_event = None
        for event in received:
            if event['name'] == 'error':
                error_event = event
                break
                
        assert error_event is not None

    def test_join_channel_unauthenticated_connection_fails(self, app):
        """Test join_channel without authentication fails at connection level."""
        # Arrange
        socketio_client = SocketIOTestClient(app)
        
        # Act - Connect without auth token
        success = socketio_client.connect('/socket.io/')
        
        # Assert - Connection should fail for unauthenticated requests
        assert success is False