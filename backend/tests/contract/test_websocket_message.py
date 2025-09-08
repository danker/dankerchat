"""
Contract tests for send_message WebSocket event.

These tests verify message sending WebSocket contract.
CRITICAL: These tests MUST FAIL initially (RED phase of TDD)
"""

import pytest
import json
import uuid
from flask_socketio import SocketIOTestClient


class TestWebSocketMessageContract:
    """Contract tests for send_message WebSocket event."""

    def test_send_channel_message_emits_message_ack(self, app, auth_token):
        """Test send_message to channel emits message_ack."""
        # Arrange
        socketio_client = SocketIOTestClient(app)
        socketio_client.connect('/socket.io/', auth={'token': auth_token})
        
        channel_id = str(uuid.uuid4())
        temp_id = "temp_123"
        
        # Act
        socketio_client.emit('send_message', {
            'type': 'channel',
            'target_id': channel_id,
            'content': 'Hello channel!',
            'temp_id': temp_id
        })
        
        # Assert
        received = socketio_client.get_received()
        
        # Should receive message_ack event
        message_ack_event = None
        for event in received:
            if event['name'] == 'message_ack':
                message_ack_event = event
                break
                
        assert message_ack_event is not None
        data = message_ack_event['args'][0]
        
        # Contract validation: message_ack payload
        assert 'temp_id' in data
        assert 'message_id' in data
        assert 'timestamp' in data
        assert data['temp_id'] == temp_id
        assert isinstance(data['message_id'], str)

    def test_send_direct_message_emits_message_ack(self, app, auth_token):
        """Test send_message to user emits message_ack."""
        # Arrange
        socketio_client = SocketIOTestClient(app)
        socketio_client.connect('/socket.io/', auth={'token': auth_token})
        
        recipient_id = str(uuid.uuid4())
        temp_id = "temp_456"
        
        # Act
        socketio_client.emit('send_message', {
            'type': 'direct',
            'target_id': recipient_id,
            'content': 'Hello user!',
            'temp_id': temp_id
        })
        
        # Assert
        received = socketio_client.get_received()
        
        # Should receive message_ack event
        message_ack_event = None
        for event in received:
            if event['name'] == 'message_ack':
                message_ack_event = event
                break
                
        assert message_ack_event is not None
        data = message_ack_event['args'][0]
        
        # Contract validation
        assert data['temp_id'] == temp_id
        assert 'message_id' in data
        assert 'timestamp' in data

    def test_send_message_missing_type_emits_error(self, app, auth_token):
        """Test send_message without type emits error."""
        # Arrange
        socketio_client = SocketIOTestClient(app)
        socketio_client.connect('/socket.io/', auth={'token': auth_token})
        
        # Act
        socketio_client.emit('send_message', {
            'target_id': str(uuid.uuid4()),
            'content': 'Message without type',
            'temp_id': 'temp_error'
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

    def test_send_message_missing_content_emits_error(self, app, auth_token):
        """Test send_message without content emits error."""
        # Arrange
        socketio_client = SocketIOTestClient(app)
        socketio_client.connect('/socket.io/', auth={'token': auth_token})
        
        # Act
        socketio_client.emit('send_message', {
            'type': 'channel',
            'target_id': str(uuid.uuid4()),
            'temp_id': 'temp_error'
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

    def test_send_message_empty_content_emits_error(self, app, auth_token):
        """Test send_message with empty content emits error."""
        # Arrange
        socketio_client = SocketIOTestClient(app)
        socketio_client.connect('/socket.io/', auth={'token': auth_token})
        
        # Act
        socketio_client.emit('send_message', {
            'type': 'channel',
            'target_id': str(uuid.uuid4()),
            'content': '',  # Empty content
            'temp_id': 'temp_error'
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

    def test_send_message_invalid_type_emits_error(self, app, auth_token):
        """Test send_message with invalid type emits error."""
        # Arrange
        socketio_client = SocketIOTestClient(app)
        socketio_client.connect('/socket.io/', auth={'token': auth_token})
        
        # Act
        socketio_client.emit('send_message', {
            'type': 'invalid_type',  # Should be 'channel' or 'direct'
            'target_id': str(uuid.uuid4()),
            'content': 'Test message',
            'temp_id': 'temp_error'
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

    def test_send_message_nonexistent_target_emits_error(self, app, auth_token):
        """Test send_message to nonexistent target emits error."""
        # Arrange
        socketio_client = SocketIOTestClient(app)
        socketio_client.connect('/socket.io/', auth={'token': auth_token})
        
        # Act
        socketio_client.emit('send_message', {
            'type': 'channel',
            'target_id': str(uuid.uuid4()),  # Nonexistent channel
            'content': 'Message to nowhere',
            'temp_id': 'temp_error'
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

    def test_send_message_without_temp_id_still_works(self, app, auth_token):
        """Test send_message without temp_id still processes (temp_id optional)."""
        # Arrange
        socketio_client = SocketIOTestClient(app)
        socketio_client.connect('/socket.io/', auth={'token': auth_token})
        
        # Act
        socketio_client.emit('send_message', {
            'type': 'channel',
            'target_id': str(uuid.uuid4()),
            'content': 'Message without temp_id'
        })
        
        # Assert - Should not immediately error (may error later due to nonexistent channel)
        received = socketio_client.get_received()
        
        # If there's an error, it should be about the channel, not missing temp_id
        for event in received:
            if event['name'] == 'error':
                data = event['args'][0]
                # Error should not be about missing temp_id
                assert 'temp_id' not in data.get('message', '').lower()