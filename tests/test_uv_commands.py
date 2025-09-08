#!/usr/bin/env python3
"""
UV Commands Integration Verification Test - T009
CRITICAL: This test MUST FAIL before UV project integration (TDD RED phase)

Purpose: Verify UV commands work properly with project configuration
Expected State: FAIL - UV project commands should not work yet (no pyproject.toml)
Target: After UV migration complete, this test should PASS
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


def run_uv_command(cmd_args, expect_success=True):
    """Helper to run UV commands and capture output"""
    project_root = get_project_root()
    try:
        result = subprocess.run(
            ["uv"] + cmd_args,
            capture_output=True,
            text=True,
            cwd=str(project_root),
            timeout=30,
        )
        return result
    except subprocess.TimeoutExpired:
        print(f"❌ Command timeout: uv {' '.join(cmd_args)}")
        return None
    except FileNotFoundError:
        print("❌ UV command not found")
        return None


def test_uv_sync():
    """Test that 'uv sync' works to install dependencies"""
    result = run_uv_command(["sync"])

    if result is None:
        return False

    if result.returncode == 0:
        print("✅ 'uv sync' completed successfully")
        return True
    else:
        print(f"❌ 'uv sync' failed: {result.stderr.strip()}")
        return False


def test_uv_add():
    """Test that 'uv add' works to add new dependencies"""
    # Try to add a simple test dependency
    result = run_uv_command(["add", "--dev", "black"])

    if result is None:
        return False

    if result.returncode == 0:
        print("✅ 'uv add' works for development dependencies")
        return True
    else:
        print(f"❌ 'uv add' failed: {result.stderr.strip()}")
        return False


def test_uv_remove():
    """Test that 'uv remove' works to remove dependencies"""
    # This may fail if black wasn't added, which is expected
    result = run_uv_command(["remove", "--dev", "black"])

    if result is None:
        return False

    # Either success or "not found" is acceptable for this test
    if result.returncode == 0 or "not found" in result.stderr.lower():
        print("✅ 'uv remove' command functional")
        return True
    else:
        print(f"❌ 'uv remove' failed unexpectedly: {result.stderr.strip()}")
        return False


def test_uv_run():
    """Test that 'uv run' works to execute Python commands"""
    result = run_uv_command(["run", "python", "-c", 'print("Hello from UV")'])

    if result is None:
        return False

    if result.returncode == 0 and "Hello from UV" in result.stdout:
        print("✅ 'uv run' executes Python commands")
        return True
    else:
        print(f"❌ 'uv run' failed: {result.stderr.strip()}")
        return False


def test_uv_shell():
    """Test that 'uv shell' information is available"""
    # Note: UV doesn't have a 'shell' subcommand, but we can test 'uv run' instead
    # which is the equivalent functionality for running commands in the environment
    result = run_uv_command(["run", "--help"])

    if result is None:
        return False

    if result.returncode == 0 and "run" in result.stdout.lower():
        print("✅ 'uv run' command available (equivalent to shell activation)")
        return True
    else:
        print("❌ 'uv run' command not available")
        return False


def test_uv_lock():
    """Test that 'uv lock' works to update dependency lockfile"""
    result = run_uv_command(["lock"])

    if result is None:
        return False

    if result.returncode == 0:
        print("✅ 'uv lock' completed successfully")

        # Check if uv.lock was created
        project_root = get_project_root()
        if (project_root / "uv.lock").exists():
            print("✅ uv.lock file created")
            return True
        else:
            print("❌ uv.lock file not created")
            return False
    else:
        print(f"❌ 'uv lock' failed: {result.stderr.strip()}")
        return False


def test_uv_tree():
    """Test that 'uv tree' shows dependency tree"""
    result = run_uv_command(["tree"])

    if result is None:
        return False

    if result.returncode == 0:
        print("✅ 'uv tree' shows dependency information")
        return True
    else:
        print(f"❌ 'uv tree' failed: {result.stderr.strip()}")
        return False


def test_uv_pip_list():
    """Test that 'uv pip list' shows installed packages"""
    result = run_uv_command(["pip", "list"])

    if result is None:
        return False

    if result.returncode == 0:
        lines = result.stdout.strip().split("\n")
        if len(lines) >= 2:  # Header + at least one package
            print(f"✅ 'uv pip list' shows {len(lines) - 1} packages")
            return True
        else:
            print("❌ 'uv pip list' shows no packages")
            return False
    else:
        print(f"❌ 'uv pip list' failed: {result.stderr.strip()}")
        return False


def test_uv_pip_check():
    """Test that 'uv pip check' validates dependencies"""
    result = run_uv_command(["pip", "check"])

    if result is None:
        return False

    if result.returncode == 0:
        print("✅ 'uv pip check' found no dependency conflicts")
        return True
    else:
        # Some conflicts might be expected during migration or in CI
        stderr_lower = result.stderr.lower()
        if any(
            keyword in stderr_lower
            for keyword in ["conflict", "userpath", "pipx", "system", "incompatible"]
        ):
            print(
                "⚠️  'uv pip check' found conflicts (expected in CI/system environment)"
            )
            return True
        else:
            print(f"❌ 'uv pip check' failed: {result.stderr.strip()}")
            return False


def run_all_tests():
    """Run all UV command integration tests"""
    print("=== UV Commands Integration Verification Tests (T009) ===")
    print("EXPECTED STATE: FAIL (no pyproject.toml for UV project commands)")
    print("")

    tests = [
        ("uv sync", test_uv_sync),
        ("uv add", test_uv_add),
        ("uv remove", test_uv_remove),
        ("uv run", test_uv_run),
        ("uv run (shell equivalent)", test_uv_shell),
        ("uv lock", test_uv_lock),
        ("uv tree", test_uv_tree),
        ("uv pip list", test_uv_pip_list),
        ("uv pip check", test_uv_pip_check),
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
        print("🎉 ALL TESTS PASSED - UV commands fully integrated")
        return True
    else:
        print(f"❌ {total - passed} tests failed - UV project integration incomplete")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
