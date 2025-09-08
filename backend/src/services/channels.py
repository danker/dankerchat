"""
Channel service for DankerChat application.

Handles channel creation, management, membership, and permissions.
Based on specs/001-chat-application/tasks.md T035
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import and_, or_

from database import db
from models.channel import Channel
from models.channel_membership import ChannelMembership, MembershipRole
from models.user import User
from models.message import Message, MessageType
from services.auth import AuthService, AuthorizationError


class ChannelError(Exception):
    """Custom exception for channel errors."""
    pass


class ChannelService:
    """
    Service for handling channel operations.
    
    Provides methods for creating, managing, and moderating channels,
    as well as handling channel memberships and permissions.
    """
    
    @classmethod
    def create_channel(cls, creator: User, name: str, display_name: Optional[str] = None,
                      description: Optional[str] = None, is_private: bool = False,
                      max_members: int = 50) -> Channel:
        """
        Create a new channel.
        
        Args:
            creator: User creating the channel
            name: Channel name (3-50 chars, lowercase + hyphens)
            display_name: Human-readable name (optional)
            description: Channel description (optional)
            is_private: Whether channel is private
            max_members: Maximum number of members
            
        Returns:
            Created Channel object
            
        Raises:
            ChannelError: If creation fails or validation errors
        """
        # Check permissions
        if not AuthService.user_has_permission(creator, 'can_create_channels'):
            raise AuthorizationError("User does not have permission to create channels")
        
        # Validate channel name
        if not Channel.validate_name(name):
            raise ChannelError("Invalid channel name format")
        
        # Check if channel name already exists
        if Channel.query.filter_by(name=name.lower()).first():
            raise ChannelError("Channel name already exists")
        
        # Validate max_members
        if not Channel.validate_max_members(max_members):
            raise ChannelError("Invalid max_members value (must be 2-200)")
        
        # Create channel
        channel = Channel(
            name=name,
            created_by=str(creator.id),
            display_name=display_name,
            description=description,
            is_private=is_private,
            max_members=max_members
        )
        
        db.session.add(channel)
        db.session.flush()  # Get channel ID
        
        # Add creator as admin member
        membership = ChannelMembership(
            channel_id=str(channel.id),
            user_id=str(creator.id),
            role=MembershipRole.ADMIN
        )
        
        db.session.add(membership)
        db.session.commit()
        
        # Create welcome system message
        from services.messaging import MessagingService
        MessagingService.create_system_message(
            content=f"Channel '{channel.display_name}' created by {creator.display_name}",
            channel_id=str(channel.id),
            message_type=MessageType.SYSTEM
        )
        
        return channel
    
    @classmethod
    def join_channel(cls, user: User, channel_id: str, invited_by: Optional[User] = None) -> bool:
        """
        Add user to a channel.
        
        Args:
            user: User joining the channel
            channel_id: Channel ID
            invited_by: User who invited (for private channels)
            
        Returns:
            True if join successful
            
        Raises:
            ChannelError: If user cannot join channel
        """
        channel = Channel.query.get(channel_id)
        if not channel:
            raise ChannelError("Channel not found")
        
        # Check if user can join
        can_join, reason = channel.can_user_join(str(user.id))
        if not can_join and channel.is_private and invited_by:
            # For private channels, check if inviter has permission
            inviter_membership = ChannelMembership.query.filter_by(
                channel_id=channel_id,
                user_id=str(invited_by.id)
            ).first()
            
            if not inviter_membership or not inviter_membership.has_moderation_privileges():
                raise ChannelError("Inviter does not have permission to add members")
        elif not can_join:
            raise ChannelError(reason)
        
        # Create membership
        membership = ChannelMembership(
            channel_id=channel_id,
            user_id=str(user.id),
            role=MembershipRole.MEMBER
        )
        
        db.session.add(membership)
        db.session.commit()
        
        # Create join system message
        from services.messaging import MessagingService
        MessagingService.create_system_message(
            content=f"{user.display_name} joined the channel",
            channel_id=channel_id,
            message_type=MessageType.JOIN
        )
        
        return True
    
    @classmethod
    def leave_channel(cls, user: User, channel_id: str) -> bool:
        """
        Remove user from a channel.
        
        Args:
            user: User leaving the channel
            channel_id: Channel ID
            
        Returns:
            True if leave successful
            
        Raises:
            ChannelError: If user cannot leave channel
        """
        channel = Channel.query.get(channel_id)
        if not channel:
            raise ChannelError("Channel not found")
        
        membership = ChannelMembership.query.filter_by(
            channel_id=channel_id,
            user_id=str(user.id)
        ).first()
        
        if not membership:
            raise ChannelError("User is not a member of this channel")
        
        # Check if user is the only admin
        admin_count = ChannelMembership.query.filter_by(
            channel_id=channel_id,
            role=MembershipRole.ADMIN
        ).count()
        
        if membership.is_admin() and admin_count == 1:
            member_count = channel.get_member_count()
            if member_count > 1:
                raise ChannelError("Cannot leave: you are the only admin. Transfer ownership first.")
        
        # Remove membership
        db.session.delete(membership)
        db.session.commit()
        
        # Create leave system message
        from services.messaging import MessagingService
        MessagingService.create_system_message(
            content=f"{user.display_name} left the channel",
            channel_id=channel_id,
            message_type=MessageType.LEAVE
        )
        
        return True
    
    @classmethod
    def kick_user(cls, moderator: User, channel_id: str, user_id: str) -> bool:
        """
        Remove user from channel (kick).
        
        Args:
            moderator: User performing the kick
            channel_id: Channel ID
            user_id: User ID to kick
            
        Returns:
            True if kick successful
            
        Raises:
            ChannelError: If kick is not allowed
        """
        channel = Channel.query.get(channel_id)
        if not channel:
            raise ChannelError("Channel not found")
        
        # Check moderator permissions
        mod_membership = ChannelMembership.query.filter_by(
            channel_id=channel_id,
            user_id=str(moderator.id)
        ).first()
        
        if not mod_membership or not mod_membership.can_manage_members():
            raise ChannelError("Insufficient permissions to kick users")
        
        # Get target user membership
        target_membership = ChannelMembership.query.filter_by(
            channel_id=channel_id,
            user_id=user_id
        ).first()
        
        if not target_membership:
            raise ChannelError("User is not a member of this channel")
        
        # Check if target can be managed by moderator
        if not target_membership.can_be_managed_by(mod_membership):
            raise ChannelError("Cannot kick this user: insufficient permissions")
        
        # Get user for system message
        target_user = User.query.get(user_id)
        
        # Remove membership
        db.session.delete(target_membership)
        db.session.commit()
        
        # Create kick system message
        from services.messaging import MessagingService
        MessagingService.create_system_message(
            content=f"{target_user.display_name if target_user else 'User'} was removed from the channel by {moderator.display_name}",
            channel_id=channel_id,
            message_type=MessageType.SYSTEM
        )
        
        return True
    
    @classmethod
    def update_member_role(cls, moderator: User, channel_id: str, user_id: str,
                          new_role: MembershipRole) -> bool:
        """
        Update a member's role in a channel.
        
        Args:
            moderator: User performing the update
            channel_id: Channel ID
            user_id: User ID to update
            new_role: New role to assign
            
        Returns:
            True if update successful
            
        Raises:
            ChannelError: If update is not allowed
        """
        channel = Channel.query.get(channel_id)
        if not channel:
            raise ChannelError("Channel not found")
        
        # Check moderator permissions
        mod_membership = ChannelMembership.query.filter_by(
            channel_id=channel_id,
            user_id=str(moderator.id)
        ).first()
        
        if not mod_membership or not mod_membership.can_manage_members():
            raise ChannelError("Insufficient permissions to manage member roles")
        
        # Get target user membership
        target_membership = ChannelMembership.query.filter_by(
            channel_id=channel_id,
            user_id=user_id
        ).first()
        
        if not target_membership:
            raise ChannelError("User is not a member of this channel")
        
        # Check if target can be managed by moderator
        if not target_membership.can_be_managed_by(mod_membership):
            raise ChannelError("Cannot manage this user: insufficient permissions")
        
        # Update role
        old_role = target_membership.role
        target_membership.role = new_role
        db.session.commit()
        
        # Create role change system message
        target_user = User.query.get(user_id)
        from services.messaging import MessagingService
        MessagingService.create_system_message(
            content=f"{target_user.display_name if target_user else 'User'} role changed from {old_role.value} to {new_role.value} by {moderator.display_name}",
            channel_id=channel_id,
            message_type=MessageType.SYSTEM
        )
        
        return True
    
    @classmethod
    def mute_user(cls, moderator: User, channel_id: str, user_id: str) -> bool:
        """
        Mute a user in a channel.
        
        Args:
            moderator: User performing the mute
            channel_id: Channel ID
            user_id: User ID to mute
            
        Returns:
            True if mute successful
            
        Raises:
            ChannelError: If mute is not allowed
        """
        return cls._toggle_user_mute(moderator, channel_id, user_id, True)
    
    @classmethod
    def unmute_user(cls, moderator: User, channel_id: str, user_id: str) -> bool:
        """
        Unmute a user in a channel.
        
        Args:
            moderator: User performing the unmute
            channel_id: Channel ID
            user_id: User ID to unmute
            
        Returns:
            True if unmute successful
            
        Raises:
            ChannelError: If unmute is not allowed
        """
        return cls._toggle_user_mute(moderator, channel_id, user_id, False)
    
    @classmethod
    def _toggle_user_mute(cls, moderator: User, channel_id: str, user_id: str, mute: bool) -> bool:
        """
        Toggle user mute status in a channel.
        
        Args:
            moderator: User performing the action
            channel_id: Channel ID
            user_id: User ID to toggle
            mute: True to mute, False to unmute
            
        Returns:
            True if toggle successful
            
        Raises:
            ChannelError: If action is not allowed
        """
        channel = Channel.query.get(channel_id)
        if not channel:
            raise ChannelError("Channel not found")
        
        # Check moderator permissions
        mod_membership = ChannelMembership.query.filter_by(
            channel_id=channel_id,
            user_id=str(moderator.id)
        ).first()
        
        if not mod_membership or not mod_membership.has_moderation_privileges():
            raise ChannelError("Insufficient permissions to mute/unmute users")
        
        # Get target user membership
        target_membership = ChannelMembership.query.filter_by(
            channel_id=channel_id,
            user_id=user_id
        ).first()
        
        if not target_membership:
            raise ChannelError("User is not a member of this channel")
        
        # Check if target can be managed by moderator
        if not target_membership.can_be_managed_by(mod_membership):
            raise ChannelError("Cannot manage this user: insufficient permissions")
        
        # Toggle mute status
        if mute:
            target_membership.mute()
        else:
            target_membership.unmute()
        
        db.session.commit()
        
        # Create mute/unmute system message
        target_user = User.query.get(user_id)
        action = "muted" if mute else "unmuted"
        from services.messaging import MessagingService
        MessagingService.create_system_message(
            content=f"{target_user.display_name if target_user else 'User'} was {action} by {moderator.display_name}",
            channel_id=channel_id,
            message_type=MessageType.SYSTEM
        )
        
        return True
    
    @classmethod
    def update_channel_info(cls, user: User, channel_id: str,
                          display_name: Optional[str] = None,
                          description: Optional[str] = None,
                          max_members: Optional[int] = None) -> bool:
        """
        Update channel information.
        
        Args:
            user: User updating the channel
            channel_id: Channel ID
            display_name: New display name
            description: New description
            max_members: New member limit
            
        Returns:
            True if update successful
            
        Raises:
            ChannelError: If update is not allowed
        """
        channel = Channel.query.get(channel_id)
        if not channel:
            raise ChannelError("Channel not found")
        
        # Check permissions (admin or creator)
        if not channel.is_user_admin_or_creator(str(user.id)):
            raise ChannelError("Insufficient permissions to update channel")
        
        # Update channel
        channel.update_info(
            display_name=display_name,
            description=description,
            max_members=max_members
        )
        
        db.session.commit()
        
        return True
    
    @classmethod
    def archive_channel(cls, user: User, channel_id: str) -> bool:
        """
        Archive a channel.
        
        Args:
            user: User archiving the channel
            channel_id: Channel ID
            
        Returns:
            True if archive successful
            
        Raises:
            ChannelError: If archive is not allowed
        """
        # Check permissions
        if not AuthService.user_has_permission(user, 'can_delete_channels'):
            raise AuthorizationError("User does not have permission to archive channels")
        
        channel = Channel.query.get(channel_id)
        if not channel:
            raise ChannelError("Channel not found")
        
        if channel.is_archived:
            raise ChannelError("Channel is already archived")
        
        channel.archive()
        db.session.commit()
        
        # Create archive system message
        from services.messaging import MessagingService
        MessagingService.create_system_message(
            content=f"Channel archived by {user.display_name}",
            channel_id=channel_id,
            message_type=MessageType.SYSTEM
        )
        
        return True
    
    @classmethod
    def unarchive_channel(cls, user: User, channel_id: str) -> bool:
        """
        Unarchive a channel.
        
        Args:
            user: User unarchiving the channel
            channel_id: Channel ID
            
        Returns:
            True if unarchive successful
            
        Raises:
            ChannelError: If unarchive is not allowed
        """
        # Check permissions
        if not AuthService.user_has_permission(user, 'can_delete_channels'):
            raise AuthorizationError("User does not have permission to unarchive channels")
        
        channel = Channel.query.get(channel_id)
        if not channel:
            raise ChannelError("Channel not found")
        
        if not channel.is_archived:
            raise ChannelError("Channel is not archived")
        
        channel.unarchive()
        db.session.commit()
        
        # Create unarchive system message
        from services.messaging import MessagingService
        MessagingService.create_system_message(
            content=f"Channel unarchived by {user.display_name}",
            channel_id=channel_id,
            message_type=MessageType.SYSTEM
        )
        
        return True
    
    @classmethod
    def get_public_channels(cls, limit: int = 50, include_archived: bool = False) -> List[Channel]:
        """
        Get list of public channels.
        
        Args:
            limit: Maximum number of channels
            include_archived: Whether to include archived channels
            
        Returns:
            List of Channel objects
        """
        query = Channel.query.filter_by(is_private=False)
        
        if not include_archived:
            query = query.filter_by(is_archived=False)
        
        return query.order_by(Channel.created_at.desc()).limit(limit).all()
    
    @classmethod
    def search_channels(cls, user: User, query: str, limit: int = 20) -> List[Channel]:
        """
        Search for channels by name or description.
        
        Args:
            user: User performing search
            query: Search query
            limit: Maximum results
            
        Returns:
            List of matching Channel objects
        """
        if not query or len(query.strip()) < 2:
            return []
        
        # Search public channels only
        channels = Channel.query.filter(
            and_(
                Channel.is_private == False,
                Channel.is_archived == False,
                or_(
                    Channel.name.ilike(f'%{query}%'),
                    Channel.display_name.ilike(f'%{query}%'),
                    Channel.description.ilike(f'%{query}%')
                )
            )
        ).order_by(Channel.name).limit(limit).all()
        
        return channels
    
    @classmethod
    def get_channel_members(cls, user: User, channel_id: str) -> List[Dict[str, Any]]:
        """
        Get list of channel members.
        
        Args:
            user: User requesting member list
            channel_id: Channel ID
            
        Returns:
            List of member dictionaries
            
        Raises:
            ChannelError: If user cannot access channel
        """
        # Check if user is a member
        user_membership = ChannelMembership.query.filter_by(
            channel_id=channel_id,
            user_id=str(user.id)
        ).first()
        
        if not user_membership:
            raise ChannelError("User is not a member of this channel")
        
        memberships = ChannelMembership.get_channel_memberships(channel_id)
        
        members = []
        for membership in memberships:
            if membership.user:
                members.append({
                    'user': membership.user.to_dict(),
                    'membership': membership.to_dict(),
                    'joined_at': membership.joined_at.isoformat(),
                    'role': membership.role.value
                })
        
        return members
    
    @classmethod
    def get_channel_stats(cls, user: User, channel_id: str) -> Dict[str, Any]:
        """
        Get channel statistics.
        
        Args:
            user: User requesting stats
            channel_id: Channel ID
            
        Returns:
            Dictionary with channel statistics
            
        Raises:
            ChannelError: If user cannot access channel
        """
        # Check if user is a member
        user_membership = ChannelMembership.query.filter_by(
            channel_id=channel_id,
            user_id=str(user.id)
        ).first()
        
        if not user_membership:
            raise ChannelError("User is not a member of this channel")
        
        channel = Channel.query.get(channel_id)
        if not channel:
            raise ChannelError("Channel not found")
        
        message_count = Message.query.filter_by(
            channel_id=channel_id,
            is_deleted=False
        ).count()
        
        admin_count = ChannelMembership.query.filter_by(
            channel_id=channel_id,
            role=MembershipRole.ADMIN
        ).count()
        
        moderator_count = ChannelMembership.query.filter_by(
            channel_id=channel_id,
            role=MembershipRole.MODERATOR
        ).count()
        
        stats = {
            'channel': channel.to_dict(),
            'member_count': channel.get_member_count(),
            'admin_count': admin_count,
            'moderator_count': moderator_count,
            'message_count': message_count,
            'created_at': channel.created_at.isoformat(),
            'is_full': channel.is_full()
        }
        
        return stats