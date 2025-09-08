"""
Authentication API endpoints for DankerChat application.

Provides REST endpoints for user authentication, registration, and session management.
Based on specs/001-chat-application/tasks.md T044
"""

from flask import Blueprint, request, jsonify, g
from datetime import datetime

from services.auth import AuthService, AuthenticationError, AuthorizationError, require_auth
from models.session import InterfaceType
from models.user import User


auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user account.
    
    Request body:
    {
        "username": "string (3-30 chars)",
        "password": "string (8-128 chars)", 
        "email": "string (valid email)",
        "display_name": "string (optional)"
    }
    
    Returns:
        201: User created successfully
        400: Validation error or user exists
        500: Server error
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        display_name = data.get('display_name')
        
        if not all([username, password, email]):
            return jsonify({'error': 'Username, password, and email are required'}), 400
        
        # Register user
        user, success = AuthService.register_user(
            username=username,
            password=password,
            email=email,
            display_name=display_name
        )
        
        if success:
            return jsonify({
                'message': 'User registered successfully',
                'user': user.to_dict()
            }), 201
        else:
            return jsonify({'error': 'Registration failed'}), 500
            
    except AuthenticationError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login user and create session.
    
    Request body:
    {
        "username": "string (username or email)",
        "password": "string",
        "interface_type": "string (web|cli|api, optional, default: web)",
        "expires_in_hours": "number (optional, default: 24)"
    }
    
    Returns:
        200: Login successful with token
        401: Invalid credentials
        500: Server error
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        username = data.get('username')
        password = data.get('password')
        interface_type_str = data.get('interface_type', 'web')
        expires_in_hours = data.get('expires_in_hours', 24)
        
        if not all([username, password]):
            return jsonify({'error': 'Username and password are required'}), 400
        
        # Validate interface type
        try:
            interface_type = InterfaceType(interface_type_str.lower())
        except ValueError:
            return jsonify({'error': 'Invalid interface_type. Must be web, cli, or api'}), 400
        
        # Validate expires_in_hours
        if not isinstance(expires_in_hours, (int, float)) or expires_in_hours <= 0 or expires_in_hours > 168:
            return jsonify({'error': 'expires_in_hours must be between 1 and 168'}), 400
        
        # Attempt login
        result = AuthService.login(
            username=username,
            password=password,
            interface_type=interface_type,
            expires_in_hours=int(expires_in_hours)
        )
        
        if result:
            return jsonify({
                'message': 'Login successful',
                'user': result['user'].to_dict(),
                'token': result['token'],
                'expires_at': result['expires_at'],
                'session_id': str(result['session'].id)
            }), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
            
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/logout', methods=['POST'])
@require_auth
def logout():
    """
    Logout current session.
    
    Headers:
        Authorization: Bearer <token>
    
    Returns:
        200: Logout successful
        401: Not authenticated
    """
    try:
        # Get current session from auth decorator
        session = g.current_session
        
        success = AuthService.logout(session.token_jti)
        
        if success:
            return jsonify({'message': 'Logout successful'}), 200
        else:
            return jsonify({'error': 'Logout failed'}), 500
            
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/logout-all', methods=['POST'])
@require_auth
def logout_all():
    """
    Logout all sessions for current user.
    
    Headers:
        Authorization: Bearer <token>
    
    Returns:
        200: All sessions logged out
        401: Not authenticated
    """
    try:
        user = g.current_user
        
        revoked_count = AuthService.logout_all_sessions(str(user.id))
        
        return jsonify({
            'message': 'All sessions logged out successfully',
            'sessions_revoked': revoked_count
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/refresh', methods=['POST'])
def refresh_token():
    """
    Refresh JWT token.
    
    Request body:
    {
        "token": "string (current JWT token)",
        "extends_hours": "number (optional, default: 24)"
    }
    
    Returns:
        200: New token issued
        401: Token invalid or expired
        400: Invalid request
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        token = data.get('token')
        extends_hours = data.get('extends_hours', 24)
        
        if not token:
            return jsonify({'error': 'Token is required'}), 400
        
        if not isinstance(extends_hours, (int, float)) or extends_hours <= 0 or extends_hours > 168:
            return jsonify({'error': 'extends_hours must be between 1 and 168'}), 400
        
        new_token = AuthService.refresh_token(token, int(extends_hours))
        
        if new_token:
            return jsonify({
                'message': 'Token refreshed successfully',
                'token': new_token
            }), 200
        else:
            return jsonify({'error': 'Token refresh failed'}), 401
            
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/validate', methods=['POST'])
def validate_token():
    """
    Validate JWT token and return user info.
    
    Request body:
    {
        "token": "string (JWT token)"
    }
    
    Returns:
        200: Token valid with user info
        401: Token invalid or expired
        400: Invalid request
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        token = data.get('token')
        
        if not token:
            return jsonify({'error': 'Token is required'}), 400
        
        auth_data = AuthService.validate_token(token)
        
        if auth_data:
            return jsonify({
                'message': 'Token valid',
                'user': auth_data['user'].to_dict(),
                'session': auth_data['session'].to_dict(),
                'permissions': AuthService.get_user_permissions(auth_data['user'])
            }), 200
        else:
            return jsonify({'error': 'Token invalid or expired'}), 401
            
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/me', methods=['GET'])
@require_auth
def get_current_user():
    """
    Get current authenticated user info.
    
    Headers:
        Authorization: Bearer <token>
    
    Returns:
        200: User info
        401: Not authenticated
    """
    try:
        user = g.current_user
        session = g.current_session
        
        return jsonify({
            'user': user.to_dict(),
            'session': session.to_dict(),
            'permissions': AuthService.get_user_permissions(user),
            'role': user.role.name if user.role else None
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/change-password', methods=['POST'])
@require_auth
def change_password():
    """
    Change user password.
    
    Headers:
        Authorization: Bearer <token>
    
    Request body:
    {
        "current_password": "string",
        "new_password": "string"
    }
    
    Returns:
        200: Password changed successfully
        400: Invalid passwords or validation error
        401: Not authenticated
    """
    try:
        user = g.current_user
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not all([current_password, new_password]):
            return jsonify({'error': 'Current password and new password are required'}), 400
        
        success = AuthService.change_password(user, current_password, new_password)
        
        if success:
            return jsonify({'message': 'Password changed successfully. Please login again.'}), 200
        else:
            return jsonify({'error': 'Current password is incorrect'}), 400
            
    except AuthenticationError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/sessions', methods=['GET'])
@require_auth
def get_user_sessions():
    """
    Get active sessions for current user.
    
    Headers:
        Authorization: Bearer <token>
    
    Returns:
        200: List of active sessions
        401: Not authenticated
    """
    try:
        user = g.current_user
        
        from models.session import Session
        active_sessions = Session.get_active_user_sessions(str(user.id))
        
        sessions_data = [session.to_dict() for session in active_sessions]
        
        return jsonify({
            'sessions': sessions_data,
            'total': len(sessions_data)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/sessions/<session_id>', methods=['DELETE'])
@require_auth
def revoke_session(session_id):
    """
    Revoke a specific session.
    
    Headers:
        Authorization: Bearer <token>
    
    Args:
        session_id: Session ID to revoke
    
    Returns:
        200: Session revoked
        404: Session not found
        403: Cannot revoke session
        401: Not authenticated
    """
    try:
        user = g.current_user
        current_session = g.current_session
        
        from models.session import Session
        target_session = Session.query.get(session_id)
        
        if not target_session:
            return jsonify({'error': 'Session not found'}), 404
        
        # Can only revoke own sessions
        if str(target_session.user_id) != str(user.id):
            return jsonify({'error': 'Cannot revoke this session'}), 403
        
        # Cannot revoke current session (use logout instead)
        if str(target_session.id) == str(current_session.id):
            return jsonify({'error': 'Cannot revoke current session. Use logout instead.'}), 400
        
        success = AuthService.logout(target_session.token_jti)
        
        if success:
            return jsonify({'message': 'Session revoked successfully'}), 200
        else:
            return jsonify({'error': 'Failed to revoke session'}), 500
            
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


# Health check endpoint for authentication service
@auth_bp.route('/health', methods=['GET'])
def auth_health():
    """
    Authentication service health check.
    
    Returns:
        200: Service healthy
    """
    return jsonify({
        'service': 'authentication',
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    }), 200


# Error handlers for the auth blueprint
@auth_bp.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), 400


@auth_bp.errorhandler(401)
def unauthorized(error):
    return jsonify({'error': 'Unauthorized'}), 401


@auth_bp.errorhandler(403)
def forbidden(error):
    return jsonify({'error': 'Forbidden'}), 403


@auth_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404


@auth_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500