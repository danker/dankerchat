#!/usr/bin/env python3
"""
PyProject Configuration Verification Test - T006
CRITICAL: This test MUST FAIL before pyproject.toml is created (TDD RED phase)

Purpose: Verify pyproject.toml exists and contains proper UV configuration
Expected State: FAIL - pyproject.toml should not exist yet
Target: After pyproject.toml creation, this test should PASS
"""

import sys
from pathlib import Path

try:
    import tomli

    TOMLI_AVAILABLE = True
except ImportError:
    TOMLI_AVAILABLE = False


def get_project_root():
    """Get the project root directory"""
    current = Path(__file__).parent
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    return Path.cwd()


def test_pyproject_exists():
    """Test that pyproject.toml file exists"""
    project_root = get_project_root()
    pyproject_path = project_root / "pyproject.toml"

    if pyproject_path.exists():
        print(f"✅ pyproject.toml found at {pyproject_path}")
        return True, pyproject_path
    else:
        print("❌ pyproject.toml not found in project root")
        return False, pyproject_path


def test_pyproject_valid_toml():
    """Test that pyproject.toml is valid TOML format"""
    exists, pyproject_path = test_pyproject_exists()
    if not exists:
        print("❌ Cannot validate TOML - file missing")
        return False, None

    if not TOMLI_AVAILABLE:
        print(
            "❌ Cannot validate TOML - tomli not installed (expected during migration)"
        )
        return False, None

    try:
        with open(pyproject_path, "rb") as f:
            config = tomli.load(f)
        print("✅ pyproject.toml is valid TOML format")
        return True, config
    except tomli.TOMLDecodeError as e:
        print(f"❌ pyproject.toml has invalid TOML syntax: {e}")
        return False, None
    except Exception as e:
        print(f"❌ Error reading pyproject.toml: {e}")
        return False, None


def test_project_section():
    """Test that [project] section exists with required fields"""
    valid, config = test_pyproject_valid_toml()
    if not valid:
        print("❌ Cannot validate project section - TOML invalid")
        return False

    if "project" not in config:
        print("❌ [project] section missing from pyproject.toml")
        return False

    project = config["project"]
    required_fields = ["name", "version", "requires-python"]
    missing = [field for field in required_fields if field not in project]

    if missing:
        print(f"❌ Missing required project fields: {missing}")
        return False

    print(f"✅ [project] section complete: {project['name']} v{project['version']}")
    return True


def test_dependencies_section():
    """Test that dependencies are properly defined"""
    valid, config = test_pyproject_valid_toml()
    if not valid:
        print("❌ Cannot validate dependencies - TOML invalid")
        return False

    project = config.get("project", {})
    dependencies = project.get("dependencies", [])

    # Expected dependencies based on chat application spec
    expected_deps = ["flask", "sqlalchemy", "flask-socketio"]
    found_deps = []

    for dep in dependencies:
        dep_name = dep.split(">=")[0].split("==")[0].split("[")[0].lower()
        if any(expected in dep_name for expected in expected_deps):
            found_deps.append(dep_name)

    if not dependencies:
        print("❌ No dependencies defined in pyproject.toml")
        return False
    elif len(found_deps) < 2:
        print(f"❌ Missing core dependencies, found: {found_deps}")
        return False
    else:
        print(f"✅ Dependencies properly defined: {len(dependencies)} total")
        return True


def test_build_system():
    """Test that build-system is configured for UV"""
    valid, config = test_pyproject_valid_toml()
    if not valid:
        print("❌ Cannot validate build system - TOML invalid")
        return False

    build_system = config.get("build-system", {})

    if not build_system:
        print("❌ [build-system] section missing")
        return False

    requires = build_system.get("requires", [])
    build_backend = build_system.get("build-backend", "")

    # Check for UV-compatible build system
    if "hatchling" in str(requires) or "setuptools" in str(requires):
        print(f"✅ Build system configured: {build_backend}")
        return True
    else:
        print(f"❌ Build system not properly configured: {requires}")
        return False


def test_tool_uv_section():
    """Test that [tool.uv] section exists for UV-specific configuration"""
    valid, config = test_pyproject_valid_toml()
    if not valid:
        print("❌ Cannot validate UV tool section - TOML invalid")
        return False

    tool_section = config.get("tool", {})
    uv_section = tool_section.get("uv", {})

    if not uv_section:
        print("❌ [tool.uv] section missing")
        return False

    # Check for UV-specific configuration
    dev_dependencies = uv_section.get("dev-dependencies", [])
    if dev_dependencies:
        print(
            f"✅ UV tool section configured with {len(dev_dependencies)} dev dependencies"
        )
    else:
        print("✅ UV tool section exists")

    return True


def run_all_tests():
    """Run all pyproject.toml verification tests"""
    print("=== PyProject Configuration Verification Tests (T006) ===")
    print("EXPECTED STATE: FAIL (pyproject.toml not yet created)")
    print("")

    tests = [
        ("File Existence", lambda: test_pyproject_exists()[0]),
        ("Valid TOML Format", lambda: test_pyproject_valid_toml()[0]),
        ("Project Section", test_project_section),
        ("Dependencies", test_dependencies_section),
        ("Build System", test_build_system),
        ("UV Tool Config", test_tool_uv_section),
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
        print("🎉 ALL TESTS PASSED - pyproject.toml is properly configured")
        return True
    else:
        print(f"❌ {total - passed} tests failed - pyproject.toml needs work")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
