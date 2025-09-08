"""
User API endpoints for DankerChat application.

Provides REST endpoints for user management, profiles, and user-related operations.
Based on specs/001-chat-application/tasks.md T045
"""

from flask import Blueprint, request, jsonify, g
from datetime import datetime

from services.auth import require_auth, require_permission
from services.users import UserService, UserError
from services.auth import AuthService, AuthenticationError, AuthorizationError
from models.user import User


users_bp = Blueprint('users', __name__, url_prefix='/api/users')


@users_bp.route('', methods=['GET'])
@require_auth
def get_users():
    """
    Get list of users (search functionality).
    
    Headers:
        Authorization: Bearer <token>
    
    Query parameters:
        q: Search query (username, display name, or email)
        limit: Maximum results (default: 20, max: 100)
        include_inactive: Include inactive users (default: false)
    
    Returns:
        200: List of users
        401: Not authenticated
        400: Invalid parameters
    """
    try:
        query = request.args.get('q', '').strip()
        limit = request.args.get('limit', 20, type=int)
        include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
        
        # Validate limit
        if limit < 1 or limit > 100:
            return jsonify({'error': 'limit must be between 1 and 100'}), 400
        
        if not query:
            return jsonify({'users': [], 'total': 0}), 200
        
        users = UserService.search_users(
            query=query,
            limit=limit,
            include_inactive=include_inactive
        )
        
        users_data = [user.to_dict() for user in users]
        
        return jsonify({
            'users': users_data,
            'total': len(users_data),
            'query': query
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@users_bp.route('/<user_id>', methods=['GET'])
@require_auth
def get_user(user_id):
    """
    Get user by ID.
    
    Headers:
        Authorization: Bearer <token>
    
    Args:
        user_id: User ID
    
    Returns:
        200: User info
        404: User not found
        401: Not authenticated
    """
    try:
        user = UserService.get_user_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if not user.is_active:
            return jsonify({'error': 'User account is inactive'}), 404
        
        return jsonify({'user': user.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@users_bp.route('/me', methods=['PUT'])
@require_auth
def update_profile():
    """
    Update current user's profile.
    
    Headers:
        Authorization: Bearer <token>
    
    Request body:
    {
        "display_name": "string (optional)",
        "bio": "string (optional, max 500 chars)",
        "status": "string (optional, max 100 chars)"
    }
    
    Returns:
        200: Profile updated
        400: Validation error
        401: Not authenticated
    """
    try:
        user = g.current_user
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        display_name = data.get('display_name')
        bio = data.get('bio')
        status = data.get('status')
        
        success = UserService.update_profile(
            user=user,
            display_name=display_name,
            bio=bio,
            status=status
        )
        
        if success:
            return jsonify({
                'message': 'Profile updated successfully',
                'user': user.to_dict()
            }), 200
        else:
            return jsonify({'error': 'Profile update failed'}), 500
            
    except UserError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@users_bp.route('/me/email', methods=['PUT'])
@require_auth
def change_email():
    """
    Change current user's email address.
    
    Headers:
        Authorization: Bearer <token>
    
    Request body:
    {
        "new_email": "string (valid email)",
        "password": "string (current password)"
    }
    
    Returns:
        200: Email changed
        400: Validation error or password incorrect
        401: Not authenticated
    """
    try:
        user = g.current_user
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        new_email = data.get('new_email')
        password = data.get('password')
        
        if not all([new_email, password]):
            return jsonify({'error': 'new_email and password are required'}), 400
        
        success = UserService.change_email(user, new_email, password)
        
        if success:
            return jsonify({
                'message': 'Email changed successfully. Please verify your new email address.',
                'user': user.to_dict()
            }), 200
        else:
            return jsonify({'error': 'Email change failed'}), 500
            
    except UserError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@users_bp.route('/me/stats', methods=['GET'])
@require_auth
def get_user_stats():
    """
    Get current user's statistics.
    
    Headers:
        Authorization: Bearer <token>
    
    Returns:
        200: User statistics
        401: Not authenticated
    """
    try:
        user = g.current_user
        
        stats = UserService.get_user_stats(user)
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@users_bp.route('/me/activity', methods=['GET'])
@require_auth
def get_user_activity():
    """
    Get current user's recent activity.
    
    Headers:
        Authorization: Bearer <token>
    
    Query parameters:
        days: Number of days to look back (default: 7, max: 30)
    
    Returns:
        200: User activity summary
        401: Not authenticated
        400: Invalid parameters
    """
    try:
        user = g.current_user
        days = request.args.get('days', 7, type=int)
        
        if days < 1 or days > 30:
            return jsonify({'error': 'days must be between 1 and 30'}), 400
        
        activity = UserService.get_user_activity(user, days)
        
        return jsonify(activity), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@users_bp.route('/me/channels', methods=['GET'])
@require_auth
def get_user_channels():
    """
    Get current user's channels.
    
    Headers:
        Authorization: Bearer <token>
    
    Query parameters:
        include_archived: Include archived channels (default: false)
    
    Returns:
        200: List of user's channels with membership info
        401: Not authenticated
    """
    try:
        user = g.current_user
        include_archived = request.args.get('include_archived', 'false').lower() == 'true'
        
        channels = UserService.get_user_channels(user, include_archived)
        
        return jsonify({
            'channels': channels,
            'total': len(channels)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@users_bp.route('/me/conversations', methods=['GET'])
@require_auth
def get_user_conversations():
    """
    Get current user's direct conversations.
    
    Headers:
        Authorization: Bearer <token>
    
    Returns:
        200: List of user's conversations
        401: Not authenticated
    """
    try:
        user = g.current_user
        
        conversations = UserService.get_user_conversations(user)
        
        return jsonify({
            'conversations': conversations,
            'total': len(conversations)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@users_bp.route('/me/permissions', methods=['GET'])
@require_auth
def get_user_permissions():
    """
    Get current user's permissions summary.
    
    Headers:
        Authorization: Bearer <token>
    
    Returns:
        200: User permissions and capabilities
        401: Not authenticated
    """
    try:
        user = g.current_user
        
        permissions = UserService.get_user_permissions_summary(user)
        
        return jsonify(permissions), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@users_bp.route('/online', methods=['GET'])
@require_auth
def get_online_users():
    """
    Get list of online users.
    
    Headers:
        Authorization: Bearer <token>
    
    Query parameters:
        limit: Maximum results (default: 50, max: 100)
    
    Returns:
        200: List of online users
        401: Not authenticated
        400: Invalid parameters
    """
    try:
        limit = request.args.get('limit', 50, type=int)
        
        if limit < 1 or limit > 100:
            return jsonify({'error': 'limit must be between 1 and 100'}), 400
        
        online_users = UserService.get_online_users(limit)
        
        users_data = [user.to_dict() for user in online_users]
        
        return jsonify({
            'users': users_data,
            'total': len(users_data),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


# Admin-only endpoints
@users_bp.route('/<user_id>/deactivate', methods=['POST'])
@require_auth
@require_permission('can_modify_users')
def deactivate_user(user_id):
    """
    Deactivate a user account (admin only).
    
    Headers:
        Authorization: Bearer <token>
    
    Args:
        user_id: User ID to deactivate
    
    Returns:
        200: User deactivated
        404: User not found
        403: Insufficient permissions
        400: Cannot deactivate user
        401: Not authenticated
    """
    try:
        admin = g.current_user
        
        success = UserService.deactivate_user(admin, user_id)
        
        if success:
            return jsonify({'message': 'User deactivated successfully'}), 200
        else:
            return jsonify({'error': 'User deactivation failed'}), 500
            
    except UserError as e:
        return jsonify({'error': str(e)}), 400
    except AuthorizationError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@users_bp.route('/<user_id>/reactivate', methods=['POST'])
@require_auth
@require_permission('can_modify_users')
def reactivate_user(user_id):
    """
    Reactivate a user account (admin only).
    
    Headers:
        Authorization: Bearer <token>
    
    Args:
        user_id: User ID to reactivate
    
    Returns:
        200: User reactivated
        404: User not found
        403: Insufficient permissions
        400: Cannot reactivate user
        401: Not authenticated
    """
    try:
        admin = g.current_user
        
        success = UserService.reactivate_user(admin, user_id)
        
        if success:
            return jsonify({'message': 'User reactivated successfully'}), 200
        else:
            return jsonify({'error': 'User reactivation failed'}), 500
            
    except UserError as e:
        return jsonify({'error': str(e)}), 400
    except AuthorizationError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@users_bp.route('/<user_id>/role', methods=['PUT'])
@require_auth
@require_permission('can_modify_users')
def change_user_role(user_id):
    """
    Change a user's role (admin only).
    
    Headers:
        Authorization: Bearer <token>
    
    Args:
        user_id: User ID to update
    
    Request body:
    {
        "role": "string (role name)"
    }
    
    Returns:
        200: Role changed
        404: User not found
        403: Insufficient permissions
        400: Invalid role or cannot change role
        401: Not authenticated
    """
    try:
        admin = g.current_user
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        new_role_name = data.get('role')
        
        if not new_role_name:
            return jsonify({'error': 'role is required'}), 400
        
        success = UserService.change_user_role(admin, user_id, new_role_name)
        
        if success:
            return jsonify({'message': f'User role changed to {new_role_name} successfully'}), 200
        else:
            return jsonify({'error': 'Role change failed'}), 500
            
    except UserError as e:
        return jsonify({'error': str(e)}), 400
    except AuthorizationError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@users_bp.route('/<user_id>/stats', methods=['GET'])
@require_auth
@require_permission('can_modify_users')
def get_user_admin_stats(user_id):
    """
    Get detailed user statistics (admin only).
    
    Headers:
        Authorization: Bearer <token>
    
    Args:
        user_id: User ID
    
    Returns:
        200: Detailed user statistics
        404: User not found
        403: Insufficient permissions
        401: Not authenticated
    """
    try:
        user = UserService.get_user_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        stats = UserService.get_user_stats(user)
        
        return jsonify(stats), 200
        
    except AuthorizationError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@users_bp.route('/<user_id>', methods=['DELETE'])
@require_auth
@require_permission('can_modify_users')
def delete_user_data(user_id):
    """
    Delete or anonymize user data (admin only, GDPR compliance).
    
    Headers:
        Authorization: Bearer <token>
    
    Args:
        user_id: User ID
    
    Query parameters:
        delete_messages: Delete messages instead of anonymizing (default: false)
    
    Returns:
        200: User data processed
        404: User not found
        403: Insufficient permissions
        400: Cannot delete user data
        401: Not authenticated
    """
    try:
        admin = g.current_user
        delete_messages = request.args.get('delete_messages', 'false').lower() == 'true'
        
        counts = UserService.delete_user_data(admin, user_id, delete_messages)
        
        return jsonify({
            'message': 'User data processed successfully',
            'processed_items': counts
        }), 200
        
    except UserError as e:
        return jsonify({'error': str(e)}), 400
    except AuthorizationError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


# Health check endpoint
@users_bp.route('/health', methods=['GET'])
def users_health():
    """
    Users service health check.
    
    Returns:
        200: Service healthy
    """
    return jsonify({
        'service': 'users',
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    }), 200


# Error handlers for the users blueprint
@users_bp.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), 400


@users_bp.errorhandler(401)
def unauthorized(error):
    return jsonify({'error': 'Unauthorized'}), 401


@users_bp.errorhandler(403)
def forbidden(error):
    return jsonify({'error': 'Forbidden'}), 403


@users_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404


@users_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500