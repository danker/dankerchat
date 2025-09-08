"""
Channel API endpoints for DankerChat application.

Provides REST endpoints for channel management, membership, and moderation.
Based on specs/001-chat-application/tasks.md T046
"""

from flask import Blueprint, request, jsonify, g
from datetime import datetime

from services.auth import require_auth, require_permission
from services.channels import ChannelService, ChannelError
from services.auth import AuthorizationError
from models.channel_membership import MembershipRole


channels_bp = Blueprint('channels', __name__, url_prefix='/api/channels')


@channels_bp.route('', methods=['GET'])
@require_auth
def get_channels():
    """
    Get list of public channels.
    
    Headers:
        Authorization: Bearer <token>
    
    Query parameters:
        limit: Maximum results (default: 50, max: 100)
        include_archived: Include archived channels (default: false)
    
    Returns:
        200: List of public channels
        401: Not authenticated
        400: Invalid parameters
    """
    try:
        limit = request.args.get('limit', 50, type=int)
        include_archived = request.args.get('include_archived', 'false').lower() == 'true'
        
        if limit < 1 or limit > 100:
            return jsonify({'error': 'limit must be between 1 and 100'}), 400
        
        channels = ChannelService.get_public_channels(limit, include_archived)
        
        channels_data = [channel.to_dict() for channel in channels]
        
        return jsonify({
            'channels': channels_data,
            'total': len(channels_data)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@channels_bp.route('/search', methods=['GET'])
@require_auth
def search_channels():
    """
    Search for channels by name or description.
    
    Headers:
        Authorization: Bearer <token>
    
    Query parameters:
        q: Search query (required, min 2 chars)
        limit: Maximum results (default: 20, max: 50)
    
    Returns:
        200: List of matching channels
        401: Not authenticated
        400: Invalid parameters or missing query
    """
    try:
        user = g.current_user
        query = request.args.get('q', '').strip()
        limit = request.args.get('limit', 20, type=int)
        
        if not query or len(query) < 2:
            return jsonify({'error': 'Search query must be at least 2 characters'}), 400
        
        if limit < 1 or limit > 50:
            return jsonify({'error': 'limit must be between 1 and 50'}), 400
        
        channels = ChannelService.search_channels(user, query, limit)
        
        channels_data = [channel.to_dict() for channel in channels]
        
        return jsonify({
            'channels': channels_data,
            'total': len(channels_data),
            'query': query
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@channels_bp.route('', methods=['POST'])
@require_auth
def create_channel():
    """
    Create a new channel.
    
    Headers:
        Authorization: Bearer <token>
    
    Request body:
    {
        "name": "string (3-50 chars, lowercase + hyphens)",
        "display_name": "string (optional)",
        "description": "string (optional, max 500 chars)",
        "is_private": "boolean (optional, default: false)",
        "max_members": "number (optional, default: 50, range: 2-200)"
    }
    
    Returns:
        201: Channel created successfully
        400: Validation error
        403: Insufficient permissions
        401: Not authenticated
    """
    try:
        user = g.current_user
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        name = data.get('name')
        display_name = data.get('display_name')
        description = data.get('description')
        is_private = data.get('is_private', False)
        max_members = data.get('max_members', 50)
        
        if not name:
            return jsonify({'error': 'name is required'}), 400
        
        channel = ChannelService.create_channel(
            creator=user,
            name=name,
            display_name=display_name,
            description=description,
            is_private=is_private,
            max_members=max_members
        )
        
        return jsonify({
            'message': 'Channel created successfully',
            'channel': channel.to_dict()
        }), 201
        
    except ChannelError as e:
        return jsonify({'error': str(e)}), 400
    except AuthorizationError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@channels_bp.route('/<channel_id>', methods=['GET'])
@require_auth
def get_channel(channel_id):
    """
    Get channel information.
    
    Headers:
        Authorization: Bearer <token>
    
    Args:
        channel_id: Channel ID
    
    Returns:
        200: Channel information
        404: Channel not found
        403: Cannot access private channel
        401: Not authenticated
    """
    try:
        user = g.current_user
        
        from models.channel import Channel
        from models.channel_membership import ChannelMembership
        
        channel = Channel.query.get(channel_id)
        if not channel:
            return jsonify({'error': 'Channel not found'}), 404
        
        # Check access permissions
        if channel.is_private:
            membership = ChannelMembership.query.filter_by(
                channel_id=channel_id,
                user_id=str(user.id)
            ).first()
            
            if not membership:
                return jsonify({'error': 'Access denied to private channel'}), 403
        
        # Get user's membership info if they're a member
        user_membership = ChannelMembership.query.filter_by(
            channel_id=channel_id,
            user_id=str(user.id)
        ).first()
        
        response_data = {
            'channel': channel.to_dict(),
            'is_member': user_membership is not None
        }
        
        if user_membership:
            response_data['membership'] = user_membership.to_dict()
        
        return jsonify(response_data), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@channels_bp.route('/<channel_id>', methods=['PUT'])
@require_auth
def update_channel(channel_id):
    """
    Update channel information.
    
    Headers:
        Authorization: Bearer <token>
    
    Args:
        channel_id: Channel ID
    
    Request body:
    {
        "display_name": "string (optional)",
        "description": "string (optional, max 500 chars)",
        "max_members": "number (optional, range: 2-200)"
    }
    
    Returns:
        200: Channel updated
        404: Channel not found
        403: Insufficient permissions
        400: Validation error
        401: Not authenticated
    """
    try:
        user = g.current_user
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        display_name = data.get('display_name')
        description = data.get('description')
        max_members = data.get('max_members')
        
        success = ChannelService.update_channel_info(
            user=user,
            channel_id=channel_id,
            display_name=display_name,
            description=description,
            max_members=max_members
        )
        
        if success:
            from models.channel import Channel
            channel = Channel.query.get(channel_id)
            return jsonify({
                'message': 'Channel updated successfully',
                'channel': channel.to_dict() if channel else None
            }), 200
        else:
            return jsonify({'error': 'Channel update failed'}), 500
            
    except ChannelError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@channels_bp.route('/<channel_id>/join', methods=['POST'])
@require_auth
def join_channel(channel_id):
    """
    Join a channel.
    
    Headers:
        Authorization: Bearer <token>
    
    Args:
        channel_id: Channel ID
    
    Returns:
        200: Successfully joined channel
        404: Channel not found
        400: Cannot join channel
        401: Not authenticated
    """
    try:
        user = g.current_user
        
        success = ChannelService.join_channel(user, channel_id)
        
        if success:
            return jsonify({'message': 'Successfully joined channel'}), 200
        else:
            return jsonify({'error': 'Failed to join channel'}), 500
            
    except ChannelError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@channels_bp.route('/<channel_id>/leave', methods=['POST'])
@require_auth
def leave_channel(channel_id):
    """
    Leave a channel.
    
    Headers:
        Authorization: Bearer <token>
    
    Args:
        channel_id: Channel ID
    
    Returns:
        200: Successfully left channel
        404: Channel not found
        400: Cannot leave channel
        401: Not authenticated
    """
    try:
        user = g.current_user
        
        success = ChannelService.leave_channel(user, channel_id)
        
        if success:
            return jsonify({'message': 'Successfully left channel'}), 200
        else:
            return jsonify({'error': 'Failed to leave channel'}), 500
            
    except ChannelError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@channels_bp.route('/<channel_id>/members', methods=['GET'])
@require_auth
def get_channel_members(channel_id):
    """
    Get list of channel members.
    
    Headers:
        Authorization: Bearer <token>
    
    Args:
        channel_id: Channel ID
    
    Returns:
        200: List of channel members
        404: Channel not found
        403: Not a channel member
        401: Not authenticated
    """
    try:
        user = g.current_user
        
        members = ChannelService.get_channel_members(user, channel_id)
        
        return jsonify({
            'members': members,
            'total': len(members)
        }), 200
        
    except ChannelError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@channels_bp.route('/<channel_id>/stats', methods=['GET'])
@require_auth
def get_channel_stats(channel_id):
    """
    Get channel statistics.
    
    Headers:
        Authorization: Bearer <token>
    
    Args:
        channel_id: Channel ID
    
    Returns:
        200: Channel statistics
        404: Channel not found
        403: Not a channel member
        401: Not authenticated
    """
    try:
        user = g.current_user
        
        stats = ChannelService.get_channel_stats(user, channel_id)
        
        return jsonify(stats), 200
        
    except ChannelError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@channels_bp.route('/<channel_id>/invite', methods=['POST'])
@require_auth
def invite_user_to_channel(channel_id):
    """
    Invite a user to a private channel.
    
    Headers:
        Authorization: Bearer <token>
    
    Args:
        channel_id: Channel ID
    
    Request body:
    {
        "user_id": "string (user ID to invite)"
    }
    
    Returns:
        200: User invited successfully
        404: Channel or user not found
        403: Insufficient permissions
        400: Cannot invite user
        401: Not authenticated
    """
    try:
        user = g.current_user
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        target_user_id = data.get('user_id')
        
        if not target_user_id:
            return jsonify({'error': 'user_id is required'}), 400
        
        from models.user import User
        target_user = User.query.get(target_user_id)
        if not target_user:
            return jsonify({'error': 'User not found'}), 404
        
        success = ChannelService.join_channel(target_user, channel_id, invited_by=user)
        
        if success:
            return jsonify({'message': f'User {target_user.display_name} invited successfully'}), 200
        else:
            return jsonify({'error': 'Failed to invite user'}), 500
            
    except ChannelError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


# Moderation endpoints (require moderation privileges)
@channels_bp.route('/<channel_id>/members/<user_id>/kick', methods=['POST'])
@require_auth
def kick_user(channel_id, user_id):
    """
    Remove a user from a channel.
    
    Headers:
        Authorization: Bearer <token>
    
    Args:
        channel_id: Channel ID
        user_id: User ID to kick
    
    Returns:
        200: User removed successfully
        404: Channel or user not found
        403: Insufficient permissions
        400: Cannot remove user
        401: Not authenticated
    """
    try:
        moderator = g.current_user
        
        success = ChannelService.kick_user(moderator, channel_id, user_id)
        
        if success:
            return jsonify({'message': 'User removed from channel successfully'}), 200
        else:
            return jsonify({'error': 'Failed to remove user from channel'}), 500
            
    except ChannelError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@channels_bp.route('/<channel_id>/members/<user_id>/role', methods=['PUT'])
@require_auth
def update_member_role(channel_id, user_id):
    """
    Update a member's role in a channel.
    
    Headers:
        Authorization: Bearer <token>
    
    Args:
        channel_id: Channel ID
        user_id: User ID to update
    
    Request body:
    {
        "role": "string (member|moderator|admin)"
    }
    
    Returns:
        200: Role updated successfully
        404: Channel or user not found
        403: Insufficient permissions
        400: Invalid role or cannot update role
        401: Not authenticated
    """
    try:
        moderator = g.current_user
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        role_str = data.get('role')
        
        if not role_str:
            return jsonify({'error': 'role is required'}), 400
        
        try:
            new_role = MembershipRole(role_str.lower())
        except ValueError:
            return jsonify({'error': 'Invalid role. Must be member, moderator, or admin'}), 400
        
        success = ChannelService.update_member_role(moderator, channel_id, user_id, new_role)
        
        if success:
            return jsonify({'message': f'Member role updated to {new_role.value} successfully'}), 200
        else:
            return jsonify({'error': 'Failed to update member role'}), 500
            
    except ChannelError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@channels_bp.route('/<channel_id>/members/<user_id>/mute', methods=['POST'])
@require_auth
def mute_user(channel_id, user_id):
    """
    Mute a user in a channel.
    
    Headers:
        Authorization: Bearer <token>
    
    Args:
        channel_id: Channel ID
        user_id: User ID to mute
    
    Returns:
        200: User muted successfully
        404: Channel or user not found
        403: Insufficient permissions
        400: Cannot mute user
        401: Not authenticated
    """
    try:
        moderator = g.current_user
        
        success = ChannelService.mute_user(moderator, channel_id, user_id)
        
        if success:
            return jsonify({'message': 'User muted successfully'}), 200
        else:
            return jsonify({'error': 'Failed to mute user'}), 500
            
    except ChannelError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@channels_bp.route('/<channel_id>/members/<user_id>/unmute', methods=['POST'])
@require_auth
def unmute_user(channel_id, user_id):
    """
    Unmute a user in a channel.
    
    Headers:
        Authorization: Bearer <token>
    
    Args:
        channel_id: Channel ID
        user_id: User ID to unmute
    
    Returns:
        200: User unmuted successfully
        404: Channel or user not found
        403: Insufficient permissions
        400: Cannot unmute user
        401: Not authenticated
    """
    try:
        moderator = g.current_user
        
        success = ChannelService.unmute_user(moderator, channel_id, user_id)
        
        if success:
            return jsonify({'message': 'User unmuted successfully'}), 200
        else:
            return jsonify({'error': 'Failed to unmute user'}), 500
            
    except ChannelError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


# Admin endpoints
@channels_bp.route('/<channel_id>/archive', methods=['POST'])
@require_auth
@require_permission('can_delete_channels')
def archive_channel(channel_id):
    """
    Archive a channel (admin only).
    
    Headers:
        Authorization: Bearer <token>
    
    Args:
        channel_id: Channel ID
    
    Returns:
        200: Channel archived successfully
        404: Channel not found
        403: Insufficient permissions
        400: Cannot archive channel
        401: Not authenticated
    """
    try:
        admin = g.current_user
        
        success = ChannelService.archive_channel(admin, channel_id)
        
        if success:
            return jsonify({'message': 'Channel archived successfully'}), 200
        else:
            return jsonify({'error': 'Failed to archive channel'}), 500
            
    except ChannelError as e:
        return jsonify({'error': str(e)}), 400
    except AuthorizationError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@channels_bp.route('/<channel_id>/unarchive', methods=['POST'])
@require_auth
@require_permission('can_delete_channels')
def unarchive_channel(channel_id):
    """
    Unarchive a channel (admin only).
    
    Headers:
        Authorization: Bearer <token>
    
    Args:
        channel_id: Channel ID
    
    Returns:
        200: Channel unarchived successfully
        404: Channel not found
        403: Insufficient permissions
        400: Cannot unarchive channel
        401: Not authenticated
    """
    try:
        admin = g.current_user
        
        success = ChannelService.unarchive_channel(admin, channel_id)
        
        if success:
            return jsonify({'message': 'Channel unarchived successfully'}), 200
        else:
            return jsonify({'error': 'Failed to unarchive channel'}), 500
            
    except ChannelError as e:
        return jsonify({'error': str(e)}), 400
    except AuthorizationError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


# Health check endpoint
@channels_bp.route('/health', methods=['GET'])
def channels_health():
    """
    Channels service health check.
    
    Returns:
        200: Service healthy
    """
    return jsonify({
        'service': 'channels',
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    }), 200


# Error handlers for the channels blueprint
@channels_bp.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), 400


@channels_bp.errorhandler(401)
def unauthorized(error):
    return jsonify({'error': 'Unauthorized'}), 401


@channels_bp.errorhandler(403)
def forbidden(error):
    return jsonify({'error': 'Forbidden'}), 403


@channels_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404


@channels_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500