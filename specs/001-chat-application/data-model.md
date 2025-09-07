# Data Model: Chat Application

**Feature**: Chat Application  
**Date**: 2025-09-07  
**Phase**: 1 - Data Design

## Entity Definitions

### User
Represents an individual with access to the chat system.

**Fields**:
- `id`: Primary key (UUID)
- `username`: Unique username (3-30 chars, alphanumeric + underscore)
- `email`: Email address (optional, for future auth methods)
- `password_hash`: Bcrypt hashed password
- `display_name`: User's display name (30 chars max)
- `is_active`: Boolean flag for enabled/disabled accounts
- `created_at`: Account creation timestamp
- `last_seen`: Last activity timestamp
- `role_id`: Foreign key to Role

**Relationships**:
- `role`: Many-to-One with Role
- `sent_messages`: One-to-Many with Message
- `channel_memberships`: Many-to-Many with Channel through ChannelMembership
- `direct_conversations`: Many-to-Many with DirectConversation through participants
- `sessions`: One-to-Many with Session

**Validation Rules**:
- Username must be unique and 3-30 characters
- Password must be hashed with bcrypt
- Display name defaults to username if not provided
- Email format validation if provided

### Message
Represents a single communication from one user.

**Fields**:
- `id`: Primary key (UUID)
- `content`: Message text content (5000 chars max)
- `sender_id`: Foreign key to User
- `channel_id`: Foreign key to Channel (null for direct messages)
- `direct_conversation_id`: Foreign key to DirectConversation (null for channel messages)
- `created_at`: Message timestamp
- `edited_at`: Last edit timestamp (nullable)
- `is_deleted`: Soft delete flag
- `message_type`: Enum ('text', 'system', 'join', 'leave')

**Relationships**:
- `sender`: Many-to-One with User
- `channel`: Many-to-One with Channel (optional)
- `direct_conversation`: Many-to-One with DirectConversation (optional)

**Validation Rules**:
- Content required for text messages, optional for system messages
- Either channel_id OR direct_conversation_id must be set, not both
- System messages have restricted content format
- Soft delete preserves message for conversation context

**State Transitions**:
- Created → Edited → Deleted (soft)
- System messages cannot be edited or deleted by users

### Channel
Represents a named discussion space for multiple users.

**Fields**:
- `id`: Primary key (UUID)
- `name`: Channel name (3-50 chars, unique, lowercase + hyphens)
- `display_name`: Human-readable channel name
- `description`: Channel description (500 chars max)
- `is_private`: Boolean flag for private/public access
- `is_archived`: Boolean flag for archived channels
- `max_members`: Maximum number of members (default 50)
- `created_by`: Foreign key to User (channel creator)
- `created_at`: Channel creation timestamp
- `updated_at`: Last modification timestamp

**Relationships**:
- `creator`: Many-to-One with User
- `messages`: One-to-Many with Message
- `memberships`: One-to-Many with ChannelMembership
- `members`: Many-to-Many with User through ChannelMembership

**Validation Rules**:
- Name must be unique, lowercase, 3-50 characters
- Display name defaults to capitalized name if not provided
- Private channels require explicit member addition
- Max members must be between 2 and 200

### DirectConversation
Represents a private communication thread between exactly two users.

**Fields**:
- `id`: Primary key (UUID)
- `participant1_id`: Foreign key to User
- `participant2_id`: Foreign key to User
- `created_at`: Conversation start timestamp
- `last_message_at`: Timestamp of most recent message

**Relationships**:
- `participant1`: Many-to-One with User
- `participant2`: Many-to-One with User  
- `messages`: One-to-Many with Message

**Validation Rules**:
- participant1_id and participant2_id must be different
- Unique constraint on sorted (participant1_id, participant2_id) pair
- Both participants must be active users

### Role
Represents a set of permissions assigned to users.

**Fields**:
- `id`: Primary key (UUID)
- `name`: Role name ('admin', 'moderator', 'user')
- `description`: Role description
- `permissions`: JSON field with permission flags

**Relationships**:
- `users`: One-to-Many with User

**Permission Flags** (in JSON field):
- `can_create_channels`: Boolean
- `can_delete_channels`: Boolean  
- `can_modify_channels`: Boolean
- `can_ban_users`: Boolean
- `can_delete_messages`: Boolean
- `can_create_users`: Boolean (admin only)
- `can_modify_users`: Boolean (admin only)

**Default Roles**:
- **admin**: All permissions true
- **moderator**: Channel and message moderation permissions
- **user**: Basic chat permissions only

### Session
Represents an active user connection to the system.

**Fields**:
- `id`: Primary key (UUID)
- `user_id`: Foreign key to User
- `token_jti`: JWT token identifier
- `interface_type`: Enum ('web', 'cli', 'api')
- `created_at`: Session creation timestamp
- `last_active`: Last activity timestamp
- `expires_at`: Session expiration timestamp
- `is_revoked`: Boolean flag for revoked sessions

**Relationships**:
- `user`: Many-to-One with User

**Validation Rules**:
- token_jti must be unique
- expires_at must be in the future on creation
- is_revoked defaults to False

### ChannelMembership
Join table for Channel-User many-to-many relationship.

**Fields**:
- `channel_id`: Foreign key to Channel
- `user_id`: Foreign key to User  
- `joined_at`: Membership start timestamp
- `role`: Enum ('member', 'moderator', 'admin')
- `is_muted`: Boolean flag for muted members

**Relationships**:
- `channel`: Many-to-One with Channel
- `user`: Many-to-One with User

**Validation Rules**:
- Unique constraint on (channel_id, user_id)
- Channel admin can modify member roles
- Muted members cannot send messages

## Entity Relationships Diagram

```
User (1) ←→ (M) Role
  ↓ (1)
  ↓
Session (M)

User (1) ←→ (M) Message
  ↑ (1)         ↓ (M)
  ↑             ↓  
ChannelMembership → Channel (1)
  ↑ (M)              
  ↑                  
User (M) ←→ (M) Channel

User (1) ←→ (M) DirectConversation ←→ (M) User (1)
                     ↓ (1)
                     ↓
                Message (M)
```

## Database Indexes

**Performance-critical indexes**:
- `messages.created_at DESC` - Message history pagination
- `messages.channel_id, messages.created_at DESC` - Channel message history  
- `messages.direct_conversation_id, messages.created_at DESC` - Direct message history
- `users.username` - Login lookups
- `sessions.token_jti` - JWT validation
- `sessions.user_id, sessions.expires_at` - Session cleanup
- `channel_memberships.user_id` - User's channels lookup
- `channel_memberships.channel_id` - Channel members lookup

## Data Constraints

**Business Rules**:
- Users cannot send messages to channels they're not members of
- Private channels require explicit invitation
- System messages can only be created by the system
- Soft-deleted messages remain in database for conversation context
- Channel names must be URL-safe (lowercase, hyphens only)
- Direct conversations are automatically created when first message sent

**Cascading Rules**:
- User deletion → soft delete user, keep messages with "[deleted user]"
- Channel deletion → archive channel, keep messages for audit
- Role deletion → reassign users to default "user" role
- Session expiration → automatic cleanup via background job