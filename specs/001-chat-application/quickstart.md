# Chat Application Quickstart Guide

**Version**: 0.1.0  
**Date**: 2025-09-07  

This guide walks through setting up and using the chat application across all interfaces.

## Prerequisites

- Python 3.11+
- Node.js 18+
- Redis 7.0+
- SQLite (development) or PostgreSQL (production)

## Installation & Setup

### 1. Backend Setup

```bash
# Clone and enter repository
git clone <repository-url>
cd dankerchat

# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install backend dependencies
cd backend
pip install -r requirements.txt

# Set environment variables
export FLASK_ENV=development
export DATABASE_URL=sqlite:///chat.db
export REDIS_URL=redis://localhost:6379/0
export JWT_SECRET_KEY=your-secret-key-here

# Initialize database
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Create default admin user
flask create-admin admin admin123

# Start Redis server (separate terminal)
redis-server

# Start backend server
python app.py
```

Backend will be running at `http://localhost:5000`

### 2. Frontend Setup

```bash
# In new terminal, from project root
cd frontend

# Install dependencies  
npm install

# Set environment variables
echo "REACT_APP_API_URL=http://localhost:5000/api/v1" > .env
echo "REACT_APP_SOCKET_URL=http://localhost:5000" >> .env

# Start development server
npm start
```

Frontend will be available at `http://localhost:3000`

### 3. CLI Client Setup

```bash
# Install CLI globally (from backend directory)
pip install -e .

# Or use directly
python -m chat_cli --help
```

## Usage Examples

### Web Interface

1. **Login**
   - Navigate to `http://localhost:3000`
   - Use default admin credentials: `admin` / `admin123`
   - Or create a new account

2. **Create a Channel**
   - Click "Create Channel" button
   - Enter channel name (lowercase, hyphens allowed)
   - Add description and set privacy level
   - Click "Create"

3. **Join Conversations**
   - Click on channel name in sidebar to join
   - Click on user name for direct messages
   - Type message and press Enter to send

4. **Admin Functions** (admin users only)
   - Access admin panel via settings menu
   - Create/modify/delete users
   - Manage channel settings and permissions

### REST API

#### Authentication
```bash
# Login to get JWT tokens
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Response includes access_token and refresh_token
export TOKEN="<access_token_from_response>"
```

#### Send Messages
```bash  
# Send message to channel
curl -X POST http://localhost:5000/api/v1/channels/<channel_id>/messages \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello from API!"}'

# Send direct message
curl -X POST http://localhost:5000/api/v1/conversations/<user_id>/messages \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "Private message from API"}'
```

#### Get Message History
```bash
# Get channel messages
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:5000/api/v1/channels/<channel_id>/messages?limit=20"

# Get direct message history  
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:5000/api/v1/conversations/<user_id>/messages"
```

### Command Line Interface

#### Interactive Mode
```bash
# Start interactive chat session
chat interactive --username admin --password admin123

# Once logged in, commands available:
/channels                    # List available channels
/join general               # Join channel named 'general'
/leave general              # Leave channel
/direct @alice              # Start direct message with alice
/who                        # List online users
/quit                       # Exit chat session

# Send messages by just typing (no command prefix)
Hello everyone!
```

#### Command Mode (for scripting)
```bash
# Login and get token
TOKEN=$(chat login admin admin123 --format json | jq -r .access_token)

# Send channel message
chat send --channel general --message "Automated message" --token $TOKEN

# Send direct message  
chat send --user alice --message "Private automated message" --token $TOKEN

# List channels
chat channels --token $TOKEN --format json

# Get message history
chat history --channel general --limit 10 --token $TOKEN
```

## Testing the System

### 1. Multi-Interface Test
This validates that messages appear across all interfaces in real-time:

```bash
# Terminal 1: Start CLI in interactive mode
chat interactive --username admin

# Terminal 2: Send API message
curl -X POST http://localhost:5000/api/v1/channels/<channel_id>/messages \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "API test message"}'

# Web browser: Go to same channel
# Verify message appears in CLI, browser, and API responses immediately
```

### 2. User Management Test
```bash
# Create user via API
curl -X POST http://localhost:5000/api/v1/users \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}'

# Login as new user
chat interactive --username testuser --password testpass123

# Verify user appears in web interface user list
# Test permissions (regular user should not see admin functions)
```

### 3. WebSocket Connection Test  
```bash
# Use a WebSocket client tool or browser console:
const socket = io('http://localhost:5000', {
  auth: {
    token: 'your-jwt-token'
  }
});

socket.on('connect', () => console.log('Connected'));
socket.on('message_received', (data) => console.log('New message:', data));
socket.emit('join_channel', {channel_id: 'channel-uuid'});
```

## Validation Checklist

Complete this checklist to verify the system is working correctly:

### Basic Functionality
- [ ] Backend server starts without errors
- [ ] Frontend loads and displays login page  
- [ ] Redis connection established
- [ ] Database migrations applied successfully
- [ ] Admin user created and can login

### Authentication
- [ ] Web login works with correct credentials
- [ ] API authentication returns valid JWT tokens
- [ ] CLI authentication works in both modes
- [ ] Invalid credentials properly rejected
- [ ] Token refresh mechanism works

### Messaging
- [ ] Send message via web interface
- [ ] Send message via REST API  
- [ ] Send message via CLI
- [ ] Messages appear in real-time across all interfaces
- [ ] Message history retrieved correctly
- [ ] Direct messages work between users

### Channels  
- [ ] Create channel via web interface
- [ ] Join/leave channels works
- [ ] Channel message history loads
- [ ] Private channels restrict access properly
- [ ] Channel member list updates

### Administration
- [ ] Admin can create new users
- [ ] Admin can modify user roles
- [ ] Admin can manage channels
- [ ] Regular users cannot access admin functions
- [ ] User disable/enable works correctly

### Error Handling
- [ ] Invalid API requests return proper error codes
- [ ] WebSocket disconnection/reconnection works  
- [ ] Rate limiting prevents spam
- [ ] Graceful handling of Redis/database outages
- [ ] Clear error messages for users

## Troubleshooting

### Backend Not Starting
- Check Python version: `python --version` (should be 3.11+)
- Verify Redis is running: `redis-cli ping` (should return PONG)
- Check database connection and migrations
- Verify environment variables are set

### WebSocket Connection Issues  
- Check CORS settings in Flask-SocketIO configuration
- Verify JWT token is valid and not expired
- Check Redis pub/sub functionality
- Monitor browser network tab for WebSocket errors

### Message Delivery Problems
- Check Redis pub/sub channels: `redis-cli monitor`
- Verify database message persistence
- Check WebSocket room membership
- Monitor Flask-SocketIO debug logs

### Performance Issues
- Monitor Redis memory usage
- Check database query performance with EXPLAIN
- Verify connection pooling configuration
- Monitor WebSocket connection count

## Next Steps

After completing the quickstart:

1. **Production Deployment**: Configure PostgreSQL, proper Redis setup, reverse proxy
2. **Security Hardening**: Environment-specific JWT secrets, HTTPS, rate limiting
3. **Monitoring**: Set up logging, metrics collection, health checks
4. **Testing**: Run full test suite with `pytest backend/tests/`
5. **Documentation**: Read API documentation at `/docs` endpoint

For development, see `/specs/001-chat-application/tasks.md` for implementation task details.