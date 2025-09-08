"""
Messaging service for DankerChat application.

Handles message creation, editing, deletion, and retrieval for both channel and direct messages.
Based on specs/001-chat-application/tasks.md T034
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import and_, or_

from database import db
from models.message import Message, MessageType
from models.channel import Channel
from models.channel_membership import ChannelMembership, MembershipRole
from models.direct_conversation import DirectConversation
from models.user import User
from services.auth import AuthService, AuthorizationError


class MessagingError(Exception):
    """Custom exception for messaging errors."""
    pass


class MessagingService:
    """
    Service for handling message operations.
    
    Provides methods for creating, editing, deleting, and retrieving messages
    in both channels and direct conversations.
    """
    
    @classmethod
    def send_channel_message(cls, sender: User, channel_id: str, content: str,
                           message_type: MessageType = MessageType.TEXT) -> Message:
        """
        Send a message to a channel.
        
        Args:
            sender: User sending the message
            channel_id: Target channel ID
            content: Message content
            message_type: Type of message (default: TEXT)
            
        Returns:
            Created Message object
            
        Raises:
            MessagingError: If user cannot send message to channel
        """
        # Get channel
        channel = Channel.query.get(channel_id)
        if not channel:
            raise MessagingError("Channel not found")
        
        if channel.is_archived:
            raise MessagingError("Cannot send messages to archived channel")
        
        # Check if user is a member
        membership = ChannelMembership.query.filter_by(
            channel_id=channel_id,
            user_id=str(sender.id)
        ).first()
        
        if not membership:
            raise MessagingError("User is not a member of this channel")
        
        # Check if user can send messages (not muted)
        if not membership.can_send_messages():
            raise MessagingError("User is muted in this channel")
        
        # Validate content for text messages
        if not Message.validate_content(content, message_type):
            raise MessagingError("Invalid message content")
        
        # Create message
        message = Message(
            sender_id=str(sender.id),
            content=content,
            channel_id=channel_id,
            message_type=message_type
        )
        
        db.session.add(message)
        db.session.commit()
        
        return message
    
    @classmethod
    def send_direct_message(cls, sender: User, recipient_id: str, content: str,
                          message_type: MessageType = MessageType.TEXT) -> Message:
        """
        Send a direct message to another user.
        
        Args:
            sender: User sending the message
            recipient_id: Target user ID
            content: Message content
            message_type: Type of message (default: TEXT)
            
        Returns:
            Created Message object
            
        Raises:
            MessagingError: If message cannot be sent
        """
        # Validate recipient exists
        recipient = User.query.get(recipient_id)
        if not recipient:
            raise MessagingError("Recipient not found")
        
        if not recipient.is_active:
            raise MessagingError("Recipient account is inactive")
        
        # Cannot send message to self
        if str(sender.id) == str(recipient_id):
            raise MessagingError("Cannot send message to yourself")
        
        # Validate content
        if not Message.validate_content(content, message_type):
            raise MessagingError("Invalid message content")
        
        # Find or create conversation
        conversation = DirectConversation.find_or_create(
            str(sender.id), 
            str(recipient_id)
        )
        
        # Create message
        message = Message(
            sender_id=str(sender.id),
            content=content,
            direct_conversation_id=str(conversation.id),
            message_type=message_type
        )
        
        db.session.add(message)
        
        # Update conversation timestamp
        conversation.update_last_message_timestamp(message.created_at)
        
        db.session.commit()
        
        return message
    
    @classmethod
    def edit_message(cls, user: User, message_id: str, new_content: str) -> bool:
        """
        Edit a message.
        
        Args:
            user: User attempting to edit
            message_id: Message ID to edit
            new_content: New message content
            
        Returns:
            True if edit successful, False otherwise
            
        Raises:
            MessagingError: If edit is not allowed
        """
        message = Message.query.get(message_id)
        if not message:
            raise MessagingError("Message not found")
        
        # Check edit permissions
        if not message.can_be_edited_by(str(user.id)):
            raise MessagingError("Cannot edit this message")
        
        # Perform edit
        success = message.edit_content(new_content, str(user.id))
        if success:
            db.session.commit()
        
        return success
    
    @classmethod
    def delete_message(cls, user: User, message_id: str) -> bool:
        """
        Delete (soft delete) a message.
        
        Args:
            user: User attempting to delete
            message_id: Message ID to delete
            
        Returns:
            True if deletion successful, False otherwise
            
        Raises:
            MessagingError: If deletion is not allowed
        """
        message = Message.query.get(message_id)
        if not message:
            raise MessagingError("Message not found")
        
        # Check basic delete permissions
        if not message.can_be_deleted_by(str(user.id)):
            # Check if user has moderation permissions in channel
            if message.is_channel_message():
                membership = ChannelMembership.query.filter_by(
                    channel_id=message.channel_id,
                    user_id=str(user.id)
                ).first()
                
                if not membership or not membership.can_moderate_messages():
                    raise MessagingError("Cannot delete this message")
            else:
                # For direct messages, only sender can delete
                raise MessagingError("Cannot delete this message")
        
        # Perform deletion
        success = message.soft_delete(str(user.id))
        if success:
            db.session.commit()
        
        return success
    
    @classmethod
    def get_channel_messages(cls, user: User, channel_id: str, limit: int = 50,
                           before_timestamp: Optional[datetime] = None) -> List[Message]:
        """
        Get messages from a channel.
        
        Args:
            user: User requesting messages
            channel_id: Channel ID
            limit: Maximum number of messages
            before_timestamp: Get messages before this timestamp (pagination)
            
        Returns:
            List of Message objects
            
        Raises:
            MessagingError: If user cannot access channel
        """
        # Check if user is a member of the channel
        membership = ChannelMembership.query.filter_by(
            channel_id=channel_id,
            user_id=str(user.id)
        ).first()
        
        if not membership:
            raise MessagingError("User is not a member of this channel")
        
        # Build query
        query = Message.query.filter_by(
            channel_id=channel_id,
            is_deleted=False
        )
        
        if before_timestamp:
            query = query.filter(Message.created_at < before_timestamp)
        
        messages = query.order_by(Message.created_at.desc()).limit(limit).all()
        
        # Return in chronological order (oldest first)
        return list(reversed(messages))
    
    @classmethod
    def get_direct_messages(cls, user: User, conversation_id: str, limit: int = 50,
                          before_timestamp: Optional[datetime] = None) -> List[Message]:
        """
        Get messages from a direct conversation.
        
        Args:
            user: User requesting messages
            conversation_id: Conversation ID
            limit: Maximum number of messages
            before_timestamp: Get messages before this timestamp (pagination)
            
        Returns:
            List of Message objects
            
        Raises:
            MessagingError: If user cannot access conversation
        """
        # Get conversation and verify user is a participant
        conversation = DirectConversation.query.get(conversation_id)
        if not conversation:
            raise MessagingError("Conversation not found")
        
        if not conversation.is_participant(str(user.id)):
            raise MessagingError("User is not a participant in this conversation")
        
        return conversation.get_messages(limit, before_timestamp)
    
    @classmethod
    def get_user_direct_conversations(cls, user: User, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get all direct conversations for a user.
        
        Args:
            user: User requesting conversations
            limit: Maximum number of conversations
            
        Returns:
            List of conversation dictionaries with other user info
        """
        conversations = DirectConversation.get_user_conversations(str(user.id), limit)
        
        result = []
        for conversation in conversations:
            other_user = conversation.get_other_participant(str(user.id))
            if other_user:
                result.append({
                    'conversation': conversation.to_dict(str(user.id)),
                    'other_user': other_user.to_dict(),
                    'last_message': conversation.get_last_message(),
                    'unread_count': conversation.get_unread_count(str(user.id))
                })
        
        return result
    
    @classmethod
    def get_user_channels(cls, user: User) -> List[Dict[str, Any]]:
        """
        Get all channels a user is a member of.
        
        Args:
            user: User requesting channels
            
        Returns:
            List of channel dictionaries with membership info
        """
        memberships = ChannelMembership.get_user_memberships(str(user.id))
        
        result = []
        for membership in memberships:
            channel = membership.channel
            if channel and not channel.is_archived:
                result.append({
                    'channel': channel.to_dict(),
                    'membership': membership.to_dict(),
                    'last_message': channel.get_recent_messages(1)[0] if channel.get_recent_messages(1) else None,
                    'member_count': channel.get_member_count()
                })
        
        return result
    
    @classmethod
    def search_messages(cls, user: User, query: str, channel_id: Optional[str] = None,
                       conversation_id: Optional[str] = None, limit: int = 50) -> List[Message]:
        """
        Search messages by content.
        
        Args:
            user: User performing search
            query: Search query
            channel_id: Optional channel to search in
            conversation_id: Optional conversation to search in
            limit: Maximum results
            
        Returns:
            List of matching Message objects
            
        Raises:
            MessagingError: If user cannot access specified channel/conversation
        """
        if not query or len(query.strip()) < 2:
            raise MessagingError("Search query must be at least 2 characters")
        
        base_query = Message.query.filter(
            Message.is_deleted == False,
            Message.content.ilike(f'%{query}%')
        )
        
        if channel_id:
            # Verify user can access channel
            membership = ChannelMembership.query.filter_by(
                channel_id=channel_id,
                user_id=str(user.id)
            ).first()
            
            if not membership:
                raise MessagingError("User is not a member of this channel")
            
            base_query = base_query.filter(Message.channel_id == channel_id)
        
        elif conversation_id:
            # Verify user can access conversation
            conversation = DirectConversation.query.get(conversation_id)
            if not conversation or not conversation.is_participant(str(user.id)):
                raise MessagingError("User is not a participant in this conversation")
            
            base_query = base_query.filter(Message.direct_conversation_id == conversation_id)
        
        else:
            # Search across all accessible messages
            # Get user's channel IDs
            user_channel_ids = [
                m.channel_id for m in 
                ChannelMembership.get_user_memberships(str(user.id))
            ]
            
            # Get user's conversation IDs
            user_conversations = DirectConversation.get_user_conversations(str(user.id))
            user_conversation_ids = [str(c.id) for c in user_conversations]
            
            # Filter to accessible messages
            base_query = base_query.filter(
                or_(
                    Message.channel_id.in_(user_channel_ids),
                    Message.direct_conversation_id.in_(user_conversation_ids)
                )
            )
        
        return base_query.order_by(Message.created_at.desc()).limit(limit).all()
    
    @classmethod
    def create_system_message(cls, content: str, channel_id: Optional[str] = None,
                            conversation_id: Optional[str] = None,
                            message_type: MessageType = MessageType.SYSTEM) -> Message:
        """
        Create a system message.
        
        Args:
            content: System message content
            channel_id: Target channel ID (for channel messages)
            conversation_id: Target conversation ID (for direct messages)
            message_type: Type of system message
            
        Returns:
            Created Message object
            
        Raises:
            MessagingError: If neither channel nor conversation specified
        """
        if not channel_id and not conversation_id:
            raise MessagingError("Must specify either channel_id or conversation_id")
        
        if channel_id and conversation_id:
            raise MessagingError("Cannot specify both channel_id and conversation_id")
        
        message = Message.create_system_message(
            content=content,
            target_channel_id=channel_id,
            target_conversation_id=conversation_id,
            message_type=message_type
        )
        
        db.session.add(message)
        db.session.commit()
        
        return message
    
    @classmethod
    def get_message_stats(cls, user: User) -> Dict[str, int]:
        """
        Get message statistics for a user.
        
        Args:
            user: User to get stats for
            
        Returns:
            Dictionary with message statistics
        """
        stats = {
            'total_sent': Message.query.filter_by(
                sender_id=str(user.id),
                is_deleted=False
            ).count(),
            'channel_messages': Message.query.filter_by(
                sender_id=str(user.id),
                is_deleted=False
            ).filter(Message.channel_id.isnot(None)).count(),
            'direct_messages': Message.query.filter_by(
                sender_id=str(user.id),
                is_deleted=False
            ).filter(Message.direct_conversation_id.isnot(None)).count(),
            'deleted_messages': Message.query.filter_by(
                sender_id=str(user.id),
                is_deleted=True
            ).count()
        }
        
        return stats
    
    @classmethod
    def get_recent_activity(cls, user: User, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get recent messaging activity for a user.
        
        Args:
            user: User to get activity for
            limit: Maximum number of activity items
            
        Returns:
            List of activity dictionaries
        """
        # Get user's channel IDs
        user_channel_ids = [
            m.channel_id for m in 
            ChannelMembership.get_user_memberships(str(user.id))
        ]
        
        # Get user's conversation IDs
        user_conversations = DirectConversation.get_user_conversations(str(user.id))
        user_conversation_ids = [str(c.id) for c in user_conversations]
        
        # Get recent messages from accessible channels and conversations
        recent_messages = Message.query.filter(
            Message.is_deleted == False,
            or_(
                Message.channel_id.in_(user_channel_ids),
                Message.direct_conversation_id.in_(user_conversation_ids)
            )
        ).order_by(Message.created_at.desc()).limit(limit).all()
        
        activity = []
        for message in recent_messages:
            activity_item = {
                'message': message.to_dict(),
                'timestamp': message.created_at.isoformat(),
                'type': 'channel_message' if message.is_channel_message() else 'direct_message'
            }
            
            if message.is_channel_message():
                activity_item['channel'] = message.channel.to_dict() if message.channel else None
            else:
                activity_item['conversation'] = message.direct_conversation.to_dict(str(user.id)) if message.direct_conversation else None
            
            activity.append(activity_item)
        
        return activity