# Developer Onboarding Guide

**Project**: DankerChat  
**Updated**: 2025-09-08  
**Technologies**: Python 3.11+, Flask, UV Package Manager  

Welcome to DankerChat! This guide will get you up and running with our development environment in under 5 minutes.

## 🚀 Quick Start (< 5 minutes)

### Prerequisites
- **Python 3.11+** (Check: `python --version`)
- **Git** (Check: `git --version`)
- **Terminal/Command Line** access

### Lightning-Fast Setup with UV

**Step 1: Install UV Package Manager**
```bash
# macOS/Linux (Recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env

# Verify installation
uv --version
```

**Step 2: Clone and Setup Project** 
```bash
# Clone repository
git clone https://github.com/your-org/dankerchat.git
cd dankerchat

# Complete environment setup (< 30 seconds!)
uv sync

# Verify everything works
uv run python -c "import flask, sqlalchemy; print('✅ Ready to code!')"
```

**🎉 Done!** You now have a fully functional development environment.

## 🛠️ Development Workflow

### Daily Commands
```bash
# Activate development environment
uv shell

# Install new dependencies  
uv add package-name              # Production dependency
uv add --dev package-name        # Development dependency

# Run the application
uv run python app.py

# Run tests
uv run pytest

# Code quality
uv run black src/                # Format code
uv run ruff check                # Lint code  

# Exit environment
exit  # or Ctrl+D
```

### Helper Scripts
We provide convenient scripts for common tasks:

```bash
# Complete development setup
./scripts/dev-commands.sh install

# Run tests with coverage
./scripts/dev-commands.sh test

# Format and lint all code
./scripts/dev-commands.sh format
./scripts/dev-commands.sh lint

# Run the application in development mode
./scripts/dev-commands.sh run
```

## 📁 Project Structure

```
dankerchat/
├── src/dankerchat/          # Main application code
│   ├── __init__.py         
│   ├── app.py              # Flask application entry point
│   ├── models/             # Database models (SQLAlchemy)
│   ├── routes/             # API endpoints and web routes  
│   ├── services/           # Business logic and external services
│   └── utils/              # Utility functions and helpers
├── tests/                   # Test suite
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── fixtures/           # Test data and fixtures
├── scripts/                # Development and deployment scripts
├── specs/                  # Project specifications and planning docs
├── .github/workflows/      # CI/CD configuration
├── pyproject.toml          # Project configuration and dependencies
├── uv.lock                 # Locked dependency versions
└── README.md               # Project overview
```

## 🏗️ Architecture Overview

DankerChat is built with a **library-first architecture**:

### Core Technologies
- **Backend**: Flask (Python web framework)
- **Database**: SQLAlchemy ORM with configurable backends
- **Real-time**: Flask-SocketIO for WebSocket communication
- **Authentication**: JWT tokens with PyJWT
- **Package Management**: UV (100x faster than pip!)

### Key Design Principles
- **Specification-Driven Development**: Features planned in `specs/` before implementation
- **Test-Driven Development**: Tests written before implementation
- **Library-First**: Reusable components in `src/dankerchat/`
- **Modern Python**: Type hints, dataclasses, async where beneficial

## 🧪 Testing

### Running Tests
```bash
# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov=src/dankerchat --cov-report=term-missing

# Run specific test files
uv run pytest tests/unit/test_models.py

# Run tests in watch mode (if pytest-watch installed)
uv run ptw
```

### Writing Tests
- **Unit tests**: Test individual functions/classes in isolation
- **Integration tests**: Test component interactions
- **Follow TDD**: Write tests first, then implementation
- **Use fixtures**: Leverage `tests/fixtures/` for test data

Example test structure:
```python
# tests/unit/test_example.py
import pytest
from src.dankerchat.models import User

def test_user_creation():
    """Test creating a new user"""
    user = User(username="test", email="test@example.com")
    assert user.username == "test"
    assert user.email == "test@example.com"
```

## 🔧 IDE Setup

### VS Code (Recommended)
1. **Install Python Extension**: Microsoft Python extension
2. **Configure Interpreter**: 
   - Press `Ctrl/Cmd+Shift+P`
   - Type "Python: Select Interpreter"
   - Choose `./.venv/bin/python`
3. **Settings**: Use provided `.vscode/settings.json`

### PyCharm
1. **Configure Project Interpreter**:
   - File → Settings → Project → Python Interpreter
   - Add → Existing Environment → Select `.venv/bin/python`
2. **Enable UV Integration**: PyCharm 2024.1+ has built-in UV support

### Vim/Neovim
- Use provided `.venv/bin/python` for language servers
- Configure your Python plugin to use the project's virtual environment

## 🚀 Performance Benefits

Our UV-based setup provides significant performance improvements:

| Operation | Traditional pip/venv | UV | Improvement |
|-----------|---------------------|-----|-------------|
| Environment Setup | 45-120 seconds | 0.38 seconds | **118-315x faster** |
| Installing Dependencies | 30-60 seconds | 1.2 seconds | **25-50x faster** |
| Adding New Package | 15-30 seconds | 2-5 seconds | **3-15x faster** |
| CI/CD Build Time | 5-8 minutes | 1-2 minutes | **3-5x faster** |

**Translation**: What used to take 2+ minutes now takes 10-15 seconds!

## 🛡️ Code Quality

### Standards
- **Python Style**: Black formatter (automatically applied)
- **Linting**: Ruff linter (faster than flake8/pylint)  
- **Type Hints**: Required for public APIs
- **Documentation**: Docstrings for public functions
- **Testing**: Minimum 80% test coverage target

### Pre-commit Hooks (Optional)
```bash
# Install pre-commit hooks
uv add --dev pre-commit
uv run pre-commit install

# Run manually
uv run pre-commit run --all-files
```

### Code Review Process
1. **Create Feature Branch**: `git checkout -b feature/your-feature-name`
2. **Write Tests First**: Follow TDD principles
3. **Implement Feature**: Write clean, documented code
4. **Run Quality Checks**: `uv run ruff check && uv run black src/`
5. **Run Tests**: `uv run pytest` 
6. **Create Pull Request**: Use provided PR template
7. **Code Review**: Address feedback promptly
8. **Merge**: Squash and merge when approved

## 🌐 Environment Configuration

### Environment Variables
Create a `.env` file for local development:
```bash
# .env (create this file - it's gitignored)
FLASK_ENV=development
FLASK_DEBUG=true
DATABASE_URL=sqlite:///development.db
SECRET_KEY=your-development-secret-key
```

### Production vs Development
- **Development**: SQLite database, debug enabled, hot reloading
- **Testing**: In-memory database, fixtures for data
- **Production**: PostgreSQL/MySQL, optimized settings, logging

## 🚨 Troubleshooting

### Common Issues

**Issue 1: UV not found**
```bash
# Add UV to PATH
export PATH="$HOME/.cargo/bin:$PATH"
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

**Issue 2: Import errors**
```bash
# Ensure you're using UV's Python
uv run python -c "import sys; print(sys.executable)"
# Should show: /path/to/project/.venv/bin/python
```

**Issue 3: Dependencies not found**
```bash
# Resync dependencies
uv sync --reinstall
```

**Issue 4: Tests failing**
```bash
# Check Python path in tests
uv run python -m pytest --version
# Ensure using project's pytest
```

### Getting Help
1. **Check Documentation**: Read README.md and this guide
2. **Search Issues**: Look for existing GitHub issues
3. **Ask Team**: Use development Slack channel
4. **Create Issue**: Report bugs with detailed reproduction steps

## 📚 Learning Resources

### Project-Specific
- **Specifications**: Read `specs/` directory for feature planning
- **Code Examples**: Explore `src/dankerchat/` for patterns
- **Test Examples**: Study `tests/` for testing approaches

### Technologies
- **Flask**: https://flask.palletsprojects.com/
- **SQLAlchemy**: https://docs.sqlalchemy.org/
- **UV Package Manager**: https://docs.astral.sh/uv/
- **Pytest**: https://docs.pytest.org/

### Python Best Practices
- **PEP 8**: Style guide (enforced by Black)
- **PEP 257**: Docstring conventions
- **Type Hints**: https://docs.python.org/3/library/typing.html

## 🎯 Your First Contribution

Ready to make your first contribution? Here's a suggested path:

### 1. Explore the Codebase (30 minutes)
- [ ] Read `README.md` and project specifications in `specs/`
- [ ] Browse `src/dankerchat/` to understand structure
- [ ] Run the application: `uv run python src/dankerchat/app.py`
- [ ] Run the tests: `uv run pytest`

### 2. Pick a Starter Issue (Choose one)
- [ ] Fix a typo in documentation
- [ ] Add a unit test for an existing function
- [ ] Implement a small utility function
- [ ] Improve error handling in an existing endpoint

### 3. Development Process
- [ ] Create feature branch: `git checkout -b fix/issue-description`
- [ ] Write tests first (TDD approach)
- [ ] Implement changes
- [ ] Run quality checks: `uv run ruff check && uv run black src/`
- [ ] Run tests: `uv run pytest`
- [ ] Commit changes: `git commit -m "Clear description of changes"`
- [ ] Push branch: `git push origin fix/issue-description`  
- [ ] Create Pull Request with description

### 4. Code Review
- [ ] Address reviewer feedback promptly
- [ ] Ask questions if requirements are unclear
- [ ] Update tests/docs if requested
- [ ] Celebrate when merged! 🎉

## 📞 Support and Community

### Team Communication
- **Development Chat**: #development Slack channel
- **Code Reviews**: GitHub Pull Requests
- **Architecture Discussions**: Weekly team meetings
- **Bug Reports**: GitHub Issues with "bug" label

### Office Hours
- **Onboarding Support**: First week, daily check-ins available
- **Technical Questions**: Ask anytime in development channel
- **Pair Programming**: Available upon request for complex features

---

**Welcome to the team! 🎉** 

You're now equipped to contribute to DankerChat. The UV package manager will give you a lightning-fast development experience, and our specifications-driven approach ensures quality code.

**Questions?** Ask in the #development channel or create a GitHub issue.

**Ready to code?** Pick your first issue and let's build something amazing together!