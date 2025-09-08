# Team Migration Checklist: UV Package Manager

**Project**: DankerChat  
**Migration Date**: 2025-09-08  
**Status**: Ready for Team Adoption  

## 📋 Pre-Migration Checklist

### For Team Leaders
- [ ] **Review Migration Benefits**
  - 100x+ faster environment setup (0.38s vs 45-120s)
  - Reliable dependency locking with uv.lock
  - Better CI/CD performance (3-5x faster builds)
  - Modern Python packaging standards (PEP 518)

- [ ] **Verify Prerequisites**
  - [ ] Team has Python 3.11+ available
  - [ ] UV installation access (can install via curl/pip/package manager)
  - [ ] Git repository access for migration branch
  - [ ] CI/CD system supports custom actions (GitHub Actions ready)

- [ ] **Communication Plan**
  - [ ] Schedule team meeting to explain UV benefits
  - [ ] Share MIGRATION-NOTICE.md with timeline
  - [ ] Set migration deadline (recommend 1-2 week transition)
  - [ ] Identify migration champions/early adopters

### For Individual Developers
- [ ] **Environment Assessment**
  - [ ] Document current Python version: `python --version`
  - [ ] Note current virtual environment setup
  - [ ] List any custom development scripts used
  - [ ] Check for IDE-specific venv configurations

- [ ] **Backup Current Setup**
  - [ ] Export current requirements: `pip freeze > my-backup.txt`
  - [ ] Note environment variables in use
  - [ ] Document any custom activation procedures
  - [ ] Save IDE workspace configuration

## 🚀 Migration Steps

### Step 1: Install UV
Choose your installation method:

**macOS/Linux (Recommended)**:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env
```

**Via pip** (if you have Python already):
```bash
pip install uv
```

**Verify installation**:
```bash
uv --version
# Should show: uv x.x.x
```

### Step 2: Clone and Setup Project
```bash
# Clone repository with UV branch
git clone <repository-url>
cd dankerchat
git checkout 002-uv-migration  # or main if merged

# Fast UV setup (< 30 seconds total)
uv sync

# Verify setup
uv run python --version
uv run python -c "import flask, sqlalchemy; print('✅ Dependencies work')"
```

### Step 3: Update Your Workflow

**Old Workflow** → **New UV Workflow**

| Old Command | New UV Command | Speed |
|-------------|----------------|-------|
| `python -m venv venv` | `uv venv` (auto-created) | 100x faster |
| `source venv/bin/activate` | `uv shell` | Instant |
| `pip install -r requirements.txt` | `uv sync` | 50-100x faster |
| `pip install package` | `uv add package` | 10x faster |
| `pip install -e .` | `uv sync --dev` | Built-in |
| `python script.py` | `uv run python script.py` | Same |
| `pytest` | `uv run pytest` | Same |

**Development Commands**:
```bash
# Environment management
uv sync                 # Install all dependencies
uv sync --dev          # Include development dependencies  
uv add requests        # Add new dependency
uv remove requests     # Remove dependency
uv shell               # Activate environment

# Running commands
uv run python app.py   # Run Python scripts
uv run pytest         # Run tests
uv run black src/      # Run code formatting
uv run ruff check      # Run linting

# Project commands (see scripts/dev-commands.sh)
./scripts/dev-commands.sh install  # Full setup
./scripts/dev-commands.sh test     # Run tests
./scripts/dev-commands.sh lint     # Run linting
./scripts/dev-commands.sh format   # Format code
```

### Step 4: IDE Configuration Updates

**VS Code**:
```json
// .vscode/settings.json
{
    "python.interpreter": "./.venv/bin/python",
    "python.terminal.activateEnvironment": false
}
```

**PyCharm**:
1. File → Settings → Project → Python Interpreter
2. Add Interpreter → Existing Environment
3. Select: `project/.venv/bin/python`

**Vim/Neovim**: Update any venv activation in your config to use `.venv/`

### Step 5: Update Personal Scripts
If you have custom scripts, update them:

```bash
# Replace in your scripts:
sed -i 's/source venv\/bin\/activate/uv shell/g' your-script.sh
sed -i 's/pip install/uv add/g' your-script.sh  
sed -i 's/python /uv run python /g' your-script.sh
```

## ✅ Verification Checklist

### Environment Setup Verification
- [ ] **UV Command Works**: `uv --version` shows version
- [ ] **Project Syncs**: `uv sync` completes in < 15 seconds
- [ ] **Dependencies Import**: `uv run python -c "import flask, sqlalchemy"`
- [ ] **Tests Run**: `uv run pytest` (if tests exist)
- [ ] **Environment Active**: `uv shell` activates environment

### Development Workflow Verification
- [ ] **Code Runs**: Your application starts with `uv run python app.py`
- [ ] **Linting Works**: `uv run ruff check` passes
- [ ] **Formatting Works**: `uv run black src/` works  
- [ ] **IDE Integration**: Code completion and debugging work
- [ ] **Git Status Clean**: No unexpected file changes

### Performance Verification
Time these operations and compare to old workflow:

```bash
# Time environment setup
time (rm -rf .venv && uv sync)
# Target: < 15 seconds (vs 45-120s with pip)

# Time dependency addition
time uv add requests
# Target: < 5 seconds (vs 30-60s with pip)
```

## 🔧 Troubleshooting Common Issues

### Issue 1: UV Not Found
```bash
# Add UV to PATH
export PATH="$HOME/.cargo/bin:$PATH"
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Issue 2: Permission Denied
```bash
# Fix UV installation permissions
chmod +x ~/.cargo/bin/uv
```

### Issue 3: Old Venv Conflicts
```bash
# Clean up old virtual environments
rm -rf venv/
rm -rf env/
# UV will create .venv/ automatically
```

### Issue 4: Import Errors
```bash
# Ensure you're using UV's Python
uv run python -c "import sys; print(sys.executable)"
# Should show: /path/to/project/.venv/bin/python
```

### Issue 5: IDE Not Recognizing Environment
- Point IDE to `.venv/bin/python` (not old `venv/bin/python`)
- Restart IDE after changing Python interpreter
- Clear IDE caches if needed

## 📚 Learning Resources

### Quick Reference
- **UV Docs**: https://docs.astral.sh/uv/
- **Command Reference**: `uv help` or see CLAUDE.md
- **Project Examples**: See scripts/dev-commands.sh for common workflows

### Team Resources
- **Migration Notice**: See MIGRATION-NOTICE.md for executive summary
- **Rollback Guide**: See specs/002-uv-migration/rollback-guide.md if issues
- **Performance Benchmarks**: See rollback-test-report.md for metrics

## 🆘 Getting Help

### Self-Service
1. **Check UV Status**: `uv --version && uv sync --dry-run`
2. **Review Logs**: UV provides detailed error messages
3. **Compare with Working Setup**: Use `uv export` to compare environments

### Team Support
- **Slack Channel**: #development (mention UV migration)
- **Migration Champions**: [List team champions here]
- **Office Hours**: [Schedule team help sessions]

### Emergency Rollback
If UV migration blocks your work:

```bash
# Quick rollback (5 minutes)
git stash  # Save current work
git checkout HEAD~1  # Return to pre-migration state
python -m venv venv
source venv/bin/activate
pip install -r backup-requirements.txt
```

See rollback-guide.md for complete procedures.

## 📊 Success Metrics

Track your migration success:

- [ ] **Setup Time**: Environment setup < 30 seconds
- [ ] **Daily Workflow**: All development tasks work with `uv run`
- [ ] **Team Velocity**: No productivity loss during transition
- [ ] **CI/CD Performance**: Build times improve by 3-5x
- [ ] **Developer Satisfaction**: Team prefers UV workflow

## ✨ Post-Migration Benefits

After successful migration, you'll have:

### Performance Gains
- **118-315x faster** environment setup
- **50-100x faster** dependency installation
- **3-5x faster** CI/CD builds
- **10x faster** dependency changes

### Developer Experience Improvements
- **Reliable Builds**: Locked dependencies prevent "works on my machine"
- **Modern Tooling**: Built on Rust for speed and reliability  
- **Better Caching**: UV's cache dramatically speeds up repeated operations
- **Simplified Commands**: `uv run` prefix unifies workflow

### Project Quality Improvements
- **Reproducible Environments**: uv.lock ensures identical setups
- **Better Dependencies**: pyproject.toml follows modern Python standards
- **Faster CI/CD**: Reduced build times improve feedback cycles
- **Future-Proof**: UV is the future of Python package management

## 📅 Migration Timeline

**Week 1**: Early Adopters
- [ ] Migration champions install UV and test workflow
- [ ] Document any project-specific issues
- [ ] Update this checklist with findings

**Week 2**: Team Migration
- [ ] All developers migrate to UV workflow
- [ ] Update team documentation and processes
- [ ] Monitor for issues and provide support

**Week 3**: Validation & Cleanup
- [ ] Verify all team members using UV successfully
- [ ] Remove deprecated pip/venv references
- [ ] Celebrate improved development velocity! 🎉

---

**Questions?** Check CLAUDE.md for UV commands or create an issue with the "uv-migration" label.

**Remember**: The migration provides 100x+ performance improvements. The initial learning investment pays dividends immediately!