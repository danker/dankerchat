# Contributing to DankerChat

**Welcome to the DankerChat project!** 🎉

We're excited you want to contribute. This guide will help you get started quickly and follow our development workflow using UV package manager for lightning-fast development.

## 🚀 Quick Start for Contributors

### Prerequisites
- **Python 3.11+** (`python --version`)
- **Git** (`git --version`)  
- **UV Package Manager** (we'll help you install this!)

### Lightning-Fast Setup (< 2 minutes)
```bash
# 1. Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env

# 2. Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/dankerchat.git
cd dankerchat

# 3. Complete development setup (< 30 seconds!)
uv sync

# 4. Verify everything works
uv run python -c "import flask, sqlalchemy; print('✅ Ready to contribute!')"
```

**🎉 You're ready to contribute!** This setup is 100x+ faster than traditional pip/venv.

## 🛠️ Development Workflow

### Branch Strategy
```bash
# Create feature branch from main
git checkout main
git pull origin main
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/issue-description

# Or for documentation
git checkout -b docs/documentation-improvement
```

### Development Commands
```bash
# Activate development environment
uv shell

# Install new dependencies
uv add package-name              # Production dependency
uv add --dev package-name        # Development dependency

# Run the application
uv run python src/dankerchat/app.py

# Run tests
uv run pytest                    # All tests
uv run pytest tests/unit/        # Unit tests only
uv run pytest --cov             # With coverage

# Code quality (run before committing)
uv run black src/ tests/         # Format code
uv run ruff check src/ tests/    # Lint code
uv run ruff check --fix          # Auto-fix linting issues

# Type checking (if configured)
uv run mypy src/
```

### Convenient Helper Scripts
```bash
# Complete development setup
./scripts/dev-commands.sh install

# Run all code quality checks
./scripts/dev-commands.sh lint
./scripts/dev-commands.sh format

# Run tests with coverage
./scripts/dev-commands.sh test

# Run the application in development mode
./scripts/dev-commands.sh run
```

## 📝 Contribution Process

### 1. Plan Your Contribution

**For New Features**:
- [ ] Check existing issues and discussions
- [ ] Create/comment on GitHub issue to discuss approach
- [ ] Read relevant specifications in `specs/` directory
- [ ] Consider creating a specification if it's a major feature

**For Bug Fixes**:
- [ ] Reproduce the bug locally
- [ ] Create GitHub issue if none exists
- [ ] Identify root cause before coding

**For Documentation**:
- [ ] Check for accuracy and clarity
- [ ] Ensure UV workflow is properly documented
- [ ] Test any code examples provided

### 2. Follow Test-Driven Development (TDD)

We use TDD principles - write tests first, then implementation:

```bash
# 1. Write failing test (RED phase)
# Create test in tests/unit/ or tests/integration/
cat > tests/unit/test_new_feature.py << 'EOF'
def test_new_feature():
    """Test the new feature works correctly."""
    # This test should fail initially
    result = new_feature()
    assert result == expected_output
EOF

# 2. Run test to confirm it fails
uv run pytest tests/unit/test_new_feature.py -v
# Should show: FAILED - function doesn't exist yet

# 3. Implement feature (GREEN phase) 
# Write minimal code to make test pass

# 4. Run test to confirm it passes
uv run pytest tests/unit/test_new_feature.py -v
# Should show: PASSED

# 5. Refactor if needed (REFACTOR phase)
# Improve code quality while keeping tests green
```

### 3. Code Quality Standards

**Python Style**:
- **Formatting**: Black (automatic via `uv run black`)
- **Linting**: Ruff (faster than flake8/pylint)
- **Type Hints**: Required for public APIs and recommended elsewhere
- **Docstrings**: Required for public functions, classes, and modules

**Example of well-formatted code**:
```python
"""Module for user authentication and management."""

from typing import Optional
from datetime import datetime


class User:
    """Represents a chat application user.
    
    Args:
        username: Unique identifier for the user
        email: User's email address
        created_at: When the user account was created
    """
    
    def __init__(
        self, 
        username: str, 
        email: str,
        created_at: Optional[datetime] = None
    ) -> None:
        self.username = username
        self.email = email
        self.created_at = created_at or datetime.now()
    
    def is_active(self) -> bool:
        """Check if user account is active.
        
        Returns:
            True if user is active, False otherwise
        """
        # Implementation here
        return True
```

**Testing Standards**:
- **Unit Tests**: Test individual functions/classes in isolation
- **Integration Tests**: Test component interactions
- **Coverage**: Aim for 80%+ coverage on new code
- **Test Naming**: Descriptive names explaining what is being tested

### 4. Commit Messages

Follow conventional commit format:

```bash
# Feature commits
git commit -m "feat: add user authentication system"
git commit -m "feat(api): implement user login endpoint"

# Bug fixes
git commit -m "fix: resolve database connection timeout"
git commit -m "fix(auth): handle expired JWT tokens properly"

# Documentation
git commit -m "docs: update API documentation for user endpoints"
git commit -m "docs(setup): improve UV installation instructions"

# Tests
git commit -m "test: add unit tests for user model"
git commit -m "test(api): add integration tests for auth endpoints"

# Refactoring
git commit -m "refactor: simplify user validation logic"
git commit -m "refactor(database): optimize query performance"
```

### 5. Pull Request Process

**Before Creating PR**:
```bash
# 1. Ensure all tests pass
uv run pytest

# 2. Run code quality checks
uv run black src/ tests/
uv run ruff check src/ tests/

# 3. Check test coverage (if configured)
uv run pytest --cov=src/dankerchat --cov-report=term-missing

# 4. Update documentation if needed
# Edit relevant .md files

# 5. Commit changes
git add .
git commit -m "feat: your descriptive commit message"

# 6. Push feature branch
git push origin feature/your-feature-name
```

**Creating the PR**:

1. **Navigate to GitHub**: Go to your forked repository
2. **Create Pull Request**: Click "New Pull Request"
3. **Fill out PR template**:

```markdown
## Summary
Brief description of changes and motivation.

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to change)
- [ ] Documentation update

## Testing
- [ ] Tests pass locally with `uv run pytest`
- [ ] Code follows style guidelines (`uv run black` and `uv run ruff check`)
- [ ] Self-review completed
- [ ] New tests added for changes (if applicable)

## Changes Made
- List key changes
- Reference any issues fixed (closes #123)

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review of code completed
- [ ] Tests added/updated and passing
- [ ] Documentation updated if needed
- [ ] No breaking changes (or clearly documented)
```

## 🏗️ Project Structure

Understanding the codebase structure helps with contributions:

```
dankerchat/
├── src/dankerchat/              # Main application code
│   ├── __init__.py             # Package initialization
│   ├── app.py                  # Flask application entry point
│   ├── models/                 # Database models (SQLAlchemy)
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── message.py
│   ├── routes/                 # API endpoints and web routes
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   └── chat.py
│   ├── services/               # Business logic and external services
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   └── message_service.py
│   └── utils/                  # Utility functions and helpers
│       ├── __init__.py
│       └── validators.py
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── unit/                   # Unit tests
│   │   ├── test_models.py
│   │   └── test_services.py
│   ├── integration/            # Integration tests
│   │   └── test_api.py
│   └── fixtures/               # Test data and fixtures
│       └── sample_data.py
├── scripts/                    # Development and deployment scripts
├── specs/                      # Project specifications
├── .github/workflows/          # CI/CD configuration
├── pyproject.toml              # Project configuration and dependencies
├── uv.lock                     # Locked dependency versions
└── README.md                   # Project overview
```

**Where to Make Changes**:
- **Models**: Add/modify database models in `src/dankerchat/models/`
- **API Endpoints**: Add routes in `src/dankerchat/routes/`
- **Business Logic**: Add services in `src/dankerchat/services/`
- **Utilities**: Add helpers in `src/dankerchat/utils/`
- **Tests**: Match structure under `tests/unit/` or `tests/integration/`

## 🧪 Testing Guidelines

### Writing Good Tests

**Unit Test Example**:
```python
# tests/unit/test_user_model.py
import pytest
from datetime import datetime
from src.dankerchat.models.user import User


class TestUser:
    """Test suite for User model."""
    
    def test_user_creation(self):
        """Test creating a new user with valid data."""
        user = User(username="testuser", email="test@example.com")
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert isinstance(user.created_at, datetime)
    
    def test_user_validation(self):
        """Test user validation with invalid data."""
        with pytest.raises(ValueError):
            User(username="", email="invalid-email")
    
    def test_user_is_active(self):
        """Test user active status checking."""
        user = User(username="testuser", email="test@example.com")
        assert user.is_active() is True
```

**Integration Test Example**:
```python
# tests/integration/test_auth_api.py
import pytest
from src.dankerchat.app import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app(testing=True)
    with app.test_client() as client:
        yield client


class TestAuthAPI:
    """Test suite for authentication API."""
    
    def test_user_registration(self, client):
        """Test user registration endpoint."""
        response = client.post('/api/auth/register', json={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'securepassword'
        })
        
        assert response.status_code == 201
        assert 'token' in response.json
    
    def test_user_login(self, client):
        """Test user login endpoint."""
        # First register user
        client.post('/api/auth/register', json={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'securepassword'
        })
        
        # Then login
        response = client.post('/api/auth/login', json={
            'username': 'testuser',
            'password': 'securepassword'
        })
        
        assert response.status_code == 200
        assert 'token' in response.json
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test files
uv run pytest tests/unit/test_user_model.py

# Run with coverage
uv run pytest --cov=src/dankerchat --cov-report=term-missing

# Run tests in watch mode (if pytest-watch installed)
uv run ptw

# Run only failed tests
uv run pytest --lf

# Run tests with verbose output
uv run pytest -v
```

## 🔧 Environment Management

### Adding Dependencies

```bash
# Production dependencies (will be installed for all users)
uv add flask
uv add sqlalchemy
uv add requests

# Development dependencies (only for developers)
uv add --dev pytest
uv add --dev black
uv add --dev ruff

# Specific version constraints
uv add "flask>=2.3.0,<3.0"
uv add "sqlalchemy>=2.0.0"

# Remove dependencies
uv remove package-name
```

### Managing Python Versions

```bash
# Check available Python versions
uv python list

# Use specific Python version
uv python install 3.11
uv venv --python 3.11

# Check current Python version
uv run python --version
```

### Environment Variables

Create `.env` file for local development (this file is gitignored):

```bash
# .env
FLASK_ENV=development
FLASK_DEBUG=true
DATABASE_URL=sqlite:///development.db
SECRET_KEY=your-development-secret-key-here
```

## 🚀 Performance Considerations

Thanks to UV, our development workflow is incredibly fast:

### What Makes Us Fast
- **Environment Setup**: 0.38s (vs 45-120s with pip)
- **Dependency Installation**: 1.2s (vs 30-90s with pip)  
- **Package Addition**: 2-5s (vs 15-45s with pip)
- **CI/CD Builds**: 1.5-2.5min (vs 5-8min with pip)

### Best Practices for Speed
```bash
# Cache-friendly operations
uv sync                    # Sync with lockfile (fastest)
uv add package --no-sync   # Add without immediate sync
uv sync                    # Sync when ready

# Parallel operations
uv sync --resolution=highest

# Efficient environment management
uv shell                   # Enter environment
uv run command            # Run single command
```

## 📚 Learning Resources

### Project-Specific Resources
- **README.md**: Project overview and basic setup
- **DEVELOPER-ONBOARDING.md**: Comprehensive onboarding guide
- **migration-checklist.md**: UV migration information
- **uv-troubleshooting.md**: Common issues and solutions
- **specs/**: Feature specifications and planning documents

### Technology Resources
- **Flask**: https://flask.palletsprojects.com/
- **SQLAlchemy**: https://docs.sqlalchemy.org/
- **UV**: https://docs.astral.sh/uv/
- **Pytest**: https://docs.pytest.org/
- **Black**: https://black.readthedocs.io/
- **Ruff**: https://docs.astral.sh/ruff/

### Python Best Practices
- **PEP 8**: Python style guide (enforced by Black)
- **PEP 257**: Docstring conventions
- **Type Hints**: https://docs.python.org/3/library/typing.html

## 🆘 Getting Help

### Self-Help Resources
1. **Read Documentation**: Check README.md and this guide
2. **Search Issues**: Look for existing GitHub issues
3. **Check Troubleshooting**: See uv-troubleshooting.md
4. **Run Health Check**: Use scripts/uv-health-check.sh

### Community Support
- **GitHub Discussions**: For general questions and ideas
- **GitHub Issues**: For bugs and feature requests  
- **Development Chat**: #development Slack channel (if team member)
- **Code Review**: Pull request discussions

### Information to Include When Asking for Help

```bash
# System information
uv --version
python --version
uname -a  # or systeminfo on Windows

# Project state
ls -la pyproject.toml uv.lock .venv/

# Error details (if applicable)
# Include complete error message and command that failed
```

## 🏷️ Issue and PR Labels

When creating issues or PRs, use these labels:

**Type Labels**:
- `bug`: Something isn't working
- `feature`: New functionality
- `enhancement`: Improvement to existing functionality
- `documentation`: Documentation updates
- `test`: Testing improvements
- `refactor`: Code restructuring without functionality change

**Priority Labels**:
- `critical`: Blocks development or production
- `high`: Important but not blocking
- `medium`: Normal priority
- `low`: Nice to have

**Status Labels**:
- `help wanted`: Good for contributors
- `good first issue`: Perfect for newcomers
- `question`: Needs clarification
- `wontfix`: Will not be addressed

## 🎯 Types of Contributions We Welcome

### Code Contributions
- **Bug fixes**: Fix issues in existing functionality
- **New features**: Add new functionality based on specifications
- **Performance improvements**: Optimize existing code
- **Test additions**: Improve test coverage
- **Refactoring**: Improve code structure and maintainability

### Documentation Contributions  
- **API documentation**: Document endpoints and usage
- **Code examples**: Add helpful usage examples
- **Setup guides**: Improve installation and setup instructions
- **Troubleshooting**: Add solutions to common problems
- **Architecture docs**: Explain system design decisions

### Other Contributions
- **Issue reporting**: Report bugs with clear reproduction steps
- **Feature requests**: Suggest new functionality with use cases
- **Code review**: Review other contributors' pull requests
- **Testing**: Manual testing of new features
- **Design feedback**: UI/UX suggestions and improvements

## 🎉 Recognition

We value all contributions! Contributors will be:
- **Credited**: Listed in project contributors
- **Acknowledged**: Mentioned in release notes for significant contributions  
- **Welcomed**: Invited to team discussions for regular contributors
- **Supported**: Provided mentorship and growth opportunities

## ⚡ Performance Impact of Your Contributions

Remember that UV gives us incredible development speed:
- **Your setup time**: < 30 seconds (vs 2+ minutes traditionally)
- **Your testing cycle**: Seconds instead of minutes
- **Your contribution velocity**: Much higher due to fast tooling

This means you can iterate faster, test more thoroughly, and contribute more effectively!

---

**Thank you for contributing to DankerChat!** 🚀

Your contributions help build a better chat application with lightning-fast development workflows. Whether you're fixing a typo or implementing a major feature, every contribution is valued and appreciated.

**Questions?** 
- Check the troubleshooting guide: `uv-troubleshooting.md`
- Ask in GitHub Discussions
- Create an issue with the "question" label

**Ready to contribute?** 
- Pick an issue labeled "good first issue"
- Fork the repository and start coding
- Follow this guide and you'll be successful!

Happy coding! 🎯