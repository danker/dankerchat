"""
ChannelMembership model for DankerChat application.

Join table for Channel-User many-to-many relationship with additional metadata.
Based on specs/001-chat-application/data-model.md
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, ForeignKey, Boolean, Enum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import db
import enum


class MembershipRole(enum.Enum):
    """Enumeration of membership roles within a channel."""
    MEMBER = 'member'
    MODERATOR = 'moderator'
    ADMIN = 'admin'


class ChannelMembership(db.Model):
    """
    ChannelMembership model representing user membership in channels.
    
    Join table for Channel-User many-to-many relationship with additional metadata.
    
    Attributes:
        channel_id: Foreign key to Channel
        user_id: Foreign key to User
        joined_at: Membership start timestamp
        role: Member role within the channel ('member', 'moderator', 'admin')
        is_muted: Boolean flag for muted members
    """
    
    __tablename__ = 'channel_memberships'
    
    # Composite primary key (channel_id, user_id)
    channel_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey('channels.id'),
        primary_key=True
    )
    
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey('users.id'),
        primary_key=True,
        index=True  # For user's channels lookup
    )
    
    # Membership metadata
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )
    
    role: Mapped[MembershipRole] = mapped_column(
        Enum(MembershipRole),
        nullable=False,
        default=MembershipRole.MEMBER
    )
    
    is_muted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )
    
    # Relationships
    channel: Mapped['Channel'] = relationship(
        'Channel',
        back_populates='memberships',
        lazy='select'
    )
    
    user: Mapped['User'] = relationship(
        'User',
        back_populates='channel_memberships',
        lazy='select'
    )
    
    # Database constraints
    __table_args__ = (
        # Unique constraint on (channel_id, user_id) - already enforced by composite PK
        # but included for clarity
        UniqueConstraint(
            'channel_id', 'user_id',
            name='unique_channel_membership'
        ),
    )
    
    def __init__(self, channel_id: str, user_id: str, 
                 role: MembershipRole = MembershipRole.MEMBER,
                 is_muted: bool = False):
        """
        Initialize a new ChannelMembership.
        
        Args:
            channel_id: Foreign key to Channel
            user_id: Foreign key to User
            role: Member role (default: MEMBER)
            is_muted: Whether member is muted (default: False)
        """
        self.channel_id = channel_id
        self.user_id = user_id
        self.role = role
        self.is_muted = is_muted
        self.joined_at = datetime.utcnow()
    
    def __repr__(self) -> str:
        """String representation of ChannelMembership."""
        return f'<ChannelMembership {self.user_id[:8]} in {self.channel_id[:8]} ({self.role.value})>'
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """
        Convert ChannelMembership to dictionary representation.
        
        Args:
            include_sensitive: Whether to include sensitive fields
            
        Returns:
            Dictionary representation of the membership
        """
        data = {
            'user': self.user.to_dict() if self.user else None,
            'channel': self.channel.to_dict() if self.channel else None,
            'joined_at': self.joined_at.isoformat(),
            'role': self.role.value,
            'is_muted': self.is_muted
        }
        
        if include_sensitive:
            data['channel_id'] = str(self.channel_id)
            data['user_id'] = str(self.user_id)
        
        return data
    
    def is_admin(self) -> bool:
        """
        Check if this membership has admin role.
        
        Returns:
            True if admin, False otherwise
        """
        return self.role == MembershipRole.ADMIN
    
    def is_moderator(self) -> bool:
        """
        Check if this membership has moderator role.
        
        Returns:
            True if moderator, False otherwise
        """
        return self.role == MembershipRole.MODERATOR
    
    def is_member(self) -> bool:
        """
        Check if this membership has member role.
        
        Returns:
            True if member, False otherwise
        """
        return self.role == MembershipRole.MEMBER
    
    def has_moderation_privileges(self) -> bool:
        """
        Check if this membership has moderation privileges.
        
        Returns:
            True if admin or moderator, False otherwise
        """
        return self.role in [MembershipRole.ADMIN, MembershipRole.MODERATOR]
    
    def can_send_messages(self) -> bool:
        """
        Check if member can send messages.
        
        Returns:
            True if not muted, False if muted
        """
        return not self.is_muted
    
    def can_manage_members(self) -> bool:
        """
        Check if member can manage other members.
        
        Returns:
            True if admin, False otherwise
        """
        return self.is_admin()
    
    def can_moderate_messages(self) -> bool:
        """
        Check if member can moderate messages.
        
        Returns:
            True if admin or moderator, False otherwise
        """
        return self.has_moderation_privileges()
    
    def promote_to_moderator(self) -> bool:
        """
        Promote member to moderator role.
        
        Returns:
            True if promotion successful, False if already moderator or admin
        """
        if self.role == MembershipRole.MEMBER:
            self.role = MembershipRole.MODERATOR
            return True
        return False
    
    def promote_to_admin(self) -> bool:
        """
        Promote member to admin role.
        
        Returns:
            True if promotion successful, False if already admin
        """
        if self.role != MembershipRole.ADMIN:
            self.role = MembershipRole.ADMIN
            return True
        return False
    
    def demote_to_member(self) -> bool:
        """
        Demote member to basic member role.
        
        Returns:
            True if demotion successful, False if already member
        """
        if self.role != MembershipRole.MEMBER:
            self.role = MembershipRole.MEMBER
            return True
        return False
    
    def mute(self) -> None:
        """Mute this member."""
        self.is_muted = True
    
    def unmute(self) -> None:
        """Unmute this member."""
        self.is_muted = False
    
    def get_membership_duration(self) -> datetime:
        """
        Get duration of membership.
        
        Returns:
            Timedelta since joining
        """
        return datetime.utcnow() - self.joined_at
    
    @classmethod
    def create_membership(cls, channel_id: str, user_id: str, 
                         role: MembershipRole = MembershipRole.MEMBER) -> Optional['ChannelMembership']:
        """
        Create a new channel membership.
        
        Args:
            channel_id: ID of the channel
            user_id: ID of the user
            role: Role for the new member
            
        Returns:
            New ChannelMembership object, or None if membership already exists
        """
        # Check if membership already exists
        existing = cls.query.filter_by(channel_id=channel_id, user_id=user_id).first()
        if existing:
            return None
        
        membership = cls(channel_id=channel_id, user_id=user_id, role=role)
        db.session.add(membership)
        return membership
    
    @classmethod
    def get_user_memberships(cls, user_id: str) -> list['ChannelMembership']:
        """
        Get all memberships for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of ChannelMembership objects
        """
        return cls.query.filter_by(user_id=user_id).all()
    
    @classmethod
    def get_channel_memberships(cls, channel_id: str) -> list['ChannelMembership']:
        """
        Get all memberships for a channel.
        
        Args:
            channel_id: ID of the channel
            
        Returns:
            List of ChannelMembership objects
        """
        return cls.query.filter_by(channel_id=channel_id).all()
    
    @classmethod
    def get_channel_admins(cls, channel_id: str) -> list['ChannelMembership']:
        """
        Get all admin memberships for a channel.
        
        Args:
            channel_id: ID of the channel
            
        Returns:
            List of admin ChannelMembership objects
        """
        return cls.query.filter_by(
            channel_id=channel_id,
            role=MembershipRole.ADMIN
        ).all()
    
    @classmethod
    def get_channel_moderators(cls, channel_id: str) -> list['ChannelMembership']:
        """
        Get all moderator and admin memberships for a channel.
        
        Args:
            channel_id: ID of the channel
            
        Returns:
            List of moderator/admin ChannelMembership objects
        """
        return cls.query.filter_by(channel_id=channel_id).filter(
            cls.role.in_([MembershipRole.MODERATOR, MembershipRole.ADMIN])
        ).all()
    
    def can_be_managed_by(self, manager_membership: 'ChannelMembership') -> bool:
        """
        Check if this membership can be managed by another membership.
        
        Args:
            manager_membership: Membership of the potential manager
            
        Returns:
            True if manager can manage this membership, False otherwise
        """
        # Admins can manage everyone except other admins
        if manager_membership.is_admin():
            return not self.is_admin() or manager_membership.user_id == self.user_id
        
        # Moderators can manage regular members
        if manager_membership.is_moderator():
            return self.is_member()
        
        # Regular members can't manage anyone
        return False