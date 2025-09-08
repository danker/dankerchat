"""
Session model for DankerChat application.

Represents active user connections to the system.
Based on specs/001-chat-application/data-model.md
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import db
import enum


class InterfaceType(enum.Enum):
    """Enumeration of interface types for sessions."""
    WEB = 'web'
    CLI = 'cli'
    API = 'api'


class Session(db.Model):
    """
    Session model representing active user connections.
    
    Attributes:
        id: Primary key (UUID)
        user_id: Foreign key to User
        token_jti: JWT token identifier
        interface_type: Type of interface ('web', 'cli', 'api')
        created_at: Session creation timestamp
        last_active: Last activity timestamp
        expires_at: Session expiration timestamp
        is_revoked: Boolean flag for revoked sessions
    """
    
    __tablename__ = 'sessions'
    
    # Primary key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()))
    
    # Foreign keys
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey('users.id'),
        nullable=False,
        index=True
    )
    
    # Session identification
    token_jti: Mapped[str] = mapped_column(
        String(36),  # UUID string length
        unique=True,
        nullable=False,
        index=True
    )
    
    interface_type: Mapped[InterfaceType] = mapped_column(
        Enum(InterfaceType),
        nullable=False
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )
    
    last_active: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )
    
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    
    # Session status
    is_revoked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )
    
    # Relationships
    user: Mapped['User'] = relationship(
        'User',
        back_populates='sessions',
        lazy='select'
    )
    
    def __init__(self, user_id: str, token_jti: str, interface_type: InterfaceType,
                 expires_in_hours: int = 24):
        """
        Initialize a new Session.
        
        Args:
            user_id: Foreign key to User
            token_jti: JWT token identifier
            interface_type: Type of interface
            expires_in_hours: Hours until session expires (default 24)
        """
        self.user_id = user_id
        self.token_jti = token_jti
        self.interface_type = interface_type
        self.created_at = datetime.utcnow()
        self.last_active = datetime.utcnow()
        self.expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        self.is_revoked = False
    
    def __repr__(self) -> str:
        """String representation of Session."""
        return f'<Session {self.token_jti} ({self.interface_type.value})>'
    
    def to_dict(self) -> dict:
        """
        Convert Session to dictionary representation.
        
        Returns:
            Dictionary representation of the session
        """
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'token_jti': self.token_jti,
            'interface_type': self.interface_type.value,
            'created_at': self.created_at.isoformat(),
            'last_active': self.last_active.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'is_revoked': self.is_revoked,
            'is_expired': self.is_expired(),
            'is_active': self.is_active()
        }
    
    def update_activity(self) -> None:
        """Update the session's last_active timestamp."""
        self.last_active = datetime.utcnow()
    
    def is_expired(self) -> bool:
        """
        Check if session is expired.
        
        Returns:
            True if session has expired, False otherwise
        """
        return datetime.utcnow() > self.expires_at
    
    def is_active(self) -> bool:
        """
        Check if session is active (not revoked and not expired).
        
        Returns:
            True if session is active, False otherwise
        """
        return not self.is_revoked and not self.is_expired()
    
    def revoke(self) -> None:
        """Revoke this session."""
        self.is_revoked = True
    
    def extend_expiration(self, hours: int = 24) -> None:
        """
        Extend the session expiration.
        
        Args:
            hours: Hours to extend from now
        """
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)
    
    @classmethod
    def cleanup_expired_sessions(cls) -> int:
        """
        Remove expired sessions from the database.
        
        Returns:
            Number of sessions removed
        """
        expired_sessions = cls.query.filter(
            cls.expires_at < datetime.utcnow()
        ).all()
        
        count = len(expired_sessions)
        
        for session in expired_sessions:
            db.session.delete(session)
        
        db.session.commit()
        return count
    
    @classmethod
    def revoke_user_sessions(cls, user_id: str) -> int:
        """
        Revoke all sessions for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Number of sessions revoked
        """
        sessions = cls.query.filter_by(user_id=user_id, is_revoked=False).all()
        
        count = 0
        for session in sessions:
            session.revoke()
            count += 1
        
        db.session.commit()
        return count
    
    @classmethod
    def find_by_token_jti(cls, token_jti: str) -> Optional['Session']:
        """
        Find session by JWT token identifier.
        
        Args:
            token_jti: JWT token identifier
            
        Returns:
            Session object if found, None otherwise
        """
        return cls.query.filter_by(token_jti=token_jti).first()
    
    @classmethod
    def get_active_user_sessions(cls, user_id: str) -> list['Session']:
        """
        Get all active sessions for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of active Session objects
        """
        return cls.query.filter_by(
            user_id=user_id,
            is_revoked=False
        ).filter(
            cls.expires_at > datetime.utcnow()
        ).all()
    
    def time_until_expiry(self) -> timedelta:
        """
        Get time remaining until session expires.
        
        Returns:
            Timedelta until expiration (negative if already expired)
        """
        return self.expires_at - datetime.utcnow()
    
    def get_duration(self) -> timedelta:
        """
        Get total session duration from creation to last activity.
        
        Returns:
            Timedelta of session duration
        """
        return self.last_active - self.created_at