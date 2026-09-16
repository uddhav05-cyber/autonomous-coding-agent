"""
Repository Understanding module for Autonomous Coding Agent.

This module provides repository discovery and metadata management capabilities
for the autonomous coding agent, enabling it to understand repository structure,
identify relevant files, and operate within workspace boundaries.
"""

from .discovery import RepositoryDiscovery, RepositoryMetadata
from .metadata import RepositoryMetadataManager, create_repository_understanding_system

__all__ = [
    "RepositoryDiscovery",
    "RepositoryMetadata",
    "RepositoryMetadataManager",
    "create_repository_understanding_system",
]