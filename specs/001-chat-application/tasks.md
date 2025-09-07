# Tasks: Chat Application

**Input**: Design documents from `/specs/001-chat-application/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → Tech stack: Python 3.11, Flask, SQLAlchemy, Flask-SocketIO, React, Click
   → Libraries: chat-auth, chat-messaging, chat-channels, chat-admin
   → Structure: backend/, frontend/, shared/contracts/
2. Load design documents:
   → data-model.md: 7 entities (User, Message, Channel, DirectConversation, Role, Session, ChannelMembership)
   → contracts/: rest-api.yml, websocket-events.yml
   → research.md: Flask-SocketIO, multi-client sessions, SQLAlchemy patterns
3. Generate tasks by category following TDD workflow
4. Apply [P] for parallel execution (different files, no dependencies)
5. Number tasks sequentially (T001, T002...)
6. Validate: All contracts tested, all entities modeled, tests before implementation
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Phase 3.1: Setup
- [ ] T001 Create project structure: backend/, frontend/, shared/contracts/ directories
- [ ] T002 Initialize Python backend with Flask, SQLAlchemy, Flask-SocketIO, pytest dependencies
- [ ] T003 [P] Initialize React frontend with WebSocket client dependencies
- [ ] T004 [P] Configure backend linting (flake8, black) and formatting tools
- [ ] T005 [P] Configure frontend linting (ESLint, Prettier) and formatting tools
- [ ] T006 [P] Setup SQLite database configuration for development

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Contract Tests - REST API
- [ ] T007 [P] Contract test POST /api/auth/login in backend/tests/contract/test_auth_login.py
- [ ] T008 [P] Contract test POST /api/auth/register in backend/tests/contract/test_auth_register.py
- [ ] T009 [P] Contract test GET /api/users/me in backend/tests/contract/test_users_me.py
- [ ] T010 [P] Contract test POST /api/channels in backend/tests/contract/test_channels_post.py
- [ ] T011 [P] Contract test GET /api/channels in backend/tests/contract/test_channels_get.py
- [ ] T012 [P] Contract test GET /api/channels/{id}/messages in backend/tests/contract/test_channel_messages.py
- [ ] T013 [P] Contract test POST /api/messages/direct in backend/tests/contract/test_direct_messages.py
- [ ] T014 [P] Contract test GET /api/conversations in backend/tests/contract/test_conversations_get.py

### Contract Tests - WebSocket Events
- [ ] T015 [P] Contract test join_channel event in backend/tests/contract/test_websocket_join.py
- [ ] T016 [P] Contract test send_message event in backend/tests/contract/test_websocket_message.py
- [ ] T017 [P] Contract test message_received event in backend/tests/contract/test_websocket_receive.py
- [ ] T018 [P] Contract test user_typing event in backend/tests/contract/test_websocket_typing.py

### Integration Tests
- [ ] T019 [P] Integration test user registration flow in backend/tests/integration/test_user_registration.py
- [ ] T020 [P] Integration test authentication flow in backend/tests/integration/test_auth_flow.py
- [ ] T021 [P] Integration test channel creation and messaging in backend/tests/integration/test_channel_messaging.py
- [ ] T022 [P] Integration test direct messaging in backend/tests/integration/test_direct_messaging.py
- [ ] T023 [P] Integration test real-time WebSocket messaging in backend/tests/integration/test_realtime_messaging.py
- [ ] T024 [P] Integration test multi-client session sync in backend/tests/integration/test_multi_client.py

## Phase 3.3: Core Implementation (ONLY after tests are failing)

### Database Models
- [ ] T025 [P] User model in backend/src/models/user.py
- [ ] T026 [P] Role model in backend/src/models/role.py  
- [ ] T027 [P] Session model in backend/src/models/session.py
- [ ] T028 [P] Channel model in backend/src/models/channel.py
- [ ] T029 [P] Message model in backend/src/models/message.py
- [ ] T030 [P] DirectConversation model in backend/src/models/direct_conversation.py
- [ ] T031 [P] ChannelMembership model in backend/src/models/channel_membership.py
- [ ] T032 Database migration scripts in backend/src/migrations/

### Service Libraries (chat-auth)
- [ ] T033 [P] AuthService for login/register in backend/src/services/auth_service.py
- [ ] T034 [P] SessionService for JWT handling in backend/src/services/session_service.py
- [ ] T035 [P] CLI auth commands in backend/cli/auth_commands.py

### Service Libraries (chat-messaging)
- [ ] T036 [P] MessageService for CRUD operations in backend/src/services/message_service.py
- [ ] T037 [P] DirectConversationService in backend/src/services/direct_conversation_service.py
- [ ] T038 [P] CLI messaging commands in backend/cli/message_commands.py

### Service Libraries (chat-channels)
- [ ] T039 [P] ChannelService for CRUD operations in backend/src/services/channel_service.py
- [ ] T040 [P] ChannelMembershipService in backend/src/services/channel_membership_service.py
- [ ] T041 [P] CLI channel commands in backend/cli/channel_commands.py

### Service Libraries (chat-admin)
- [ ] T042 [P] AdminService for user/channel management in backend/src/services/admin_service.py
- [ ] T043 [P] CLI admin commands in backend/cli/admin_commands.py

### REST API Endpoints
- [ ] T044 POST /api/auth/login endpoint in backend/src/api/auth.py
- [ ] T045 POST /api/auth/register endpoint in backend/src/api/auth.py
- [ ] T046 GET /api/users/me endpoint in backend/src/api/users.py
- [ ] T047 POST /api/channels endpoint in backend/src/api/channels.py
- [ ] T048 GET /api/channels endpoint in backend/src/api/channels.py
- [ ] T049 GET /api/channels/{id}/messages endpoint in backend/src/api/channels.py
- [ ] T050 POST /api/messages/direct endpoint in backend/src/api/messages.py
- [ ] T051 GET /api/conversations endpoint in backend/src/api/conversations.py

### WebSocket Handlers
- [ ] T052 [P] join_channel event handler in backend/src/websocket/channel_handlers.py
- [ ] T053 [P] send_message event handler in backend/src/websocket/message_handlers.py
- [ ] T054 [P] message_received event handler in backend/src/websocket/message_handlers.py
- [ ] T055 [P] user_typing event handler in backend/src/websocket/typing_handlers.py
- [ ] T056 WebSocket connection management in backend/src/websocket/connection_manager.py

## Phase 3.4: Frontend Implementation

### React Components
- [ ] T057 [P] LoginForm component in frontend/src/components/auth/LoginForm.js
- [ ] T058 [P] RegisterForm component in frontend/src/components/auth/RegisterForm.js
- [ ] T059 [P] ChannelList component in frontend/src/components/channels/ChannelList.js
- [ ] T060 [P] MessageList component in frontend/src/components/messages/MessageList.js
- [ ] T061 [P] MessageInput component in frontend/src/components/messages/MessageInput.js
- [ ] T062 [P] DirectMessageList component in frontend/src/components/direct/DirectMessageList.js

### React Pages
- [ ] T063 [P] Login page in frontend/src/pages/LoginPage.js
- [ ] T064 [P] Chat main page in frontend/src/pages/ChatPage.js
- [ ] T065 [P] Channel page in frontend/src/pages/ChannelPage.js
- [ ] T066 [P] Direct messages page in frontend/src/pages/DirectMessagesPage.js

### Frontend Services
- [ ] T067 [P] API client service in frontend/src/services/apiClient.js
- [ ] T068 [P] WebSocket client service in frontend/src/services/websocketClient.js
- [ ] T069 [P] Authentication service in frontend/src/services/authService.js

### React Hooks
- [ ] T070 [P] useAuth hook in frontend/src/hooks/useAuth.js
- [ ] T071 [P] useWebSocket hook in frontend/src/hooks/useWebSocket.js
- [ ] T072 [P] useMessages hook in frontend/src/hooks/useMessages.js

## Phase 3.5: Integration & Polish

### Database Integration
- [ ] T073 Connect all services to SQLAlchemy database in backend/src/database.py
- [ ] T074 JWT middleware for API authentication in backend/src/middleware/auth.py
- [ ] T075 CORS and security headers in backend/src/middleware/security.py
- [ ] T076 Request/response logging middleware in backend/src/middleware/logging.py

### CLI Integration
- [ ] T077 Main CLI entry point with subcommands in backend/cli/main.py
- [ ] T078 CLI configuration and help system in backend/cli/config.py

### Structured Logging
- [ ] T079 [P] Structured JSON logging setup in backend/src/logging/logger.py
- [ ] T080 [P] Frontend error logging to backend in frontend/src/services/errorLogger.js

### Unit Tests
- [ ] T081 [P] Unit tests for AuthService in backend/tests/unit/test_auth_service.py
- [ ] T082 [P] Unit tests for MessageService in backend/tests/unit/test_message_service.py
- [ ] T083 [P] Unit tests for ChannelService in backend/tests/unit/test_channel_service.py
- [ ] T084 [P] Unit tests for React components in frontend/tests/unit/components/

### Performance & Documentation
- [ ] T085 Performance tests (<200ms message delivery) in backend/tests/performance/test_message_latency.py
- [ ] T086 [P] Update quickstart.md with setup and usage instructions
- [ ] T087 [P] Create API documentation from contracts
- [ ] T088 Remove code duplication and refactor
- [ ] T089 Manual testing following quickstart.md scenarios

## Dependencies
- Setup (T001-T006) before all other phases
- Tests (T007-T024) before implementation (T025-T076)
- Models (T025-T032) before services (T033-T043)
- Services before API endpoints (T044-T051)
- Services before WebSocket handlers (T052-T056)
- Backend implementation before frontend integration
- Integration (T073-T078) before polish (T079-T089)

## Parallel Execution Groups

### Group 1: Contract Tests (T007-T024)
All contract and integration tests can run in parallel as they create independent test scenarios.

### Group 2: Database Models (T025-T031)
All model files can be created in parallel as they represent independent entities.

### Group 3: Service Libraries (T033-T043)
Services can be implemented in parallel within each library group:
- auth-services: T033, T034, T035
- messaging-services: T036, T037, T038  
- channel-services: T039, T040, T041
- admin-services: T042, T043

### Group 4: WebSocket Handlers (T052-T055)
Handler files can be implemented in parallel as they handle different event types.

### Group 5: React Components (T057-T072)
All frontend components, pages, services, and hooks can be developed in parallel.

## Validation Checklist
*GATE: Checked before task execution*

- [x] All contracts have corresponding tests (T007-T018 cover rest-api.yml and websocket-events.yml)
- [x] All entities have model tasks (T025-T031 cover all 7 entities from data-model.md)
- [x] All tests come before implementation (Phase 3.2 before Phase 3.3)
- [x] Parallel tasks truly independent (different files, no shared dependencies)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
- [x] TDD workflow enforced (tests must fail before implementation)
- [x] Library-first architecture maintained (services before endpoints)
- [x] CLI interfaces provided for each library
- [x] Structured logging included
- [x] Integration tests cover multi-client scenarios