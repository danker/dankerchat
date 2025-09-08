"""
Message API endpoints for DankerChat application.

Provides REST endpoints for message operations including sending, editing, deleting, and retrieving.
Based on specs/001-chat-application/tasks.md T047
"""

from flask import Blueprint, request, jsonify, g
from datetime import datetime

from services.auth import require_auth, require_permission
from services.messaging import MessagingService, MessagingError
from models.message import MessageType


messages_bp = Blueprint('messages', __name__, url_prefix='/api/messages')


@messages_bp.route('/channel/<channel_id>', methods=['POST'])
@require_auth
def send_channel_message(channel_id):
    """
    Send a message to a channel.
    
    Headers:
        Authorization: Bearer <token>
    
    Args:
        channel_id: Channel ID
    
    Request body:
    {
        "content": "string (required, max 5000 chars)",
        "message_type": "string (optional, default: text)"
    }
    
    Returns:
        201: Message sent successfully
        400: Validation error
        403: Cannot send message to channel
        404: Channel not found
        401: Not authenticated
    """
    try:
        user = g.current_user
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        content = data.get('content')
        message_type_str = data.get('message_type', 'text')
        
        if not content:
            return jsonify({'error': 'content is required'}), 400
        
        try:
            message_type = MessageType(message_type_str.lower())
        except ValueError:
            return jsonify({'error': 'Invalid message_type. Must be text, system, join, or leave'}), 400
        
        message = MessagingService.send_channel_message(
            sender=user,
            channel_id=channel_id,
            content=content,
            message_type=message_type
        )
        
        return jsonify({
            'message': 'Message sent successfully',
            'data': message.to_dict()
        }), 201
        
    except MessagingError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@messages_bp.route('/direct/<user_id>', methods=['POST'])
@require_auth
def send_direct_message(user_id):
    """
    Send a direct message to a user.
    
    Headers:
        Authorization: Bearer <token>
    
    Args:
        user_id: Recipient user ID
    
    Request body:
    {
        "content": "string (required, max 5000 chars)",
        "message_type": "string (optional, default: text)"
    }
    
    Returns:
        201: Message sent successfully
        400: Validation error
        404: User not found
        401: Not authenticated
    """
    try:
        user = g.current_user
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        content = data.get('content')
        message_type_str = data.get('message_type', 'text')
        
        if not content:
            return jsonify({'error': 'content is required'}), 400
        
        try:
            message_type = MessageType(message_type_str.lower())
        except ValueError:
            return jsonify({'error': 'Invalid message_type. Must be text, system, join, or leave'}), 400
        
        message = MessagingService.send_direct_message(
            sender=user,
            recipient_id=user_id,
            content=content,
            message_type=message_type
        )
        
        return jsonify({
            'message': 'Direct message sent successfully',
            'data': message.to_dict()
        }), 201
        
    except MessagingError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@messages_bp.route('/<message_id>', methods=['PUT'])
@require_auth
def edit_message(message_id):
    """
    Edit a message.
    
    Headers:
        Authorization: Bearer <token>
    
    Args:
        message_id: Message ID
    
    Request body:
    {
        "content": "string (required, max 5000 chars)"
    }
    
    Returns:
        200: Message edited successfully
        400: Validation error or cannot edit
        404: Message not found
        403: Cannot edit this message
        401: Not authenticated
    """
    try:
        user = g.current_user
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        new_content = data.get('content')
        
        if not new_content:
            return jsonify({'error': 'content is required'}), 400
        
        success = MessagingService.edit_message(user, message_id, new_content)
        
        if success:
            return jsonify({'message': 'Message edited successfully'}), 200
        else:
            return jsonify({'error': 'Failed to edit message'}), 500
            
    except MessagingError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@messages_bp.route('/<message_id>', methods=['DELETE'])
@require_auth
def delete_message(message_id):
    """
    Delete a message.
    
    Headers:
        Authorization: Bearer <token>
    
    Args:
        message_id: Message ID
    
    Returns:
        200: Message deleted successfully
        404: Message not found
        403: Cannot delete this message
        401: Not authenticated
    """
    try:
        user = g.current_user
        
        success = MessagingService.delete_message(user, message_id)
        
        if success:
            return jsonify({'message': 'Message deleted successfully'}), 200
        else:
            return jsonify({'error': 'Failed to delete message'}), 500
            
    except MessagingError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@messages_bp.route('/channel/<channel_id>', methods=['GET'])
@require_auth
def get_channel_messages(channel_id):
    """
    Get messages from a channel.
    
    Headers:
        Authorization: Bearer <token>
    
    Args:
        channel_id: Channel ID
    
    Query parameters:
        limit: Maximum messages (default: 50, max: 100)
        before: Get messages before this timestamp (ISO format)
    
    Returns:
        200: List of messages
        400: Invalid parameters
        403: Cannot access channel
        404: Channel not found
        401: Not authenticated
    """
    try:
        user = g.current_user
        limit = request.args.get('limit', 50, type=int)
        before_str = request.args.get('before')
        
        if limit < 1 or limit > 100:
            return jsonify({'error': 'limit must be between 1 and 100'}), 400
        
        before_timestamp = None
        if before_str:
            try:
                before_timestamp = datetime.fromisoformat(before_str.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid before timestamp format. Use ISO format.'}), 400
        
        messages = MessagingService.get_channel_messages(
            user=user,
            channel_id=channel_id,
            limit=limit,
            before_timestamp=before_timestamp
        )
        
        messages_data = [message.to_dict() for message in messages]
        
        return jsonify({
            'messages': messages_data,
            'total': len(messages_data),
            'channel_id': channel_id
        }), 200
        
    except MessagingError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@messages_bp.route('/conversation/<conversation_id>', methods=['GET'])
@require_auth
def get_direct_messages(conversation_id):
    """
    Get messages from a direct conversation.
    
    Headers:
        Authorization: Bearer <token>
    
    Args:
        conversation_id: Conversation ID
    
    Query parameters:
        limit: Maximum messages (default: 50, max: 100)
        before: Get messages before this timestamp (ISO format)
    
    Returns:
        200: List of messages
        400: Invalid parameters
        403: Cannot access conversation
        404: Conversation not found
        401: Not authenticated
    """
    try:
        user = g.current_user
        limit = request.args.get('limit', 50, type=int)
        before_str = request.args.get('before')
        
        if limit < 1 or limit > 100:
            return jsonify({'error': 'limit must be between 1 and 100'}), 400
        
        before_timestamp = None
        if before_str:
            try:
                before_timestamp = datetime.fromisoformat(before_str.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid before timestamp format. Use ISO format.'}), 400
        
        messages = MessagingService.get_direct_messages(
            user=user,
            conversation_id=conversation_id,
            limit=limit,
            before_timestamp=before_timestamp
        )
        
        messages_data = [message.to_dict() for message in messages]
        
        return jsonify({
            'messages': messages_data,
            'total': len(messages_data),
            'conversation_id': conversation_id
        }), 200
        
    except MessagingError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@messages_bp.route('/conversations', methods=['GET'])
@require_auth
def get_user_conversations():
    """
    Get user's direct conversations.
    
    Headers:
        Authorization: Bearer <token>
    
    Query parameters:
        limit: Maximum conversations (default: 50, max: 100)
    
    Returns:
        200: List of conversations
        400: Invalid parameters
        401: Not authenticated
    """
    try:
        user = g.current_user
        limit = request.args.get('limit', 50, type=int)
        
        if limit < 1 or limit > 100:
            return jsonify({'error': 'limit must be between 1 and 100'}), 400
        
        conversations = MessagingService.get_user_direct_conversations(user, limit)
        
        return jsonify({
            'conversations': conversations,
            'total': len(conversations)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@messages_bp.route('/channels', methods=['GET'])
@require_auth
def get_user_channels():
    """
    Get user's channels with recent message info.
    
    Headers:
        Authorization: Bearer <token>
    
    Returns:
        200: List of user's channels
        401: Not authenticated
    """
    try:
        user = g.current_user
        
        channels = MessagingService.get_user_channels(user)
        
        return jsonify({
            'channels': channels,
            'total': len(channels)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@messages_bp.route('/search', methods=['GET'])
@require_auth
def search_messages():
    """
    Search messages by content.
    
    Headers:
        Authorization: Bearer <token>
    
    Query parameters:
        q: Search query (required, min 2 chars)
        channel_id: Search within specific channel (optional)
        conversation_id: Search within specific conversation (optional)
        limit: Maximum results (default: 50, max: 100)
    
    Returns:
        200: List of matching messages
        400: Invalid parameters or missing query
        403: Cannot access specified channel/conversation
        401: Not authenticated
    """
    try:
        user = g.current_user
        query = request.args.get('q', '').strip()
        channel_id = request.args.get('channel_id')
        conversation_id = request.args.get('conversation_id')
        limit = request.args.get('limit', 50, type=int)
        
        if not query:
            return jsonify({'error': 'Search query (q) is required'}), 400
        
        if limit < 1 or limit > 100:
            return jsonify({'error': 'limit must be between 1 and 100'}), 400
        
        if channel_id and conversation_id:
            return jsonify({'error': 'Cannot specify both channel_id and conversation_id'}), 400
        
        messages = MessagingService.search_messages(
            user=user,
            query=query,
            channel_id=channel_id,
            conversation_id=conversation_id,
            limit=limit
        )
        
        messages_data = [message.to_dict() for message in messages]
        
        return jsonify({
            'messages': messages_data,
            'total': len(messages_data),
            'query': query
        }), 200
        
    except MessagingError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@messages_bp.route('/stats', methods=['GET'])
@require_auth
def get_message_stats():
    """
    Get message statistics for current user.
    
    Headers:
        Authorization: Bearer <token>
    
    Returns:
        200: Message statistics
        401: Not authenticated
    """
    try:
        user = g.current_user
        
        stats = MessagingService.get_message_stats(user)
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@messages_bp.route('/activity', methods=['GET'])
@require_auth
def get_recent_activity():
    """
    Get recent messaging activity for current user.
    
    Headers:
        Authorization: Bearer <token>
    
    Query parameters:
        limit: Maximum activity items (default: 20, max: 50)
    
    Returns:
        200: Recent activity
        400: Invalid parameters
        401: Not authenticated
    """
    try:
        user = g.current_user
        limit = request.args.get('limit', 20, type=int)
        
        if limit < 1 or limit > 50:
            return jsonify({'error': 'limit must be between 1 and 50'}), 400
        
        activity = MessagingService.get_recent_activity(user, limit)
        
        return jsonify({
            'activity': activity,
            'total': len(activity)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@messages_bp.route('/<message_id>', methods=['GET'])
@require_auth
def get_message(message_id):
    """
    Get a specific message by ID.
    
    Headers:
        Authorization: Bearer <token>
    
    Args:
        message_id: Message ID
    
    Returns:
        200: Message data
        404: Message not found
        403: Cannot access message
        401: Not authenticated
    """
    try:
        user = g.current_user
        
        from models.message import Message
        from models.channel_membership import ChannelMembership
        from models.direct_conversation import DirectConversation
        
        message = Message.query.get(message_id)
        if not message:
            return jsonify({'error': 'Message not found'}), 404
        
        # Check access permissions
        if message.is_channel_message():
            # Check if user is a member of the channel
            membership = ChannelMembership.query.filter_by(
                channel_id=message.channel_id,
                user_id=str(user.id)
            ).first()
            
            if not membership:
                return jsonify({'error': 'Cannot access this message'}), 403
        
        elif message.is_direct_message():
            # Check if user is a participant in the conversation
            conversation = DirectConversation.query.get(message.direct_conversation_id)
            if not conversation or not conversation.is_participant(str(user.id)):
                return jsonify({'error': 'Cannot access this message'}), 403
        
        return jsonify({
            'message': message.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


# System message creation (admin only)
@messages_bp.route('/system', methods=['POST'])
@require_auth
@require_permission('can_delete_messages')
def create_system_message():
    """
    Create a system message (admin only).
    
    Headers:
        Authorization: Bearer <token>
    
    Request body:
    {
        "content": "string (required)",
        "channel_id": "string (optional, for channel messages)",
        "conversation_id": "string (optional, for direct messages)",
        "message_type": "string (optional, default: system)"
    }
    
    Returns:
        201: System message created
        400: Validation error
        403: Insufficient permissions
        401: Not authenticated
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        content = data.get('content')
        channel_id = data.get('channel_id')
        conversation_id = data.get('conversation_id')
        message_type_str = data.get('message_type', 'system')
        
        if not content:
            return jsonify({'error': 'content is required'}), 400
        
        try:
            message_type = MessageType(message_type_str.lower())
        except ValueError:
            return jsonify({'error': 'Invalid message_type'}), 400
        
        message = MessagingService.create_system_message(
            content=content,
            channel_id=channel_id,
            conversation_id=conversation_id,
            message_type=message_type
        )
        
        return jsonify({
            'message': 'System message created successfully',
            'data': message.to_dict()
        }), 201
        
    except MessagingError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


# Health check endpoint
@messages_bp.route('/health', methods=['GET'])
def messages_health():
    """
    Messages service health check.
    
    Returns:
        200: Service healthy
    """
    return jsonify({
        'service': 'messages',
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    }), 200


# Error handlers for the messages blueprint
@messages_bp.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), 400


@messages_bp.errorhandler(401)
def unauthorized(error):
    return jsonify({'error': 'Unauthorized'}), 401


@messages_bp.errorhandler(403)
def forbidden(error):
    return jsonify({'error': 'Forbidden'}), 403


@messages_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404


@messages_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500