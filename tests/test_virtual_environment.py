#!/usr/bin/env python3
"""
Virtual Environment Verification Test - T008
CRITICAL: This test MUST FAIL before .venv is created (TDD RED phase)

Purpose: Verify UV-managed virtual environment is properly created and configured
Expected State: FAIL - .venv should not exist yet
Target: After UV sync, this test should PASS
"""

import os
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


def test_venv_directory_exists():
    """Test that .venv directory exists"""
    project_root = get_project_root()
    venv_dir = project_root / ".venv"

    if venv_dir.exists() and venv_dir.is_dir():
        print(f"✅ .venv directory exists at {venv_dir}")
        return True
    else:
        print("❌ .venv directory not found")
        return False


def test_venv_python_executable():
    """Test that .venv contains Python executable"""
    project_root = get_project_root()

    # Check for Python executable in different OS locations
    python_paths = [
        project_root / ".venv" / "bin" / "python",  # Unix/Linux/macOS
        project_root / ".venv" / "Scripts" / "python.exe",  # Windows
    ]

    for python_path in python_paths:
        if python_path.exists():
            print(f"✅ Python executable found at {python_path}")
            return True, python_path

    print("❌ Python executable not found in .venv")
    return False, None


def test_venv_python_version():
    """Test that .venv Python matches expected version"""
    exists, python_path = test_venv_python_executable()
    if not exists:
        print("❌ Cannot check Python version - executable missing")
        return False

    try:
        result = subprocess.run(
            [str(python_path), "--version"], capture_output=True, text=True, check=True
        )
        version_output = result.stdout.strip()

        # Check for Python 3.11+ (UV migration requirement)
        if "Python 3." in version_output:
            version_num = version_output.split()[-1]
            major, minor = version_num.split(".")[:2]

            if int(major) >= 3 and int(minor) >= 11:
                print(f"✅ Virtual environment Python version: {version_output}")
                return True
            else:
                print(f"❌ Python version too old: {version_output} (need 3.11+)")
                return False
        else:
            print(f"❌ Unexpected Python version output: {version_output}")
            return False

    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Cannot execute Python in virtual environment")
        return False


def test_venv_pip_available():
    """Test that package management is available (UV manages packages, not pip)"""
    # UV doesn't install pip by default, which is expected and correct
    # Instead, verify that UV can manage packages in this environment
    try:
        result = subprocess.run(
            ["uv", "run", "python", "-c", "import sys; print('Package management via UV')"],
            capture_output=True, text=True, check=True
        )
        if "Package management via UV" in result.stdout:
            print("✅ UV package management available (pip not needed)")
            return True
        else:
            print("❌ UV package management check failed")
            return False
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ UV package management not available")
        return False


def test_venv_site_packages():
    """Test that site-packages directory exists and is writable"""
    project_root = get_project_root()
    venv_dir = project_root / ".venv"

    if not venv_dir.exists():
        print("❌ Cannot check site-packages - .venv missing")
        return False

    # Find site-packages directory
    site_packages_paths = list(venv_dir.rglob("site-packages"))

    if not site_packages_paths:
        print("❌ site-packages directory not found")
        return False

    site_packages = site_packages_paths[0]

    # Test if directory is writable
    if os.access(site_packages, os.W_OK):
        print(f"✅ site-packages writable at {site_packages}")
        return True
    else:
        print(f"❌ site-packages not writable at {site_packages}")
        return False


def test_venv_activation_script():
    """Test that virtual environment activation script exists"""
    project_root = get_project_root()

    activation_paths = [
        project_root / ".venv" / "bin" / "activate",  # Unix/Linux/macOS
        project_root / ".venv" / "Scripts" / "activate.bat",  # Windows
    ]

    for activate_path in activation_paths:
        if activate_path.exists():
            print(f"✅ Activation script found at {activate_path}")
            return True

    print("❌ Virtual environment activation script not found")
    return False


def test_venv_isolated_from_system():
    """Test that virtual environment is isolated from system Python"""
    exists, python_path = test_venv_python_executable()
    if not exists:
        print("❌ Cannot test isolation - Python executable missing")
        return False

    try:
        # Get sys.path from virtual environment Python
        result = subprocess.run(
            [str(python_path), "-c", "import sys; print(sys.path)"],
            capture_output=True,
            text=True,
            check=True,
        )

        venv_sys_path = result.stdout.strip()
        project_root = get_project_root()

        # Check that .venv path is in sys.path
        if str(project_root / ".venv") in venv_sys_path:
            print("✅ Virtual environment properly isolated")
            return True
        else:
            print("❌ Virtual environment not properly isolated")
            return False

    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Cannot test virtual environment isolation")
        return False


def test_uv_manages_venv():
    """Test that UV recognizes and manages the virtual environment"""
    project_root = get_project_root()

    try:
        # Run uv command in project directory to see if it detects .venv
        result = subprocess.run(
            ["uv", "pip", "list"], capture_output=True, text=True, cwd=str(project_root)
        )

        # UV should either succeed (if .venv exists) or fail with specific message
        if result.returncode == 0:
            print("✅ UV successfully manages virtual environment")
            return True
        else:
            # Check error message for virtual environment related issues
            stderr = result.stderr.lower()
            if "virtual environment" in stderr or "venv" in stderr:
                print("❌ UV cannot manage virtual environment")
                return False
            else:
                print("❌ UV command failed for unknown reason")
                return False

    except FileNotFoundError:
        print("❌ UV command not found")
        return False


def run_all_tests():
    """Run all virtual environment verification tests"""
    print("=== Virtual Environment Verification Tests (T008) ===")
    print("EXPECTED STATE: FAIL (.venv not yet created)")
    print("")

    tests = [
        ("Directory Exists", test_venv_directory_exists),
        ("Python Executable", lambda: test_venv_python_executable()[0]),
        ("Python Version", test_venv_python_version),
        ("pip Available", test_venv_pip_available),
        ("site-packages", test_venv_site_packages),
        ("Activation Script", test_venv_activation_script),
        ("System Isolation", test_venv_isolated_from_system),
        ("UV Management", test_uv_manages_venv),
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
        print("🎉 ALL TESTS PASSED - Virtual environment properly configured")
        return True
    else:
        print(f"❌ {total - passed} tests failed - Virtual environment needs setup")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
