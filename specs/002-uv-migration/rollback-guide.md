# Rollback Guide: UV to Venv Migration

**Project**: DankerChat  
**Document Date**: 2025-09-07  
**Purpose**: Complete reversion from uv back to venv/pip setup

## When to Use This Guide

Use this rollback procedure if:
- UV migration causes development environment issues
- Performance degradation instead of improvement
- Team members cannot successfully use uv
- Critical dependencies are incompatible with uv
- CI/CD pipelines fail after migration

## Prerequisites for Rollback

- Access to backup files created during migration
- Git repository with pre-migration state
- Admin access to remove uv installation (optional)

## Emergency Quick Rollback

For immediate restoration of working environment:

```bash
# 1. Return to pre-migration git state
git checkout HEAD~1  # or specific commit before uv migration

# 2. Recreate traditional venv
python -m venv venv
source venv/bin/activate  # Linux/macOS
# OR: venv\Scripts\activate  # Windows

# 3. Install dependencies from backup
pip install -r backup-requirements.txt
# OR: pip install -r requirements.txt (if it still exists)

# 4. Verify environment
python --version
pip list
```

## Complete Step-by-Step Rollback

### Step 1: Assess Current State

```bash
# Check what uv created
ls -la | grep -E "(pyproject.toml|uv.lock|\.venv)"

# Check if backup files exist
ls -la backup-requirements.txt 2>/dev/null && echo "Backup found" || echo "No backup found"

# Check git history for pre-migration state
git log --oneline -5
```

### Step 2: Save Current Work

```bash
# Commit any current work
git add .
git commit -m "WIP: Save work before uv rollback" || true

# Create rollback branch for safety
git checkout -b rollback-to-venv-$(date +%Y%m%d)
```

### Step 3: Remove UV Configuration

```bash
# Remove uv-specific files
rm -f pyproject.toml
rm -f uv.lock
rm -rf .venv/  # uv's default venv location

# Remove uv cache (optional, frees disk space)
uv cache clean 2>/dev/null || true
```

### Step 4: Restore Pre-Migration Files

**Option A: From Backup Files**
```bash
# Restore requirements.txt from backup
cp backup-requirements.txt requirements.txt

# If you had separate dev requirements
cp backup-requirements-dev.txt requirements-dev.txt 2>/dev/null || true
```

**Option B: From Git History**
```bash
# Find commit before uv migration
git log --oneline | grep -i "before.*uv\|pre.*migration\|venv"

# Restore specific files (replace COMMIT_HASH)
git checkout COMMIT_HASH -- requirements.txt
git checkout COMMIT_HASH -- requirements-dev.txt 2>/dev/null || true
git checkout COMMIT_HASH -- setup.py 2>/dev/null || true
```

**Option C: Manual Recreation**
```bash
# Create requirements.txt from current environment
uv pip freeze > requirements.txt 2>/dev/null || pip freeze > requirements.txt
```

### Step 5: Create Traditional Venv

```bash
# Remove any existing venv
rm -rf venv/

# Create new venv
python -m venv venv

# Activate venv
source venv/bin/activate  # Linux/macOS
# OR: venv\Scripts\activate  # Windows

# Upgrade pip
pip install --upgrade pip
```

### Step 6: Install Dependencies

```bash
# Install from requirements.txt
pip install -r requirements.txt

# Install development dependencies if they exist
pip install -r requirements-dev.txt 2>/dev/null || true

# Install project in development mode if setup.py exists
pip install -e . 2>/dev/null || true
```

### Step 7: Restore Scripts and Configuration

**Update scripts that were modified for uv**:

```bash
# Restore original script patterns
find scripts/ -name "*.sh" -exec sed -i 's/uv run //g' {} \; 2>/dev/null || true

# Restore activation patterns
find scripts/ -name "*.sh" -exec sed -i 's/uv shell/source venv\/bin\/activate/g' {} \; 2>/dev/null || true
```

**Restore CI/CD configuration**:
```bash
# Restore GitHub Actions workflow (if modified)
git checkout HEAD~1 -- .github/workflows/ 2>/dev/null || true
```

### Step 8: Verify Rollback Success

**Environment Check**:
```bash
# Verify venv activation
which python
# Should show: /path/to/project/venv/bin/python

python --version
pip --version

# Check virtual environment
echo $VIRTUAL_ENV
# Should show: /path/to/project/venv
```

**Dependencies Check**:
```bash
# Verify core dependencies
python -c "
import sys
print(f'Python: {sys.version}')
print(f'Location: {sys.executable}')
print('Testing imports...')

try:
    import flask, sqlalchemy
    print('✓ Core dependencies work')
except ImportError as e:
    print(f'✗ Import error: {e}')
    
try:
    import pytest
    print('✓ Development tools work')  
except ImportError:
    print('ⓘ Development tools not installed')
"
```

**Functionality Check**:
```bash
# Test application startup
python -c "print('Python environment working')"

# Run tests if they exist
python -m pytest 2>/dev/null || echo "Tests not configured yet"

# Test any existing scripts
./scripts/setup.sh 2>/dev/null || echo "Setup script not found"
```

### Step 9: Update Documentation

**Restore README.md setup instructions**:
```markdown
## Development Setup

### Prerequisites
- Python 3.11+

### Setup
```bash
# Clone repository
git clone <repository-url>
cd dankerchat

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# OR: venv\Scripts\activate  # Windows

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Run application
python app.py
```

### Step 10: Team Communication

**Notify team of rollback**:
```markdown
## UV Migration Rollback

The uv migration has been rolled back due to [reason].

### For Developers:
1. Pull latest changes: `git pull origin main`
2. Remove uv environment: `rm -rf .venv pyproject.toml uv.lock`
3. Create traditional venv: `python -m venv venv`
4. Activate venv: `source venv/bin/activate` (Linux/macOS)
5. Install dependencies: `pip install -r requirements.txt`

### Issues Encountered:
- [List specific issues that caused rollback]

### Next Steps:
- [Plan for addressing issues or alternative approaches]
```

## Optional: Remove UV Installation

If you want to completely remove uv:

**Linux/macOS**:
```bash
# Remove uv binary
rm -f ~/.cargo/bin/uv

# Remove from PATH (edit ~/.bashrc, ~/.zshrc, etc.)
# Remove line: export PATH="$HOME/.cargo/bin:$PATH"

# Clean up cache
rm -rf ~/.cache/uv/
```

**Windows**:
```powershell
# Remove uv from PATH via System Properties
# Or use Windows settings to manage PATH

# Clean up cache
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\uv\cache"
```

## Post-Rollback Checklist

Verify rollback completion:
- [ ] UV configuration files removed (pyproject.toml, uv.lock)
- [ ] Traditional venv created and activated
- [ ] requirements.txt restored and dependencies installed
- [ ] Python environment shows correct venv path
- [ ] All project dependencies import successfully
- [ ] Scripts updated to use traditional activation
- [ ] CI/CD workflows restored to pre-migration state
- [ ] Documentation updated with venv instructions
- [ ] Team notified of rollback and next steps
- [ ] Git commits show rollback changes

## Troubleshooting Rollback Issues

### Issue 1: Missing Requirements
```bash
# Generate from any working environment
pip freeze > requirements.txt

# Or manually recreate based on project imports
grep -r "^import\|^from" . --include="*.py" | sort -u
```

### Issue 2: Python Version Problems
```bash
# Use system Python
deactivate
which python3
python3 -m venv venv
source venv/bin/activate
```

### Issue 3: Permission Errors
```bash
# Fix venv permissions
chmod -R u+w venv/
```

### Issue 4: Import Errors After Rollback
```bash
# Clear Python cache
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Reinstall dependencies
pip uninstall -r requirements.txt -y
pip install -r requirements.txt
```

## Prevention for Future Migrations

To avoid rollback situations in future:
1. **Test migration on branch first**: Use feature branch for migration testing
2. **Create comprehensive backups**: Save entire working directory state
3. **Document issues immediately**: Record problems for team learning
4. **Pilot with subset**: Test with 1-2 developers before full team
5. **Have rollback plan**: Always plan rollback before starting migration

## Support

If rollback fails or additional issues arise:
- **Git Help**: `git reflog` to see all recent changes
- **Environment Debug**: Share output of `python --version && which python && pip list`
- **Team Support**: Ask in development channel with specific error messages
- **Repository Issues**: Create issue with "rollback" label for tracking

---

**Note**: This rollback guide assumes the migration was recent. For older migrations, some steps may need adjustment based on subsequent changes to the repository.