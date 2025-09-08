"""
Authentication service for DankerChat application.

Handles user authentication, registration, session management, and JWT tokens.
Based on specs/001-chat-application/tasks.md T033
"""

import bcrypt
import jwt
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from flask import current_app

from database import db
from models.user import User
from models.role import Role
from models.session import Session, InterfaceType


class AuthenticationError(Exception):
    """Custom exception for authentication errors."""
    pass


class AuthorizationError(Exception):
    """Custom exception for authorization errors."""
    pass


class AuthService:
    """
    Authentication and authorization service.
    
    Provides methods for user registration, login, logout, session management,
    and JWT token creation/validation.
    """
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password string
        """
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            password: Plain text password
            password_hash: Hashed password
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception:
            return False
    
    @classmethod
    def register_user(cls, username: str, password: str, email: str,
                     display_name: Optional[str] = None,
                     role_name: str = 'user') -> Tuple[User, bool]:
        """
        Register a new user.
        
        Args:
            username: Unique username (3-30 chars, alphanumeric + underscore/hyphen)
            password: Password (8-128 chars)
            email: Valid email address
            display_name: Optional display name (defaults to username)
            role_name: Role name (defaults to 'user')
            
        Returns:
            Tuple of (User object, success boolean)
            
        Raises:
            AuthenticationError: If validation fails or user exists
        """
        # Validate input
        if not cls._validate_username(username):
            raise AuthenticationError("Invalid username format")
        
        if not cls._validate_password(password):
            raise AuthenticationError("Invalid password format")
        
        if not cls._validate_email(email):
            raise AuthenticationError("Invalid email format")
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            raise AuthenticationError("Username already exists")
        
        if User.query.filter_by(email=email).first():
            raise AuthenticationError("Email already registered")
        
        # Get role
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            raise AuthenticationError(f"Role '{role_name}' not found")
        
        # Create user
        user = User(
            username=username,
            password_hash=cls.hash_password(password),
            email=email,
            display_name=display_name or username,
            role_id=str(role.id)
        )
        
        try:
            db.session.add(user)
            db.session.commit()
            return user, True
        except Exception as e:
            db.session.rollback()
            raise AuthenticationError(f"Failed to create user: {str(e)}")
    
    @classmethod
    def authenticate_user(cls, username: str, password: str) -> Optional[User]:
        """
        Authenticate a user with username and password.
        
        Args:
            username: Username or email
            password: Password
            
        Returns:
            User object if authentication successful, None otherwise
        """
        # Try to find user by username or email
        user = (User.query.filter_by(username=username).first() or
                User.query.filter_by(email=username).first())
        
        if not user:
            return None
        
        if not user.is_active:
            return None
        
        if not cls.verify_password(password, user.password_hash):
            return None
        
        # Update last login
        user.update_last_login()
        db.session.commit()
        
        return user
    
    @classmethod
    def create_session(cls, user: User, interface_type: InterfaceType,
                      expires_in_hours: int = 24) -> Tuple[Session, str]:
        """
        Create a new session and JWT token for a user.
        
        Args:
            user: User object
            interface_type: Type of interface (web, cli, api)
            expires_in_hours: Session expiration time
            
        Returns:
            Tuple of (Session object, JWT token string)
        """
        # Generate token JTI (JWT ID)
        token_jti = str(uuid.uuid4())
        
        # Create session
        session = Session(
            user_id=str(user.id),
            token_jti=token_jti,
            interface_type=interface_type,
            expires_in_hours=expires_in_hours
        )
        
        db.session.add(session)
        db.session.commit()
        
        # Create JWT token
        token = cls._create_jwt_token(user, session, expires_in_hours)
        
        return session, token
    
    @classmethod
    def login(cls, username: str, password: str, interface_type: InterfaceType,
              expires_in_hours: int = 24) -> Optional[Dict[str, Any]]:
        """
        Complete login process: authenticate user and create session.
        
        Args:
            username: Username or email
            password: Password
            interface_type: Interface type
            expires_in_hours: Session duration
            
        Returns:
            Login result dict with user, session, and token, or None if failed
        """
        user = cls.authenticate_user(username, password)
        if not user:
            return None
        
        session, token = cls.create_session(user, interface_type, expires_in_hours)
        
        return {
            'user': user,
            'session': session,
            'token': token,
            'expires_at': session.expires_at.isoformat()
        }
    
    @classmethod
    def logout(cls, token_jti: str) -> bool:
        """
        Logout by revoking a session.
        
        Args:
            token_jti: JWT token identifier
            
        Returns:
            True if logout successful, False if session not found
        """
        session = Session.find_by_token_jti(token_jti)
        if session:
            session.revoke()
            db.session.commit()
            return True
        return False
    
    @classmethod
    def logout_all_sessions(cls, user_id: str) -> int:
        """
        Logout all sessions for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of sessions revoked
        """
        return Session.revoke_user_sessions(user_id)
    
    @classmethod
    def validate_token(cls, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate a JWT token and return user/session info.
        
        Args:
            token: JWT token string
            
        Returns:
            Dict with user and session info, or None if invalid
        """
        try:
            # Decode token
            payload = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )
            
            # Get session
            session = Session.find_by_token_jti(payload['jti'])
            if not session or not session.is_active():
                return None
            
            # Update session activity
            session.update_activity()
            db.session.commit()
            
            return {
                'user': session.user,
                'session': session,
                'payload': payload
            }
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        except Exception:
            return None
    
    @classmethod
    def refresh_token(cls, token: str, extends_hours: int = 24) -> Optional[str]:
        """
        Refresh a JWT token by extending its expiration.
        
        Args:
            token: Current JWT token
            extends_hours: Hours to extend
            
        Returns:
            New JWT token string, or None if refresh failed
        """
        token_data = cls.validate_token(token)
        if not token_data:
            return None
        
        session = token_data['session']
        user = token_data['user']
        
        # Extend session expiration
        session.extend_expiration(extends_hours)
        db.session.commit()
        
        # Create new token
        return cls._create_jwt_token(user, session, extends_hours)
    
    @classmethod
    def get_user_permissions(cls, user: User) -> Dict[str, bool]:
        """
        Get permissions for a user based on their role.
        
        Args:
            user: User object
            
        Returns:
            Dictionary of permission keys and boolean values
        """
        if not user.role:
            return {}
        
        return user.role.permissions or {}
    
    @classmethod
    def user_has_permission(cls, user: User, permission: str) -> bool:
        """
        Check if user has a specific permission.
        
        Args:
            user: User object
            permission: Permission key to check
            
        Returns:
            True if user has permission, False otherwise
        """
        permissions = cls.get_user_permissions(user)
        return permissions.get(permission, False)
    
    @classmethod
    def require_permission(cls, user: User, permission: str) -> None:
        """
        Require user to have a specific permission.
        
        Args:
            user: User object
            permission: Required permission
            
        Raises:
            AuthorizationError: If user lacks permission
        """
        if not cls.user_has_permission(user, permission):
            raise AuthorizationError(f"Permission '{permission}' required")
    
    @classmethod
    def change_password(cls, user: User, current_password: str, new_password: str) -> bool:
        """
        Change user's password.
        
        Args:
            user: User object
            current_password: Current password for verification
            new_password: New password
            
        Returns:
            True if password changed successfully, False if current password invalid
            
        Raises:
            AuthenticationError: If new password is invalid
        """
        # Verify current password
        if not cls.verify_password(current_password, user.password_hash):
            return False
        
        # Validate new password
        if not cls._validate_password(new_password):
            raise AuthenticationError("Invalid new password format")
        
        # Update password
        user.password_hash = cls.hash_password(new_password)
        user.password_changed_at = datetime.utcnow()
        
        # Revoke all existing sessions to force re-login
        Session.revoke_user_sessions(str(user.id))
        
        db.session.commit()
        return True
    
    @classmethod
    def cleanup_expired_sessions(cls) -> int:
        """
        Clean up expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        return Session.cleanup_expired_sessions()
    
    @classmethod
    def _create_jwt_token(cls, user: User, session: Session, expires_in_hours: int) -> str:
        """
        Create a JWT token for a user session.
        
        Args:
            user: User object
            session: Session object
            expires_in_hours: Token expiration time
            
        Returns:
            JWT token string
        """
        payload = {
            'user_id': str(user.id),
            'username': user.username,
            'role': user.role.name if user.role else 'user',
            'interface_type': session.interface_type.value,
            'jti': session.token_jti,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=expires_in_hours)
        }
        
        return jwt.encode(
            payload,
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )
    
    @staticmethod
    def _validate_username(username: str) -> bool:
        """
        Validate username format.
        
        Args:
            username: Username to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not username or not isinstance(username, str):
            return False
        
        if len(username) < 3 or len(username) > 30:
            return False
        
        # Only alphanumeric characters, underscore, and hyphen
        return all(c.isalnum() or c in ['_', '-'] for c in username)
    
    @staticmethod
    def _validate_password(password: str) -> bool:
        """
        Validate password format.
        
        Args:
            password: Password to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not password or not isinstance(password, str):
            return False
        
        return len(password) >= 8 and len(password) <= 128
    
    @staticmethod
    def _validate_email(email: str) -> bool:
        """
        Validate email format.
        
        Args:
            email: Email to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not email or not isinstance(email, str):
            return False
        
        # Basic email validation
        if '@' not in email or '.' not in email:
            return False
        
        parts = email.split('@')
        if len(parts) != 2:
            return False
        
        local, domain = parts
        if not local or not domain:
            return False
        
        if len(email) > 254:  # RFC 5321 limit
            return False
        
        return True


# Helper decorator for route authentication
def require_auth(f):
    """Decorator to require authentication for a route."""
    from functools import wraps
    from flask import request, jsonify, g
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'error': 'Token missing'}), 401
        
        # Validate token
        auth_data = AuthService.validate_token(token)
        if not auth_data:
            return jsonify({'error': 'Token invalid or expired'}), 401
        
        # Store user and session in Flask's g object
        g.current_user = auth_data['user']
        g.current_session = auth_data['session']
        
        return f(*args, **kwargs)
    
    return decorated_function


def require_permission(permission: str):
    """Decorator to require specific permission for a route."""
    def decorator(f):
        from functools import wraps
        from flask import jsonify, g
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'current_user') or not g.current_user:
                return jsonify({'error': 'Authentication required'}), 401
            
            if not AuthService.user_has_permission(g.current_user, permission):
                return jsonify({'error': f'Permission "{permission}" required'}), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator