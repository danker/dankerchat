#!/usr/bin/env python3
"""
Dependency Installation Verification Test - T007
CRITICAL: This test MUST FAIL before dependencies are installed (TDD RED phase)

Purpose: Verify project dependencies are properly installed via UV
Expected State: FAIL - dependencies should not be installed yet
Target: After UV sync, this test should PASS
"""

import subprocess
import sys
from pathlib import Path


def get_project_root():
    """Get the project root directory"""
    current = Path(__file__).parent
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    return Path.cwd()


def test_flask_available():
    """Test that Flask is installed and importable"""
    try:
        import flask

        print(f"✅ Flask available: {flask.__version__}")
        return True
    except ImportError:
        print("❌ Flask not installed")
        return False


def test_sqlalchemy_available():
    """Test that SQLAlchemy is installed and importable"""
    try:
        import sqlalchemy

        print(f"✅ SQLAlchemy available: {sqlalchemy.__version__}")
        return True
    except ImportError:
        print("❌ SQLAlchemy not installed")
        return False


def test_flask_socketio_available():
    """Test that Flask-SocketIO is installed and importable"""
    try:
        import flask_socketio

        version = getattr(flask_socketio, "__version__", "installed")
        print(f"✅ Flask-SocketIO available: {version}")
        return True
    except ImportError:
        print("❌ Flask-SocketIO not installed")
        return False


def test_pytest_available():
    """Test that pytest is available for testing"""
    try:
        import pytest

        print(f"✅ pytest available: {pytest.__version__}")
        return True
    except ImportError:
        print("❌ pytest not installed")
        return False


def test_tomli_available():
    """Test that tomli is available for TOML parsing"""
    try:
        import tomli

        print(f"✅ tomli available: {tomli.__version__}")
        return True
    except ImportError:
        print("❌ tomli not installed")
        return False


def test_uv_lock_exists():
    """Test that uv.lock file exists (dependency lockfile)"""
    project_root = get_project_root()
    uv_lock = project_root / "uv.lock"

    if uv_lock.exists():
        print(f"✅ uv.lock found at {uv_lock}")
        return True
    else:
        print("❌ uv.lock not found - dependencies not locked")
        return False


def test_venv_directory():
    """Test that .venv directory exists with installed packages"""
    project_root = get_project_root()
    venv_dir = project_root / ".venv"

    if not venv_dir.exists():
        print("❌ .venv directory not found")
        return False

    # Check for site-packages indicating installed packages
    site_packages = None
    for path in venv_dir.rglob("site-packages"):
        site_packages = path
        break

    if site_packages and any(site_packages.iterdir()):
        print(f"✅ .venv directory with packages at {venv_dir}")
        return True
    else:
        print("❌ .venv directory empty or missing packages")
        return False


def test_uv_pip_list():
    """Test that UV environment has installed packages"""
    try:
        # Test key package imports
        result = subprocess.run(
            ["uv", "run", "python", "-c", 
             "import flask, sqlalchemy, flask_socketio; print('Core packages available')"],
            capture_output=True, text=True, check=True
        )

        if "Core packages available" in result.stdout:
            print("✅ UV environment has core packages available")
            return True
        else:
            print("❌ UV environment package check failed")
            return False

    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ UV package availability check failed")
        return False


def test_import_compatibility():
    """Test that dependencies work together (no conflicts)"""
    try:
        # Test basic Flask app creation
        from flask import Flask

        app = Flask(__name__)

        # Test SQLAlchemy integration
        from sqlalchemy import create_engine

        create_engine("sqlite:///:memory:")

        # Test SocketIO integration
        from flask_socketio import SocketIO

        SocketIO(app)

        print("✅ All dependencies work together without conflicts")
        return True

    except ImportError as e:
        print(f"❌ Import error - dependency conflict: {e}")
        return False
    except Exception as e:
        print(f"❌ Runtime error - compatibility issue: {e}")
        return False


def run_all_tests():
    """Run all dependency installation tests"""
    print("=== Dependency Installation Verification Tests (T007) ===")
    print("EXPECTED STATE: FAIL (dependencies not yet installed)")
    print("")

    tests = [
        ("Flask Import", test_flask_available),
        ("SQLAlchemy Import", test_sqlalchemy_available),
        ("Flask-SocketIO Import", test_flask_socketio_available),
        ("pytest Import", test_pytest_available),
        ("tomli Import", test_tomli_available),
        ("UV Lock File", test_uv_lock_exists),
        ("Virtual Environment", test_venv_directory),
        ("UV Pip List", test_uv_pip_list),
        ("Import Compatibility", test_import_compatibility),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"Running: {test_name}")
        if test_func():
            passed += 1
        print("")

    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL TESTS PASSED - Dependencies properly installed")
        return True
    else:
        print(f"❌ {total - passed} tests failed - Dependency installation incomplete")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
