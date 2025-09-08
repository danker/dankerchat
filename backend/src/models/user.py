"""
User model for DankerChat application.

Represents individual users with access to the chat system.
Based on specs/001-chat-application/data-model.md
"""

import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from database import db


class User(db.Model):
    """
    User model representing chat application users.
    
    Attributes:
        id: Primary key (UUID)
        username: Unique username (3-30 chars, alphanumeric + underscore)
        email: Email address (optional)
        password_hash: Bcrypt hashed password
        display_name: User's display name (30 chars max)
        is_active: Boolean flag for enabled/disabled accounts
        created_at: Account creation timestamp
        last_seen: Last activity timestamp
        role_id: Foreign key to Role
    """
    
    __tablename__ = 'users'
    
    # Primary key
    id: Mapped[str] = mapped_column(
        String(36),  # UUID as string for SQLite compatibility
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    
    # User identification
    username: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False,
        index=True
    )
    
    email: Mapped[Optional[str]] = mapped_column(
        String(254),  # RFC 5321 maximum email length
        unique=True,
        nullable=True
    )
    
    # Authentication
    password_hash: Mapped[str] = mapped_column(
        String(128),  # Bcrypt hash length
        nullable=False
    )
    
    # User profile
    display_name: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )
    
    # Account status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=db.text("true")
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        server_default=db.text("CURRENT_TIMESTAMP")
    )
    
    last_seen: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Foreign keys
    role_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey('roles.id'),
        nullable=False
    )
    
    # Relationships
    role: Mapped['Role'] = relationship(
        'Role',
        back_populates='users',
        lazy='select'
    )
    
    sent_messages: Mapped[List['Message']] = relationship(
        'Message',
        back_populates='sender',
        lazy='dynamic'
    )
    
    channel_memberships: Mapped[List['ChannelMembership']] = relationship(
        'ChannelMembership',
        back_populates='user',
        lazy='dynamic'
    )
    
    sessions: Mapped[List['Session']] = relationship(
        'Session',
        back_populates='user',
        lazy='dynamic'
    )
    
    created_channels: Mapped[List['Channel']] = relationship(
        'Channel',
        back_populates='creator',
        lazy='dynamic'
    )
    
    # Direct conversation participants (handled via DirectConversation model)
    participant1_conversations: Mapped[List['DirectConversation']] = relationship(
        'DirectConversation',
        foreign_keys='DirectConversation.participant1_id',
        back_populates='participant1',
        lazy='dynamic'
    )
    
    participant2_conversations: Mapped[List['DirectConversation']] = relationship(
        'DirectConversation',
        foreign_keys='DirectConversation.participant2_id',
        back_populates='participant2',
        lazy='dynamic'
    )
    
    def __init__(self, username: str, password_hash: str, role_id: str, 
                 email: Optional[str] = None, display_name: Optional[str] = None):
        """
        Initialize a new User.
        
        Args:
            username: Unique username (3-30 chars)
            password_hash: Bcrypt hashed password
            role_id: Foreign key to Role
            email: Optional email address
            display_name: Optional display name (defaults to username)
        """
        self.username = username
        self.password_hash = password_hash
        self.role_id = role_id
        self.email = email
        self.display_name = display_name or username
        self.is_active = True
        self.created_at = datetime.utcnow()
    
    def __repr__(self) -> str:
        """String representation of User."""
        return f'<User {self.username}>'
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """
        Convert User to dictionary representation.
        
        Args:
            include_sensitive: Whether to include sensitive fields like password_hash
            
        Returns:
            Dictionary representation of the user
        """
        data = {
            'id': str(self.id),
            'username': self.username,
            'email': self.email,
            'display_name': self.display_name,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'role': self.role.to_dict() if self.role else None
        }
        
        if include_sensitive:
            data['password_hash'] = self.password_hash
            data['role_id'] = str(self.role_id)
        
        return data
    
    @classmethod
    def validate_username(cls, username: str) -> bool:
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
        
        # Only alphanumeric characters and underscores
        return username.replace('_', '').replace('-', '').isalnum()
    
    @classmethod
    def validate_email(cls, email: str) -> bool:
        """
        Validate email format.
        
        Args:
            email: Email to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not email:
            return True  # Email is optional
        
        # Basic email validation
        return '@' in email and len(email) <= 254
    
    def update_last_seen(self) -> None:
        """Update the user's last_seen timestamp."""
        self.last_seen = datetime.utcnow()
    
    def get_direct_conversations(self) -> List['DirectConversation']:
        """
        Get all direct conversations for this user.
        
        Returns:
            List of DirectConversation objects where user is a participant
        """
        return (self.participant1_conversations.all() + 
                self.participant2_conversations.all())
    
    def get_channels(self) -> List['Channel']:
        """
        Get all channels this user is a member of.
        
        Returns:
            List of Channel objects
        """
        return [membership.channel for membership in self.channel_memberships.all()]
    
    def is_channel_member(self, channel_id: str) -> bool:
        """
        Check if user is a member of the specified channel.
        
        Args:
            channel_id: UUID of the channel
            
        Returns:
            True if user is a member, False otherwise
        """
        return self.channel_memberships.filter_by(channel_id=channel_id).first() is not None
    
    def can_access_direct_conversation(self, conversation_id: str) -> bool:
        """
        Check if user can access the specified direct conversation.
        
        Args:
            conversation_id: UUID of the direct conversation
            
        Returns:
            True if user is a participant, False otherwise
        """
        return (self.participant1_conversations.filter_by(id=conversation_id).first() is not None or
                self.participant2_conversations.filter_by(id=conversation_id).first() is not None)