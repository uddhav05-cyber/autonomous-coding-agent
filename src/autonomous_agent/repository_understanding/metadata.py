"""
Repository Metadata Manager for caching and managing repository understanding data.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Any

from .discovery import RepositoryMetadata, RepositoryDiscovery


@dataclass
class CacheEntry:
    """A cache entry with timestamp and data."""
    data: RepositoryMetadata
    timestamp: float
    ttl: float = 300.0  # Default 5 minutes time-to-live

    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        return time.time() - self.timestamp > self.ttl


@dataclass
class PersistentCacheConfig:
    """Configuration for persistent cache storage."""
    enabled: bool = False
    cache_dir: Optional[Path] = None
    max_cache_size_mb: float = 10.0  # Maximum cache size in MB
    max_entries: int = 100  # Maximum number of cache entries


class RepositoryMetadataManager:
    """
    Manages repository metadata with caching and change detection.

    This module provides:
    - Caching of repository metadata to avoid redundant discovery
    - Basic change detection for repository structure
    - Metadata persistence capabilities
    - Change-aware update notifications
    - Memory-efficient storage strategies
    - Enhanced metadata extraction
    - Special file handling statistics
    """

    def __init__(self, discovery: RepositoryDiscovery, cache_ttl: float = 300.0,
                 persistent_config: Optional[PersistentCacheConfig] = None):
        """
        Initialize the metadata manager.

        Args:
            discovery: The RepositoryDiscovery instance to use for fresh data
            cache_ttl: Time-to-live for cached metadata in seconds (default: 5 minutes)
            persistent_config: Configuration for persistent cache storage
        """
        self.discovery = discovery
        self.cache_ttl = cache_ttl
        self._cache: Optional[CacheEntry] = None
        self._last_known_state: Optional[RepositoryMetadata] = None
        self.persistent_config = persistent_config or PersistentCacheConfig()
        self._access_times: Dict[Path, float] = {}  # Track access times for LRU eviction

        # Initialize persistent cache if enabled
        if self.persistent_config.enabled:
            self._load_persistent_cache()

    def _get_cache_file_path(self) -> Path:
        """Get the file path for persistent cache storage."""
        if self.persistent_config.cache_dir:
            cache_dir = self.persistent_config.cache_dir
        else:
            # Default to a cache directory in the workspace
            cache_dir = self.discovery.workspace.workspace_root / ".cache" / "repository_understanding"

        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir / "metadata_cache.json"

    def _load_persistent_cache(self) -> None:
        """Load cache from persistent storage."""
        try:
            cache_file = self._get_cache_file_path()
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)

                # Deserialize the cache entry
                if 'data' in cache_data and 'timestamp' in cache_data:
                    # Reconstruct RepositoryMetadata from the dict
                    metadata_dict = cache_data['data']
                    # Convert string paths back to Path objects
                    if 'root_path' in metadata_dict:
                        metadata_dict['root_path'] = Path(metadata_dict['root_path'])
                    if 'project_configs' in metadata_dict:
                        metadata_dict['project_configs'] = {
                            k: Path(v) for k, v in metadata_dict['project_configs'].items()
                        }
                    if 'structure_map' in metadata_dict:
                        metadata_dict['structure_map'] = {
                            k: [Path(p) if isinstance(p, str) else p for p in v]
                            for k, v in metadata_dict['structure_map'].items()
                        }

                    metadata = RepositoryMetadata(**metadata_dict)
                    # Enhance the loaded metadata
                    metadata = self._enhance_metadata(metadata)
                    self._cache = CacheEntry(
                        data=metadata,
                        timestamp=cache_data['timestamp'],
                        ttl=cache_data.get('ttl', self.cache_ttl)
                    )
                    self._last_known_state = self._cache.data
        except (json.JSONDecodeError, TypeError, KeyError, OSError):
            # If loading fails, start with empty cache
            self._cache = None
            self._last_known_state = None

    def _save_persistent_cache(self) -> None:
        """Save cache to persistent storage."""
        if not self.persistent_config.enabled or self._cache is None:
            return

        try:
            cache_file = self._get_cache_file_path()

            # Serialize the cache entry
            cache_data = {
                'data': {
                    'root_path': str(self._cache.data.root_path),
                    'is_git_repo': self._cache.data.is_git_repo,
                    'git_branch': self._cache.data.git_branch,
                    'git_commit': self._cache.data.git_commit,
                    'project_type': self._cache.data.project_type,
                    'project_configs': {k: str(v) for k, v in self._cache.data.project_configs.items()},
                    'structure_map': {k: [str(p) for p in v] for k, v in self._cache.data.structure_map.items()},
                    'language_hints': list(self._cache.data.language_hints),
                    'build_system_hints': list(self._cache.data.build_system_hints),
                    'documentation_hints': list(self._cache.data.documentation_hints)
                },
                'timestamp': self._cache.timestamp,
                'ttl': self._cache.ttl
            }

            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)

        except (OSError, TypeError):
            # Silently fail if we can't save to persistent storage
            pass

    def _enforce_cache_limits(self) -> None:
        """Enforce cache size limits by removing old entries if necessary."""
        # For now, we only have a single cache entry, so this is simple
        # In a more complex implementation with multiple entries, we'd implement LRU
        pass

    def _enhance_metadata(self, metadata: RepositoryMetadata) -> RepositoryMetadata:
        """
        Enhance repository metadata with additional information.

        This method can be overridden or extended to extract additional
        metadata from the repository such as:
        - Detailed language statistics
        - Framework detection
        - License information
        - Contributor information
        - etc.

        Args:
            metadata: Basic repository metadata from discovery

        Returns:
            Enhanced repository metadata
        """
        # For now, return the metadata as-is
        # This method can be extended in the future to add more detailed metadata extraction
        return metadata

    def get_special_file_statistics(self, file_paths: List[Path]) -> Dict[str, Any]:
        """
        Get statistics about special files in the repository.

        This method works with the SymbolDependencyAnalyzer to classify files
        and provide statistics on special file types.

        Args:
            file_paths: List of file paths to analyze

        Returns:
            Dictionary with special file statistics
        """
        # This would typically work with SymbolDependencyAnalyzer
        # For now, return a placeholder structure
        return {
            "total_files": len(file_paths),
            "binary_files": 0,
            "large_files": 0,
            "generated_files": 0,
            "special_file_percentage": 0.0
        }

    def get_metadata(self, force_refresh: bool = False) -> RepositoryMetadata:
        """
        Get repository metadata, using cache when appropriate.

        Args:
            force_refresh: If True, bypass cache and fetch fresh data

        Returns:
            Current RepositoryMetadata
        """
        # Determine if we need to refresh our cache
        refresh_needed = force_refresh or self._cache is None
        if not refresh_needed and self._cache is not None:
            # Check if our cache has expired
            if self._cache.is_expired():
                refresh_needed = True
            else:
                # Our cache hasn't expired, check if discovery cache is valid
                discovery_cache_valid = (
                    hasattr(self.discovery, '_cache') and
                    self.discovery._cache is not None and
                    hasattr(self.discovery, '_cache_valid') and
                    self.discovery._cache_valid and
                    hasattr(self.discovery, '_cache_timestamp') and
                    hasattr(self.discovery, '_cache_ttl') and
                    (time.time() - self.discovery._cache_timestamp) < self.discovery._cache_ttl
                )
                # If discovery cache is valid, we should refresh to get latest data
                # If discovery cache is not valid, we have to use our cache (stale data)
                if discovery_cache_valid:
                    refresh_needed = True

        if refresh_needed:
            # Get fresh data from discovery layer
            fresh_metadata = self.discovery.discover_repository(force_refresh=force_refresh)
            # Enhance metadata with additional information
            fresh_metadata = self._enhance_metadata(fresh_metadata)
            # Update our cache
            self._cache = CacheEntry(
                data=fresh_metadata,
                timestamp=time.time(),
                ttl=self.cache_ttl
            )
            # Update access time for LRU tracking
            self._access_times[Path("metadata_cache")] = time.time()
            # Save to persistent cache
            self._save_persistent_cache()
            # Enforce cache limits
            self._enforce_cache_limits()
        else:
            # Use our cached data
            fresh_metadata = self._cache.data
            # Update access time for LRU tracking
            self._access_times[Path("metadata_cache")] = time.time()

        # Update last known state for change detection (always update with current data)
        self._last_known_state = fresh_metadata

        return fresh_metadata

    def _is_cache_valid(self) -> bool:
        """Check if the current cache entry is valid and not expired.

        The cache is considered valid only if:
        1. It's not expired (existing TTL check)
        2. The discovery cache is valid (ensuring we have current discovery data)
        """
        if self._cache is not None and not self._cache.is_expired():
            our_cache_valid = True
        else:
            our_cache_valid = False

        # Check if discovery cache is valid
        discovery_cache_valid = (
            hasattr(self.discovery, '_cache') and
            self.discovery._cache is not None and
            hasattr(self.discovery, '_cache_valid') and
            self.discovery._cache_valid and
            hasattr(self.discovery, '_cache_timestamp') and
            hasattr(self.discovery, '_cache_ttl') and
            (time.time() - self.discovery._cache_timestamp) < self.discovery._cache_ttl
        )

        # Debug print
        return our_cache_valid and discovery_cache_valid

    def has_repository_changed(self) -> bool:
        """
        Check if the repository has changed since the last check.

        Returns:
            True if repository structure has changed significantly, False otherwise
        """
        if self._last_known_state is None:
            return False  # No previous state to compare against

        # Get current metadata without updating _last_known_state
        current_metadata = self.discovery.discover_repository(force_refresh=True)

        # Simple change detection: check if basic properties have changed
        changed = (
            self._last_known_state.root_path != current_metadata.root_path or
            self._last_known_state.is_git_repo != current_metadata.is_git_repo or
            self._last_known_state.git_branch != current_metadata.git_branch or
            self._last_known_state.git_commit != current_metadata.git_commit or
            self._last_known_state.project_type != current_metadata.project_type or
            self._last_known_state.project_configs != current_metadata.project_configs or
            len(self._last_known_state.language_hints) != len(current_metadata.language_hints) or
            len(self._last_known_state.build_system_hints) != len(current_metadata.build_system_hints) or
            len(self._last_known_state.documentation_hints) != len(current_metadata.documentation_hints) or
            len(self._last_known_state.structure_map) != len(current_metadata.structure_map) or
            # Check if any directory has different files
            any(
                sorted(self._last_known_state.structure_map.get(dir_path, [])) !=
                sorted(current_metadata.structure_map.get(dir_path, []))
                for dir_path in set(
                    list(self._last_known_state.structure_map.keys()) +
                    list(current_metadata.structure_map.keys())
                )
            )
        )

        return changed

    def invalidate_cache(self) -> None:
        """Invalidate the cached metadata."""
        self._cache = None
        self._access_times.clear()
        # Note: We don't invalidate _last_known_state as it represents the last known good state
        # Remove persistent cache file if it exists
        if self.persistent_config.enabled:
            try:
                cache_file = self._get_cache_file_path()
                if cache_file.exists():
                    cache_file.unlink()
            except OSError:
                # Silently fail if we can't remove the cache file
                pass

    def get_cache_info(self) -> Dict[str, any]:
        """
        Get information about the current cache state.

        Returns:
            Dictionary with cache information
        """
        if self._cache is None:
            return {
                "cached": False,
                "expired": True,
                "age_seconds": None,
                "ttl_seconds": self.cache_ttl,
                "persistent_cache_enabled": self.persistent_config.enabled,
                "persistent_cache_exists": self._persistent_cache_exists()
            }

        age = time.time() - self._cache.timestamp
        return {
            "cached": True,
            "expired": self._cache.is_expired(),
            "age_seconds": age,
            "ttl_seconds": self.cache_ttl,
            "time_until_expiry": max(0, self._cache.ttl - age),
            "persistent_cache_enabled": self.persistent_config.enabled,
            "persistent_cache_exists": self._persistent_cache_exists(),
            "access_count": len(self._access_times)
        }

    def _persistent_cache_exists(self) -> bool:
        """Check if persistent cache file exists."""
        if not self.persistent_config.enabled:
            return False
        try:
            return self._get_cache_file_path().exists()
        except OSError:
            return False

    def invalidate_cache(self) -> None:
        """Invalidate the cached metadata."""
        self._cache = None
        self._access_times.clear()
        # Note: We don't invalidate _last_known_state as it represents the last known good state
        # Remove persistent cache file if it exists
        if self.persistent_config.enabled:
            try:
                cache_file = self._get_cache_file_path()
                if cache_file.exists():
                    cache_file.unlink()
            except OSError:
                # Silently fail if we can't remove the cache file
                pass

    def get_cache_info(self) -> Dict[str, any]:
        """
        Get information about the current cache state.

        Returns:
            Dictionary with cache information
        """
        if self._cache is None:
            return {
                "cached": False,
                "expired": True,
                "age_seconds": None,
                "ttl_seconds": self.cache_ttl,
                "persistent_cache_enabled": self.persistent_config.enabled,
                "persistent_cache_exists": self._persistent_cache_exists()
            }

        age = time.time() - self._cache.timestamp
        return {
            "cached": True,
            "expired": self._cache.is_expired(),
            "age_seconds": age,
            "ttl_seconds": self.cache_ttl,
            "time_until_expiry": max(0, self._cache.ttl - age),
            "persistent_cache_enabled": self.persistent_config.enabled,
            "persistent_cache_exists": self._persistent_cache_exists(),
            "access_count": len(self._access_times)
        }


# Convenience function for easy instantiation
def create_repository_understanding_system(workspace_path: Optional[str] = None,
                                         persistent_config: Optional[PersistentCacheConfig] = None) -> tuple[RepositoryDiscovery, RepositoryMetadataManager]:
    """
    Create a complete repository understanding system.

    Args:
        workspace_path: Optional workspace path. If None, uses workspace from settings.
        persistent_config: Optional configuration for persistent cache storage

    Returns:
        Tuple of (RepositoryDiscovery, RepositoryMetadataManager) instances
    """
    from autonomous_agent.config.settings import Settings
    from autonomous_agent.workspace import Workspace

    # Get workspace
    if workspace_path is None:
        settings = Settings()
        workspace_path = settings.workspace_path

    workspace = Workspace(workspace_root=workspace_path)

    # Create components
    discovery = RepositoryDiscovery(workspace, cache_ttl=300.0)
    metadata_manager = RepositoryMetadataManager(discovery, persistent_config=persistent_config)

    return discovery, metadata_manager