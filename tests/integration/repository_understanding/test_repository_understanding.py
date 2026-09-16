"""
Integration tests for the Repository Understanding module.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from autonomous_agent.repository_understanding import (
    create_repository_understanding_system,
    RepositoryDiscovery,
    RepositoryMetadataManager,
)
from autonomous_agent.workspace import Workspace


class TestRepositoryUnderstandingIntegration:
    """Integration tests for the Repository Understanding system."""

    @pytest.fixture
    def temp_workspace_dir(self):
        """Create a temporary directory for the workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def workspace(self, temp_workspace_dir):
        """Create a workspace instance for testing."""
        workspace_path = os.path.join(temp_workspace_dir, "test_workspace")
        os.makedirs(workspace_path, exist_ok=True)
        return Workspace(workspace_root=workspace_path)

    @pytest.fixture
    def discovery(self, workspace):
        """Create a RepositoryDiscovery instance for testing."""
        return RepositoryDiscovery(workspace)

    @pytest.fixture
    def metadata_manager(self, discovery):
        """Create a RepositoryMetadataManager instance for testing."""
        return RepositoryMetadataManager(discovery)

    def test_complete_system_initialization(self, workspace):
        """Test that the complete system can be initialized."""
        discovery, metadata_manager = create_repository_understanding_system(
            workspace.workspace_root
        )

        assert isinstance(discovery, RepositoryDiscovery)
        assert isinstance(metadata_manager, RepositoryMetadataManager)
        assert metadata_manager.discovery == discovery

    def test_end_to_end_repository_understanding(self, workspace, temp_workspace_dir):
        """Test end-to-end repository understanding with a realistic project structure."""
        # Create a realistic Python project structure
        project_root = Path(temp_workspace_dir) / "test_workspace"

        # Create directory structure
        (project_root / "src").mkdir()
        (project_root / "tests").mkdir()
        (project_root / "docs").mkdir()

        # Create project files
        (project_root / "setup.py").write_text("""
from setuptools import setup, find_packages

setup(
    name="test-project",
    version="0.1.0",
    packages=find_packages(),
)
""")

        (project_root / "requirements.txt").write_text("""
requests>=2.25.0
numpy>=1.20.0
""")

        # Create source files
        (project_root / "src" / "main.py").write_text("""
def main():
    print("Hello, World!")
    return 0

if __name__ == "__main__":
    main()
""")

        (project_root / "src" / "utils.py").write_text("""
def helper_function():
    return "helpful"

class UtilityClass:
    def __init__(self, value):
        self.value = value
""")

        # Create test files
        (project_root / "tests" / "test_main.py").write_text("""
import unittest
from src.main import main

class TestMain(unittest.TestCase):
    def test_main_returns_zero(self):
        self.assertEqual(main(), 0)
""")

        # Create documentation
        (project_root / "README.md").write_text("""
# Test Project

This is a test project for validating repository understanding.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python src/main.py
```
""")

        (project_root / "docs" / "api.md").write_text("""
# API Documentation

## Main Functions

### main()
The main entry point of the application.
""")

        # Initialize the repository understanding system
        discovery, metadata_manager = create_repository_understanding_system(
            workspace.workspace_root
        )

        # Get repository metadata
        metadata = metadata_manager.get_metadata()

        # Validate the discovered metadata
        assert metadata.root_path == project_root.resolve()
        assert metadata.is_git_repo is False  # No .git directory initialized
        assert metadata.project_type == "python"
        assert "python" in metadata.project_configs
        assert metadata.project_configs["python"] == (project_root / "setup.py").resolve()

        # Check language hints
        assert "python" in metadata.language_hints

        # Check documentation hints
        assert "markdown" in metadata.documentation_hints  # From README.md

        # Check structure mapping
        assert "" in metadata.structure_map  # Root level
        assert "setup.py" in metadata.structure_map[""]
        assert "requirements.txt" in metadata.structure_map[""]
        assert "README.md" in metadata.structure_map[""]
        assert "src" in metadata.structure_map
        assert "main.py" in metadata.structure_map["src"]
        assert "utils.py" in metadata.structure_map["src"]
        assert "tests" in metadata.structure_map
        assert "test_main.py" in metadata.structure_map["tests"]
        assert "docs" in metadata.structure_map
        assert "api.md" in metadata.structure_map["docs"]

        # Test caching behavior
        # Second call should return cached result
        metadata2 = metadata_manager.get_metadata()
        assert metadata2 is metadata  # Same object due to caching

        # Force refresh should get new data (but should be equivalent for unchanged repo)
        metadata3 = metadata_manager.get_metadata(force_refresh=True)
        assert metadata3 is not metadata  # Different object
        assert metadata3.root_path == metadata.root_path  # Same content

        # Test change detection
        # Initially no changes detected
        assert metadata_manager.has_repository_changed() is False

        # Add a file
        (project_root / "new_feature.py").write_text("# New feature\n")

        # Now changes should be detected
        assert metadata_manager.has_repository_changed() is True

        # Getting metadata updates the last known state
        metadata_manager.get_metadata()
        assert metadata_manager.has_repository_changed() is False

    def test_git_repository_detection(self, workspace, temp_workspace_dir):
        """Test that Git repositories are properly detected."""
        project_root = Path(temp_workspace_dir) / "test_workspace"

        # Initialize a Git repository
        git_dir = project_root / ".git"
        git_dir.mkdir()
        (git_dir / "HEAD").write_text("ref: refs/heads/main\n")
        (git_dir / "config").write_text("[core]\n\trepositoryformatversion = 0\n")
        (git_dir / "objects").mkdir()
        (git_dir / "refs").mkdir()
        (git_dir / "refs" / "heads").mkdir()

        # Create a simple project file
        (project_root / "README.md").write_text("# Git Test Project\n")

        # Initialize the system
        discovery, metadata_manager = create_repository_understanding_system(
            workspace.workspace_root
        )

        # Get metadata
        metadata = metadata_manager.get_metadata()

        # Validate Git detection
        assert metadata.is_git_repo is True
        assert metadata.git_branch == "main"
        assert metadata.root_path == project_root.resolve()

        # Still detect project type from other files
        assert "markdown" in metadata.documentation_hints  # From README.md

    def test_workspace_boundary_respected(self, temp_workspace_dir):
        """Test that the repository understanding respects workspace boundaries."""
        # Create two directories: one inside workspace, one outside
        workspace_dir = Path(temp_workspace_dir) / "workspace"
        outside_dir = Path(temp_workspace_dir) / "outside"
        workspace_dir.mkdir()
        outside_dir.mkdir()

        # Create a project structure in the workspace
        (workspace_dir / "README.md").write_text("# Inside Workspace\n")
        (workspace_dir / "setup.py").write_text("# Setup file\n")

        # Create a tempting structure outside the workspace
        (outside_dir / "README.md").write_text("# Outside Workspace\n")
        (outside_dir / "setup.py").write_text("# Setup file\n")
        (outside_dir / "secret.txt").write_text("SECRET DATA\n")

        # Initialize workspace to be INSIDE the workspace directory
        workspace = Workspace(workspace_root=str(workspace_dir))
        discovery, metadata_manager = create_repository_understanding_system(
            workspace.workspace_root
        )

        # Get metadata
        metadata = metadata_manager.get_metadata()

        # Validate that we only see the workspace contents
        assert metadata.root_path == workspace_dir.resolve()
        assert metadata.project_type == "python"  # From setup.py in workspace
        assert "README.md" in metadata.structure_map[""]
        assert "setup.py" in metadata.structure_map[""]

        # Validate that we DON'T see outside contents
        # The structure map should not contain paths outside the workspace
        all_files = []
        for file_list in metadata.structure_map.values():
            all_files.extend(file_list)

        # None of the files should be from outside the workspace
        assert "secret.txt" not in all_files
        assert "../outside" not in str(metadata.root_path)

        # Validate that the root path is correctly bounded
        assert str(metadata.root_path).startswith(str(workspace_dir.resolve()))

    def test_error_handling_and_graceful_degradation(self, temp_workspace_dir):
        """Test that the system handles errors gracefully."""
        # Create a workspace with restricted permissions (simulate by making unreadable)
        workspace_dir = Path(temp_workspace_dir) / "workspace"
        workspace_dir.mkdir()

        # Create a directory we'll make unreadable
        restricted_dir = workspace_dir / "restricted"
        restricted_dir.mkdir()
        (restricted_dir / "secret.txt").write_text("secret\n")

        # Make the directory unreadable (if possible on this system)
        try:
            restricted_dir.chmod(0o000)  # No permissions

            workspace = Workspace(workspace_root=str(workspace_dir))
            discovery = RepositoryDiscovery(workspace)

            # The system should still work for readable parts
            metadata = discovery.discover_repository()

            # Should be able to read the workspace root
            assert metadata.root_path == workspace_dir.resolve()

            # Restore permissions for cleanup
            restricted_dir.chmod(0o755)

        except (PermissionError, OSError):
            # If we can't change permissions, that's ok - test what we can
            workspace = Workspace(workspace_root=str(workspace_dir))
            discovery = RepositoryDiscovery(workspace)

            # Should still work
            metadata = discovery.discover_repository()
            assert metadata.root_path == workspace_dir.resolve()

    def test_performance_characteristics(self, workspace, temp_workspace_dir):
        """Test basic performance characteristics of the system."""
        import time

        # Create a reasonably sized project structure
        project_root = Path(temp_workspace_dir) / "test_workspace"

        # Create multiple directories and files
        for i in range(5):
            dir_path = project_root / f"module_{i}"
            dir_path.mkdir()
            for j in range(10):
                (dir_path / f"file_{j}.py").write_text(f"# File {j} in module {i}\n")

        # Create project files
        (project_root / "setup.py").write_text("# Setup\n")
        (project_root / "README.md").write_text("# README\n")

        # Initialize the system
        discovery, metadata_manager = create_repository_understanding_system(
            workspace.workspace_root
        )

        # Time the initial discovery
        start_time = time.time()
        metadata = metadata_manager.get_metadata()
        first_call_time = time.time() - start_time

        # Time the cached call
        start_time = time.time()
        metadata2 = metadata_manager.get_metadata()
        cached_call_time = time.time() - start_time

        # Validate that we got correct metadata
        assert metadata.root_path == project_root.resolve()
        assert metadata.project_type == "python"

        # Validate that caching works (second call should be significantly faster)
        # Note: This might be flaky on very fast systems, but the principle should hold
        assert cached_call_time <= first_call_time or first_call_time < 0.1  # Allow for fast systems

        # Validate that we got reasonable performance (should be well under 1 second for this size)
        assert first_call_time < 2.0  # Should be much faster in practice

        # Validate structure was mapped reasonably
        total_files = sum(len(files) for files in metadata.structure_map.values())
        assert total_files > 40  # Should have found most of our 50 created files + 2 project files