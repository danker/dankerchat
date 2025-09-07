# DankerChat

A modern, multi-interface chat application with real-time messaging, built using specification-driven development principles.

## Overview

DankerChat is a comprehensive chat platform that provides seamless communication through multiple interfaces:

- **Web Interface**: Modern, responsive React-based chat with real-time messaging
- **REST API**: Full programmatic access for integrations and automation
- **CLI Client**: Command-line interface for terminal users and scripting
- **Admin Dashboard**: Complete user and channel management interface

### Key Features

- 🚀 **Real-time Messaging**: WebSocket-powered instant message delivery
- 💬 **Multi-format Chat**: Direct messages and public/private channels
- 🔐 **Secure Authentication**: JWT-based auth with session management
- 👥 **User Management**: Role-based permissions and admin controls  
- 🌐 **Multi-interface**: Consistent experience across web, API, and CLI
- 📱 **Responsive Design**: Modern UI that works on all devices
- 🔧 **Developer-friendly**: Comprehensive API documentation and CLI tools

## Architecture

Built following strict **Test-Driven Development** principles with a **library-first architecture**:

### Tech Stack

**Backend**
- Python 3.11+ with Flask framework
- SQLAlchemy ORM with PostgreSQL/SQLite
- Flask-SocketIO for real-time WebSocket messaging
- Redis for session management and message brokering
- JWT authentication with refresh token support

**Frontend** 
- React 18+ with TypeScript
- Socket.io client for real-time updates
- Modern responsive CSS framework
- Progressive Web App capabilities

**CLI**
- Click framework for command-line interface
- JSON output support for scripting
- Interactive and non-interactive modes

### Core Libraries

- `chat-auth`: Authentication and session management
- `chat-messaging`: Direct message handling and delivery
- `chat-channels`: Channel management and group messaging  
- `chat-admin`: User and channel administration

## Development Workflow

This project follows a **specification-driven development** approach with strict TDD practices:

### 1. Feature Development Process

```bash
# Create new feature specification
./scripts/create-new-feature.sh "feature description"

# Generate implementation plan
./scripts/setup-plan.sh

# Check prerequisites before implementation
./scripts/check-task-prerequisites.sh

# Generate implementation tasks
# (Future: /tasks command)
```

### 2. Constitutional Principles

- **Library-First**: Every feature implemented as standalone, testable library
- **CLI Interface**: All libraries expose functionality via command-line tools  
- **Test-First**: RED-GREEN-Refactor cycle strictly enforced
- **Integration Testing**: Real dependencies, no mocking for integration tests
- **Observability**: Structured logging with correlation IDs

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+  
- Redis 7.0+
- Git

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/danker/dankerchat.git
   cd dankerchat
   ```

2. **Backend setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   
   # Set environment variables
   export FLASK_ENV=development
   export DATABASE_URL=sqlite:///chat.db
   export REDIS_URL=redis://localhost:6379/0
   
   # Initialize database
   flask db upgrade
   python app.py
   ```

3. **Frontend setup**
   ```bash
   cd frontend
   npm install
   npm start
   ```

4. **CLI setup**
   ```bash
   cd backend
   pip install -e .
   chat --help
   ```

### Usage Examples

**Web Interface**: Navigate to `http://localhost:3000`

**API Usage**:
```bash
# Login
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Send message
curl -X POST http://localhost:5000/api/v1/channels/{channel_id}/messages \
  -H "Authorization: Bearer {token}" \
  -d '{"content": "Hello from API!"}'
```

**CLI Usage**:
```bash
# Interactive mode
chat interactive --username admin

# Command mode  
chat send --channel general --message "Hello world!"
```

## Project Structure

```
dankerchat/
├── README.md                    # This file
├── CLAUDE.md                    # AI assistant guidance
├── backend/                     # Python Flask backend (planned)
│   ├── src/
│   │   ├── models/             # SQLAlchemy models
│   │   ├── services/           # Business logic libraries  
│   │   ├── api/                # REST API endpoints
│   │   └── websocket/          # SocketIO event handlers
│   ├── tests/                  # Backend test suite
│   └── cli/                    # Command-line interface
├── frontend/                   # React frontend (planned)
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── pages/              # Main application pages
│   │   └── services/           # API and WebSocket clients
│   └── tests/                  # Frontend test suite
├── specs/                      # Feature specifications
│   └── 001-chat-application/   # Current feature docs
│       ├── spec.md             # Feature requirements
│       ├── plan.md             # Implementation plan
│       ├── data-model.md       # Database design
│       ├── contracts/          # API specifications
│       └── quickstart.md       # Setup guide
├── scripts/                    # Development workflow scripts
├── templates/                  # Specification templates
└── memory/                     # Project constitution and guidelines
```

## Current Status

🚧 **In Development** - Currently in specification and planning phase

### Completed
- ✅ Feature specification with 29 functional requirements
- ✅ Implementation plan and technical architecture
- ✅ Database design with 6 core entities  
- ✅ REST API specification (OpenAPI 3.0)
- ✅ WebSocket event specifications
- ✅ Comprehensive setup and usage documentation

### Next Steps
- 📋 Generate implementation task list
- 🧪 Create contract tests (API and WebSocket)
- 🏗️ Implement core libraries following TDD
- 🎨 Build React frontend components
- 🖥️ Develop CLI client
- 🧪 Full integration test suite

## Documentation

- **Feature Specification**: [`specs/001-chat-application/spec.md`](specs/001-chat-application/spec.md)
- **Implementation Plan**: [`specs/001-chat-application/plan.md`](specs/001-chat-application/plan.md)  
- **Database Design**: [`specs/001-chat-application/data-model.md`](specs/001-chat-application/data-model.md)
- **API Documentation**: [`specs/001-chat-application/contracts/rest-api.yml`](specs/001-chat-application/contracts/rest-api.yml)
- **WebSocket Events**: [`specs/001-chat-application/contracts/websocket-events.yml`](specs/001-chat-application/contracts/websocket-events.yml)
- **Setup Guide**: [`specs/001-chat-application/quickstart.md`](specs/001-chat-application/quickstart.md)

## Contributing

This project follows specification-driven development:

1. **All features start with a specification** defining WHAT users need (not HOW to implement)
2. **Implementation plans** are created after specification approval  
3. **Tests are written first** and must fail before implementation begins
4. **Every feature becomes a library** with CLI interface
5. **Integration tests use real dependencies** (no mocking)

See [`CLAUDE.md`](CLAUDE.md) for detailed development workflow and constitutional principles.

## API Reference

### Authentication
- `POST /api/v1/auth/login` - User login with JWT tokens
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Invalidate user session

### Users  
- `GET /api/v1/users` - List users (admin only)
- `POST /api/v1/users` - Create user (admin only)
- `GET|PUT /api/v1/users/{id}` - Get/update user details

### Channels
- `GET /api/v1/channels` - List accessible channels
- `POST /api/v1/channels` - Create new channel
- `GET|PUT /api/v1/channels/{id}` - Get/update channel

### Messages
- `GET|POST /api/v1/channels/{id}/messages` - Channel messaging
- `GET|POST /api/v1/conversations/{user_id}/messages` - Direct messaging

Full API documentation available in OpenAPI format at [`specs/001-chat-application/contracts/rest-api.yml`](specs/001-chat-application/contracts/rest-api.yml).

## WebSocket Events

Real-time messaging via Socket.IO:

**Client → Server**: `connect`, `join_channel`, `send_message`, `start_typing`
**Server → Client**: `message_received`, `user_joined_channel`, `user_typing`

Complete event documentation: [`specs/001-chat-application/contracts/websocket-events.yml`](specs/001-chat-application/contracts/websocket-events.yml)

## License

MIT License - see LICENSE file for details.

## Support

- 📖 **Documentation**: Check the `/specs/` directory for comprehensive guides
- 🐛 **Issues**: Report bugs via GitHub Issues  
- 💡 **Feature Requests**: Create feature specifications following the established pattern
- 🤝 **Contributing**: Follow the specification-driven development workflow

---

Built with ❤️ using specification-driven development and test-first principles.