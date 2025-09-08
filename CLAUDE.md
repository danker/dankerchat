# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a specification-driven development framework that enforces strict Test-Driven Development (TDD) practices. Features are developed in numbered branches (e.g., `001-feature-name`) with comprehensive documentation before any implementation.

**Current Features**:
- **Chat Application** (branch: `001-chat-application`): Multi-interface chat with Web, CLI, and REST API
- **UV Migration** (branch: `002-uv-migration`): Package management migration from venv to uv

**Package Management**: Uses UV instead of venv/pip for 10-100x faster dependency management  
**Libraries**: Flask, SQLAlchemy, Flask-SocketIO, React, Click  
**Architecture**: Frontend + Backend + CLI client structure

## Key Commands

### UV-Based Development Workflow

```bash
# Environment Setup (one-time)
uv sync                              # Install all dependencies (fast!)
./scripts/env-setup.sh setup        # Create .env file and directories

# Daily Development Commands
./scripts/dev-commands.sh test       # Run test suite with coverage
./scripts/dev-commands.sh lint       # Run ruff + black checks
./scripts/dev-commands.sh format     # Format code with black + ruff
./scripts/dev-commands.sh server     # Start development server
./scripts/dev-commands.sh shell      # Interactive Python shell

# UV Utilities
./scripts/uv-helpers.sh status       # Show environment status
./scripts/uv-helpers.sh health       # Health check
./scripts/uv-helpers.sh benchmark    # Performance benchmark
./scripts/uv-helpers.sh sync         # Smart sync (only if needed)

# Package Management
uv add package-name                  # Add runtime dependency  
uv add --dev package-name            # Add development dependency
uv remove package-name               # Remove dependency
uv sync                             # Sync all dependencies

# Environment Management
uv run python script.py             # Run Python with UV environment
uv run pytest tests/                # Run tests with UV environment
./scripts/env-setup.sh validate     # Validate environment configuration
```

### Feature Development Workflow

```bash
# 1. Create a new feature branch and spec
./scripts/create-new-feature.sh "feature description"
# Creates: 00X-feature-name branch and specs/00X-feature-name/spec.md

# 2. Setup implementation plan
./scripts/setup-plan.sh
# Creates: specs/BRANCH_NAME/plan.md from template

# 3. Check prerequisites before task generation
./scripts/check-task-prerequisites.sh
# Verifies: plan.md exists, lists available design docs

# 4. Update agent context (for AI assistants)
./scripts/update-agent-context.sh [claude|gemini|copilot]
# Updates: CLAUDE.md, GEMINI.md, or .github/copilot-instructions.md

# 5. Get feature paths for current branch
./scripts/get-feature-paths.sh
# Returns: All paths for specs, plans, tasks, contracts
```

### Script Options
- All scripts support `--json` flag for JSON output
- Use `--help` or `-h` for usage information

### Python Environment Commands

**UV Package Management** (preferred):
```bash
# Setup environment and dependencies
uv sync

# Run Python commands
uv run python app.py
uv run pytest
uv run flask run

# Add/remove packages  
uv add package-name
uv remove package-name

# Interactive shell
uv shell

# Update all dependencies
uv sync --upgrade
```

**Traditional Commands** (for reference):
```bash
# Create and activate venv (deprecated)
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install dependencies (deprecated)
pip install -r requirements.txt
```

## Project Structure

### Feature Documentation
Each feature lives in a numbered branch with its own spec directory:

```
specs/00X-feature-name/
├── spec.md           # Feature specification (WHAT and WHY)
├── plan.md           # Implementation plan (HOW)
├── research.md       # Technical research and decisions
├── data-model.md     # Entity definitions
├── quickstart.md     # User guide
├── contracts/        # API contracts (OpenAPI/GraphQL)
└── tasks.md          # Numbered implementation tasks
```

### Development Phases

1. **Specification Phase** (`spec.md`)
   - Focus on WHAT users need, not HOW to implement
   - Mark ambiguities with `[NEEDS CLARIFICATION: question]`
   - All requirements must be testable

2. **Planning Phase** (`plan.md`)
   - Research unknowns → `research.md`
   - Design contracts and data models
   - Must pass Constitution checks before proceeding

3. **Task Generation** (`tasks.md`)
   - Tests ALWAYS written before implementation
   - Tasks marked `[P]` can execute in parallel
   - Follow: Contract → Integration → E2E → Unit test order

4. **Implementation**
   - RED-GREEN-Refactor cycle mandatory
   - Tests must fail first, then implement to make green
   - Every feature implemented as a library with CLI

## Constitutional Principles

### Core Rules (NON-NEGOTIABLE)
1. **Library-First**: Every feature starts as a standalone library
2. **CLI Interface**: Every library exposes functionality via CLI
3. **Test-First**: TDD mandatory - tests written → fail → implement
4. **Integration Testing**: Required for new libraries, contract changes
5. **Observability**: Structured logging required
6. **Versioning**: MAJOR.MINOR.BUILD format
7. **Simplicity**: Start simple, avoid patterns without proven need

### Constitution Checks
Before any implementation:
- Maximum 3 projects (e.g., api, cli, tests)
- Use frameworks directly (no wrapper classes)
- Single data model (no DTOs unless serialization differs)
- Avoid Repository/UoW patterns without justification

## UV Package Management

### Why UV?
- **Performance**: 10-100x faster than pip/venv for environment creation
- **Reliability**: Reproducible builds with uv.lock lockfiles
- **Simplicity**: Single tool for Python version management, virtual environments, and packages
- **Modern**: Built in Rust with modern dependency resolution

### Key Files
- `pyproject.toml`: Project configuration, dependencies, and tool settings
- `uv.lock`: Locked dependency versions for reproducible builds (commit this!)
- `.venv/`: Virtual environment (ignored by git)
- `.env.example`: Environment variable template

### UV Best Practices
1. **Always use `uv run`** for executing Python commands in the project
2. **Commit `uv.lock`** for reproducible builds across team and CI/CD
3. **Use `./scripts/uv-helpers.sh`** for common UV operations and health checks
4. **Smart dependencies**: Use `./scripts/dev-commands.sh add` for auto-dev-detection
5. **Environment validation**: Run `./scripts/env-setup.sh validate` before major work

### Migration Notes
- Project migrated from pip/venv to UV for better performance and reliability
- All development scripts now UV-based with fallback instructions
- Environment setup reduced from 45-120s to <1s
- All CI/CD will be updated to use UV in Phase 3.7

## Branch Naming Convention
- Features: `00X-feature-name` (e.g., `001-user-auth`, `002-data-export`)
- Numbers auto-increment from highest existing feature
- Branch name derived from feature description

## Error Handling Patterns
- User input errors → Clear error messages to stdout
- System errors → Structured logs to stderr
- CLI tools return non-zero exit codes on failure
- All errors include context for debugging

## When Working on Features

1. **Always check current branch**: Features must be on `00X-` branches
2. **Verify prerequisites**: Run `check-task-prerequisites.sh` before tasks
3. **Follow TDD strictly**: Never implement before test fails
4. **Document ambiguities**: Use `[NEEDS CLARIFICATION]` markers
5. **Update incrementally**: Use `update-agent-context.sh` to keep this file current

## Common Pitfalls to Avoid
- Creating implementation before tests
- Skipping the RED phase of RED-GREEN-Refactor
- Adding unnecessary abstraction layers
- Creating files outside the structured workflow
- Implementing features directly without library structure
- ALWAYS use gh command for any git or github commands