# UV Troubleshooting Guide

**Project**: DankerChat  
**Updated**: 2025-09-08  
**UV Version**: Latest stable  

This guide helps you diagnose and resolve common issues with UV package manager in the DankerChat development environment.

## 🚨 Quick Diagnosis

Before diving into specific issues, run this diagnostic script:

```bash
#!/bin/bash
# UV Health Check Script
echo "=== UV Health Check ==="

# Check UV installation
echo "1. UV Installation:"
if command -v uv >/dev/null 2>&1; then
    echo "   ✅ UV found: $(uv --version)"
else
    echo "   ❌ UV not found in PATH"
fi

# Check Python version
echo "2. Python Version:"
python_version=$(uv run python --version 2>/dev/null || echo "Not available")
echo "   Python: $python_version"

# Check project structure
echo "3. Project Structure:"
if [ -f "pyproject.toml" ]; then
    echo "   ✅ pyproject.toml exists"
else
    echo "   ❌ pyproject.toml missing"
fi

if [ -f "uv.lock" ]; then
    echo "   ✅ uv.lock exists"  
else
    echo "   ⚠️  uv.lock missing (run 'uv sync')"
fi

if [ -d ".venv" ]; then
    echo "   ✅ .venv directory exists"
else
    echo "   ⚠️  .venv missing (run 'uv sync')"
fi

# Check environment
echo "4. Environment Status:"
if [ -f ".venv/bin/python" ] || [ -f ".venv/Scripts/python.exe" ]; then
    echo "   ✅ Virtual environment ready"
else
    echo "   ❌ Virtual environment not ready"
fi

echo "=== End Health Check ==="
```

Save this as `scripts/uv-health-check.sh` and run it when experiencing issues.

## 🔧 Installation Issues

### Issue 1: "uv: command not found"

**Symptoms**:
```bash
$ uv --version
bash: uv: command not found
```

**Causes**:
- UV not installed
- UV not in PATH
- Installation corrupted

**Solutions**:

**Option A: Install UV (first time)**:
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add to PATH
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Verify
uv --version
```

**Option B: Fix PATH issues**:
```bash
# Check if UV binary exists
ls -la ~/.cargo/bin/uv

# Add to current session
export PATH="$HOME/.cargo/bin:$PATH"

# Make permanent (choose your shell)
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc    # bash
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.zshrc     # zsh

# Reload shell configuration
source ~/.bashrc  # or ~/.zshrc
```

**Option C: Reinstall UV**:
```bash
# Remove old installation
rm -rf ~/.cargo/bin/uv

# Reinstall
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
```

### Issue 2: Permission Denied During Installation

**Symptoms**:
```bash
Permission denied (publickey,password).
curl: (7) Failed to connect to astral.sh port 443
```

**Solutions**:

**For corporate networks**:
```bash
# Use pip installation instead
pip install uv

# Or use package managers
brew install uv          # macOS
sudo apt install uv      # Ubuntu (if available)
```

**For permission issues**:
```bash
# Install to user directory
curl -LsSf https://astral.sh/uv/install.sh | sh

# If that fails, manual installation
mkdir -p ~/.local/bin
# Download UV binary manually and place in ~/.local/bin/
export PATH="$HOME/.local/bin:$PATH"
```

## 🌍 Environment Issues

### Issue 3: "No such file or directory: .venv/bin/python"

**Symptoms**:
```bash
$ uv run python --version
No such file or directory: .venv/bin/python
```

**Causes**:
- Virtual environment not created
- Virtual environment corrupted
- Wrong Python interpreter path

**Solutions**:

**Option A: Create/recreate environment**:
```bash
# Remove corrupted environment
rm -rf .venv

# Recreate environment
uv sync

# Verify
uv run python --version
```

**Option B: Manual environment creation**:
```bash
# Create virtual environment manually
uv venv

# Install dependencies
uv sync

# Test
uv run python -c "print('Environment works!')"
```

**Option C: Check Python path**:
```bash
# Check what Python UV is trying to use
uv python list

# Specify Python version explicitly
uv venv --python 3.11
```

### Issue 4: Import Errors After Environment Creation

**Symptoms**:
```bash
$ uv run python -c "import flask"
ModuleNotFoundError: No module named 'flask'
```

**Causes**:
- Dependencies not installed
- Environment path issues
- Package installation failed

**Solutions**:

**Option A: Reinstall dependencies**:
```bash
# Force reinstall all packages
uv sync --reinstall

# Check what's installed
uv pip list
```

**Option B: Clear cache and retry**:
```bash
# Clear UV cache
uv cache clean

# Remove environment and recreate
rm -rf .venv
uv sync

# Verify installation
uv run python -c "import flask, sqlalchemy; print('✅ All imports work')"
```

**Option C: Check environment isolation**:
```bash
# Make sure you're using UV's Python
uv run python -c "import sys; print(f'Python: {sys.executable}')"
# Should show: /path/to/project/.venv/bin/python

# Not: /usr/bin/python or /opt/homebrew/bin/python
```

## 📦 Dependency Issues

### Issue 5: "Package Not Found" or Resolution Failures

**Symptoms**:
```bash
$ uv add some-package
No such package: some-package
```

**Causes**:
- Package name typo
- Package not available on PyPI
- Network connectivity issues
- Index configuration problems

**Solutions**:

**Option A: Verify package name**:
```bash
# Search for package
uv pip search package-name

# Check on PyPI directly
curl -s https://pypi.org/pypi/package-name/json | grep -q "name" && echo "Found" || echo "Not found"
```

**Option B: Use alternative indexes**:
```bash
# Add with specific index
uv add package-name --index-url https://pypi.org/simple/

# Use test PyPI
uv add package-name --index-url https://test.pypi.org/simple/
```

**Option C: Network troubleshooting**:
```bash
# Test PyPI connectivity
curl -I https://pypi.org/

# Check proxy settings
echo $HTTP_PROXY
echo $HTTPS_PROXY

# Use alternative index if needed
uv add package-name --trusted-host pypi.org
```

### Issue 6: Conflicting Dependencies

**Symptoms**:
```bash
$ uv add new-package
ResolutionImpossible: Could not find compatible versions
```

**Causes**:
- Version conflicts between packages
- Overly restrictive version constraints
- Incompatible Python version requirements

**Solutions**:

**Option A: Analyze conflicts**:
```bash
# Get detailed resolution information
uv add new-package --verbose

# Check current dependencies
uv pip show flask sqlalchemy

# Show dependency tree
uv pip tree
```

**Option B: Resolve version conflicts**:
```bash
# Specify compatible versions
uv add "new-package>=1.0,<2.0"

# Update existing packages
uv sync --upgrade

# Force specific versions in pyproject.toml
[tool.uv]
dependencies = [
    "flask>=2.3.0,<3.0",
    "sqlalchemy>=2.0.0,<3.0"
]
```

**Option C: Create clean environment**:
```bash
# Start fresh with minimal dependencies
rm -rf .venv uv.lock
uv init
uv add flask
uv add new-package
```

## 🔨 Build and Runtime Issues

### Issue 7: Build Failures

**Symptoms**:
```bash
$ uv sync
Building wheels for collected packages: some-package
Failed building wheel for some-package
```

**Causes**:
- Missing build dependencies
- Compiler issues
- Platform incompatibility

**Solutions**:

**Option A: Install build tools**:
```bash
# macOS
xcode-select --install

# Ubuntu/Debian
sudo apt-get install build-essential python3-dev

# Install build dependencies
uv add --dev build setuptools wheel
```

**Option B: Use precompiled wheels**:
```bash
# Prefer binary wheels
uv add package-name --only-binary=all

# Or specific package
uv add package-name --only-binary=package-name
```

**Option C: Skip problematic packages temporarily**:
```bash
# Add to pyproject.toml with build constraints
[tool.uv]
dependencies = [
    "problematic-package ; platform_system != 'Darwin'"
]
```

### Issue 8: Runtime Errors with UV Commands

**Symptoms**:
```bash
$ uv run pytest
FileNotFoundError: [Errno 2] No such file or directory: 'pytest'
```

**Causes**:
- Package not installed in environment
- Wrong environment activated
- Path issues with UV

**Solutions**:

**Option A: Install missing packages**:
```bash
# Install test dependencies
uv add --dev pytest pytest-cov

# Run again
uv run pytest
```

**Option B: Use explicit Python execution**:
```bash
# Run via Python module
uv run python -m pytest

# Or activate environment first
uv shell
pytest
exit
```

**Option C: Check package installation**:
```bash
# List installed packages
uv pip list | grep pytest

# Install if missing
uv sync --dev

# Verify installation
uv run python -c "import pytest; print(pytest.__version__)"
```

## 🌐 Network and Proxy Issues

### Issue 9: Corporate Firewall/Proxy Problems

**Symptoms**:
```bash
$ uv sync
SSL: CERTIFICATE_VERIFY_FAILED
```

**Solutions**:

**Option A: Configure proxy**:
```bash
# Set proxy environment variables
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080

# Or in pyproject.toml
[tool.uv]
index-url = "https://pypi.org/simple/"
trusted-hosts = ["pypi.org", "pypi.python.org"]
```

**Option B: Use internal PyPI mirror**:
```bash
# Configure internal index
uv add package --index-url https://internal-pypi.company.com/simple/

# Set as default in pyproject.toml
[tool.uv]
index-url = "https://internal-pypi.company.com/simple/"
```

**Option C: Certificate issues**:
```bash
# Skip SSL verification (CAUTION: less secure)
uv add package --trusted-host pypi.org

# Or install corporate certificates
# Contact IT department for certificate bundle
```

### Issue 10: Slow Package Installation

**Symptoms**: UV operations taking much longer than expected

**Causes**:
- Network latency
- Large packages
- Cache issues
- Bandwidth limitations

**Solutions**:

**Option A: Optimize cache**:
```bash
# Check cache size
du -sh ~/.cache/uv/

# Clean cache if corrupted
uv cache clean

# Use parallel downloads
uv sync --resolution=highest
```

**Option B: Use faster mirrors**:
```bash
# Use faster PyPI mirror
uv add package --index-url https://mirrors.aliyun.com/pypi/simple/

# For Chinese users
[tool.uv]
index-url = "https://mirrors.aliyun.com/pypi/simple/"
```

## 🆔 IDE Integration Issues

### Issue 11: VS Code Not Recognizing Environment

**Symptoms**: Code completion not working, import errors in IDE

**Solutions**:

**Option A: Configure VS Code Python interpreter**:
```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": "./.venv/bin/python",
    "python.pythonPath": "./.venv/bin/python",
    "python.terminal.activateEnvironment": false
}
```

**Option B: Reload VS Code**:
```bash
# From command line
code --reload-window

# Or: Cmd/Ctrl + Shift + P -> "Developer: Reload Window"
```

**Option C: Manual interpreter selection**:
1. Press `Ctrl/Cmd + Shift + P`
2. Type "Python: Select Interpreter"
3. Choose `.venv/bin/python`

### Issue 12: PyCharm Environment Issues

**Solutions**:

**Option A: Configure PyCharm interpreter**:
1. File → Settings → Project → Python Interpreter
2. Add Interpreter → Existing Environment
3. Select `.venv/bin/python`
4. Apply and restart PyCharm

**Option B: Clear PyCharm caches**:
1. File → Invalidate Caches and Restart
2. Select all caches to clear
3. Restart PyCharm

## 🔄 Migration Issues

### Issue 13: Migrating from pip/venv Projects

**Symptoms**: Existing projects not working with UV

**Solutions**:

**Option A: Gradual migration**:
```bash
# Export current requirements
pip freeze > requirements.txt

# Initialize UV project
uv init

# Import dependencies
uv add -r requirements.txt

# Test the environment
uv run python -c "import all_your_packages"
```

**Option B: Clean migration**:
```bash
# Deactivate old environment
deactivate

# Remove old environment
rm -rf venv/

# Setup UV
uv sync

# Verify migration
uv run python --version
```

### Issue 14: CI/CD Pipeline Failures After Migration

**Symptoms**: GitHub Actions or other CI failing

**Solutions**:

**Option A: Update CI configuration**:
```yaml
# .github/workflows/ci.yml
- name: Set up UV
  uses: astral-sh/setup-uv@v3

- name: Install dependencies
  run: uv sync

- name: Run tests
  run: uv run pytest
```

**Option B: Cache configuration**:
```yaml
- name: Cache UV
  uses: actions/cache@v3
  with:
    path: ~/.cache/uv
    key: uv-${{ runner.os }}-${{ hashFiles('uv.lock') }}
```

## 🚑 Emergency Procedures

### Issue 15: Complete Environment Corruption

**When all else fails**:

**Option A: Nuclear option - complete reset**:
```bash
# Save your work first!
git add . && git commit -m "Save work before UV reset"

# Remove all UV artifacts
rm -rf .venv uv.lock

# Clear UV cache
uv cache clean

# Restart from clean state
uv sync

# Verify environment
uv run python -c "print('Environment restored')"
```

**Option B: Rollback to pip/venv**:
```bash
# Follow rollback guide
# See specs/002-uv-migration/rollback-guide.md

# Quick rollback
git checkout HEAD~1  # or specific pre-UV commit
python -m venv venv
source venv/bin/activate
pip install -r backup-requirements.txt
```

## 📊 Getting Help

### Self-Diagnosis Steps

1. **Run health check script** (provided at top of guide)
2. **Check UV version**: `uv --version`
3. **Test basic commands**: `uv sync`, `uv run python --version`
4. **Review error messages** carefully
5. **Check documentation**: UV docs, project README

### Information to Gather

When asking for help, provide:

```bash
# System information
uv --version
python --version
uname -a  # or systeminfo on Windows

# Project state
ls -la pyproject.toml uv.lock .venv/
cat pyproject.toml

# Error details
# Paste complete error message
# Include command that failed
```

### Support Channels

1. **Project Documentation**:
   - README.md
   - DEVELOPER-ONBOARDING.md
   - migration-checklist.md

2. **Team Support**:
   - Development Slack channel (#development)
   - GitHub Issues with "uv-troubleshooting" label
   - Pair programming sessions

3. **UV Community**:
   - UV Documentation: https://docs.astral.sh/uv/
   - UV GitHub Issues: https://github.com/astral-sh/uv/issues
   - Python Discourse UV section

### Creating Issues

**Good issue template**:
```markdown
## Problem Description
Brief description of the issue

## Environment
- UV Version: `uv --version`
- Python Version: `python --version`
- OS: macOS/Linux/Windows
- Project: DankerChat

## Steps to Reproduce
1. Run `uv sync`
2. Execute `uv run python app.py`
3. Error occurs

## Expected vs Actual
Expected: Application starts
Actual: Import error

## Error Message
```
[paste complete error message here]
```

## Additional Context
Any other relevant information
```

---

## 💡 Pro Tips

### Prevention Best Practices

1. **Regular cache cleanup**: `uv cache clean` monthly
2. **Keep UV updated**: Check for UV updates regularly
3. **Monitor dependencies**: Use `uv pip tree` to understand relationships
4. **Backup working state**: Commit uv.lock regularly
5. **Test in clean environments**: Regularly test from scratch

### Performance Optimization

```bash
# Speed up operations
export UV_CONCURRENT_DOWNLOADS=10
export UV_CACHE_DIR=/path/to/fast/storage

# Use UV efficiently
uv sync --resolution=highest  # Fastest resolution
uv add package --no-sync     # Add without syncing
uv sync                      # Sync when ready
```

### Common Gotchas

1. **Don't mix pip and uv**: Use one or the other consistently
2. **Mind the cache**: UV cache can grow large, clean periodically
3. **Check Python version**: Ensure compatibility with project requirements
4. **Environment isolation**: Always use `uv run` for commands
5. **Lock file changes**: Commit uv.lock to ensure reproducible builds

Remember: UV is designed to be fast and reliable. Most issues stem from mixing old and new workflows or environment configuration problems. When in doubt, clean slate often resolves issues quickly!