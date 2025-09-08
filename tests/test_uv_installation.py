#!/usr/bin/env python3
"""
UV Installation Verification Test - T005
CRITICAL: This test MUST FAIL before UV is installed (TDD RED phase)

Purpose: Verify UV package manager is properly installed and functional
Expected State: FAIL - UV should not be installed yet
Target: After UV installation, this test should PASS
"""

import subprocess
import sys


def test_uv_installed():
    """Test that UV is installed and accessible in PATH"""
    try:
        result = subprocess.run(
            ["uv", "--version"], capture_output=True, text=True, check=True
        )
        print(f"✅ UV installed: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ UV not found in PATH")
        return False


def test_uv_minimum_version():
    """Test that UV meets minimum version requirement (0.1.0+)"""
    try:
        result = subprocess.run(
            ["uv", "--version"], capture_output=True, text=True, check=True
        )
        # Extract version from output like "uv 0.1.35"
        version_str = result.stdout.strip().split()[-1]
        version_parts = version_str.split(".")
        major, minor = int(version_parts[0]), int(version_parts[1])

        if major >= 0 and minor >= 1:
            print(f"✅ UV version {version_str} meets requirements")
            return True
        else:
            print(f"❌ UV version {version_str} too old (need 0.1.0+)")
            return False
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
        print("❌ Cannot verify UV version")
        return False


def test_uv_help_accessible():
    """Test that UV help command works (basic functionality)"""
    try:
        result = subprocess.run(
            ["uv", "help"], capture_output=True, text=True, check=True
        )
        if "usage" in result.stdout.lower() or "commands" in result.stdout.lower():
            print("✅ UV help command functional")
            return True
        else:
            print("❌ UV help command not working properly")
            return False
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ UV help command failed")
        return False


def test_uv_python_compatibility():
    """Test that UV can detect current Python installation"""
    try:
        result = subprocess.run(
            ["uv", "python", "list"], capture_output=True, text=True, check=True
        )
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}"

        if python_version in result.stdout:
            print(f"✅ UV detected Python {python_version}")
            return True
        else:
            print(f"❌ UV did not detect current Python {python_version}")
            return False
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ UV python detection failed")
        return False


def run_all_tests():
    """Run all UV installation tests"""
    print("=== UV Installation Verification Tests (T005) ===")
    print("EXPECTED STATE: FAIL (UV not yet installed)")
    print("")

    tests = [
        ("UV Installation", test_uv_installed),
        ("UV Version Check", test_uv_minimum_version),
        ("UV Help Command", test_uv_help_accessible),
        ("Python Compatibility", test_uv_python_compatibility),
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
        print("🎉 ALL TESTS PASSED - UV is properly installed")
        return True
    else:
        print(f"❌ {total - passed} tests failed - UV installation incomplete")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
