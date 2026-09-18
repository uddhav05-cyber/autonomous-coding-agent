"""
Repository Understanding module for Autonomous Coding Agent.

This module provides repository discovery, metadata management, relevance scoring,
code search, and symbol and dependency analysis capabilities for the autonomous
coding agent, enabling it to understand repository structure, identify relevant
files, perform efficient code search, extract symbols and dependencies, and
operate within workspace boundaries.
"""

from .discovery import RepositoryDiscovery, RepositoryMetadata
from .metadata import (
    PersistentCacheConfig,
    RepositoryMetadataManager,
    create_repository_understanding_system,
)
from .relevance import RelevanceEngine, RelevanceSignals
from .search import CodeSearchModule, SearchResult
from .symbol_analyzer import (
    DependencyEdge,
    SpecialFileClassification,
    Symbol,
    SymbolDependencyAnalyzer,
    create_symbol_dependency_analyzer,
)
from .system import RepositoryUnderstandingSystem

# Expose RelevanceWeights at module level for backward compatibility
RelevanceWeights = RelevanceEngine.RelevanceWeights

__all__ = [
    "CodeSearchModule",
    "DependencyEdge",
    "PersistentCacheConfig",
    "RelevanceEngine",
    "RelevanceSignals",
    "RelevanceWeights",
    "RepositoryDiscovery",
    "RepositoryMetadata",
    "RepositoryMetadataManager",
    "RepositoryUnderstandingSystem",
    "SearchResult",
    "SpecialFileClassification",
    "Symbol",
    "SymbolDependencyAnalyzer",
    "create_repository_understanding_system",
    "create_symbol_dependency_analyzer",
]