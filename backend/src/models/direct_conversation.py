"""
DirectConversation model for DankerChat application.

Represents private communication threads between exactly two users.
Based on specs/001-chat-application/data-model.md
"""

import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import db


class DirectConversation(db.Model):
    """
    DirectConversation model representing private communications between two users.
    
    Attributes:
        id: Primary key (UUID)
        participant1_id: Foreign key to User (first participant)
        participant2_id: Foreign key to User (second participant)
        created_at: Conversation start timestamp
        last_message_at: Timestamp of most recent message
    """
    
    __tablename__ = 'direct_conversations'
    
    # Primary key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()))
    
    # Foreign keys to participants
    participant1_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey('users.id'),
        nullable=False,
        index=True
    )
    
    participant2_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey('users.id'),
        nullable=False,
        index=True
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )
    
    last_message_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True  # For conversation sorting
    )
    
    # Relationships
    participant1: Mapped['User'] = relationship(
        'User',
        foreign_keys=[participant1_id],
        back_populates='participant1_conversations',
        lazy='select'
    )
    
    participant2: Mapped['User'] = relationship(
        'User',
        foreign_keys=[participant2_id],
        back_populates='participant2_conversations',
        lazy='select'
    )
    
    messages: Mapped[List['Message']] = relationship(
        'Message',
        back_populates='direct_conversation',
        lazy='dynamic',
        order_by='Message.created_at'
    )
    
    # Database constraints
    __table_args__ = (
        # Participants must be different users
        CheckConstraint(
            'participant1_id != participant2_id',
            name='different_participants_constraint'
        ),
        # Unique constraint on sorted participant pair to prevent duplicates
        UniqueConstraint(
            'participant1_id', 'participant2_id',
            name='unique_conversation_constraint'
        ),
    )
    
    def __init__(self, participant1_id: str, participant2_id: str):
        """
        Initialize a new DirectConversation.
        
        Args:
            participant1_id: Foreign key to first User
            participant2_id: Foreign key to second User
        """
        # Always store participants in consistent order (smaller UUID first)
        # This ensures uniqueness constraint works properly
        if participant1_id < participant2_id:
            self.participant1_id = participant1_id
            self.participant2_id = participant2_id
        else:
            self.participant1_id = participant2_id
            self.participant2_id = participant1_id
        
        self.created_at = datetime.utcnow()
    
    def __repr__(self) -> str:
        """String representation of DirectConversation."""
        return f'<DirectConversation {self.id[:8]} ({self.participant1_id[:8]}-{self.participant2_id[:8]})>'
    
    def to_dict(self, current_user_id: str, include_sensitive: bool = False) -> dict:
        """
        Convert DirectConversation to dictionary representation.
        
        Args:
            current_user_id: ID of the current user (to determine "other_user")
            include_sensitive: Whether to include sensitive fields
            
        Returns:
            Dictionary representation of the conversation
        """
        other_user = self.get_other_participant(current_user_id)
        last_message = self.get_last_message()
        
        data = {
            'id': str(self.id),
            'other_user': other_user.to_dict() if other_user else None,
            'created_at': self.created_at.isoformat(),
            'last_message_at': self.last_message_at.isoformat() if self.last_message_at else None,
            'last_message': last_message.to_dict() if last_message else None,
            'unread_count': self.get_unread_count(current_user_id)
        }
        
        if include_sensitive:
            data['participant1_id'] = str(self.participant1_id)
            data['participant2_id'] = str(self.participant2_id)
        
        return data
    
    def get_other_participant(self, user_id: str) -> Optional['User']:
        """
        Get the other participant in the conversation.
        
        Args:
            user_id: ID of one participant
            
        Returns:
            User object of the other participant, or None if user_id is not a participant
        """
        if str(self.participant1_id) == str(user_id):
            return self.participant2
        elif str(self.participant2_id) == str(user_id):
            return self.participant1
        else:
            return None
    
    def is_participant(self, user_id: str) -> bool:
        """
        Check if user is a participant in this conversation.
        
        Args:
            user_id: ID of the user
            
        Returns:
            True if user is a participant, False otherwise
        """
        return (str(self.participant1_id) == str(user_id) or
                str(self.participant2_id) == str(user_id))
    
    def get_messages(self, limit: int = 50, before_timestamp: Optional[datetime] = None) -> List['Message']:
        """
        Get messages from this conversation.
        
        Args:
            limit: Maximum number of messages to return
            before_timestamp: Get messages before this timestamp (for pagination)
            
        Returns:
            List of Message objects, most recent first
        """
        query = self.messages.filter_by(is_deleted=False)
        
        if before_timestamp:
            query = query.filter(Message.created_at < before_timestamp)
        
        return query.order_by(Message.created_at.desc()).limit(limit).all()
    
    def get_last_message(self) -> Optional['Message']:
        """
        Get the most recent message in this conversation.
        
        Returns:
            Most recent Message object, or None if no messages
        """
        return (self.messages
                .filter_by(is_deleted=False)
                .order_by(Message.created_at.desc())
                .first())
    
    def update_last_message_timestamp(self, timestamp: Optional[datetime] = None) -> None:
        """
        Update the last_message_at timestamp.
        
        Args:
            timestamp: Timestamp to set (defaults to current time)
        """
        self.last_message_at = timestamp or datetime.utcnow()
    
    def get_unread_count(self, user_id: str) -> int:
        """
        Get count of unread messages for a user.
        
        Note: This is a placeholder implementation.
        In a full implementation, you'd track read receipts per user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Number of unread messages (placeholder: always returns 0)
        """
        # TODO: Implement proper read receipt tracking
        # This would require a separate ReadReceipt model or additional fields
        return 0
    
    def add_message(self, message: 'Message') -> None:
        """
        Add a message to this conversation and update last_message_at.
        
        Args:
            message: Message object to add
        """
        message.direct_conversation_id = str(self.id)
        self.update_last_message_timestamp(message.created_at)
    
    @classmethod
    def find_or_create(cls, user1_id: str, user2_id: str) -> 'DirectConversation':
        """
        Find existing conversation between two users or create a new one.
        
        Args:
            user1_id: ID of first user
            user2_id: ID of second user
            
        Returns:
            DirectConversation object (existing or new)
        """
        # Ensure consistent ordering for database lookup
        if user1_id > user2_id:
            user1_id, user2_id = user2_id, user1_id
        
        conversation = cls.query.filter_by(
            participant1_id=user1_id,
            participant2_id=user2_id
        ).first()
        
        if not conversation:
            conversation = cls(user1_id, user2_id)
            db.session.add(conversation)
            db.session.flush()  # Get the ID without committing
        
        return conversation
    
    @classmethod
    def get_user_conversations(cls, user_id: str, limit: int = 50) -> List['DirectConversation']:
        """
        Get all conversations for a user, ordered by most recent activity.
        
        Args:
            user_id: ID of the user
            limit: Maximum number of conversations to return
            
        Returns:
            List of DirectConversation objects
        """
        return (cls.query
                .filter(
                    (cls.participant1_id == user_id) |
                    (cls.participant2_id == user_id)
                )
                .order_by(cls.last_message_at.desc())
                .limit(limit)
                .all())
    
    def get_message_count(self) -> int:
        """
        Get total number of messages in this conversation.
        
        Returns:
            Total message count
        """
        return self.messages.filter_by(is_deleted=False).count()
    
    def get_participants(self) -> tuple['User', 'User']:
        """
        Get both participants in the conversation.
        
        Returns:
            Tuple of (participant1, participant2)
        """
        return self.participant1, self.participant2
    
    def delete_conversation(self) -> None:
        """
        Delete this conversation and all its messages.
        
        Note: This is a hard delete. In production, you might want soft delete.
        """
        # Delete all messages first
        for message in self.messages.all():
            db.session.delete(message)
        
        # Delete the conversation
        db.session.delete(self)
    
    def is_active(self) -> bool:
        """
        Check if conversation has any messages.
        
        Returns:
            True if conversation has messages, False otherwise
        """
        return self.messages.count() > 0