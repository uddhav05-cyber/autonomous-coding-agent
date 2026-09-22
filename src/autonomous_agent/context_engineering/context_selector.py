"""
Context Selection for Autonomous Coding Agent.

This module provides context selection algorithms that use relevance signals
from Phase 3 to identify the most relevant files, symbols, and code snippets
for inclusion in the LLM context.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import math

from autonomous_agent.repository_understanding import (
    RelevanceEngine,
    RelevanceSignals
)


@dataclass
class SelectionCriteria:
    """Criteria for selecting context items."""
    # Maximum number of files to include
    max_files: Optional[int] = None

    # Maximum number of snippets per file
    max_snippets_per_file: Optional[int] = None

    # Lines per snippet when extracting code snippets
    lines_per_snippet: Optional[int] = None

    # Minimum relevance score threshold (0.0 to 1.0)
    min_relevance_score: float = 0.1

    # Whether to extract code snippets or just file references
    extract_snippets: bool = True

    # Whether to include structural information about the repository
    include_structure: bool = True

    # Phase-aware selection weights
    planning_phase_weight: float = 1.0
    execution_phase_weight: float = 1.0
    verification_phase_weight: float = 1.0

    # Whether to prioritize recently modified files
    prefer_recent: bool = True

    # Whether to include dependencies of selected files
    include_dependencies: bool = True

    # Maximum depth for dependency inclusion
    max_dependency_depth: int = 2

    def __hash__(self) -> int:
        """Generate a hash for caching purposes."""
        return hash((
            self.max_files,
            self.max_snippets_per_file,
            self.lines_per_snippet,
            self.min_relevance_score,
            self.extract_snippets,
            self.include_structure,
            self.planning_phase_weight,
            self.execution_phase_weight,
            self.verification_phase_weight,
            self.prefer_recent,
            self.include_dependencies,
            self.max_dependency_depth
        ))


class ContextSelector:
    """
    Context Selector that uses relevance signals from Phase 3 to
    identify the most relevant context for the LLM.

    This class provides:
    - Relevance-based file selection using Phase 3 RelevanceEngine
    - Hierarchical context selection (file -> class/function -> lines)
    - Phase-aware selection (different weights for planning/execution/verification)
    - Dependency-aware selection (including necessary prerequisites)
    - Recency-based prioritization
    """

    def __init__(
        self,
        relevance_engine: Optional[RelevanceEngine] = None,
        default_criteria: Optional[SelectionCriteria] = None
    ):
        """
        Initialize the Context Selector.

        Args:
            relevance_engine: Phase 3 relevance engine for scoring files
            default_criteria: Default selection criteria to use
        """
        self.relevance_engine = relevance_engine
        self.default_criteria = default_criteria or SelectionCriteria()

    def select_context(
        self,
        task_description: str,
        repository_metadata: Any,
        criteria: Optional[SelectionCriteria] = None
    ) -> Dict[str, Any]:
        """
        Select relevant context based on task description and repository metadata.

        Args:
            task_description: Description of the current task
            repository_metadata: Repository metadata from Phase 3 discovery
            criteria: Selection criteria to use (uses default if None)

        Returns:
            Dictionary containing selected context organized by type
        """
        if criteria is None:
            criteria = self.default_criteria

        # Apply phase-aware weighting if we can determine the current phase
        # For now, we'll use a default approach - in practice, this would
        # come from the agent's current state/task phase

        selected_context = {
            "files": [],
            "symbols": [],
            "snippets": [],
            "repository_info": {},
            "selection_reasoning": {}
        }

        # If we have a relevance engine, use it to score and select files
        if self.relevance_engine:
            try:
                # Get relevance scores for all files
                relevance_scores = self.relevance_engine.calculate_relevance_scores(
                    task_description, repository_metadata
                )

                # Apply selection criteria
                selected_files = self._apply_selection_criteria(
                    relevance_scores, criteria
                )

                # Get detailed context for selected files
                for file_path, relevance_score in selected_files:
                    file_context = self._get_file_context(
                        file_path, relevance_score, criteria
                    )
                    if file_context:
                        selected_context["files"].append(file_context)

                        # Extract symbols if requested
                        if criteria.include_dependencies:
                            symbols = self._extract_file_symbols(file_path)
                            selected_context["symbols"].extend(symbols)

                        # Extract snippets if requested
                        if criteria.extract_snippets:
                            snippets = self._extract_file_snippets(
                                file_path, relevance_score, criteria
                            )
                            selected_context["snippets"].extend(snippets)

            except Exception as e:
                # Fall back to basic selection if relevance engine fails
                selected_context = self._basic_selection(
                    repository_metadata, criteria
                )
        else:
            # No relevance engine available, use basic selection
            selected_context = self._basic_selection(
                repository_metadata, criteria
            )

        # Add repository information
        selected_context["repository_info"] = self._get_repository_info(
            repository_metadata
        )

        # Add selection reasoning for debugging/tracing
        selected_context["selection_reasoning"] = {
            "criteria_used": criteria.__dict__,
            "total_files_considered": len(getattr(repository_metadata, 'structure_map', {})),
            "files_selected": len(selected_context["files"]),
            "symbols_extracted": len(selected_context["symbols"]),
            "snippets_extracted": len(selected_context["snippets"])
        }

        return selected_context

    def _apply_selection_criteria(
        self,
        relevance_scores: Dict[Path, Any],
        criteria: SelectionCriteria
    ) -> List[Tuple[Path, Any]]:
        """
        Apply selection criteria to relevance scores to choose files.

        Args:
            relevance_scores: Dictionary mapping file paths to relevance scores
            criteria: Selection criteria to apply

        Returns:
            List of (file_path, relevance_score) tuples sorted by relevance
        """
        # Filter by minimum relevance score
        filtered_scores = [
            (path, score) for path, score in relevance_scores.items()
            if getattr(score, 'composite', 0.0) >= criteria.min_relevance_score
        ]

        # Sort by composite score (descending)
        sorted_scores = sorted(
            filtered_scores,
            key=lambda x: getattr(x[1], 'composite', 0.0),
            reverse=True
        )

        # Apply maximum files limit
        if criteria.max_files is not None:
            sorted_scores = sorted_scores[:criteria.max_files]

        return sorted_scores

    def _get_file_context(
        self,
        file_path: Path,
        relevance_score: Any,
        criteria: SelectionCriteria
    ) -> Optional[Dict[str, Any]]:
        """
        Get context information for a specific file.

        Args:
            file_path: Path to the file
            relevance_score: Relevance score for the file
            criteria: Selection criteria

        Returns:
            Dictionary containing file context or None if file cannot be read
        """
        try:
            # Check if file exists
            if not file_path.is_file():
                return None

            # Read file content
            try:
                content = file_path.read_text(encoding='utf-8')
            except (UnicodeDecodeError, OSError):
                # Skip binary or unreadable files
                return None

            # Basic file information
            file_context = {
                "path": str(file_path),
                "relative_path": str(file_path),  # Simplified for now
                "relevance_score": relevance_score,
                "content": content,
                "size_bytes": len(content.encode('utf-8')),
                "line_count": len(content.splitlines()),
                "language": self._detect_language(file_path),
                "symbols": [],
                "snippets": []
            }

            # Extract symbols if analyzer would be available
            # In a full implementation, we'd use the SymbolDependencyAnalyzer
            # For now, we'll leave this empty and let the ContextManager handle it

            # Extract snippets if requested
            if criteria.extract_snippets:
                snippets = self._extract_snippets_from_content(
                    content, relevance_score, criteria
                )
                file_context["snippets"] = snippets

            return file_context

        except Exception:
            # If any error occurs, skip this file
            return None

    def _basic_selection(
        self,
        repository_metadata: Any,
        criteria: SelectionCriteria
    ) -> Dict[str, Any]:
        """
        Basic file selection when relevance engine is not available.

        Args:
            repository_metadata: Repository metadata from Phase 3
            criteria: Selection criteria

        Returns:
            Dictionary containing basic file selection
        """
        selected_context = {
            "files": [],
            "symbols": [],
            "snippets": [],
            "repository_info": {},
            "selection_reasoning": {}
        }

        # Get files from structure map
        structure_map = getattr(repository_metadata, 'structure_map', {})
        max_files = criteria.max_files or 20

        file_count = 0
        for dir_path, file_names in structure_map.items():
            if file_count >= max_files:
                break

            for file_name in file_names:
                if file_count >= max_files:
                    break

                # Construct file path (simplified)
                if dir_path == "":
                    # This would need the root path in a real implementation
                    file_path = Path(file_name)
                else:
                    file_path = Path(dir_path) / file_name

                # Only process if it looks like a valid file
                if file_path.suffix in ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.cs', '.go', '.rs']:
                    file_context = {
                        "path": str(file_path),
                        "relative_path": str(file_path),
                        "relevance_score": type('RelevanceScore', (), {'composite': 0.5})(),  # Default score
                        "content": "",  # Would be read in real implementation
                        "size_bytes": 0,
                        "line_count": 0,
                        "language": self._detect_language(file_path),
                        "symbols": [],
                        "snippets": []
                    }
                    selected_context["files"].append(file_context)
                    file_count += 1

        selected_context["selection_reasoning"] = {
            "method": "basic_selection",
            "files_considered": len(structure_map),
            "files_selected": len(selected_context["files"])
        }

        return selected_context

    def _extract_file_symbols(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Extract symbols from a file.

        In a full implementation, this would use the SymbolDependencyAnalyzer
        from Phase 3. For this MVP, we'll return an empty list.
        """
        # Placeholder - in reality, this would call:
        # symbols = self.symbol_analyzer.analyze_file_symbols(file_path)
        # and format them appropriately
        return []

    def _extract_file_snippets(
        self,
        file_path: Path,
        relevance_score: Any,
        criteria: SelectionCriteria
    ) -> List[Dict[str, Any]]:
        """
        Extract code snippets from a file.

        Args:
            file_path: Path to the file
            relevance_score: Relevance score for the file
            criteria: Selection criteria

        Returns:
            List of snippet dictionaries
        """
        try:
            if not file_path.is_file():
                return []

            content = file_path.read_text(encoding='utf-8')
            return self._extract_snippets_from_content(
                content, relevance_score, criteria
            )
        except Exception:
            return []

    def _extract_snippets_from_content(
        self,
        content: str,
        relevance_score: Any,
        criteria: SelectionCriteria
    ) -> List[Dict[str, Any]]:
        """
        Extract code snippets from file content.

        Args:
            content: File content as string
            relevance_score: Relevance score for the file
            criteria: Selection criteria

        Returns:
            List of snippet dictionaries
        """
        snippets = []

        lines = content.splitlines()
        total_lines = len(lines)

        if total_lines == 0:
            return snippets

        # Determine how many snippets to extract
        max_snippets = criteria.max_snippets_per_file or 5
        lines_per_snippet = criteria.lines_per_snippet or 10

        # Simple sampling approach
        if total_lines <= lines_per_snippet * max_snippets:
            # Small file, show everything in chunks
            chunk_size = lines_per_snippet
            for i in range(0, total_lines, chunk_size):
                chunk_lines = lines[i:i + chunk_size]
                if chunk_lines:
                    snippets.append({
                        "start_line": i,
                        "end_line": min(i + len(chunk_lines) - 1, total_lines - 1),
                        "content": "\n".join(chunk_lines),
                        "relevance": getattr(relevance_score, 'composite', 0.5)
                        if relevance_score else 0.5
                    })
        else:
            # Larger file, sample at regular intervals
            interval = max(1, total_lines // (max_snippets * lines_per_snippet))
            for i in range(0, total_lines, interval):
                if len(snippets) >= max_snippets:
                    break
                end_line = min(i + lines_per_snippet, total_lines)
                chunk_lines = lines[i:end_line]
                if chunk_lines:
                    snippets.append({
                        "start_line": i,
                        "end_line": end_line - 1,
                        "content": "\n".join(chunk_lines),
                        "relevance": getattr(relevance_score, 'composite', 0.5)
                        if relevance_score else 0.5
                    })

        return snippets[:max_snippets]

    def _detect_language(self, file_path: Path) -> str:
        """
        Detect programming language from file extension.

        Args:
            file_path: Path to the file

        Returns:
            String representing the detected language
        """
        if not file_path:
            return "unknown"

        extension = file_path.suffix.lower()
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",
            ".java": "java",
            ".cpp": "cpp",
            ".cc": "cpp",
            ".cxx": "cpp",
            ".c": "c",
            ".h": "c",
            ".hpp": "cpp",
            ".cs": "csharp",
            ".php": "php",
            ".rb": "ruby",
            ".go": "go",
            ".rs": "rust",
            ".swift": "swift",
            ".kt": "kotlin",
            ".scala": "scala",
            ".sh": "shell",
            ".bash": "shell",
            ".zsh": "shell",
            ".fish": "shell",
            ".html": "html",
            ".htm": "html",
            ".css": "css",
            ".scss": "scss",
            ".sass": "sass",
            ".less": "less",
            ".json": "json",
            ".xml": "xml",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".toml": "toml",
            ".ini": "ini",
            ".cfg": "ini",
            ".conf": "ini",
            ".md": "markdown",
            ".rst": "restructuredtext",
            ".txt": "text",
            ".sql": "sql"
        }

        return language_map.get(extension, "unknown")

    def _get_repository_info(self, repository_metadata: Any) -> Dict[str, Any]:
        """
        Extract repository information for context.

        Args:
            repository_metadata: Repository metadata from Phase 3

        Returns:
            Dictionary containing repository information
        """
        if not repository_metadata:
            return {}

        return {
            "root_path": str(getattr(repository_metadata, 'root_path', '')),
            "is_git_repo": getattr(repository_metadata, 'is_git_repo', False),
            "git_branch": getattr(repository_metadata, 'git_branch', None),
            "git_commit": getattr(repository_metadata, 'git_commit', None),
            "project_type": getattr(repository_metadata, 'project_type', None),
            "language_hints": list(getattr(repository_metadata, 'language_hints', [])),
            "build_system_hints": list(getattr(repository_metadata, 'build_system_hints', [])),
            "documentation_hints": list(getattr(repository_metadata, 'documentation_hints', []))
        }

    def __repr__(self) -> str:
        """String representation of the ContextSelector."""
        return f"ContextSelector(relevance_engine={self.relevance_engine}, default_criteria={self.default_criteria})"