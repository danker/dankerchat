"""Test dependency synchronization functionality.

This test verifies that UV can properly sync dependencies.
These tests MUST FAIL initially (RED phase) before migration.
"""

import shutil
import subprocess
from pathlib import Path

import pytest


class TestDependencySync:
    """Test UV dependency synchronization."""

    @property
    def project_root(self):
        return Path(__file__).parent.parent.parent

    def test_uv_sync_creates_lockfile(self):
        """Test that UV sync creates uv.lock file."""
        lockfile_path = self.project_root / "uv.lock"

        # This will fail initially since we don't have pyproject.toml
        try:
            subprocess.run(
                ["uv", "sync"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
            )
            assert lockfile_path.exists(), "uv.lock not created after sync"
        except subprocess.CalledProcessError:
            pytest.fail("UV sync failed - likely missing pyproject.toml")

    def test_uv_sync_creates_venv(self):
        """Test that UV sync creates .venv directory."""
        venv_path = self.project_root / ".venv"

        try:
            subprocess.run(
                ["uv", "sync"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
            )
            assert venv_path.exists(), ".venv directory not created after sync"
            assert venv_path.is_dir(), ".venv is not a directory"
        except subprocess.CalledProcessError:
            pytest.fail("UV sync failed to create virtual environment")

    def test_uv_run_python_works(self):
        """Test that uv run python executes correctly."""
        try:
            result = subprocess.run(
                ["uv", "run", "python", "--version"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
            )
            assert "Python" in result.stdout
        except subprocess.CalledProcessError:
            pytest.fail("uv run python failed")

    def test_uv_environment_isolation(self):
        """Test that UV creates isolated environment."""
        try:
            # Check that UV environment has different site-packages than system
            result = subprocess.run(
                ["uv", "run", "python", "-c", "import sys; print(sys.path)"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
            )
            # Should contain .venv path
            assert ".venv" in result.stdout
        except subprocess.CalledProcessError:
            pytest.fail("UV environment isolation check failed")

    def test_uv_sync_performance(self):
        """Test that UV sync completes within reasonable time (<15 seconds)."""
        import time

        # Clean state for timing test
        lockfile_path = self.project_root / "uv.lock"
        venv_path = self.project_root / ".venv"

        if lockfile_path.exists():
            lockfile_path.unlink()
        if venv_path.exists():
            shutil.rmtree(venv_path)

        start_time = time.time()
        try:
            subprocess.run(
                ["uv", "sync"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
                timeout=30,  # Fail if takes longer than 30 seconds
            )
            sync_time = time.time() - start_time
            assert sync_time < 15.0, f"UV sync took {sync_time:.2f}s, expected <15s"
        except subprocess.CalledProcessError:
            pytest.fail("UV sync performance test failed")
        except subprocess.TimeoutExpired:
            pytest.fail("UV sync timed out (>30s)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

