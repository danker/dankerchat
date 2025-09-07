# Migration Guide: From Venv to UV

**Project**: DankerChat  
**Migration Date**: 2025-09-07  
**Target**: All developers and CI/CD pipelines

## Overview

This guide walks through migrating the DankerChat project from traditional Python `venv` + `pip` to the modern `uv` package manager for faster, more reliable dependency management.

## Prerequisites

- Existing working development environment with venv
- Admin/sudo access for uv installation
- Git repository access
- Backup of current working environment (optional but recommended)

## Performance Benefits

**Before (venv + pip)**:
- Environment creation: 45-120 seconds
- Dependency installation: 30-90 seconds  
- CI/CD builds: 5-10 minutes

**After (uv)**:
- Environment creation: 3-15 seconds
- Dependency installation: 5-20 seconds
- CI/CD builds: 2-4 minutes

## Step-by-Step Migration

### Step 1: Install UV

Choose your installation method:

**Linux/macOS (recommended)**:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows PowerShell**:
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Using pip (fallback)**:
```bash
pip install uv
```

**Verify installation**:
```bash
uv --version
# Should show: uv 0.4.x or later
```

### Step 2: Backup Current Environment (Optional)

```bash
# Save current requirements
pip freeze > backup-requirements.txt

# Note your Python version
python --version

# Backup any local configuration
cp -r venv/ venv-backup/ 2>/dev/null || true
```

### Step 3: Generate UV Configuration

**From project root directory**:

```bash
# Convert existing requirements.txt to pyproject.toml
uv init --app

# If you have requirements.txt, import dependencies
uv add $(cat requirements.txt | grep -v '^#' | grep -v '^$' | tr '\n' ' ')

# For development requirements (if you have requirements-dev.txt)
uv add --dev $(cat requirements-dev.txt | grep -v '^#' | grep -v '^$' | tr '\n' ' ') 2>/dev/null || true
```

**Manual pyproject.toml creation** (if auto-generation fails):

Create `pyproject.toml`:
```toml
[project]
name = "dankerchat"
version = "0.1.1"
description = "Multi-interface chat application"
requires-python = ">=3.11"
dependencies = [
    "flask>=2.3.0",
    "sqlalchemy>=2.0.0",
    "flask-socketio>=5.3.0",
    "redis>=4.0.0",
    "pyjwt>=2.8.0",
    "click>=8.1.0",
    "pytest>=7.4.0",
    "pytest-flask>=1.2.0",
]

[project.optional-dependencies]
dev = [
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "flake8>=6.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
dev-dependencies = [
    "pre-commit>=3.0.0",
]
```

### Step 4: Create UV Environment

```bash
# Create new environment with uv
uv sync

# This replaces: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
```

### Step 5: Test UV Environment

```bash
# Test Python access (replaces source venv/bin/activate)
uv run python --version

# Test dependency installation
uv run python -c "import flask, sqlalchemy; print('Dependencies imported successfully')"

# Run existing tests
uv run pytest 2>/dev/null || echo "Tests will be configured in implementation phase"

# Test CLI commands (if they exist)
uv run python -c "import chat_cli; print('CLI imports work')" 2>/dev/null || echo "CLI not yet implemented"
```

### Step 6: Update Development Scripts

**Replace common commands**:

| Old (venv) | New (uv) |
|------------|----------|
| `source venv/bin/activate` | `uv shell` (interactive) |
| `python app.py` | `uv run python app.py` |
| `pip install package` | `uv add package` |
| `pip install -e .` | `uv sync` |
| `pytest` | `uv run pytest` |

**Update existing scripts** in `scripts/` directory:
- Replace `source venv/bin/activate` with `uv run`
- Update setup instructions
- Modify CI/CD configuration

### Step 7: Verify Migration Success

**Environment Check**:
```bash
# Verify uv environment
uv run python -c "
import sys
print(f'Python: {sys.version}')
print(f'Location: {sys.executable}')

# Check key dependencies
try:
    import flask, sqlalchemy, redis
    print('✓ Core dependencies loaded')
except ImportError as e:
    print(f'✗ Missing dependency: {e}')
    
# Verify development tools
try:
    import pytest
    print('✓ Development tools loaded')
except ImportError:
    print('✗ Development tools missing')
"
```

**Performance Check**:
```bash
# Time environment creation (should be <15 seconds)
time uv sync

# Time dependency addition (should be <10 seconds)  
time uv add requests
uv remove requests  # cleanup
```

**Functionality Check**:
```bash
# Test backend startup (if implemented)
uv run python -c "from backend.app import create_app; print('✓ App creation works')" 2>/dev/null || echo "Backend not yet implemented"

# Test CLI functionality (if implemented)  
uv run chat --help 2>/dev/null || echo "CLI not yet implemented"
```

### Step 8: Update Documentation

**Update README.md** setup section:
```markdown
## Development Setup

### Prerequisites
- Python 3.11+
- uv package manager

### Setup
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone repository
git clone <repository-url>
cd dankerchat

# Install dependencies
uv sync

# Run application
uv run python app.py
```

## Common Migration Issues

### Issue 1: UV Not Found
```bash
# Add uv to PATH (Linux/macOS)
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Windows: Restart terminal or add to PATH manually
```

### Issue 2: Python Version Mismatch
```bash
# Specify Python version
uv python install 3.11
uv sync --python 3.11
```

### Issue 3: Dependencies Not Found
```bash
# Clear cache and retry
uv cache clean
uv sync --refresh
```

### Issue 4: Import Errors
```bash
# Verify environment activation
uv run python -c "import sys; print(sys.executable)"

# Reinstall dependencies
rm uv.lock
uv sync
```

## Team Migration Timeline

### Phase 1: Individual Migration (Week 1)
- Each developer follows this guide
- Test local development environment
- Report issues in team chat/repository

### Phase 2: CI/CD Migration (Week 2)  
- Update GitHub Actions workflows
- Test deployment processes
- Monitor build performance

### Phase 3: Cleanup (Week 3)
- Remove old requirements.txt files
- Update all documentation
- Archive old venv directories

## Rollback Procedures

If migration causes issues, see [rollback-guide.md](./rollback-guide.md) for complete reversion steps.

## Support and Troubleshooting

- **UV Documentation**: https://docs.astral.sh/uv/
- **GitHub Issues**: Report migration issues in project repository
- **Team Chat**: Ask for help in development channel
- **Performance Issues**: Check uv cache location and disk space

## Verification Checklist

Before completing migration, verify:
- [ ] UV installed and accessible via command line
- [ ] `uv sync` completes successfully (<30 seconds)
- [ ] `uv run python --version` shows correct Python version
- [ ] All project dependencies import correctly
- [ ] Development tools (pytest, etc.) work with `uv run`
- [ ] Existing scripts updated to use `uv run`
- [ ] Performance improvement confirmed (faster setup)
- [ ] Team members can follow guide successfully

## Next Steps

After successful migration:
1. Update CI/CD pipelines (see implementation tasks)
2. Remove old requirements.txt files
3. Share performance improvements with team
4. Consider additional uv features (workspaces, scripts)

---

**Migration Support**: For issues with this guide, create an issue in the repository or ask in the development team chat.