"""Test cross-platform compatibility for UV migration.

This test verifies that UV works across different platforms.
These tests MUST FAIL initially (RED phase) before migration.
"""

import platform
import subprocess
import sys
from pathlib import Path

import pytest


class TestCrossPlatformCompat:
    """Test cross-platform compatibility."""

    @property
    def project_root(self):
        return Path(__file__).parent.parent.parent

    def test_python_version_compatibility(self):
        """Test that current Python version is supported (3.11+)."""
        version_info = sys.version_info
        assert version_info.major == 3, f"Python 3.x required, got {version_info.major}"
        assert version_info.minor >= 11, (
            f"Python 3.11+ required, got 3.{version_info.minor}"
        )

    def test_platform_detection(self):
        """Test that platform is correctly detected."""
        current_platform = platform.system()
        supported_platforms = ["Linux", "Darwin", "Windows"]
        assert current_platform in supported_platforms, (
            f"Unsupported platform: {current_platform}"
        )

    def test_uv_platform_specific_install(self):
        """Test that UV installation works on current platform."""
        try:
            result = subprocess.run(
                ["uv", "--version"], capture_output=True, text=True, check=True
            )
            # Should work on all supported platforms
            assert "uv" in result.stdout.lower()
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.fail(f"UV not available on {platform.system()}")

    def test_path_handling_cross_platform(self):
        """Test that file paths work correctly across platforms."""
        # Test that we can create and access paths correctly
        test_path = self.project_root / "test_temp_file.txt"

        try:
            # Create a temporary file
            test_path.write_text("test content")
            assert test_path.exists()

            # Read it back
            content = test_path.read_text()
            assert content == "test content"

        finally:
            # Clean up
            if test_path.exists():
                test_path.unlink()

    def test_uv_executable_permissions(self):
        """Test that UV executable has proper permissions."""
        try:
            # On Unix systems, check that uv is executable
            if platform.system() in ["Linux", "Darwin"]:
                result = subprocess.run(
                    ["which", "uv"], capture_output=True, text=True, check=True
                )
                uv_path = Path(result.stdout.strip())
                assert uv_path.exists()

                # Check if executable
                import stat

                mode = uv_path.stat().st_mode
                assert mode & stat.S_IEXEC, "UV executable lacks execute permission"

        except subprocess.CalledProcessError:
            pytest.fail("UV executable not found in PATH")

    def test_environment_variables_handling(self):
        """Test that environment variables are handled correctly."""
        # Test that UV respects common environment variables
        import os

        # UV should respect PATH
        path_env = os.environ.get("PATH", "")
        assert len(path_env) > 0, "PATH environment variable not set"

        # Test UV-specific environment variables if any
        # This ensures UV configuration can be customized per platform
        uv_cache_dir = os.environ.get("UV_CACHE_DIR")
        if uv_cache_dir:
            cache_path = Path(uv_cache_dir)
            # If set, should be a valid path
            assert cache_path.parent.exists(), (
                "UV_CACHE_DIR parent directory doesn't exist"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
