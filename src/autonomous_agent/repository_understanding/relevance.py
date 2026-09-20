"""
Relevance Engine for scoring file relevance based on multiple signals.
"""
from __future__ import annotations

import math
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import Counter, defaultdict

from .discovery import RepositoryMetadata
from autonomous_agent.workspace import Workspace


@dataclass
class RelevanceSignals:
    """Individual relevance signals for a file."""
    path_similarity: float = 0.0
    name_pattern: float = 0.0
    content_keyword: float = 0.0
    dependency: float = 0.0
    modification_history: float = 0.0
    file_type: float = 0.0
    size_inversion: float = 0.0
    composite: float = 0.0


class RelevanceEngine:
    """
    Calculates file relevance scores using multiple signals.

    Implements a weighted scoring system combining:
    - Path Similarity Score: Based on directory proximity to task-related paths
    - Name Pattern Score: Filename matches to task terminology
    - Content Keyword Score: Occurrence of task-domain terms in file contents
    - Dependency Score: Centrality in import/export chains
    - Modification History Score: Based on git activity and recent changes
    - File Type Score: Preferences for certain extensions
    - Size Inversion Score: Preference for smaller, focused files
    """

    @dataclass
    class RelevanceWeights:
        """Weights for combining relevance signals."""
        path_similarity: float = 0.20
        name_pattern: float = 0.15
        content_keyword: float = 0.25
        dependency: float = 0.15
        modification_history: float = 0.10
        file_type: float = 0.10
        size_inversion: float = 0.05

        def normalize(self) -> None:
            """Normalize weights to sum to 1.0."""
            total = (
                self.path_similarity +
                self.name_pattern +
                self.content_keyword +
                self.dependency +
                self.modification_history +
                self.file_type +
                self.size_inversion
            )
            if total > 0:
                self.path_similarity /= total
                self.name_pattern /= total
                self.content_keyword /= total
                self.dependency /= total
                self.modification_history /= total
                self.file_type /= total
                self.size_inversion /= total
    """
    Calculates file relevance scores using multiple signals.

    Implements a weighted scoring system combining:
    - Path Similarity Score: Based on directory proximity to task-related paths
    - Name Pattern Score: Filename matches to task terminology
    - Content Keyword Score: Occurrence of task-domain terms in file contents
    - Dependency Score: Centrality in import/export chains
    - Modification History Score: Based on git activity and recent changes
    - File Type Score: Preferences for certain extensions
    - Size Inversion Score: Preference for smaller, focused files
    """

    def __init__(self, workspace: Workspace):
        """
        Initialize the relevance engine.

        Args:
            workspace: The workspace instance to operate within
        """
        self.workspace = workspace
        self.weights = self.RelevanceWeights()
        self._file_cache: Dict[Path, str] = {}  # Cache for file contents
        self._dependency_cache: Dict[Path, Set[Path]] = {}  # Cache for dependencies

    def calculate_relevance_scores(
        self,
        task_query: str,
        metadata: RepositoryMetadata
    ) -> Dict[Path, float]:
        """
        Calculate relevance scores for all files in the repository.

        Args:
            task_query: The task description to calculate relevance against
            metadata: Repository metadata from discovery module

        Returns:
            Dictionary mapping file paths to relevance scores (0.0-1.0)
        """
        # Extract task terms from the query
        task_terms = self._extract_task_terms(task_query)

        # Get all files in the repository
        all_files = self._get_all_files(metadata)

        # Calculate scores for each file
        scores = {}
        for file_path in all_files:
            signals = self._calculate_file_signals(
                file_path, task_terms, task_query, metadata
            )
            composite_score = self._calculate_composite_score(signals)
            signals.composite = composite_score
            scores[file_path] = composite_score

        return scores

    def _extract_task_terms(self, task_query: str) -> List[str]:
        """
        Extract meaningful terms from the task query.

        Args:
            task_query: The task description

        Returns:
            List of extracted terms
        """
        # Convert to lowercase and split by non-alphanumeric characters
        terms = re.findall(r'\b[a-zA-Z][a-zA-Z0-9_]*\b', task_query.lower())

        # Filter out common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'
        }

        return [term for term in terms if term not in stop_words and len(term) > 2]

    def _get_all_files(self, metadata: RepositoryMetadata) -> List[Path]:
        """
        Get all files in the repository from the structure map.

        Args:
            metadata: Repository metadata containing structure map

        Returns:
            List of absolute file paths
        """
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

    def _calculate_file_signals(
        self,
        file_path: Path,
        task_terms: List[str],
        task_query: str,
        metadata: RepositoryMetadata
    ) -> RelevanceSignals:
        """
        Calculate all relevance signals for a single file.

        Args:
            file_path: Path to the file to score
            task_terms: Extracted terms from task query
            task_query: Original task query string
            metadata: Repository metadata

        Returns:
            RelevanceSignals object containing all signal scores
        """
        signals = RelevanceSignals()

        # Calculate each signal
        signals.path_similarity = self._calculate_path_similarity(
            file_path, task_terms, metadata
        )
        signals.name_pattern = self._calculate_name_pattern(
            file_path, task_terms
        )
        signals.content_keyword = self._calculate_content_keyword(
            file_path, task_terms, task_query
        )
        signals.dependency = self._calculate_dependency(
            file_path, metadata
        )
        signals.modification_history = self._calculate_modification_history(
            file_path
        )
        signals.file_type = self._calculate_file_type(
            file_path, task_terms
        )
        signals.size_inversion = self._calculate_size_inversion(
            file_path
        )

        return signals

    def _calculate_path_similarity(
        self,
        file_path: Path,
        task_terms: List[str],
        metadata: RepositoryMetadata
    ) -> float:
        """
        Calculate path similarity score based on directory proximity to task-related paths.

        Args:
            file_path: Path to the file
            task_terms: Task terms to match against path
            metadata: Repository metadata

        Returns:
            Score between 0.0 and 1.0
        """
        if not task_terms:
            return 0.5  # Neutral score when no task terms

        # Handle case where metadata is None (for testing)
        if metadata is None:
            # For testing purposes, use the file path directly
            # We'll consider the path relative to the file's parent directory's parent
            # This is a simplified approach for testing
            try:
                # Go up two levels to get a reasonable test root
                test_root = file_path.parent.parent
                relative_path = file_path.relative_to(test_root)
            except ValueError:
                # Fallback to using the file name only
                relative_path = Path(file_path.name)
        else:
            # Get relative path from repository root
            try:
                relative_path = file_path.relative_to(metadata.root_path)
            except ValueError:
                # File is outside repository (shouldn't happen with proper filtering)
                return 0.0

        # Convert path to lowercase string for matching
        path_str = str(relative_path).lower()
        path_parts = path_str.split('/')

        # Check for term matches in path components
        matches = 0
        total_terms = len(task_terms)

        for term in task_terms:
            # Check if term appears in any path component
            for part in path_parts:
                if term in part:
                    matches += 1
                    break  # Count each term only once

        # Normalize by number of terms
        if total_terms > 0:
            return min(matches / total_terms, 1.0)
        return 0.0

    def _calculate_name_pattern(
        self,
        file_path: Path,
        task_terms: List[str]
    ) -> float:
        """
        Calculate name pattern score based on filename matches to task terminology.

        Args:
            file_path: Path to the file
            task_terms: Task terms to match against filename

        Returns:
            Score between 0.0 and 1.0
        """
        if not task_terms:
            return 0.5

        filename = file_path.name.lower()
        name_without_ext = file_path.stem.lower()

        # Check for matches in filename
        matches = 0
        total_terms = len(task_terms)

        for term in task_terms:
            # Check for exact match (highest score)
            if term == filename or term == name_without_ext:
                matches += 2  # Weight exact matches higher
            # Check for partial match
            elif term in filename or term in name_without_ext:
                matches += 1.5  # Weight partial matches moderately
            # Check for substring matches in compound names
            elif '_' in filename or '_' in name_without_ext:
                # Split by underscore and check if term matches any part
                filename_parts = filename.replace('.py', '').split('_')
                name_parts = name_without_ext.split('_')
                all_parts = set(filename_parts + name_parts)
                for part in all_parts:
                    if term in part or part in term:
                        matches += 1
                        break

        # Normalize score
        if total_terms > 0:
            # Max possible score is 2 * total_terms (all exact matches)
            # Normalize to 0-1 range
            raw_score = matches / (2 * total_terms)
            return min(raw_score, 1.0)
        return 0.0

    def _calculate_content_keyword(
        self,
        file_path: Path,
        task_terms: List[str],
        task_query: str
    ) -> float:
        """
        Calculate content keyword score based on occurrence of task-domain terms in file contents.

        Args:
            file_path: Path to the file
            task_terms: Task terms to search for in content
            task_query: Original task query

        Returns:
            Score between 0.0 and 1.0
        """
        if not task_terms:
            return 0.5

        # Get file content (with caching)
        content = self._get_file_content(file_path)
        if not content:
            return 0.0

        content_lower = content.lower()

        # Count term occurrences
        total_matches = 0
        for term in task_terms:
            # Use word boundaries to avoid partial matches within words
            pattern = r'\b' + re.escape(term) + r'\b'
            matches = len(re.findall(pattern, content_lower))
            total_matches += matches

        # Normalize by file length (to avoid favoring large files)
        # Use log scale to prevent huge files from dominating
        content_length = len(content)
        if content_length > 0:
            # Normalize term frequency by log of content length
            normalized_score = total_matches / math.log(content_length + 1)
            # Scale to 0-1 range (empirical scaling factor)
            return min(normalized_score * 10.0, 1.0)
        return 0.0

    def _calculate_dependency(
        self,
        file_path: Path,
        metadata: RepositoryMetadata
    ) -> float:
        """
        Calculate dependency score based on centrality in import/export chains.

        Args:
            file_path: Path to the file
            metadata: Repository metadata

        Returns:
            Score between 0.0 and 1.0
        """
        # For Stage 2, we'll implement a basic version
        # In later stages, this would use actual dependency analysis

        # Check if file is likely to be a dependency based on naming
        filename = file_path.name.lower()

        # Common indicators of dependency/utility files
        dependency_indicators = [
            'util', 'helper', 'common', 'shared', 'lib', 'base', 'core',
            'interface', 'abstract', 'proto', 'contract', 'api', 'service'
        ]

        score = 0.0
        for indicator in dependency_indicators:
            if indicator in filename:
                score = 0.8  # High score for dependency-like names
                break

        # Also give some score to files in common lib/util directories
        path_str = str(file_path).lower()
        lib_indicators = ['/util', '/lib', '/common', '/shared', '/helper']
        for indicator in lib_indicators:
            if indicator in path_str:
                score = max(score, 0.6)
                break

        return score

    def _calculate_modification_history(self, file_path: Path) -> float:
        """
        Calculate modification history score based on git activity and recent changes.

        Args:
            file_path: Path to the file

        Returns:
            Score between 0.0 and 1.0
        """
        try:
            # Get file modification time
            mtime = file_path.stat().st_mtime
            current_time = time.time()

            # Calculate age in days
            age_days = (current_time - mtime) / (24 * 3600)

            # More recent files get higher scores
            # Files modified within last 7 days get full score
            # Files older than 90 days get minimal score
            if age_days <= 7:
                return 1.0
            elif age_days >= 90:
                return 0.1
            else:
                # Linear interpolation between 7 and 90 days
                return 1.0 - (0.9 * (age_days - 7) / (90 - 7))

        except (OSError, IOError):
            # If we can't get file stats, return neutral score
            return 0.5

    def _calculate_file_type(
        self,
        file_path: Path,
        task_terms: List[str]
    ) -> float:
        """
        Calculate file type score based on preferences for certain extensions.

        Args:
            file_path: Path to the file
            task_terms: Task terms to determine preferred file types

        Returns:
            Score between 0.0 and 1.0
        """
        extension = file_path.suffix.lower()

        # Define file type preferences
        # Higher scores for source code and configuration files
        preferred_extensions = {
            # Source code
            '.py': 0.9, '.js': 0.9, '.ts': 0.9, '.jsx': 0.8, '.tsx': 0.8,
            '.java': 0.9, '.cpp': 0.9, '.c': 0.8, '.h': 0.7, '.hpp': 0.8,
            '.cs': 0.9, '.go': 0.9, '.rs': 0.9, '.rb': 0.8, '.php': 0.8,
            '.swift': 0.9, '.kt': 0.9, '.scala': 0.8,

            # Configuration files
            '.json': 0.7, '.yaml': 0.8, '.yml': 0.8, '.toml': 0.8,
            '.ini': 0.6, '.cfg': 0.6, '.conf': 0.6,
            '.xml': 0.6, '.properties': 0.6,

            # Documentation
            '.md': 0.6, '.rst': 0.6, '.txt': 0.4,

            # Build files (no extension but special names)
            'makefile': 0.8, 'dockerfile': 0.8,
        }

        # Check for exact filename matches (like Makefile, Dockerfile)
        filename_lower = file_path.name.lower()
        if filename_lower in preferred_extensions:
            return preferred_extensions[filename_lower]

        # Return extension-based score or default
        return preferred_extensions.get(extension, 0.3)  # Default for unknown types

    def _calculate_size_inversion(self, file_path: Path) -> float:
        """
        Calculate size inversion score based on preference for smaller, focused files.

        Args:
            file_path: Path to the file

        Returns:
            Score between 0.0 and 1.0 (higher for smaller files)
        """
        try:
            size = file_path.stat().st_size

            # Define size thresholds (in bytes)
            # Adjusted to make larger files get lower scores
            # Tiny files (<1KB) get very high scores
            # Small files (1-3KB) get high scores
            # Medium files (3-10KB) get moderate scores
            # Large files (10-20KB) get lower scores
            # Huge files (>20KB) get minimal scores

            if size < 1024:  # < 1KB
                return 1.0
            elif size < 3 * 1024:  # < 3KB
                return 0.9
            elif size < 10 * 1024:  # < 10KB
                return 0.7
            elif size < 20 * 1024:  # < 20KB
                return 0.4
            else:  # >= 20KB
                return 0.1

        except (OSError, IOError):
            # If we can't get file size, return neutral score
            return 0.5

    def _get_file_content(self, file_path: Path) -> str:
        """
        Get file content with caching.

        Args:
            file_path: Path to the file

        Returns:
            File content as string, or empty string if file cannot be read
        """
        # Check cache first
        if file_path in self._file_cache:
            return self._file_cache[file_path]

        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            # Cache the content (limit cache size to prevent memory issues)
            if len(self._file_cache) < 100:  # Simple LRU-like behavior
                self._file_cache[file_path] = content
            return content
        except (OSError, IOError, UnicodeDecodeError):
            # Return empty string for unreadable files
            return ""

    def _calculate_composite_score(self, signals: RelevanceSignals) -> float:
        """
        Calculate composite score from individual signals using weights.

        Args:
            signals: Individual relevance signals

        Returns:
            Composite score between 0.0 and 1.0
        """
        # Ensure weights are normalized
        self.weights.normalize()

        # Calculate weighted sum
        composite = (
            signals.path_similarity * self.weights.path_similarity +
            signals.name_pattern * self.weights.name_pattern +
            signals.content_keyword * self.weights.content_keyword +
            signals.dependency * self.weights.dependency +
            signals.modification_history * self.weights.modification_history +
            signals.file_type * self.weights.file_type +
            signals.size_inversion * self.weights.size_inversion
        )

        # Ensure score is in valid range
        return max(0.0, min(1.0, composite))

    def update_signal_weights(self, task_type: str, weights: Dict[str, float]) -> None:
        """
        Update signal weights based on task type.

        Args:
            task_type: Type of task (e.g., 'debugging', 'feature', 'refactoring')
            weights: Dictionary mapping signal names to weight values
        """
        # Update only the weights that are provided
        for signal_name, weight in weights.items():
            if hasattr(self.weights, signal_name):
                setattr(self.weights, signal_name, weight)

    def get_top_files(
        self,
        scores: Dict[Path, float],
        limit: int = 10,
        threshold: float = 0.1
    ) -> List[Tuple[Path, float]]:
        """
        Get top-ranked files above a relevance threshold.

        Args:
            scores: Dictionary mapping file paths to relevance scores
            limit: Maximum number of files to return
            threshold: Minimum relevance score to include

        Returns:
            List of (file_path, score) tuples sorted by score descending
        """
        # Filter by threshold and sort by score descending
        filtered_scores = [
            (path, score) for path, score in scores.items()
            if score >= threshold
        ]
        filtered_scores.sort(key=lambda x: x[1], reverse=True)

        # Return top results up to limit
        return filtered_scores[:limit]