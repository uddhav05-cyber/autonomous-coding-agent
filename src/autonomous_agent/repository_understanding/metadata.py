"""
Repository Metadata Manager for caching and managing repository understanding data.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

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


class RepositoryMetadataManager:
    """
    Manages repository metadata with caching and change detection.

    This module provides:
    - Caching of repository metadata to avoid redundant discovery
    - Basic change detection for repository structure
    - Metadata persistence capabilities
    - Change-aware update notifications
    """

    def __init__(self, discovery: RepositoryDiscovery, cache_ttl: float = 300.0):
        """
        Initialize the metadata manager.

        Args:
            discovery: The RepositoryDiscovery instance to use for fresh data
            cache_ttl: Time-to-live for cached metadata in seconds (default: 5 minutes)
        """
        self.discovery = discovery
        self.cache_ttl = cache_ttl
        self._cache: Optional[CacheEntry] = None
        self._last_known_state: Optional[RepositoryMetadata] = None

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
            # Update our cache
            self._cache = CacheEntry(
                data=fresh_metadata,
                timestamp=time.time(),
                ttl=self.cache_ttl
            )
        else:
            # Use our cached data
            fresh_metadata = self._cache.data

        # Update last known state for change detection (always update with current data)
        self._last_known_state = fresh_metadata

        return fresh_metadata

    def _is_cache_valid(self) -> bool:
        """Check if the current cache entry is valid and not expired.

        The cache is considered valid only if:
        1. It's not expired (existing TTL check)
        2. The discovery cache is valid (ensuring we have current discovery data)
        """
        # Check if our cache is not expired and exists
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
        # Note: We don't invalidate _last_known_state as it represents the last known good state

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
                "ttl_seconds": self.cache_ttl
            }

        age = time.time() - self._cache.timestamp
        return {
            "cached": True,
            "expired": self._cache.is_expired(),
            "age_seconds": age,
            "ttl_seconds": self.cache_ttl,
            "time_until_expiry": max(0, self._cache.ttl - age)
        }


# Convenience function for easy instantiation
def create_repository_understanding_system(workspace_path: Optional[str] = None) -> tuple[RepositoryDiscovery, RepositoryMetadataManager]:
    """
    Create a complete repository understanding system.

    Args:
        workspace_path: Optional workspace path. If None, uses workspace from settings.

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
    metadata_manager = RepositoryMetadataManager(discovery)

    return discovery, metadata_manager