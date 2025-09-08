"""Test UV installation and availability.

This test verifies that UV is properly installed and accessible.
These tests MUST FAIL initially (RED phase) before UV installation.
"""

import subprocess
from pathlib import Path

import pytest


class TestUVInstallation:
    """Test UV package manager installation."""

    def test_uv_command_available(self):
        """Test that uv command is available in PATH."""
        try:
            result = subprocess.run(
                ["uv", "--version"], capture_output=True, text=True, check=True
            )
            assert "uv" in result.stdout.lower()
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.fail("UV command not found in PATH")

    def test_uv_version_compatible(self):
        """Test that UV version is compatible (0.1.0+)."""
        try:
            result = subprocess.run(
                ["uv", "--version"], capture_output=True, text=True, check=True
            )
            version_line = result.stdout.strip()
            # Extract version number from output like "uv 0.1.35"
            version_parts = version_line.split()
            if len(version_parts) >= 2:
                version = version_parts[1]
                major, minor, patch = map(int, version.split("."))
                assert major >= 0 and minor >= 1
            else:
                pytest.fail(f"Could not parse UV version from: {version_line}")
        except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
            pytest.fail("Could not determine UV version")

    def test_uv_python_management(self):
        """Test that UV can manage Python versions."""
        try:
            result = subprocess.run(
                ["uv", "python", "list"], capture_output=True, text=True, check=True
            )
            # Should not fail and should show available Python versions
            assert len(result.stdout.strip()) > 0
        except subprocess.CalledProcessError:
            pytest.fail("UV python management not working")

    def test_uv_sync_capability(self):
        """Test that UV can sync dependencies successfully."""
        try:
            subprocess.run(
                ["uv", "sync"],
                capture_output=True,
                text=True,
                check=True,
                cwd=Path(__file__).parent.parent.parent,  # Project root
            )
            # If we get here, sync succeeded
            assert True
        except subprocess.CalledProcessError as e:
            pytest.fail(f"UV sync failed: {e.stderr}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
