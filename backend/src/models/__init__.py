"""
Database models for DankerChat application.

All models use SQLAlchemy ORM with Flask-SQLAlchemy integration.
Models are designed based on specs/001-chat-application/data-model.md
"""

from database import db

# Import all models for proper relationship resolution
from .role import Role
from .user import User
from .session import Session
from .channel import Channel
from .direct_conversation import DirectConversation
from .message import Message
from .channel_membership import ChannelMembership

# Export all models
__all__ = [
    'db',
    'User',
    'Role', 
    'Session',
    'Channel',
    'Message',
    'DirectConversation',
    'ChannelMembership'
]