"""Test pyproject.toml configuration validation.

This test verifies that pyproject.toml is properly configured.
These tests MUST FAIL initially (RED phase) before migration.
"""

import pytest
import tomllib
from pathlib import Path


class TestPyprojectConfig:
    """Test pyproject.toml configuration."""
    
    @property
    def project_root(self):
        return Path(__file__).parent.parent.parent
    
    @property  
    def pyproject_path(self):
        return self.project_root / "pyproject.toml"
    
    def test_pyproject_toml_exists(self):
        """Test that pyproject.toml file exists."""
        assert self.pyproject_path.exists(), "pyproject.toml not found"
    
    def test_pyproject_toml_valid_format(self):
        """Test that pyproject.toml is valid TOML format."""
        try:
            with open(self.pyproject_path, "rb") as f:
                tomllib.load(f)
        except Exception as e:
            pytest.fail(f"pyproject.toml is not valid TOML: {e}")
    
    def test_project_metadata_present(self):
        """Test that required project metadata is present."""
        with open(self.pyproject_path, "rb") as f:
            config = tomllib.load(f)
        
        assert "project" in config, "Missing [project] section"
        project = config["project"]
        
        required_fields = ["name", "version", "description"]
        for field in required_fields:
            assert field in project, f"Missing required field: project.{field}"
    
    def test_dependencies_section_present(self):
        """Test that dependencies section exists."""
        with open(self.pyproject_path, "rb") as f:
            config = tomllib.load(f)
        
        assert "project" in config, "Missing [project] section"
        project = config["project"]
        assert "dependencies" in project, "Missing project.dependencies"
        assert isinstance(project["dependencies"], list), "dependencies must be a list"
    
    def test_build_system_present(self):
        """Test that build-system is configured."""
        with open(self.pyproject_path, "rb") as f:
            config = tomllib.load(f)
        
        assert "build-system" in config, "Missing [build-system] section"
        build_system = config["build-system"]
        assert "requires" in build_system, "Missing build-system.requires"
        assert "build-backend" in build_system, "Missing build-system.build-backend"
    
    def test_tool_uv_section_present(self):
        """Test that UV-specific configuration exists."""
        with open(self.pyproject_path, "rb") as f:
            config = tomllib.load(f)
        
        # UV configuration is optional, but if present should be valid
        if "tool" in config and "uv" in config["tool"]:
            uv_config = config["tool"]["uv"]
            assert isinstance(uv_config, dict), "tool.uv must be a dictionary"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])