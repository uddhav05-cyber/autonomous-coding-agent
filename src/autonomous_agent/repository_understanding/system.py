"""
Integrated Repository Understanding System for Autonomous Coding Agent.

This module provides the main RepositoryUnderstandingSystem class that integrates
all five components of the repository understanding system:
1. Repository Discovery
2. Metadata Management
3. Relevance Engine
4. Code Search
5. Symbol and Dependency Analysis

The system provides a unified interface for repository understanding operations
while maintaining workspace boundary enforcement and security.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field

from .discovery import RepositoryDiscovery, RepositoryMetadata
from .metadata import RepositoryMetadataManager, PersistentCacheConfig
from .relevance import RelevanceEngine, RelevanceSignals
from .search import CodeSearchModule, SearchResult
from .symbol_analyzer import (
    SymbolDependencyAnalyzer,
    Symbol,
    DependencyEdge,
    SpecialFileClassification
)
from autonomous_agent.workspace import Workspace


@dataclass
class RepositoryUnderstandingResult:
    """Result of a complete repository understanding operation."""
    # Discovery results
    metadata: RepositoryMetadata

    # Relevance results
    relevance_scores: Dict[Path, float] = field(default_factory=dict)
    top_relevant_files: List[Tuple[Path, float]] = field(default_factory=list)

    # Search results
    search_results: List[SearchResult] = field(default_factory=list)

    # Symbol and dependency results
    symbols: Dict[Path, List[Symbol]] = field(default_factory=dict)
    dependencies: Dict[Path, List[DependencyEdge]] = field(default_factory=dict)
    special_files: Dict[Path, SpecialFileClassification] = field(default_factory=dict)

    # System metadata
    timestamp: float = field(default_factory=time.time)
    operation_time: float = 0.0  # Time taken to perform the understanding operation


class RepositoryUnderstandingSystem:
    """
    Integrated Repository Understanding System.

    This class combines all five repository understanding components into a
    cohesive system that provides:
    - Workspace boundary enforcement and security
    - Integrated repository discovery, metadata management, relevance scoring,
      code search, and symbol/dependency analysis
    - Caching and performance optimizations
    - Change detection and notification capabilities
    - Proper error handling and graceful degradation
    """

    def __init__(
        self,
        workspace: Workspace,
        discovery_cache_ttl: float = 300.0,
        metadata_persistent_config: Optional[PersistentCacheConfig] = None,
        enable_incremental_updates: bool = True,
        change_notification_callback: Optional[Callable[[bool], None]] = None
    ):
        """
        Initialize the integrated repository understanding system.

        Args:
            workspace: The workspace instance to operate within
            discovery_cache_ttl: Time-to-live for discovery cache in seconds
            metadata_persistent_config: Configuration for persistent metadata cache
            enable_incremental_updates: Whether to enable incremental updates
            change_notification_callback: Callback function to notify of repository changes
        """
        self.workspace = workspace
        self.enable_incremental_updates = enable_incremental_updates
        self.change_notification_callback = change_notification_callback
        self._last_known_state: Optional[RepositoryMetadata] = None
        self._last_understanding_result: Optional[RepositoryUnderstandingResult] = None

        # Initialize all five components
        self.discovery = RepositoryDiscovery(workspace, cache_ttl=discovery_cache_ttl)
        self.metadata_manager = RepositoryMetadataManager(
            self.discovery,
            persistent_config=metadata_persistent_config
        )
        self.relevance_engine = RelevanceEngine(workspace)
        self.search_module = CodeSearchModule(workspace)
        self.symbol_analyzer = SymbolDependencyAnalyzer(workspace)

        # Performance optimization caches
        self._relevance_cache: Dict[Tuple[str, str], Dict[Path, float]] = {}  # (task_query, metadata_hash) -> scores
        self._search_cache: Dict[Tuple[str, str], List[SearchResult]] = {}  # (query, file_hash) -> results
        self._max_cache_size = 100  # Maximum entries in performance caches

        # Track last notification state to avoid spam
        self._last_change_notification_time = 0.0
        self._change_notification_cooldown = 5.0  # seconds between notifications

    def understand_repository(
        self,
        task_query: Optional[str] = None,
        search_query: Optional[str] = None,
        force_refresh: bool = False
    ) -> RepositoryUnderstandingResult:
        """
        Perform a complete repository understanding operation.

        This method integrates all five components to provide a comprehensive
        understanding of the repository relevant to the given task.

        Args:
            task_query: Optional task description to calculate relevance against
            search_query: Optional search query to execute for code search
            force_refresh: If True, bypass all caches and perform fresh discovery

        Returns:
            RepositoryUnderstandingResult containing all understanding data
        """
        start_time = time.time()

        # Check if we should check for changes (unless forcing refresh)
        repository_changed = False
        if not force_refresh and self._last_known_state is not None:
            repository_changed = self.metadata_manager.has_repository_changed()

            # Notify of changes if callback is provided and cooldown has passed
            if (repository_changed and
                self.change_notification_callback and
                time.time() - self._last_change_notification_time > self._change_notification_cooldown):
                try:
                    self.change_notification_callback(True)
                    self._last_change_notification_time = time.time()
                except Exception:
                    # Don't let callback errors break the system
                    pass

        # Get repository metadata (this may trigger discovery)
        metadata = self.metadata_manager.get_metadata(force_refresh=force_refresh)

        # Check if we actually got new data (important for caching decisions)
        metadata_changed = (
            self._last_known_state is None or
            metadata.root_path != self._last_known_state.root_path or
            metadata.git_commit != self._last_known_state.git_commit
        )

        # Update last known state
        self._last_known_state = metadata

        # Initialize result object
        result = RepositoryUnderstandingResult(metadata=metadata)

        try:
            # Step 1: Calculate relevance scores (if task query provided)
            if task_query:
                result.relevance_scores = self._calculate_relevance_scores(
                    task_query, metadata, force_refresh
                )
                # Get top relevant files
                result.top_relevant_files = self.relevance_engine.get_top_files(
                    result.relevance_scores, limit=20, threshold=0.1
                )

            # Step 2: Perform code search (if search query provided)
            if search_query:
                # Determine which files to search (top relevant files if available, else all files)
                files_to_search = self._get_files_for_search(
                    metadata,
                    result.top_relevant_files if task_query else None
                )
                result.search_results = self._perform_code_search(
                    search_query, files_to_search, force_refresh
                )

            # Step 3: Extract symbols and dependencies
            files_for_analysis = self._get_files_for_analysis(metadata, result.top_relevant_files if task_query else None)
            result.symbols = self._extract_symbols(files_for_analysis, force_refresh)
            result.dependencies = self._extract_dependencies(files_for_analysis, force_refresh)
            result.special_files = self._classify_special_files(files_for_analysis, force_refresh)

        except Exception as e:
            # In case of errors, we still return what we have so far
            # This ensures graceful degradation
            pass

        # Calculate operation time
        result.operation_time = time.time() - start_time

        # Cache the result for potential incremental updates
        self._last_understanding_result = result

        return result

    def _calculate_relevance_scores(
        self,
        task_query: str,
        metadata: RepositoryMetadata,
        force_refresh: bool
    ) -> Dict[Path, float]:
        """Calculate relevance scores with caching."""
        # Create a cache key based on task query and metadata hash
        metadata_hash = str(hash((
            str(metadata.root_path),
            metadata.git_commit,
            str(sorted(metadata.project_configs.items())) if metadata.project_configs else "",
            str(sorted(metadata.language_hints)),
            str(sorted(metadata.build_system_hints)),
            str(sorted(metadata.documentation_hints))
        )))

        cache_key = (task_query, metadata_hash)

        # Check cache unless forcing refresh
        if not force_refresh and cache_key in self._relevance_cache:
            return self._relevance_cache[cache_key]

        # Calculate fresh scores
        scores = self.relevance_engine.calculate_relevance_scores(task_query, metadata)

        # Cache the result
        self._cache_relevance_scores(cache_key, scores)

        return scores

    def _get_files_for_search(
        self,
        metadata: RepositoryMetadata,
        top_relevant_files: Optional[List[Tuple[Path, float]]]
    ) -> List[Path]:
        """Determine which files to search based on relevance or fallback to all files."""
        if top_relevant_files:
            # Search top relevant files plus some additional files for breadth
            file_paths = [path for path, _ in top_relevant_files[:10]]  # Top 10

            # Add some additional files from the repository for discovery
            all_files = self._get_all_files_from_metadata(metadata)
            # Add files that aren't already in our top list
            top_file_set = set(path for path, _ in top_relevant_files)
            additional_files = [
                f for f in all_files[:20]  # First 20 files
                if f not in top_file_set
            ][:5]  # Add up to 5 additional files

            file_paths.extend(additional_files)
            return file_paths
        else:
            # If no relevance scoring, search all files (but limit for performance)
            all_files = self._get_all_files_from_metadata(metadata)
            # Limit to reasonable number for search performance
            return all_files[:50]  # Search first 50 files

    def _get_files_for_analysis(
        self,
        metadata: RepositoryMetadata,
        top_relevant_files: Optional[List[Tuple[Path, float]]]
    ) -> List[Path]:
        """Determine which files to analyze for symbols, dependencies, and special files."""
        if top_relevant_files:
            # Analyze top relevant files
            return [path for path, _ in top_relevant_files[:20]]  # Top 20 for analysis
        else:
            # If no relevance scoring, analyze all files (but limit for performance)
            all_files = self._get_all_files_from_metadata(metadata)
            return all_files[:30]  # Analyze first 30 files

    def _get_all_files_from_metadata(self, metadata: RepositoryMetadata) -> List[Path]:
        """Extract all file paths from repository metadata structure map."""
        files = []
        root_path = metadata.root_path

        for dir_path, file_names in metadata.structure_map.items():
            if dir_path == "":
                # Root directory
                dir_abs_path = root_path
            else:
                dir_abs_path = root_path / dir_path

            for file_name in file_names:
                file_path = dir_abs_path / file_name
                if file_path.is_file():
                    files.append(file_path.resolve())

        return files

    def _perform_code_search(
        self,
        search_query: str,
        file_paths: List[Path],
        force_refresh: bool
    ) -> List[SearchResult]:
        """Perform code search with caching."""
        # Create a cache key based on search query and file list hash
        # We hash the file paths to avoid huge cache keys
        file_hash = str(hash(tuple(sorted([str(p) for p in file_paths]))))
        cache_key = (search_query, file_hash)

        # Check cache unless forcing refresh
        if not force_refresh and cache_key in self._search_cache:
            return self._search_cache[cache_key]

        # Perform fresh search
        results = self.search_module.execute_search(
            query=search_query,
            file_paths=file_paths,
            context_lines=2
        )

        # Cache the result
        self._cache_search_results(cache_key, results)

        return results

    def _extract_symbols(
        self,
        file_paths: List[Path],
        force_refresh: bool
    ) -> Dict[Path, List[Symbol]]:
        """Extract symbols from files with caching."""
        symbols = {}

        for file_path in file_paths:
            # Skip if not within workspace (shouldn't happen, but safety check)
            if not self._is_within_workspace(file_path):
                continue

            # Check cache unless forcing refresh
            if not force_refresh and file_path in self.symbol_analyzer._symbol_cache:
                symbols[file_path] = self.symbol_analyzer._symbol_cache[file_path]
            else:
                # Extract fresh symbols
                file_symbols = self.symbol_analyzer.analyze_file_symbols(file_path)
                symbols[file_path] = file_symbols
                # The analyzer caches internally, so we don't need to cache here

        return symbols

    def _extract_dependencies(
        self,
        file_paths: List[Path],
        force_refresh: bool
    ) -> Dict[Path, List[DependencyEdge]]:
        """Extract dependencies from files with caching."""
        dependencies = {}

        for file_path in file_paths:
            # Skip if not within workspace (shouldn't happen, but safety check)
            if not self._is_within_workspace(file_path):
                continue

            # Check cache unless forcing refresh
            if not force_refresh and file_path in self.symbol_analyzer._dependency_cache:
                dependencies[file_path] = self.symbol_analyzer._dependency_cache[file_path]
            else:
                # Extract fresh dependencies
                file_dependencies = self.symbol_analyzer.analyze_file_dependencies(file_path)
                dependencies[file_path] = file_dependencies
                # The analyzer caches internally

        return dependencies

    def _classify_special_files(
        self,
        file_paths: List[Path],
        force_refresh: bool
    ) -> Dict[Path, SpecialFileClassification]:
        """Classify special files with caching."""
        special_files = {}

        for file_path in file_paths:
            # Skip if not within workspace (shouldn't happen, but safety check)
            if not self._is_within_workspace(file_path):
                continue

            # Check cache unless forcing refresh
            if not force_refresh and file_path in self.symbol_analyzer._special_file_cache:
                special_files[file_path] = self.symbol_analyzer._special_file_cache[file_path]
            else:
                # Classify fresh
                classification = self.symbol_analyzer.classify_special_file(file_path)
                special_files[file_path] = classification
                # The analyzer caches internally

        return special_files

    def _is_within_workspace(self, file_path: Path) -> bool:
        """Check if a file path is within the workspace boundaries."""
        try:
            if isinstance(file_path, str):
                file_path = Path(file_path)
            resolved_file = file_path.resolve()
            resolved_workspace = Path(self.workspace.workspace_root).resolve()
            return resolved_workspace in resolved_file.parents or resolved_file == resolved_workspace
        except (OSError, ValueError):
            return False

    def _cache_relevance_scores(self, key: Tuple[str, str], scores: Dict[Path, float]) -> None:
        """Cache relevance scores with LRU eviction."""
        self._relevance_cache[key] = scores

        # Evict oldest entries if cache is too large
        if len(self._relevance_cache) > self._max_cache_size:
            # Remove the oldest entry (simple FIFO for now)
            oldest_key = next(iter(self._relevance_cache))
            del self._relevance_cache[oldest_key]

    def _cache_search_results(self, key: Tuple[str, str], results: List[SearchResult]) -> None:
        """Cache search results with LRU eviction."""
        self._search_cache[key] = results

        # Evict oldest entries if cache is too large
        if len(self._search_cache) > self._max_cache_size:
            # Remove the oldest entry (simple FIFO for now)
            oldest_key = next(iter(self._search_cache))
            del self._search_cache[oldest_key]

    def get_cached_understanding(self) -> Optional[RepositoryUnderstandingResult]:
        """
        Get the last understanding result if available.

        Returns:
            Cached RepositoryUnderstandingResult or None if not available
        """
        return self._last_understanding_result

    def invalidate_all_caches(self) -> None:
        """Invalidate all caches in the system."""
        self.metadata_manager.invalidate_cache()
        self.symbol_analyzer.clear_cache()
        self._relevance_cache.clear()
        self._search_cache.clear()
        self._last_understanding_result = None
        self._last_known_state = None

    def get_system_info(self) -> Dict[str, Any]:
        """
        Get information about the system and its components.

        Returns:
            Dictionary containing system information
        """
        return {
            "workspace_root": self.workspace.workspace_root,
            "discovery_cache_valid": self.discovery.is_cache_valid(),
            "metadata_cache_info": self.metadata_manager.get_cache_info(),
            "relevance_cache_size": len(self._relevance_cache),
            "search_cache_size": len(self._search_cache),
            "symbol_cache_size": len(self.symbol_analyzer._symbol_cache),
            "dependency_cache_size": len(self.symbol_analyzer._dependency_cache),
            "special_file_cache_size": len(self.symbol_analyzer._special_file_cache),
            "incremental_updates_enabled": self.enable_incremental_updates,
            "has_change_callback": self.change_notification_callback is not None
        }


# Convenience function for easy instantiation
def create_repository_understanding_system(
    workspace_path: Optional[str] = None,
    discovery_cache_ttl: float = 300.0,
    metadata_persistent_config: Optional[PersistentCacheConfig] = None,
    enable_incremental_updates: bool = True,
    change_notification_callback: Optional[Callable[[bool], None]] = None
) -> tuple[Workspace, RepositoryUnderstandingSystem]:
    """
    Create a complete repository understanding system with workspace.

    Args:
        workspace_path: Optional workspace path. If None, uses workspace from settings.
        discovery_cache_ttl: Time-to-live for discovery cache in seconds
        metadata_persistent_config: Configuration for persistent metadata cache
        enable_incremental_updates: Whether to enable incremental updates
        change_notification_callback: Callback function to notify of repository changes

    Returns:
        Tuple of (Workspace, RepositoryUnderstandingSystem) instances
    """
    from autonomous_agent.config.settings import Settings
    from autonomous_agent.workspace import Workspace

    # Get workspace
    if workspace_path is None:
        settings = Settings()
        workspace_path = settings.workspace_path

    workspace = Workspace(workspace_root=workspace_path)

    # Create the integrated system
    system = RepositoryUnderstandingSystem(
        workspace=workspace,
        discovery_cache_ttl=discovery_cache_ttl,
        metadata_persistent_config=metadata_persistent_config,
        enable_incremental_updates=enable_incremental_updates,
        change_notification_callback=change_notification_callback
    )

    return workspace, system