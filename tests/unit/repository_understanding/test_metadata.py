"""
Tests for the Repository Metadata Manager component.
"""
import tempfile
import os
import time
from pathlib import Path
from unittest.mock import Mock, patch

from autonomous_agent.repository_understanding import (
    RepositoryMetadata,
    RepositoryDiscovery,
    RepositoryMetadataManager,
    PersistentCacheConfig,
    create_repository_understanding_system
)


class MockWorkspace:
    """Mock workspace for testing."""
    def __init__(self, root_path):
        self.workspace_root = root_path


class MockDiscovery(RepositoryDiscovery):
    """Mock discovery for testing."""
    def __init__(self, workspace, cache_ttl=300.0):
        # Don't call super().__init__ to avoid needing real workspace
        self.workspace = workspace
        self._cache_ttl = cache_ttl
        self._cache = None  # Will be set when discover_repository is called
        self._cache_valid = False
        self._cache_timestamp = 0

    def discover_repository(self, force_refresh=False):
        """Return mock repository metadata and update cache state."""
        metadata = RepositoryMetadata(
            root_path=Path(self.workspace.workspace_root),
            is_git_repo=True,
            git_branch="main",
            git_commit="abc123",
            project_type="python",
            project_configs={"setup.py": Path(self.workspace.workspace_root) / "setup.py"},
            structure_map={"src": ["main.py", "utils.py"]},
            language_hints={"python"},
            build_system_hints={"setuptools"},
            documentation_hints={"readme.md"}
        )

        # Update cache state to simulate successful discovery
        self._cache = metadata
        self._cache_valid = True
        self._cache_timestamp = time.time()

        return metadata


def test_repository_metadata_manager_init():
    """Test RepositoryMetadataManager initialization."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = MockWorkspace(temp_dir)
        discovery = MockDiscovery(workspace)
        manager = RepositoryMetadataManager(discovery)

        assert manager.discovery == discovery
        assert manager.cache_ttl == 300.0
        assert manager._cache is None
        assert manager._last_known_state is None
        assert isinstance(manager.persistent_config, PersistentCacheConfig)
        assert not manager.persistent_config.enabled


def test_repository_metadata_manager_init_with_persistent_config():
    """Test RepositoryMetadataManager initialization with persistent config."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = MockWorkspace(temp_dir)
        discovery = MockDiscovery(workspace)
        persistent_config = PersistentCacheConfig(
            enabled=True,
            cache_dir=Path(temp_dir) / "cache",
            max_cache_size_mb=5.0,
            max_entries=50
        )
        manager = RepositoryMetadataManager(discovery, persistent_config=persistent_config)

        assert manager.persistent_config.enabled == True
        assert manager.persistent_config.cache_dir == Path(temp_dir) / "cache"
        assert manager.persistent_config.max_cache_size_mb == 5.0
        assert manager.persistent_config.max_entries == 50


def test_get_metadata_basic():
    """Test getting repository metadata."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = MockWorkspace(temp_dir)
        discovery = MockDiscovery(workspace)
        manager = RepositoryMetadataManager(discovery)

        # Get metadata
        metadata = manager.get_metadata()

        assert isinstance(metadata, RepositoryMetadata)
        assert metadata.root_path == Path(temp_dir)
        assert metadata.is_git_repo == True
        assert metadata.git_branch == "main"
        assert metadata.git_commit == "abc123"
        assert metadata.project_type == "python"
        assert "setup.py" in metadata.project_configs
        assert "src" in metadata.structure_map
        assert "python" in metadata.language_hints
        assert "setuptools" in metadata.build_system_hints
        assert "readme.md" in metadata.documentation_hints


def test_get_metadata_caching():
    """Test that caching works correctly."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = MockWorkspace(temp_dir)
        discovery = MockDiscovery(workspace)
        manager = RepositoryMetadataManager(discovery)

        # Get metadata first time
        metadata1 = manager.get_metadata()
        assert manager._cache is not None

        # Get metadata second time (should use cache)
        metadata2 = manager.get_metadata()
        assert metadata2 == metadata1
        # Should be the same cache entry
        assert manager._cache is not None
        assert manager._cache.data == metadata1


def test_get_metadata_force_refresh():
    """Test force refresh bypasses cache."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = MockWorkspace(temp_dir)
        discovery = MockDiscovery(workspace)
        manager = RepositoryMetadataManager(discovery)

        # Get metadata first time
        metadata1 = manager.get_metadata()
        assert manager._cache is not None

        # Force refresh should get new data
        metadata2 = manager.get_metadata(force_refresh=True)
        assert metadata2 == metadata1  # Same content because mock returns same data
        # But cache should have been updated (new timestamp)
        assert manager._cache is not None
        assert manager._cache.data == metadata1


def test_is_cache_valid():
    """Test cache validity checking."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = MockWorkspace(temp_dir)
        discovery = MockDiscovery(workspace)
        manager = RepositoryMetadataManager(discovery)

        # Initially cache is None, so not valid
        assert not manager._is_cache_valid()

        # After getting metadata, cache should be valid
        manager.get_metadata()
        assert manager._is_cache_valid()


def test_has_repository_changed():
    """Test change detection."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = MockWorkspace(temp_dir)
        discovery = MockDiscovery(workspace)
        manager = RepositoryMetadataManager(discovery)

        # Initially no change (no previous state)
        assert not manager.has_repository_changed()

        # Get metadata to establish baseline
        manager.get_metadata()
        # Should still report no change (same state)
        assert not manager.has_repository_changed()


def test_invalidate_cache():
    """Test cache invalidation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = MockWorkspace(temp_dir)
        discovery = MockDiscovery(workspace)
        manager = RepositoryMetadataManager(discovery)

        # Get metadata to populate cache
        manager.get_metadata()
        assert manager._cache is not None

        # Invalidate cache
        manager.invalidate_cache()
        assert manager._cache is None


def test_get_cache_info():
    """Test getting cache information."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = MockWorkspace(temp_dir)
        discovery = MockDiscovery(workspace)
        manager = RepositoryMetadataManager(discovery)

        # Check info when cache is empty
        info = manager.get_cache_info()
        assert info["cached"] == False
        assert info["expired"] == True
        assert info["age_seconds"] is None
        assert info["ttl_seconds"] == 300.0

        # Get metadata to populate cache
        manager.get_metadata()
        info = manager.get_cache_info()
        assert info["cached"] == True
        assert info["expired"] == False
        assert info["age_seconds"] >= 0
        assert info["ttl_seconds"] == 300.0
        assert "time_until_expiry" in info


def test_create_repository_understanding_system():
    """Test the convenience function."""
    with tempfile.TemporaryDirectory() as temp_dir:
        discovery, manager = create_repository_understanding_system(temp_dir)

        assert isinstance(discovery, RepositoryDiscovery)
        assert isinstance(manager, RepositoryMetadataManager)
        assert manager.discovery == discovery


def test_create_repository_understanding_system_with_persistent_config():
    """Test the convenience function with persistent config."""
    with tempfile.TemporaryDirectory() as temp_dir:
        persistent_config = PersistentCacheConfig(
            enabled=True,
            max_cache_size_mb=5.0
        )
        discovery, manager = create_repository_understanding_system(
            temp_dir,
            persistent_config=persistent_config
        )

        assert isinstance(discovery, RepositoryDiscovery)
        assert isinstance(manager, RepositoryMetadataManager)
        assert manager.persistent_config.enabled == True
        assert manager.persistent_config.max_cache_size_mb == 5.0


def test_enhance_metadata():
    """Test metadata enhancement (placeholder)."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = MockWorkspace(temp_dir)
        discovery = MockDiscovery(workspace)
        manager = RepositoryMetadataManager(discovery)

        # Create basic metadata
        metadata = RepositoryMetadata(
            root_path=Path(temp_dir),
            is_git_repo=False,
            project_type="unknown"
        )

        # Enhance metadata (should return same for now)
        enhanced = manager._enhance_metadata(metadata)
        assert enhanced == metadata


def test_get_special_file_statistics():
    """Test special file statistics (placeholder)."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = MockWorkspace(temp_dir)
        discovery = MockDiscovery(workspace)
        manager = RepositoryMetadataManager(discovery)

        # Create some mock file paths
        file_paths = [
            Path(temp_dir) / "file1.py",
            Path(temp_dir) / "file2.py",
            Path(temp_dir) / "file3.txt"
        ]

        stats = manager.get_special_file_statistics(file_paths)
        assert isinstance(stats, dict)
        assert "total_files" in stats
        assert stats["total_files"] == 3
        assert "binary_files" in stats
        assert "large_files" in stats
        assert "generated_files" in stats
        assert "special_file_percentage" in stats


def test_persistent_cache_disabled_by_default():
    """Test that persistent cache is disabled by default."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = MockWorkspace(temp_dir)
        discovery = MockDiscovery(workspace)
        manager = RepositoryMetadataManager(discovery)

        assert not manager.persistent_config.enabled


def test_persistent_cache_enable():
    """Test enabling persistent cache."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = MockWorkspace(temp_dir)
        discovery = MockDiscovery(workspace)
        persistent_config = PersistentCacheConfig(enabled=True)
        manager = RepositoryMetadataManager(discovery, persistent_config=persistent_config)

        assert manager.persistent_config.enabled == True


if __name__ == "__main__":
    test_repository_metadata_manager_init()
    test_repository_metadata_manager_init_with_persistent_config()
    test_get_metadata_basic()
    test_get_metadata_caching()
    test_get_metadata_force_refresh()
    test_is_cache_valid()
    test_has_repository_changed()
    test_invalidate_cache()
    test_get_cache_info()
    test_create_repository_understanding_system()
    test_create_repository_understanding_system_with_persistent_config()
    test_enhance_metadata()
    test_get_special_file_statistics()
    test_persistent_cache_disabled_by_default()
    test_persistent_cache_enable()
    print("All tests passed!")