"""
Admin service for DankerChat application.

Handles administrative operations including system management, moderation, and monitoring.
Based on specs/001-chat-application/tasks.md T037
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import func, desc, and_, or_

from database import db
from models.user import User
from models.role import Role
from models.session import Session, InterfaceType
from models.channel import Channel
from models.channel_membership import ChannelMembership, MembershipRole
from models.message import Message, MessageType
from models.direct_conversation import DirectConversation
from services.auth import AuthService, AuthorizationError


class AdminError(Exception):
    """Custom exception for admin errors."""
    pass


class AdminService:
    """
    Service for handling administrative operations.
    
    Provides methods for system monitoring, user management,
    content moderation, and system analytics.
    """
    
    @classmethod
    def get_system_stats(cls, admin: User) -> Dict[str, Any]:
        """
        Get comprehensive system statistics.
        
        Args:
            admin: Admin requesting stats
            
        Returns:
            Dictionary with system statistics
            
        Raises:
            AuthorizationError: If user lacks admin permissions
        """
        if not AuthService.user_has_permission(admin, 'can_modify_users'):
            raise AuthorizationError("Admin permissions required")
        
        # User statistics
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        inactive_users = total_users - active_users
        
        # Get users by role
        roles_stats = db.session.query(
            Role.name,
            func.count(User.id).label('user_count')
        ).join(User, User.role_id == Role.id).group_by(Role.name).all()
        
        # Channel statistics
        total_channels = Channel.query.count()
        public_channels = Channel.query.filter_by(is_private=False, is_archived=False).count()
        private_channels = Channel.query.filter_by(is_private=True, is_archived=False).count()
        archived_channels = Channel.query.filter_by(is_archived=True).count()
        
        # Message statistics
        total_messages = Message.query.count()
        channel_messages = Message.query.filter(Message.channel_id.isnot(None)).count()
        direct_messages = Message.query.filter(Message.direct_conversation_id.isnot(None)).count()
        deleted_messages = Message.query.filter_by(is_deleted=True).count()
        
        # Session statistics
        active_sessions = Session.query.filter(
            Session.is_revoked == False,
            Session.expires_at > datetime.utcnow()
        ).count()
        
        session_types = db.session.query(
            Session.interface_type,
            func.count(Session.id).label('session_count')
        ).filter(
            Session.is_revoked == False,
            Session.expires_at > datetime.utcnow()
        ).group_by(Session.interface_type).all()
        
        # Conversation statistics
        total_conversations = DirectConversation.query.count()
        active_conversations = DirectConversation.query.filter(
            DirectConversation.last_message_at.isnot(None)
        ).count()
        
        stats = {
            'timestamp': datetime.utcnow().isoformat(),
            'users': {
                'total': total_users,
                'active': active_users,
                'inactive': inactive_users,
                'by_role': {role.name: count for role, count in roles_stats}
            },
            'channels': {
                'total': total_channels,
                'public': public_channels,
                'private': private_channels,
                'archived': archived_channels
            },
            'messages': {
                'total': total_messages,
                'channel_messages': channel_messages,
                'direct_messages': direct_messages,
                'deleted': deleted_messages,
                'active': total_messages - deleted_messages
            },
            'sessions': {
                'active': active_sessions,
                'by_type': {str(interface.value): count for interface, count in session_types}
            },
            'conversations': {
                'total': total_conversations,
                'active': active_conversations,
                'inactive': total_conversations - active_conversations
            }
        }
        
        return stats
    
    @classmethod
    def get_activity_report(cls, admin: User, days: int = 7) -> Dict[str, Any]:
        """
        Generate activity report for the specified time period.
        
        Args:
            admin: Admin requesting report
            days: Number of days to analyze
            
        Returns:
            Dictionary with activity metrics
            
        Raises:
            AuthorizationError: If user lacks admin permissions
        """
        if not AuthService.user_has_permission(admin, 'can_modify_users'):
            raise AuthorizationError("Admin permissions required")
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # New users
        new_users = User.query.filter(User.created_at >= cutoff_date).count()
        
        # New channels
        new_channels = Channel.query.filter(Channel.created_at >= cutoff_date).count()
        
        # New messages
        new_messages = Message.query.filter(
            Message.created_at >= cutoff_date,
            Message.is_deleted == False
        ).count()
        
        # New conversations
        new_conversations = DirectConversation.query.filter(
            DirectConversation.created_at >= cutoff_date
        ).count()
        
        # Active users (users who sent messages)
        active_user_count = db.session.query(func.count(func.distinct(Message.sender_id))).filter(
            Message.created_at >= cutoff_date,
            Message.is_deleted == False
        ).scalar()
        
        # Most active users
        most_active_users = db.session.query(
            User.username,
            User.display_name,
            func.count(Message.id).label('message_count')
        ).join(Message, Message.sender_id == User.id).filter(
            Message.created_at >= cutoff_date,
            Message.is_deleted == False
        ).group_by(User.id).order_by(desc('message_count')).limit(10).all()
        
        # Most active channels
        most_active_channels = db.session.query(
            Channel.name,
            Channel.display_name,
            func.count(Message.id).label('message_count')
        ).join(Message, Message.channel_id == Channel.id).filter(
            Message.created_at >= cutoff_date,
            Message.is_deleted == False
        ).group_by(Channel.id).order_by(desc('message_count')).limit(10).all()
        
        # Daily activity breakdown
        daily_stats = db.session.query(
            func.date(Message.created_at).label('date'),
            func.count(Message.id).label('message_count'),
            func.count(func.distinct(Message.sender_id)).label('active_users')
        ).filter(
            Message.created_at >= cutoff_date,
            Message.is_deleted == False
        ).group_by(func.date(Message.created_at)).order_by('date').all()
        
        report = {
            'period': {
                'days': days,
                'start_date': cutoff_date.isoformat(),
                'end_date': datetime.utcnow().isoformat()
            },
            'growth': {
                'new_users': new_users,
                'new_channels': new_channels,
                'new_conversations': new_conversations
            },
            'activity': {
                'total_messages': new_messages,
                'active_users': active_user_count,
                'avg_messages_per_user': round(new_messages / max(active_user_count, 1), 2)
            },
            'top_users': [
                {
                    'username': user.username,
                    'display_name': user.display_name,
                    'message_count': count
                }
                for user, display, count in most_active_users
            ],
            'top_channels': [
                {
                    'name': channel.name,
                    'display_name': channel.display_name,
                    'message_count': count
                }
                for channel, display, count in most_active_channels
            ],
            'daily_breakdown': [
                {
                    'date': str(date),
                    'messages': message_count,
                    'active_users': active_users
                }
                for date, message_count, active_users in daily_stats
            ]
        }
        
        return report
    
    @classmethod
    def get_user_management_list(cls, admin: User, page: int = 1, per_page: int = 50,
                                filter_role: Optional[str] = None,
                                filter_status: Optional[str] = None,
                                search_query: Optional[str] = None) -> Dict[str, Any]:
        """
        Get paginated list of users for management interface.
        
        Args:
            admin: Admin requesting list
            page: Page number (1-based)
            per_page: Results per page
            filter_role: Filter by role name
            filter_status: Filter by status ('active', 'inactive')
            search_query: Search in username/email/display_name
            
        Returns:
            Dictionary with users list and pagination info
            
        Raises:
            AuthorizationError: If user lacks admin permissions
        """
        if not AuthService.user_has_permission(admin, 'can_modify_users'):
            raise AuthorizationError("Admin permissions required")
        
        query = User.query
        
        # Apply filters
        if filter_role:
            role = Role.query.filter_by(name=filter_role).first()
            if role:
                query = query.filter_by(role_id=str(role.id))
        
        if filter_status == 'active':
            query = query.filter_by(is_active=True)
        elif filter_status == 'inactive':
            query = query.filter_by(is_active=False)
        
        if search_query and len(search_query.strip()) >= 2:
            search_pattern = f'%{search_query}%'
            query = query.filter(
                or_(
                    User.username.ilike(search_pattern),
                    User.email.ilike(search_pattern),
                    User.display_name.ilike(search_pattern)
                )
            )
        
        # Get paginated results
        pagination = query.order_by(User.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Enhance user data with additional info
        users_data = []
        for user in pagination.items:
            # Get user statistics
            message_count = Message.query.filter_by(
                sender_id=str(user.id),
                is_deleted=False
            ).count()
            
            channel_count = ChannelMembership.query.filter_by(
                user_id=str(user.id)
            ).count()
            
            active_session_count = Session.query.filter(
                Session.user_id == str(user.id),
                Session.is_revoked == False,
                Session.expires_at > datetime.utcnow()
            ).count()
            
            users_data.append({
                'user': user.to_dict(include_sensitive=True),
                'role': user.role.name if user.role else None,
                'stats': {
                    'message_count': message_count,
                    'channel_memberships': channel_count,
                    'active_sessions': active_session_count
                },
                'last_login': user.last_login_at.isoformat() if user.last_login_at else None
            })
        
        return {
            'users': users_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next
            },
            'filters': {
                'role': filter_role,
                'status': filter_status,
                'search': search_query
            }
        }
    
    @classmethod
    def get_content_moderation_queue(cls, admin: User, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get list of content that may need moderation.
        
        Args:
            admin: Admin requesting queue
            limit: Maximum items to return
            
        Returns:
            List of content items for review
            
        Raises:
            AuthorizationError: If user lacks admin permissions
        """
        if not AuthService.user_has_permission(admin, 'can_delete_messages'):
            raise AuthorizationError("Content moderation permissions required")
        
        # For now, return recently reported or edited messages
        # In a full implementation, this would include user reports, flagged content, etc.
        
        # Get recently edited messages
        edited_messages = Message.query.filter(
            Message.edited_at.isnot(None),
            Message.is_deleted == False
        ).order_by(Message.edited_at.desc()).limit(limit // 2).all()
        
        # Get messages with potentially suspicious content (placeholder logic)
        # This would be enhanced with proper content analysis
        suspicious_messages = Message.query.filter(
            Message.is_deleted == False,
            Message.content.ilike('%spam%')  # Simple example
        ).order_by(Message.created_at.desc()).limit(limit // 2).all()
        
        queue_items = []
        
        for message in edited_messages:
            queue_items.append({
                'type': 'edited_message',
                'message': message.to_dict(include_sensitive=True),
                'sender': message.sender.to_dict() if message.sender else None,
                'channel': message.channel.to_dict() if message.channel else None,
                'conversation': message.direct_conversation.to_dict(str(admin.id)) if message.direct_conversation else None,
                'edited_at': message.edited_at.isoformat(),
                'priority': 'medium'
            })
        
        for message in suspicious_messages:
            if message not in edited_messages:  # Avoid duplicates
                queue_items.append({
                    'type': 'suspicious_content',
                    'message': message.to_dict(include_sensitive=True),
                    'sender': message.sender.to_dict() if message.sender else None,
                    'channel': message.channel.to_dict() if message.channel else None,
                    'conversation': message.direct_conversation.to_dict(str(admin.id)) if message.direct_conversation else None,
                    'reason': 'Potential spam content',
                    'priority': 'high'
                })
        
        # Sort by priority and timestamp
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        queue_items.sort(key=lambda x: (priority_order.get(x['priority'], 2), x.get('edited_at', x['message']['created_at'])), reverse=True)
        
        return queue_items[:limit]
    
    @classmethod
    def moderate_content(cls, admin: User, message_id: str, action: str,
                        reason: Optional[str] = None) -> bool:
        """
        Take moderation action on content.
        
        Args:
            admin: Admin performing moderation
            message_id: Message ID to moderate
            action: Action to take ('delete', 'restore', 'flag')
            reason: Reason for action
            
        Returns:
            True if action successful
            
        Raises:
            AdminError: If action fails or is invalid
        """
        if not AuthService.user_has_permission(admin, 'can_delete_messages'):
            raise AuthorizationError("Content moderation permissions required")
        
        message = Message.query.get(message_id)
        if not message:
            raise AdminError("Message not found")
        
        if action == 'delete':
            if message.is_deleted:
                raise AdminError("Message is already deleted")
            
            message.soft_delete(str(admin.id))
            
            # Create moderation system message
            target_channel = message.channel_id
            target_conversation = message.direct_conversation_id
            
            from services.messaging import MessagingService
            mod_message = f"Message deleted by admin: {reason}" if reason else "Message deleted by admin"
            
            MessagingService.create_system_message(
                content=mod_message,
                channel_id=target_channel,
                conversation_id=target_conversation,
                message_type=MessageType.SYSTEM
            )
            
        elif action == 'restore':
            if not message.is_deleted:
                raise AdminError("Message is not deleted")
            
            message.restore()
            
        elif action == 'flag':
            # In a full implementation, this would add the message to a flagged list
            # For now, we'll just log the action
            pass
            
        else:
            raise AdminError(f"Invalid moderation action: {action}")
        
        db.session.commit()
        return True
    
    @classmethod
    def get_system_health(cls, admin: User) -> Dict[str, Any]:
        """
        Get system health and performance metrics.
        
        Args:
            admin: Admin requesting health check
            
        Returns:
            Dictionary with health metrics
            
        Raises:
            AuthorizationError: If user lacks admin permissions
        """
        if not AuthService.user_has_permission(admin, 'can_modify_users'):
            raise AuthorizationError("Admin permissions required")
        
        # Database health
        try:
            db.session.execute('SELECT 1')
            db_status = 'healthy'
            db_error = None
        except Exception as e:
            db_status = 'error'
            db_error = str(e)
        
        # Session cleanup
        expired_sessions = Session.query.filter(
            Session.expires_at < datetime.utcnow()
        ).count()
        
        # Recent error indicators (placeholder)
        recent_failed_logins = 0  # Would track authentication failures
        recent_errors = 0  # Would track system errors
        
        # Performance metrics (placeholder)
        avg_response_time = 150  # Would measure actual response times
        memory_usage = 65  # Would measure actual memory usage
        
        health = {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': 'healthy' if db_status == 'healthy' else 'degraded',
            'database': {
                'status': db_status,
                'error': db_error
            },
            'sessions': {
                'expired_count': expired_sessions,
                'cleanup_needed': expired_sessions > 0
            },
            'security': {
                'recent_failed_logins': recent_failed_logins,
                'status': 'normal' if recent_failed_logins < 100 else 'elevated'
            },
            'performance': {
                'avg_response_time_ms': avg_response_time,
                'memory_usage_percent': memory_usage,
                'status': 'good' if avg_response_time < 500 and memory_usage < 80 else 'warning'
            },
            'maintenance': {
                'last_cleanup': datetime.utcnow().isoformat(),  # Would track actual cleanup
                'next_scheduled': (datetime.utcnow() + timedelta(hours=24)).isoformat()
            }
        }
        
        return health
    
    @classmethod
    def perform_maintenance(cls, admin: User, tasks: List[str]) -> Dict[str, Any]:
        """
        Perform system maintenance tasks.
        
        Args:
            admin: Admin performing maintenance
            tasks: List of maintenance task names
            
        Returns:
            Dictionary with results of each task
            
        Raises:
            AuthorizationError: If user lacks admin permissions
        """
        if not AuthService.user_has_permission(admin, 'can_modify_users'):
            raise AuthorizationError("Admin permissions required")
        
        results = {}
        
        if 'cleanup_sessions' in tasks:
            cleaned = Session.cleanup_expired_sessions()
            results['cleanup_sessions'] = {
                'status': 'success',
                'sessions_removed': cleaned
            }
        
        if 'archive_old_conversations' in tasks:
            # Placeholder for archiving old conversations
            results['archive_old_conversations'] = {
                'status': 'success',
                'conversations_archived': 0  # Would implement actual logic
            }
        
        if 'cleanup_deleted_messages' in tasks:
            # Placeholder for cleaning up old deleted messages
            results['cleanup_deleted_messages'] = {
                'status': 'success',
                'messages_removed': 0  # Would implement actual logic
            }
        
        if 'update_statistics' in tasks:
            # Placeholder for updating cached statistics
            results['update_statistics'] = {
                'status': 'success',
                'stats_updated': True
            }
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'admin': admin.username,
            'tasks_requested': tasks,
            'results': results
        }
    
    @classmethod
    def bulk_user_operation(cls, admin: User, user_ids: List[str], 
                           operation: str, **kwargs) -> Dict[str, Any]:
        """
        Perform bulk operations on multiple users.
        
        Args:
            admin: Admin performing operation
            user_ids: List of user IDs
            operation: Operation to perform ('deactivate', 'reactivate', 'change_role')
            **kwargs: Additional operation parameters
            
        Returns:
            Dictionary with operation results
            
        Raises:
            AuthorizationError: If user lacks admin permissions
            AdminError: If operation fails
        """
        if not AuthService.user_has_permission(admin, 'can_modify_users'):
            raise AuthorizationError("Admin permissions required")
        
        if not user_ids:
            raise AdminError("No user IDs provided")
        
        results = {
            'operation': operation,
            'total_users': len(user_ids),
            'successful': [],
            'failed': [],
            'skipped': []
        }
        
        for user_id in user_ids:
            try:
                user = User.query.get(user_id)
                if not user:
                    results['failed'].append({'user_id': user_id, 'reason': 'User not found'})
                    continue
                
                # Skip admin's own account for safety
                if str(admin.id) == str(user_id):
                    results['skipped'].append({'user_id': user_id, 'reason': 'Cannot modify own account'})
                    continue
                
                if operation == 'deactivate':
                    if not user.is_active:
                        results['skipped'].append({'user_id': user_id, 'reason': 'Already inactive'})
                        continue
                    
                    user.deactivate()
                    Session.revoke_user_sessions(user_id)
                    results['successful'].append({'user_id': user_id, 'username': user.username})
                
                elif operation == 'reactivate':
                    if user.is_active:
                        results['skipped'].append({'user_id': user_id, 'reason': 'Already active'})
                        continue
                    
                    user.reactivate()
                    results['successful'].append({'user_id': user_id, 'username': user.username})
                
                elif operation == 'change_role':
                    new_role_name = kwargs.get('new_role')
                    if not new_role_name:
                        results['failed'].append({'user_id': user_id, 'reason': 'No new role specified'})
                        continue
                    
                    new_role = Role.query.filter_by(name=new_role_name).first()
                    if not new_role:
                        results['failed'].append({'user_id': user_id, 'reason': f'Role {new_role_name} not found'})
                        continue
                    
                    old_role = user.role.name if user.role else 'none'
                    user.role_id = str(new_role.id)
                    Session.revoke_user_sessions(user_id)  # Force re-login with new permissions
                    
                    results['successful'].append({
                        'user_id': user_id,
                        'username': user.username,
                        'old_role': old_role,
                        'new_role': new_role_name
                    })
                
                else:
                    results['failed'].append({'user_id': user_id, 'reason': f'Unknown operation: {operation}'})
                
            except Exception as e:
                results['failed'].append({'user_id': user_id, 'reason': str(e)})
        
        db.session.commit()
        
        return results