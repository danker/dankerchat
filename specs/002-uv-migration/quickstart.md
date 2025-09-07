# Quickstart: UV Package Management Setup

**Project**: DankerChat  
**Version**: 0.1.1  
**Date**: 2025-09-07  

This guide provides fast setup instructions for new developers using the modern UV package manager.

## Prerequisites

- Python 3.11+
- Git
- Terminal/Command Prompt

## Quick Setup (5 minutes)

### 1. Install UV

**One-line installation**:
```bash
# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows PowerShell  
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Alternative (any platform)
pip install uv
```

### 2. Clone and Setup Project

```bash
# Clone repository
git clone https://github.com/danker/dankerchat.git
cd dankerchat

# Install all dependencies (replaces venv creation + pip install)
uv sync

# Verify installation
uv run python --version
```

**That's it!** Your development environment is ready.

## Development Commands

| Task | Command |
|------|---------|
| Run Python script | `uv run python app.py` |
| Install new package | `uv add package-name` |
| Install dev package | `uv add --dev package-name` |
| Run tests | `uv run pytest` |
| Interactive Python | `uv run python` |
| Interactive shell | `uv shell` |
| Update dependencies | `uv sync --upgrade` |
| Remove package | `uv remove package-name` |

## Application Startup

### Backend Server
```bash
# Start Flask development server
uv run python backend/app.py

# Or with environment variables
FLASK_ENV=development uv run python backend/app.py
```

### Frontend (once implemented)
```bash
# Frontend uses Node.js (unchanged)
cd frontend
npm install
npm start
```

### CLI Client (once implemented)
```bash
# Interactive chat mode
uv run chat interactive --username your-name

# Send single message
uv run chat send --channel general --message "Hello world!"
```

## Common Tasks

### Running Tests
```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_auth.py

# Run with coverage
uv run pytest --cov=backend
```

### Database Setup (once implemented)
```bash
# Initialize database
uv run flask db init
uv run flask db migrate -m "Initial migration"
uv run flask db upgrade

# Create admin user
uv run flask create-admin admin admin123
```

### Development Services
```bash
# Start Redis (required for chat)
redis-server

# Start backend in development mode
FLASK_ENV=development uv run python backend/app.py

# In another terminal, start frontend
cd frontend && npm start
```

## Project Structure Overview

```
dankerchat/
├── pyproject.toml          # UV configuration and dependencies
├── uv.lock                 # Locked dependency versions
├── README.md               # Project documentation
├── backend/                # Python Flask backend
│   ├── src/               # Source code
│   │   ├── models/        # Database models
│   │   ├── services/      # Business logic
│   │   ├── api/          # REST endpoints
│   │   └── websocket/    # Real-time messaging
│   └── tests/            # Backend tests
├── frontend/              # React frontend
│   ├── src/              # Frontend source
│   └── tests/            # Frontend tests
└── specs/                 # Feature specifications
```

## Configuration

### Environment Variables
Create `.env` file in project root:
```bash
# Backend configuration
FLASK_ENV=development
DATABASE_URL=sqlite:///chat.db
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=your-secret-key-here

# Frontend configuration (in frontend/.env)
REACT_APP_API_URL=http://localhost:5000/api/v1
REACT_APP_SOCKET_URL=http://localhost:5000
```

### Python Configuration
UV automatically manages Python versions. To specify a version:
```bash
# Use specific Python version
uv python install 3.11
uv sync --python 3.11
```

## IDE Setup

### VS Code
Install these extensions for optimal development:
- Python (Microsoft)
- Pylance (Microsoft)  
- Python Docstring Generator
- GitLens

UV environments are automatically detected by VS Code.

### PyCharm
1. Open project in PyCharm
2. Go to Settings → Project → Python Interpreter
3. Select "Existing Environment"
4. Point to `.venv/bin/python` in project root

## Troubleshooting

### UV Not Found
```bash
# Add to PATH (Linux/macOS)
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Verify installation
uv --version
```

### Slow Installation
```bash
# Clear cache if needed
uv cache clean

# Use different index if default is slow
uv sync --index-url https://pypi.org/simple/
```

### Import Errors
```bash
# Verify environment
uv run python -c "import sys; print(sys.executable)"

# Should show path ending in .venv/bin/python

# Reinstall if needed
rm uv.lock
uv sync
```

### Permission Issues
```bash
# Fix common permission problems
chmod +x scripts/*.sh

# For Windows, run terminal as Administrator if needed
```

## Performance Tips

### Speed Up Installs
- UV caches packages globally - subsequent installs are very fast
- Use `uv sync --frozen` to skip dependency resolution
- Keep `uv.lock` committed to ensure reproducible builds

### Development Workflow
- Use `uv shell` for interactive work (like activating venv)
- Use `uv run` for running commands (no activation needed)
- Add frequently used commands to `[tool.uv.scripts]` in pyproject.toml

## Next Steps

After setup completion:

1. **Explore the Code**:
   ```bash
   # Check project structure
   tree . -I 'node_modules|.venv|__pycache__'
   
   # Read specifications
   ls specs/*/spec.md
   ```

2. **Run Development Server**:
   ```bash
   # Start backend
   uv run python backend/app.py
   
   # In another terminal, start frontend  
   cd frontend && npm start
   ```

3. **Make Your First Change**:
   - Follow specification-driven development process
   - See `CLAUDE.md` for development workflow
   - Check `specs/` directory for current features

4. **Join Development**:
   - Read project documentation in `README.md`
   - Check open issues on GitHub
   - Follow TDD practices described in project constitution

## Migration from Venv

If you previously used venv/pip, see:
- [Migration Guide](./migration-guide.md) - Complete migration instructions  
- [Rollback Guide](./rollback-guide.md) - How to revert if needed

## Support

- **UV Documentation**: https://docs.astral.sh/uv/
- **Project Issues**: Create issue on GitHub repository
- **Development Chat**: Ask in team development channel
- **Troubleshooting**: Check common solutions above first

---

**Total setup time**: ~5 minutes for new environment  
**Subsequent syncs**: ~10-30 seconds  
**Performance improvement**: 50%+ faster than traditional venv/pip