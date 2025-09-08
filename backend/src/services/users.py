"""
User service for DankerChat application.

Handles user management, profile updates, and user-related operations.
Based on specs/001-chat-application/tasks.md T036
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import and_, or_

from database import db
from models.user import User
from models.role import Role
from models.session import Session, InterfaceType
from models.channel_membership import ChannelMembership
from models.direct_conversation import DirectConversation
from models.message import Message
from services.auth import AuthService, AuthorizationError


class UserError(Exception):
    """Custom exception for user errors."""
    pass


class UserService:
    """
    Service for handling user operations.
    
    Provides methods for user management, profile updates,
    and user-related queries.
    """
    
    @classmethod
    def get_user_by_id(cls, user_id: str) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User object or None if not found
        """
        return User.query.get(user_id)
    
    @classmethod
    def get_user_by_username(cls, username: str) -> Optional[User]:
        """
        Get user by username.
        
        Args:
            username: Username
            
        Returns:
            User object or None if not found
        """
        return User.query.filter_by(username=username).first()
    
    @classmethod
    def get_user_by_email(cls, email: str) -> Optional[User]:
        """
        Get user by email.
        
        Args:
            email: Email address
            
        Returns:
            User object or None if not found
        """
        return User.query.filter_by(email=email).first()
    
    @classmethod
    def update_profile(cls, user: User, display_name: Optional[str] = None,
                      bio: Optional[str] = None, status: Optional[str] = None) -> bool:
        """
        Update user profile information.
        
        Args:
            user: User to update
            display_name: New display name
            bio: New bio
            status: New status
            
        Returns:
            True if update successful
            
        Raises:
            UserError: If validation fails
        """
        if display_name is not None:
            if not User.validate_display_name(display_name):
                raise UserError("Invalid display name format")
            user.display_name = display_name
        
        if bio is not None:
            if not User.validate_bio(bio):
                raise UserError("Bio too long (max 500 characters)")
            user.bio = bio
        
        if status is not None:
            if not User.validate_status(status):
                raise UserError("Status too long (max 100 characters)")
            user.status = status
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return True
    
    @classmethod
    def change_email(cls, user: User, new_email: str, password: str) -> bool:
        """
        Change user's email address.
        
        Args:
            user: User to update
            new_email: New email address
            password: Current password for verification
            
        Returns:
            True if email changed successfully
            
        Raises:
            UserError: If validation fails or password incorrect
        """
        # Verify current password
        if not AuthService.verify_password(password, user.password_hash):
            raise UserError("Current password is incorrect")
        
        # Validate new email
        if not AuthService._validate_email(new_email):
            raise UserError("Invalid email format")
        
        # Check if email already exists
        existing_user = cls.get_user_by_email(new_email)
        if existing_user and existing_user.id != user.id:
            raise UserError("Email already registered to another user")
        
        user.email = new_email
        user.email_verified = False  # Require re-verification
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return True
    
    @classmethod
    def deactivate_user(cls, admin: User, user_id: str) -> bool:
        """
        Deactivate a user account.
        
        Args:
            admin: Admin performing the action
            user_id: User ID to deactivate
            
        Returns:
            True if deactivation successful
            
        Raises:
            UserError: If deactivation is not allowed
        """
        # Check admin permissions
        if not AuthService.user_has_permission(admin, 'can_modify_users'):
            raise AuthorizationError("Insufficient permissions to deactivate users")
        
        user = cls.get_user_by_id(user_id)
        if not user:
            raise UserError("User not found")
        
        if not user.is_active:
            raise UserError("User is already deactivated")
        
        # Cannot deactivate self
        if str(admin.id) == str(user_id):
            raise UserError("Cannot deactivate your own account")
        
        user.deactivate()
        
        # Revoke all user sessions
        Session.revoke_user_sessions(user_id)
        
        db.session.commit()
        
        return True
    
    @classmethod
    def reactivate_user(cls, admin: User, user_id: str) -> bool:
        """
        Reactivate a user account.
        
        Args:
            admin: Admin performing the action
            user_id: User ID to reactivate
            
        Returns:
            True if reactivation successful
            
        Raises:
            UserError: If reactivation is not allowed
        """
        # Check admin permissions
        if not AuthService.user_has_permission(admin, 'can_modify_users'):
            raise AuthorizationError("Insufficient permissions to reactivate users")
        
        user = cls.get_user_by_id(user_id)
        if not user:
            raise UserError("User not found")
        
        if user.is_active:
            raise UserError("User is already active")
        
        user.reactivate()
        db.session.commit()
        
        return True
    
    @classmethod
    def change_user_role(cls, admin: User, user_id: str, new_role_name: str) -> bool:
        """
        Change a user's role.
        
        Args:
            admin: Admin performing the action
            user_id: User ID to update
            new_role_name: New role name
            
        Returns:
            True if role change successful
            
        Raises:
            UserError: If role change is not allowed
        """
        # Check admin permissions
        if not AuthService.user_has_permission(admin, 'can_modify_users'):
            raise AuthorizationError("Insufficient permissions to change user roles")
        
        user = cls.get_user_by_id(user_id)
        if not user:
            raise UserError("User not found")
        
        # Get new role
        new_role = Role.query.filter_by(name=new_role_name).first()
        if not new_role:
            raise UserError(f"Role '{new_role_name}' not found")
        
        # Cannot change your own role
        if str(admin.id) == str(user_id):
            raise UserError("Cannot change your own role")
        
        # Update role
        old_role_name = user.role.name if user.role else 'unknown'
        user.role_id = str(new_role.id)
        user.updated_at = datetime.utcnow()
        
        # Revoke all user sessions to force re-authentication with new permissions
        Session.revoke_user_sessions(user_id)
        
        db.session.commit()
        
        return True
    
    @classmethod
    def search_users(cls, query: str, limit: int = 20, include_inactive: bool = False) -> List[User]:
        """
        Search for users by username, display name, or email.
        
        Args:
            query: Search query
            limit: Maximum results
            include_inactive: Whether to include inactive users
            
        Returns:
            List of matching User objects
        """
        if not query or len(query.strip()) < 2:
            return []
        
        base_query = User.query.filter(
            or_(
                User.username.ilike(f'%{query}%'),
                User.display_name.ilike(f'%{query}%'),
                User.email.ilike(f'%{query}%')
            )
        )
        
        if not include_inactive:
            base_query = base_query.filter_by(is_active=True)
        
        return base_query.order_by(User.username).limit(limit).all()
    
    @classmethod
    def get_user_stats(cls, user: User) -> Dict[str, Any]:
        """
        Get comprehensive statistics for a user.
        
        Args:
            user: User to get stats for
            
        Returns:
            Dictionary with user statistics
        """
        # Channel memberships
        channel_memberships = ChannelMembership.get_user_memberships(str(user.id))
        admin_channels = sum(1 for m in channel_memberships if m.is_admin())
        moderator_channels = sum(1 for m in channel_memberships if m.is_moderator())
        
        # Messages
        total_messages = Message.query.filter_by(
            sender_id=str(user.id),
            is_deleted=False
        ).count()
        
        channel_messages = Message.query.filter_by(
            sender_id=str(user.id),
            is_deleted=False
        ).filter(Message.channel_id.isnot(None)).count()
        
        direct_messages = Message.query.filter_by(
            sender_id=str(user.id),
            is_deleted=False
        ).filter(Message.direct_conversation_id.isnot(None)).count()
        
        # Direct conversations
        conversations = DirectConversation.get_user_conversations(str(user.id))
        
        # Active sessions
        active_sessions = Session.get_active_user_sessions(str(user.id))
        
        stats = {
            'user': user.to_dict(),
            'account': {
                'created_at': user.created_at.isoformat(),
                'last_login': user.last_login_at.isoformat() if user.last_login_at else None,
                'is_active': user.is_active,
                'email_verified': user.email_verified,
                'role': user.role.name if user.role else None
            },
            'channels': {
                'total_memberships': len(channel_memberships),
                'admin_channels': admin_channels,
                'moderator_channels': moderator_channels,
                'member_channels': len(channel_memberships) - admin_channels - moderator_channels
            },
            'messages': {
                'total_sent': total_messages,
                'channel_messages': channel_messages,
                'direct_messages': direct_messages
            },
            'conversations': {
                'total_conversations': len(conversations),
                'active_conversations': sum(1 for c in conversations if c.is_active())
            },
            'sessions': {
                'active_sessions': len(active_sessions),
                'session_types': [s.interface_type.value for s in active_sessions]
            }
        }
        
        return stats
    
    @classmethod
    def get_user_activity(cls, user: User, days: int = 7) -> Dict[str, Any]:
        """
        Get recent activity summary for a user.
        
        Args:
            user: User to get activity for
            days: Number of days to look back
            
        Returns:
            Dictionary with activity information
        """
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Recent messages
        recent_messages = Message.query.filter(
            Message.sender_id == str(user.id),
            Message.created_at >= cutoff_date,
            Message.is_deleted == False
        ).count()
        
        # New conversations
        new_conversations = DirectConversation.query.filter(
            or_(
                DirectConversation.participant1_id == str(user.id),
                DirectConversation.participant2_id == str(user.id)
            ),
            DirectConversation.created_at >= cutoff_date
        ).count()
        
        # Channel joins
        new_memberships = ChannelMembership.query.filter(
            ChannelMembership.user_id == str(user.id),
            ChannelMembership.joined_at >= cutoff_date
        ).count()
        
        activity = {
            'period_days': days,
            'cutoff_date': cutoff_date.isoformat(),
            'messages_sent': recent_messages,
            'new_conversations': new_conversations,
            'channels_joined': new_memberships,
            'last_seen': user.last_login_at.isoformat() if user.last_login_at else None
        }
        
        return activity
    
    @classmethod
    def get_user_channels(cls, user: User, include_archived: bool = False) -> List[Dict[str, Any]]:
        """
        Get all channels a user is a member of with membership details.
        
        Args:
            user: User to get channels for
            include_archived: Whether to include archived channels
            
        Returns:
            List of channel dictionaries with membership info
        """
        memberships = ChannelMembership.get_user_memberships(str(user.id))
        
        channels = []
        for membership in memberships:
            channel = membership.channel
            if channel and (include_archived or not channel.is_archived):
                channels.append({
                    'channel': channel.to_dict(),
                    'membership': {
                        'role': membership.role.value,
                        'joined_at': membership.joined_at.isoformat(),
                        'is_muted': membership.is_muted,
                        'can_send_messages': membership.can_send_messages(),
                        'has_moderation_privileges': membership.has_moderation_privileges()
                    }
                })
        
        return channels
    
    @classmethod
    def get_user_conversations(cls, user: User) -> List[Dict[str, Any]]:
        """
        Get all direct conversations for a user.
        
        Args:
            user: User to get conversations for
            
        Returns:
            List of conversation dictionaries
        """
        conversations = DirectConversation.get_user_conversations(str(user.id))
        
        result = []
        for conversation in conversations:
            other_user = conversation.get_other_participant(str(user.id))
            if other_user and other_user.is_active:
                last_message = conversation.get_last_message()
                result.append({
                    'conversation_id': str(conversation.id),
                    'other_user': other_user.to_dict(),
                    'created_at': conversation.created_at.isoformat(),
                    'last_message_at': conversation.last_message_at.isoformat() if conversation.last_message_at else None,
                    'last_message': last_message.to_dict() if last_message else None,
                    'unread_count': conversation.get_unread_count(str(user.id)),
                    'message_count': conversation.get_message_count()
                })
        
        return result
    
    @classmethod
    def get_online_users(cls, limit: int = 50) -> List[User]:
        """
        Get list of users with active sessions (online).
        
        Args:
            limit: Maximum number of users
            
        Returns:
            List of User objects with active sessions
        """
        # Get users with active sessions
        subquery = db.session.query(Session.user_id).filter(
            Session.is_revoked == False,
            Session.expires_at > datetime.utcnow()
        ).distinct().subquery()
        
        online_users = User.query.filter(
            User.id.in_(subquery),
            User.is_active == True
        ).order_by(User.display_name).limit(limit).all()
        
        return online_users
    
    @classmethod
    def get_user_permissions_summary(cls, user: User) -> Dict[str, Any]:
        """
        Get comprehensive permissions summary for a user.
        
        Args:
            user: User to get permissions for
            
        Returns:
            Dictionary with permissions and capabilities
        """
        permissions = AuthService.get_user_permissions(user)
        
        # Get channel-specific permissions
        memberships = ChannelMembership.get_user_memberships(str(user.id))
        channel_permissions = []
        
        for membership in memberships:
            if membership.channel:
                channel_permissions.append({
                    'channel_id': str(membership.channel.id),
                    'channel_name': membership.channel.name,
                    'role': membership.role.value,
                    'can_send_messages': membership.can_send_messages(),
                    'can_manage_members': membership.can_manage_members(),
                    'can_moderate_messages': membership.can_moderate_messages(),
                    'has_moderation_privileges': membership.has_moderation_privileges()
                })
        
        summary = {
            'user': user.to_dict(),
            'global_role': user.role.name if user.role else None,
            'global_permissions': permissions,
            'channel_permissions': channel_permissions,
            'can_create_channels': permissions.get('can_create_channels', False),
            'can_manage_users': permissions.get('can_modify_users', False),
            'is_admin': user.role and user.role.name == 'admin' if user.role else False
        }
        
        return summary
    
    @classmethod
    def delete_user_data(cls, admin: User, user_id: str, 
                        delete_messages: bool = False) -> Dict[str, int]:
        """
        Delete or anonymize user data (GDPR compliance).
        
        Args:
            admin: Admin performing the action
            user_id: User ID to process
            delete_messages: Whether to delete messages or just anonymize
            
        Returns:
            Dictionary with counts of deleted/processed items
            
        Raises:
            UserError: If deletion is not allowed
        """
        # Check admin permissions
        if not AuthService.user_has_permission(admin, 'can_modify_users'):
            raise AuthorizationError("Insufficient permissions to delete user data")
        
        user = cls.get_user_by_id(user_id)
        if not user:
            raise UserError("User not found")
        
        # Cannot delete admin's own data
        if str(admin.id) == str(user_id):
            raise UserError("Cannot delete your own user data")
        
        counts = {
            'sessions_deleted': 0,
            'memberships_deleted': 0,
            'conversations_deleted': 0,
            'messages_processed': 0
        }
        
        # Delete all sessions
        sessions = Session.query.filter_by(user_id=user_id).all()
        for session in sessions:
            db.session.delete(session)
        counts['sessions_deleted'] = len(sessions)
        
        # Remove channel memberships
        memberships = ChannelMembership.query.filter_by(user_id=user_id).all()
        for membership in memberships:
            db.session.delete(membership)
        counts['memberships_deleted'] = len(memberships)
        
        # Handle direct conversations
        conversations = DirectConversation.query.filter(
            or_(
                DirectConversation.participant1_id == user_id,
                DirectConversation.participant2_id == user_id
            )
        ).all()
        
        for conversation in conversations:
            conversation.delete_conversation()
        counts['conversations_deleted'] = len(conversations)
        
        # Handle messages
        messages = Message.query.filter_by(sender_id=user_id).all()
        for message in messages:
            if delete_messages:
                db.session.delete(message)
            else:
                # Anonymize message
                message.sender_id = "00000000-0000-0000-0000-000000000000"  # Anonymous user
                message.content = "[Message from deleted user]"
        counts['messages_processed'] = len(messages)
        
        # Deactivate user account
        user.deactivate()
        user.username = f"deleted_user_{user_id[:8]}"
        user.email = f"deleted_{user_id[:8]}@deleted.local"
        user.display_name = "Deleted User"
        user.bio = None
        user.status = None
        
        db.session.commit()
        
        return counts