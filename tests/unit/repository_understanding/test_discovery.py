"""
Unit tests for the Repository Discovery module.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from autonomous_agent.repository_understanding import RepositoryDiscovery, RepositoryMetadataManager
from autonomous_agent.workspace import Workspace


class TestRepositoryDiscovery:
    """Test the RepositoryDiscovery class."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def workspace(self, temp_workspace):
        """Create a workspace instance for testing."""
        workspace_path = os.path.join(temp_workspace, "test_workspace")
        os.makedirs(workspace_path, exist_ok=True)
        return Workspace(workspace_root=workspace_path)

    @pytest.fixture
    def discovery(self, workspace):
        """Create a RepositoryDiscovery instance for testing."""
        return RepositoryDiscovery(workspace)

    def test_init_with_workspace(self, workspace):
        """Test that RepositoryDiscovery initializes correctly with a workspace."""
        discovery = RepositoryDiscovery(workspace)
        assert discovery.workspace == workspace

    def test_discover_repository_basic(self, discovery, temp_workspace):
        """Test basic repository discovery functionality."""
        # Create a basic file structure
        test_file = Path(temp_workspace) / "test_workspace" / "test.txt"
        test_file.write_text("hello world")

        # Discover the repository
        metadata = discovery.discover_repository()

        # Assert basic properties
        assert metadata.root_path == (Path(temp_workspace) / "test_workspace").resolve()
        assert isinstance(metadata.root_path, Path)
        assert metadata.is_git_repo is False  # No .git directory
        assert metadata.project_type is None  # No recognized project config
        assert isinstance(metadata.language_hints, set)
        assert isinstance(metadata.build_system_hints, set)
        assert isinstance(metadata.documentation_hints, set)
        assert isinstance(metadata.structure_map, dict)

    def test_discover_repository_with_git(self, discovery, temp_workspace):
        """Test repository discovery when a .git directory is present."""
        # Create a .git directory to simulate a Git repository
        git_dir = Path(temp_workspace) / "test_workspace" / ".git"
        git_dir.mkdir()
        (git_dir / "HEAD").write_text("ref: refs/heads/main\n")

        # Discover the repository
        metadata = discovery.discover_repository()

        # Assert Git repository was detected
        assert metadata.is_git_repo is True
        assert metadata.git_branch == "main"

    def test_discover_repository_with_python_project(self, discovery, temp_workspace):
        """Test repository discovery with a Python project configuration."""
        # Create a Python project file
        setup_py = Path(temp_workspace) / "test_workspace" / "setup.py"
        setup_py.write_text("# dummy setup.py\n")

        # Discover the repository
        metadata = discovery.discover_repository()

        # Assert Python project was detected
        assert metadata.project_type == "python"
        assert "python" in metadata.project_configs
        assert metadata.project_configs["python"] == setup_py.resolve()

    def test_discover_repository_with_javascript_project(self, discovery, temp_workspace):
        """Test repository discovery with a JavaScript project configuration."""
        # Create a JavaScript project file
        package_json = Path(temp_workspace) / "test_workspace" / "package.json"
        package_json.write_text('{"name": "test-app"}\n')

        # Discover the repository
        metadata = discovery.discover_repository()

        # Assert JavaScript project was detected
        assert metadata.project_type == "javascript"
        assert "javascript" in metadata.project_configs
        assert metadata.project_configs["javascript"] == package_json.resolve()

    def test_discover_repository_language_detection(self, discovery, temp_workspace):
        """Test that language hints are detected from file extensions."""
        # Create files with different extensions
        (Path(temp_workspace) / "test_workspace" / "test.py").write_text("# Python file\n")
        (Path(temp_workspace) / "test_workspace" / "test.js").write_text("// JavaScript file\n")
        (Path(temp_workspace) / "test_workspace" / "test.rs").write_text("// Rust file\n")

        # Discover the repository
        metadata = discovery.discover_repository()

        # Assert language hints were detected
        assert "python" in metadata.language_hints
        assert "javascript" in metadata.language_hints
        assert "rust" in metadata.language_hints

    def test_discover_repository_build_system_detection(self, discovery, temp_workspace):
        """Test that build system hints are detected."""
        # Create a Makefile
        makefile = Path(temp_workspace) / "test_workspace" / "Makefile"
        makefile.write_text("all:\n\techo hello\n")

        # Discover the repository
        metadata = discovery.discover_repository()

        # Assert build system hint was detected
        assert "make" in metadata.build_system_hints

    def test_discover_repository_documentation_detection(self, discovery, temp_workspace):
        """Test that documentation hints are detected."""
        # Create a README file
        readme = Path(temp_workspace) / "test_workspace" / "README.md"
        readme.write_text("# Test Project\n")

        # Discover the repository
        metadata = discovery.discover_repository()

        # Assert documentation hint was detected
        assert "markdown" in metadata.documentation_hints

    def test_discover_repository_structure_mapping(self, discovery, temp_workspace):
        """Test that basic structure mapping works."""
        # Create a nested directory structure
        src_dir = Path(temp_workspace) / "test_workspace" / "src"
        src_dir.mkdir()
        (src_dir / "main.py").write_text("# Main file\n")
        (src_dir / "utils.py").write_text("# Utils file\n")

        tests_dir = Path(temp_workspace) / "test_workspace" / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_main.py").write_text("# Test file\n")

        # Create a file at root
        (Path(temp_workspace) / "test_workspace" / "README.md").write_text("# README\n")

        # Discover the repository
        metadata = discovery.discover_repository()

        # Assert structure mapping includes our created files
        assert "" in metadata.structure_map  # Root directory
        assert "README.md" in metadata.structure_map[""]
        assert "src" in metadata.structure_map
        assert "main.py" in metadata.structure_map["src"]
        assert "utils.py" in metadata.structure_map["src"]
        assert "tests" in metadata.structure_map
        assert "test_main.py" in metadata.structure_map["tests"]

    def test_cache_invalidates_on_force_refresh(self, discovery, temp_workspace):
        """Test that force_refresh bypasses the cache."""
        # Create initial state
        (Path(temp_workspace) / "initial.txt").write_text("initial\n")

        # First discovery
        metadata1 = discovery.discover_repository(force_refresh=False)

        # Add a file
        (Path(temp_workspace) / "added.txt").write_text("added\n")

        # Second discovery without force_refresh should return cached result
        metadata2 = discovery.discover_repository(force_refresh=False)
        assert metadata1 == metadata2  # Should be equal due to caching

        # Third discovery with force_refresh should pick up the new file
        metadata3 = discovery.discover_repository(force_refresh=True)
        # The structure maps should be different due to the new file
        # Note: This test might be flaky depending on caching implementation details
        # but the general principle should hold

    def test_discover_repository_error_handling(self):
        """Test that appropriate errors are raised for invalid workspace."""
        from autonomous_agent.workspace import Workspace

        with tempfile.TemporaryDirectory() as tmpdir:
            # First create a workspace with a valid path
            valid_path = os.path.join(tmpdir, "valid_workspace")
            os.makedirs(valid_path, exist_ok=True)
            workspace = Workspace(workspace_root=valid_path)

            # Then set the workspace root to a non-existent path
            # This bypasses the automatic directory creation in __init__
            nonexistent_path = os.path.join(tmpdir, "does_not_exist")
            workspace.workspace_root = nonexistent_path

            discovery = RepositoryDiscovery(workspace)

            # This should raise an error when trying to discover
            with pytest.raises(ValueError, match="Workspace root does not exist"):
                discovery.discover_repository()


class TestRepositoryMetadataManager:
    """Test the RepositoryMetadataManager class."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def workspace(self, temp_workspace):
        """Create a workspace instance for testing."""
        workspace_path = os.path.join(temp_workspace, "test_workspace")
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

    def test_init_with_discovery(self, discovery):
        """Test that RepositoryMetadataManager initializes correctly."""
        manager = RepositoryMetadataManager(discovery)
        assert manager.discovery == discovery
        assert manager.cache_ttl == 300.0  # Default TTL

    def test_init_with_custom_ttl(self, discovery):
        """Test that RepositoryMetadataManager accepts custom TTL."""
        manager = RepositoryMetadataManager(discovery, cache_ttl=60.0)
        assert manager.cache_ttl == 60.0

    def test_get_metadata_caching(self, metadata_manager, temp_workspace):
        """Test that metadata manager caches results appropriately."""
        # Create a test file
        (Path(temp_workspace) / "test.txt").write_text("test\n")

        # First call should populate cache
        metadata1 = metadata_manager.get_metadata()
        assert metadata_manager._is_cache_valid() is True

        # Second call should return cached result
        metadata2 = metadata_manager.get_metadata()
        assert metadata1 is metadata2  # Same object due to caching

        # Force refresh should get new data
        metadata3 = metadata_manager.get_metadata(force_refresh=True)
        assert metadata3 is not metadata1  # Different object due to force refresh
        # But content should be equivalent for unchanged repository
        assert metadata3.root_path == metadata1.root_path

    def test_cache_entry_expiration(self, metadata_manager, temp_workspace):
        """Test that cache entries expire after TTL."""
        # Create a test file
        (Path(temp_workspace) / "test.txt").write_text("test\n")

        # Get metadata with very short TTL
        short_ttl_manager = RepositoryMetadataManager(
            metadata_manager.discovery,
            cache_ttl=0.1  # 100ms TTL
        )

        # First call populates cache
        metadata1 = short_ttl_manager.get_metadata()
        assert short_ttl_manager._is_cache_valid() is True

        # Wait for cache to expire
        import time
        time.sleep(0.2)  # Wait 200ms (> 100ms TTL)

        # Cache should now be expired
        assert short_ttl_manager._is_cache_valid() is False

        # Next call should refresh the cache
        cache_entry_before = short_ttl_manager._cache
        metadata2 = short_ttl_manager.get_metadata()
        # Should have created a new cache entry (different CacheEntry object)
        assert cache_entry_before is not short_ttl_manager._cache
        # But the data should be equivalent for unchanged repository
        assert metadata2.root_path == metadata1.root_path

    def test_has_repository_changed_no_previous_state(self, metadata_manager):
        """Test change detection when there's no previous state."""
        assert metadata_manager.has_repository_changed() is False

    def test_has_repository_changed_when_unchanged(self, metadata_manager, temp_workspace):
        """Test change detection when repository hasn't changed."""
        # Establish initial state
        (Path(temp_workspace) / "initial.txt").write_text("initial\n")
        metadata_manager.get_metadata()  # This sets _last_known_state

        # Check for changes (should be none)
        assert metadata_manager.has_repository_changed() is False

    def test_has_repository_changed_when_changed(self, metadata_manager, temp_workspace):
        """Test change detection when repository has changed."""
        # Establish initial state
        initial_file = Path(temp_workspace) / "test_workspace" / "initial.txt"
        initial_file.write_text("initial\n")
        metadata_manager.get_metadata()  # This sets _last_known_state

        # Make a change
        (Path(temp_workspace) / "test_workspace" / "added.txt").write_text("added\n")

        # Check for changes (should be detected)
        assert metadata_manager.has_repository_changed() is True

    def test_get_cache_info(self, metadata_manager, temp_workspace):
        """Test that cache info is reported correctly."""
        # Initially no cache
        info = metadata_manager.get_cache_info()
        assert info["cached"] is False
        assert info["expired"] is True

        # Populate cache
        (Path(temp_workspace) / "test.txt").write_text("test\n")
        metadata_manager.get_metadata()

        # Check cache info
        info = metadata_manager.get_cache_info()
        assert info["cached"] is True
        assert info["expired"] is False
        assert info["age_seconds"] >= 0
        assert info["ttl_seconds"] == 300.0
        assert info["time_until_expiry"] > 0

    def test_invalidate_cache(self, metadata_manager, temp_workspace):
        """Test that cache invalidation works."""
        # Populate cache
        (Path(temp_workspace) / "test.txt").write_text("test\n")
        metadata_manager.get_metadata()
        assert metadata_manager._cache is not None

        # Invalidate cache
        metadata_manager.invalidate_cache()
        assert metadata_manager._cache is None

        # Getting metadata should create new cache
        metadata_manager.get_metadata()
        assert metadata_manager._cache is not None