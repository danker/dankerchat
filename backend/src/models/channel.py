"""
Channel model for DankerChat application.

Represents named discussion spaces for multiple users.
Based on specs/001-chat-application/data-model.md
"""

import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Boolean, DateTime, Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import db


class Channel(db.Model):
    """
    Channel model representing discussion spaces.
    
    Attributes:
        id: Primary key (UUID)
        name: Channel name (3-50 chars, unique, lowercase + hyphens)
        display_name: Human-readable channel name
        description: Channel description (500 chars max)
        is_private: Boolean flag for private/public access
        is_archived: Boolean flag for archived channels
        max_members: Maximum number of members (default 50)
        created_by: Foreign key to User (channel creator)
        created_at: Channel creation timestamp
        updated_at: Last modification timestamp
    """
    
    __tablename__ = 'channels'
    
    # Primary key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()))
    
    # Channel identification
    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )
    
    display_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    
    # Channel settings
    is_private: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )
    
    is_archived: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True
    )
    
    max_members: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=50
    )
    
    # Foreign keys
    created_by: Mapped[str] = mapped_column(
        String(36),
        ForeignKey('users.id'),
        nullable=False
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    creator: Mapped['User'] = relationship(
        'User',
        back_populates='created_channels',
        lazy='select'
    )
    
    messages: Mapped[List['Message']] = relationship(
        'Message',
        back_populates='channel',
        lazy='dynamic',
        order_by='Message.created_at'
    )
    
    memberships: Mapped[List['ChannelMembership']] = relationship(
        'ChannelMembership',
        back_populates='channel',
        lazy='dynamic'
    )
    
    def __init__(self, name: str, created_by: str, display_name: Optional[str] = None,
                 description: Optional[str] = None, is_private: bool = False,
                 max_members: int = 50):
        """
        Initialize a new Channel.
        
        Args:
            name: Channel name (3-50 chars, lowercase + hyphens)
            created_by: Foreign key to User (creator)
            display_name: Optional human-readable name
            description: Optional description
            is_private: Whether channel is private (default False)
            max_members: Maximum members (default 50)
        """
        self.name = name.lower()  # Ensure lowercase
        self.display_name = display_name or self._generate_display_name(name)
        self.description = description
        self.is_private = is_private
        self.max_members = max_members
        self.created_by = created_by
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.is_archived = False
    
    def __repr__(self) -> str:
        """String representation of Channel."""
        return f'<Channel {self.name}>'
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """
        Convert Channel to dictionary representation.
        
        Args:
            include_sensitive: Whether to include sensitive fields
            
        Returns:
            Dictionary representation of the channel
        """
        data = {
            'id': str(self.id),
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'is_private': self.is_private,
            'is_archived': self.is_archived,
            'max_members': self.max_members,
            'member_count': self.get_member_count(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'created_by': self.creator.to_dict() if self.creator else None
        }
        
        if include_sensitive:
            data['created_by_id'] = str(self.created_by)
        
        return data
    
    @staticmethod
    def _generate_display_name(name: str) -> str:
        """
        Generate a display name from channel name.
        
        Args:
            name: Channel name
            
        Returns:
            Human-readable display name
        """
        # Convert hyphens to spaces and title case
        return name.replace('-', ' ').title()
    
    @classmethod
    def validate_name(cls, name: str) -> bool:
        """
        Validate channel name format.
        
        Args:
            name: Channel name to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not name or not isinstance(name, str):
            return False
        
        if len(name) < 3 or len(name) > 50:
            return False
        
        # Only lowercase letters, numbers, and hyphens
        return all(c.islower() or c.isdigit() or c == '-' for c in name)
    
    @classmethod
    def validate_max_members(cls, max_members: int) -> bool:
        """
        Validate max_members value.
        
        Args:
            max_members: Maximum members value
            
        Returns:
            True if valid (2-200), False otherwise
        """
        return isinstance(max_members, int) and 2 <= max_members <= 200
    
    def get_member_count(self) -> int:
        """
        Get current number of members in the channel.
        
        Returns:
            Number of active members
        """
        return self.memberships.count()
    
    def is_full(self) -> bool:
        """
        Check if channel has reached maximum capacity.
        
        Returns:
            True if channel is full, False otherwise
        """
        return self.get_member_count() >= self.max_members
    
    def can_user_join(self, user_id: str) -> tuple[bool, str]:
        """
        Check if a user can join this channel.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Tuple of (can_join, reason)
        """
        if self.is_archived:
            return False, "Channel is archived"
        
        if self.is_full():
            return False, "Channel is full"
        
        if self.is_member(user_id):
            return False, "User is already a member"
        
        if self.is_private:
            return False, "Private channel requires invitation"
        
        return True, "Can join"
    
    def is_member(self, user_id: str) -> bool:
        """
        Check if user is a member of this channel.
        
        Args:
            user_id: ID of the user
            
        Returns:
            True if user is a member, False otherwise
        """
        return self.memberships.filter_by(user_id=user_id).first() is not None
    
    def get_members(self) -> List['User']:
        """
        Get all members of this channel.
        
        Returns:
            List of User objects
        """
        return [membership.user for membership in self.memberships.all()]
    
    def get_recent_messages(self, limit: int = 20) -> List['Message']:
        """
        Get recent messages from this channel.
        
        Args:
            limit: Maximum number of messages to return
            
        Returns:
            List of Message objects, most recent first
        """
        return (self.messages
                .filter_by(is_deleted=False)
                .order_by(Message.created_at.desc())
                .limit(limit)
                .all())
    
    def update_info(self, display_name: Optional[str] = None,
                   description: Optional[str] = None,
                   max_members: Optional[int] = None) -> None:
        """
        Update channel information.
        
        Args:
            display_name: New display name
            description: New description
            max_members: New member limit
        """
        if display_name is not None:
            self.display_name = display_name
        
        if description is not None:
            self.description = description
        
        if max_members is not None and self.validate_max_members(max_members):
            self.max_members = max_members
        
        self.updated_at = datetime.utcnow()
    
    def archive(self) -> None:
        """Archive this channel."""
        self.is_archived = True
        self.updated_at = datetime.utcnow()
    
    def unarchive(self) -> None:
        """Unarchive this channel."""
        self.is_archived = False
        self.updated_at = datetime.utcnow()
    
    def is_user_admin_or_creator(self, user_id: str) -> bool:
        """
        Check if user is the creator or has admin permissions in this channel.
        
        Args:
            user_id: ID of the user
            
        Returns:
            True if user can manage channel, False otherwise
        """
        if str(self.created_by) == str(user_id):
            return True
        
        membership = self.memberships.filter_by(user_id=user_id).first()
        return membership is not None and membership.role == 'admin'