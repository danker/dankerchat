"""
Message model for DankerChat application.

Represents individual communications from users.
Based on specs/001-chat-application/data-model.md
"""

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, Text, ForeignKey, Enum, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import db
import enum


class MessageType(enum.Enum):
    """Enumeration of message types."""
    TEXT = 'text'
    SYSTEM = 'system'
    JOIN = 'join'
    LEAVE = 'leave'


class Message(db.Model):
    """
    Message model representing individual communications.
    
    Attributes:
        id: Primary key (UUID)
        content: Message text content (5000 chars max)
        sender_id: Foreign key to User
        channel_id: Foreign key to Channel (null for direct messages)
        direct_conversation_id: Foreign key to DirectConversation (null for channel messages)
        created_at: Message timestamp
        edited_at: Last edit timestamp (nullable)
        is_deleted: Soft delete flag
        message_type: Type of message ('text', 'system', 'join', 'leave')
    """
    
    __tablename__ = 'messages'
    
    # Primary key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    
    # Message content
    content: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True  # Optional for system messages
    )
    
    # Foreign keys
    sender_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey('users.id'),
        nullable=False,
        index=True
    )
    
    channel_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey('channels.id'),
        nullable=True,
        index=True
    )
    
    direct_conversation_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey('direct_conversations.id'),
        nullable=True,
        index=True
    )
    
    # Message metadata
    message_type: Mapped[MessageType] = mapped_column(
        Enum(MessageType),
        nullable=False,
        default=MessageType.TEXT
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True  # For message history pagination
    )
    
    edited_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Status flags
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )
    
    # Relationships
    sender: Mapped['User'] = relationship(
        'User',
        back_populates='sent_messages',
        lazy='select'
    )
    
    channel: Mapped[Optional['Channel']] = relationship(
        'Channel',
        back_populates='messages',
        lazy='select'
    )
    
    direct_conversation: Mapped[Optional['DirectConversation']] = relationship(
        'DirectConversation',
        back_populates='messages',
        lazy='select'
    )
    
    # Database constraints
    __table_args__ = (
        # Either channel_id OR direct_conversation_id must be set, not both
        CheckConstraint(
            '(channel_id IS NOT NULL AND direct_conversation_id IS NULL) OR '
            '(channel_id IS NULL AND direct_conversation_id IS NOT NULL)',
            name='message_target_constraint'
        ),
    )
    
    def __init__(self, sender_id: str, content: Optional[str] = None,
                 channel_id: Optional[str] = None,
                 direct_conversation_id: Optional[str] = None,
                 message_type: MessageType = MessageType.TEXT):
        """
        Initialize a new Message.
        
        Args:
            sender_id: Foreign key to User (sender)
            content: Message content (required for text messages)
            channel_id: Foreign key to Channel (for channel messages)
            direct_conversation_id: Foreign key to DirectConversation (for direct messages)
            message_type: Type of message
        """
        self.sender_id = sender_id
        self.content = content
        self.channel_id = channel_id
        self.direct_conversation_id = direct_conversation_id
        self.message_type = message_type
        self.created_at = datetime.utcnow()
        self.is_deleted = False
    
    def __repr__(self) -> str:
        """String representation of Message."""
        target = f"channel:{self.channel_id}" if self.channel_id else f"dm:{self.direct_conversation_id}"
        return f'<Message {self.id[:8]} ({target})>'
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """
        Convert Message to dictionary representation.
        
        Args:
            include_sensitive: Whether to include sensitive fields
            
        Returns:
            Dictionary representation of the message
        """
        data = {
            'id': str(self.id),
            'content': self.content if not self.is_deleted else '[deleted]',
            'sender': self.sender.to_dict() if self.sender else None,
            'created_at': self.created_at.isoformat(),
            'edited_at': self.edited_at.isoformat() if self.edited_at else None,
            'message_type': self.message_type.value,
            'is_deleted': self.is_deleted
        }
        
        # Add target information based on message type
        if self.channel_id:
            data['type'] = 'channel'
            data['target_id'] = str(self.channel_id)
        elif self.direct_conversation_id:
            data['type'] = 'direct'
            data['target_id'] = str(self.direct_conversation_id)
        
        if include_sensitive:
            data['sender_id'] = str(self.sender_id)
            data['channel_id'] = str(self.channel_id) if self.channel_id else None
            data['direct_conversation_id'] = str(self.direct_conversation_id) if self.direct_conversation_id else None
        
        return data
    
    @classmethod
    def validate_content(cls, content: str, message_type: MessageType = MessageType.TEXT) -> bool:
        """
        Validate message content.
        
        Args:
            content: Message content
            message_type: Type of message
            
        Returns:
            True if valid, False otherwise
        """
        if message_type == MessageType.TEXT:
            return content and isinstance(content, str) and len(content.strip()) > 0 and len(content) <= 5000
        
        # System messages may have empty content
        return True
    
    def is_channel_message(self) -> bool:
        """
        Check if this is a channel message.
        
        Returns:
            True if channel message, False otherwise
        """
        return self.channel_id is not None
    
    def is_direct_message(self) -> bool:
        """
        Check if this is a direct message.
        
        Returns:
            True if direct message, False otherwise
        """
        return self.direct_conversation_id is not None
    
    def can_be_edited_by(self, user_id: str) -> bool:
        """
        Check if message can be edited by the specified user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            True if user can edit, False otherwise
        """
        # Only text messages can be edited
        if self.message_type != MessageType.TEXT:
            return False
        
        # Already deleted messages cannot be edited
        if self.is_deleted:
            return False
        
        # Only sender can edit their own messages
        return str(self.sender_id) == str(user_id)
    
    def can_be_deleted_by(self, user_id: str) -> bool:
        """
        Check if message can be deleted by the specified user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            True if user can delete, False otherwise
        """
        # Already deleted messages cannot be deleted again
        if self.is_deleted:
            return False
        
        # Sender can delete their own messages
        if str(self.sender_id) == str(user_id):
            return True
        
        # Check if user has moderation permissions
        # This would need to be implemented based on user roles and channel permissions
        return False
    
    def edit_content(self, new_content: str, editor_user_id: str) -> bool:
        """
        Edit message content.
        
        Args:
            new_content: New message content
            editor_user_id: ID of user making the edit
            
        Returns:
            True if edit successful, False otherwise
        """
        if not self.can_be_edited_by(editor_user_id):
            return False
        
        if not self.validate_content(new_content, self.message_type):
            return False
        
        self.content = new_content
        self.edited_at = datetime.utcnow()
        return True
    
    def soft_delete(self, deleter_user_id: str) -> bool:
        """
        Soft delete this message.
        
        Args:
            deleter_user_id: ID of user deleting the message
            
        Returns:
            True if deletion successful, False otherwise
        """
        if not self.can_be_deleted_by(deleter_user_id):
            return False
        
        self.is_deleted = True
        return True
    
    def restore(self) -> None:
        """Restore a soft-deleted message."""
        self.is_deleted = False
    
    @classmethod
    def create_system_message(cls, content: str, target_channel_id: Optional[str] = None,
                            target_conversation_id: Optional[str] = None,
                            message_type: MessageType = MessageType.SYSTEM) -> 'Message':
        """
        Create a system message.
        
        Args:
            content: System message content
            target_channel_id: Target channel ID (for channel system messages)
            target_conversation_id: Target conversation ID (for DM system messages)
            message_type: Type of system message
            
        Returns:
            New Message object
        """
        # System messages need a system user - this would be created during setup
        system_user_id = "00000000-0000-0000-0000-000000000000"  # Placeholder
        
        return cls(
            sender_id=system_user_id,
            content=content,
            channel_id=target_channel_id,
            direct_conversation_id=target_conversation_id,
            message_type=message_type
        )
    
    def get_age(self) -> datetime:
        """
        Get the age of this message.
        
        Returns:
            Timedelta since message creation
        """
        return datetime.utcnow() - self.created_at
    
    def was_edited(self) -> bool:
        """
        Check if message was edited.
        
        Returns:
            True if message has been edited, False otherwise
        """
        return self.edited_at is not None