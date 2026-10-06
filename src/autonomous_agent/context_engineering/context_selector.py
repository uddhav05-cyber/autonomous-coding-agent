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
    RelevanceSignals,
    SymbolDependencyAnalyzer
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

    # Whether to use symbol-level selection when available
    use_symbol_level_selection: bool = True

    # Weight for symbol similarity signal (0.0 to 1.0)
    symbol_similarity_weight: float = 0.1

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
            self.max_dependency_depth,
            self.use_symbol_level_selection,
            self.symbol_similarity_weight
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
        symbol_analyzer: Optional[SymbolDependencyAnalyzer] = None,
        default_criteria: Optional[SelectionCriteria] = None
    ):
        """
        Initialize the Context Selector.

        Args:
            relevance_engine: Phase 3 relevance engine for scoring files
            symbol_analyzer: Phase 3 symbol analyzer for extracting symbols
            default_criteria: Default selection criteria to use
        """
        self.relevance_engine = relevance_engine
        self.symbol_analyzer = symbol_analyzer
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

        selected_context = {
            "files": [],
            "symbols": [],
            "snippets": [],
            "repository_info": {},
            "selection_reasoning": {}
        }

        # If we have both relevance engine and symbol analyzer, use enhanced selection
        if self.relevance_engine and self.symbol_analyzer:
            try:
                selected_context = self._select_context_with_symbols(
                    task_description, repository_metadata, criteria
                )
            except Exception as e:
                # Fall back to basic selection if enhanced selection fails
                selected_context = self._basic_selection(
                    repository_metadata, criteria
                )
        # If we only have relevance engine, use relevance-based selection
        elif self.relevance_engine:
            try:
                selected_context = self._select_context_relevance_only(
                    task_description, repository_metadata, criteria
                )
            except Exception as e:
                # Fall back to basic selection if relevance-based selection fails
                selected_context = self._basic_selection(
                    repository_metadata, criteria
                )
        # If we only have symbol analyzer, use symbol-based selection
        elif self.symbol_analyzer:
            try:
                selected_context = self._select_context_symbols_only(
                    task_description, repository_metadata, criteria
                )
            except Exception as e:
                # Fall back to basic selection if symbol-based selection fails
                selected_context = self._basic_selection(
                    repository_metadata, criteria
                )
        else:
            # No analyzers available, use basic selection
            selected_context = self._basic_selection(
                repository_metadata, criteria
            )

        # Add selection reasoning for debugging/tracing
        selected_context["selection_reasoning"] = {
            "criteria_used": criteria.__dict__,
            "has_relevance_engine": self.relevance_engine is not None,
            "has_symbol_analyzer": self.symbol_analyzer is not None,
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

    def _get_file_context_enhanced(
        self,
        file_path: Path,
        relevance_score: float,
        symbols: List[Symbol],
        criteria: SelectionCriteria
    ) -> Optional[Dict[str, Any]]:
        """
        Get enhanced context information for a specific file using symbol information.

        Args:
            file_path: Path to the file
            relevance_score: Combined relevance score for the file
            symbols: List of symbols found in the file
            criteria: Selection criteria to use

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
                "symbols": [],  # Will be populated below
                "snippets": []  # Will be populated below if extract_snippets is True
            }

            # Add symbols if requested and available
            if symbols:
                file_context["symbols"] = [
                    {
                        "name": s.name,
                        "type": s.symbol_type,
                        "line_start": s.line_number,
                        "line_end": s.end_line_number or s.line_number
                    }
                    for s in symbols
                ]

            # Extract snippets if requested
            if criteria.extract_snippets:
                snippets = self._extract_snippets_from_content(
                    content,
                    type('RelevanceScore', (), {'composite': relevance_score})(),
                    criteria,
                    task_description,
                    symbols
                )
                file_context["snippets"] = snippets

            return file_context

        except Exception:
            # If any error occurs, skip this file
            return None

    def _get_file_context_basic(
        self,
        file_path: Path,
        relevance_score: Any,
        criteria: SelectionCriteria
    ) -> Optional[Dict[str, Any]]:
        """
        Get basic context information for a specific file (fallback implementation).

        Args:
            file_path: Path to the file
            relevance_score: Relevance score for the file
            criteria: Selection criteria to use

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
                "symbols": [],  # No symbol information available in basic mode
                "snippets": []  # Will be populated below if extract_snippets is True
            }

            # Extract snippets if requested
            if criteria.extract_snippets:
                snippets = self._extract_snippets_from_content(
                    content,
                    relevance_score if isinstance(relevance_score, (int, float)) else type('RelevanceScore', (), {'composite': 0.5})(),
                    criteria
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
        Extract symbols from a file using the symbol analyzer.

        Args:
            file_path: Path to the file to extract symbols from

        Returns:
            List of symbol dictionaries
        """
        if not self.symbol_analyzer:
            return []

        try:
            symbols = self.symbol_analyzer.analyze_file_symbols(file_path)
            return self._format_symbols_for_output(symbols)
        except Exception:
            # If symbol analysis fails, return empty list
            return []

    def _format_symbols_for_output(self, symbols: List[Symbol]) -> List[Dict[str, Any]]:
        """
        Format Symbol objects for output in context.

        Args:
            symbols: List of Symbol objects to format

        Returns:
            List of symbol dictionaries
        """
        return [
            {
                "name": s.name,
                "type": s.symbol_type,
                "line_start": s.line_number,
                "line_end": s.end_line_number or s.line_number
            }
            for s in symbols
        ]

    def _is_within_workspace(self, file_path: Path) -> bool:
        """
        Check if a file path is within the workspace boundaries.

        In a full implementation, this would check against the actual workspace boundaries.
        For this implementation, we'll assume all files provided by repository_metadata
        are within the workspace.

        Args:
            file_path: Path to check

        Returns:
            True if file is within workspace, False otherwise
        """
        # Simple implementation - in reality, this would check against workspace.root_path
        try:
            # For now, we'll be permissive and allow all files
            # A real implementation would check: file_path.is_relative_to(workspace.root_path)
            return True
        except Exception:
            return False

    def _calculate_symbol_relevance_bonus(
        self,
        symbols: List[Symbol],
        task_description: str,
        criteria: SelectionCriteria
    ) -> float:
        """
        Calculate relevance bonus based on symbol matches to task description.

        Args:
            symbols: List of symbols found in the file
            task_description: Description of the current task
            criteria: Selection criteria to use

        Returns:
            Symbol relevance bonus (0.0 to 1.0)
        """
        if not symbols or not task_description:
            return 0.0

        # Extract keywords from task description
        task_keywords = self._extract_keywords(task_description.lower())
        if not task_keywords:
            return 0.0

        # Count matching symbols
        matching_symbols = 0
        total_symbols = len(symbols)

        for symbol in symbols:
            symbol_name_lower = symbol.name.lower()
            # Check if any task keyword appears in the symbol name
            if any(keyword in symbol_name_lower for keyword in task_keywords):
                matching_symbols += 1
            # Also check scope if available
            elif symbol.scope:
                scope_lower = symbol.scope.lower()
                if any(keyword in scope_lower for keyword in task_keywords):
                    matching_symbols += 1

        # Calculate ratio of matching symbols
        if total_symbols > 0:
            symbol_ratio = matching_symbols / total_symbols
            # Apply the symbol similarity weight from criteria
            return symbol_ratio * criteria.symbol_similarity_weight
        else:
            return 0.0

    def _calculate_symbol_line_relevance_bonus(
        self,
        symbols: List[Symbol],
        task_keywords: List[str],
        total_lines: int,
        criteria: SelectionCriteria
    ) -> List[float]:
        """
        Calculate line-level relevance bonus based on proximity to relevant symbols.

        Args:
            symbols: List of symbols found in the file
            task_keywords: Keywords extracted from task description
            total_lines: Total number of lines in the file
            criteria: Selection criteria to use

        Returns:
            List of symbol relevance bonuses for each line (0.0 to 1.0)
        """
        # Initialize bonus scores for each line
        line_bonuses = [0.0] * total_lines

        if not symbols or not task_keywords:
            return line_bonuses

        # For each symbol, calculate its relevance based on keyword matching
        symbol_relevances = []
        for symbol in symbols:
            # Calculate how relevant this symbol is to the task
            symbol_relevance = 0.0
            symbol_name_lower = symbol.name.lower()

            # Check symbol name for keyword matches
            name_matches = sum(1 for keyword in task_keywords if keyword in symbol_name_lower)
            if name_matches > 0:
                symbol_relevance += name_matches * 0.5  # Weight for name matches

            # Check symbol scope for keyword matches if available
            if symbol.scope:
                scope_lower = symbol.scope.lower()
                scope_matches = sum(1 for keyword in task_keywords if keyword in scope_lower)
                if scope_matches > 0:
                    symbol_relevance += scope_matches * 0.3  # Weight for scope matches

            # Normalize symbol relevance to 0-1 range
            # We'll use a simple approach: if any matches, relevance is at least 0.1
            if symbol_relevance > 0:
                symbol_relevance = min(1.0, 0.1 + (symbol_relevance * 0.1))
            else:
                symbol_relevance = 0.0

            symbol_relevances.append((symbol, symbol_relevance))

        # For each relevant symbol, add bonus to nearby lines
        for symbol, symbol_relevance in symbol_relevances:
            if symbol_relevance > 0:
                # Determine symbol's line range
                start_line = symbol.line_number - 1  # Convert to 0-based indexing
                end_line = (symbol.end_line_number or symbol.line_number) - 1  # Convert to 0-based indexing

                # Ensure line numbers are within bounds
                start_line = max(0, min(start_line, total_lines - 1))
                end_line = max(0, min(end_line, total_lines - 1))

                # Define proximity range - how many lines around the symbol to consider
                # We'll use a range that decreases with distance
                proximity_range = 5  # Look at 5 lines before and after

                # Apply bonus to lines near the symbol
                for line_idx in range(max(0, start_line - proximity_range),
                                  min(total_lines, end_line + proximity_range + 1)):
                    # Calculate distance from symbol range
                    if line_idx < start_line:
                        distance = start_line - line_idx
                    elif line_idx > end_line:
                        distance = line_idx - end_line
                    else:
                        distance = 0  # Inside symbol range

                    # Calculate bonus based on inverse distance (closer = higher bonus)
                    # Max bonus when distance = 0, decreases linearly with distance
                    if distance <= proximity_range:
                        distance_factor = 1.0 - (distance / proximity_range)
                        line_bonus = symbol_relevance * distance_factor * 0.3  # Weight for symbol proximity
                        line_bonuses[line_idx] += line_bonus

        # Ensure bonuses don't exceed 1.0
        for i in range(total_lines):
            line_bonuses[i] = min(1.0, line_bonuses[i])

        return line_bonuses

    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract keywords from text for symbol matching.

        Args:
            text: Input text to extract keywords from

        Returns:
            List of extracted keywords
        """
        # Simple keyword extraction - split on non-alphanumeric characters
        import re
        # Extract words (sequences of alphanumeric characters)
        words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9_]*\b', text)
        # Filter out very short words and common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'am', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
        keywords = [word for word in words if len(word) >= 2 and word.lower() not in stop_words]
        return keywords[:20]  # Limit to prevent too many keywords

    def _expand_with_context_window(self, start_line: int, end_line: int, total_lines: int, context_lines: int) -> Tuple[int, int]:
        """
        Expand a line range by adding context window around it.

        Args:
            start_line: Start line index (0-based, inclusive)
            end_line: End line index (0-based, inclusive)
            total_lines: Total number of lines in the file
            context_lines: Number of context lines to add on each side

        Returns:
            Tuple of (expanded_start_line, expanded_end_line) both 0-based and inclusive
        """
        if context_lines <= 0:
            return start_line, end_line

        expanded_start = max(0, start_line - context_lines)
        expanded_end = min(total_lines - 1, end_line + context_lines)

        return expanded_start, expanded_end

    def _merge_line_ranges(self, line_ranges: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """
        Merge overlapping or adjacent line ranges.

        Args:
            line_ranges: List of (start_line, end_line) tuples (0-based, inclusive)

        Returns:
            List of merged (start_line, end_line) tuples (0-based, inclusive)
        """
        if not line_ranges:
            return []

        # Sort ranges by start line
        sorted_ranges = sorted(line_ranges, key=lambda x: x[0])

        merged = []
        current_start, current_end = sorted_ranges[0]

        for start, end in sorted_ranges[1:]:
            # If current range overlaps or is adjacent to the next range, merge them
            if start <= current_end + 1:  # Overlapping or adjacent
                current_end = max(current_end, end)
            else:
                # No overlap, add current range to merged and start a new one
                merged.append((current_start, current_end))
                current_start, current_end = start, end

        # Add the last range
        merged.append((current_start, current_end))

        return merged

    def _select_context_with_symbols(
        self,
        task_description: str,
        repository_metadata: Any,
        criteria: SelectionCriteria
    ) -> Dict[str, Any]:
        """
        Select context using both relevance engine and symbol analyzer.

        Args:
            task_description: Description of the current task
            repository_metadata: Repository metadata from Phase 3
            criteria: Selection criteria to use

        Returns:
            Dictionary containing selected context
        """
        selected_context = {
            "files": [],
            "symbols": [],
            "snippets": [],
            "repository_info": {},
        }

        # Get relevance scores for all files
        relevance_scores = self.relevance_engine.calculate_relevance_scores(
            task_description, repository_metadata
        )

        # Get symbol information for all files (cached for performance)
        file_symbols_map = {}
        for file_path in relevance_scores.keys():
            if self._is_within_workspace(file_path):
                try:
                    symbols = self.symbol_analyzer.analyze_file_symbols(file_path)
                    file_symbols_map[file_path] = symbols
                except Exception:
                    # If symbol analysis fails, continue with empty symbols
                    file_symbols_map[file_path] = []

        # Score each file based on combined relevance and symbol matches
        file_scores = []
        for file_path, relevance_score in relevance_scores.items():
            if not self._is_within_workspace(file_path):
                continue

            # Get symbols for this file
            symbols = file_symbols_map.get(file_path, [])

            # Calculate base relevance score
            base_score = relevance_score.composite

            # Calculate symbol relevance bonus
            symbol_bonus = self._calculate_symbol_relevance_bonus(
                symbols, task_description, criteria
            ) if criteria.use_symbol_level_selection else 0.0

            # Combined score (relevance + symbol bonus, capped at 1.0)
            combined_score = min(1.0, base_score + symbol_bonus)

            # Only include files above minimum relevance threshold
            if combined_score >= criteria.min_relevance_score:
                file_scores.append((file_path, combined_score, symbols, relevance_score))

        # Sort by combined score (descending)
        file_scores.sort(key=lambda x: x[1], reverse=True)

        # Apply maximum files limit
        max_files = criteria.max_files or 50
        if max_files > 0:
            file_scores = file_scores[:max_files]

        # Get detailed context for selected files
        for file_path, combined_score, symbols, relevance_score in file_scores:
            file_context = self._get_file_context_enhanced(
                file_path, combined_score, symbols, criteria
            )
            if file_context:
                selected_context["files"].append(file_context)
                # Add symbols to global symbols list
                selected_context["symbols"].extend(
                    self._format_symbols_for_output(symbols)
                )

        # Extract snippets from selected files
        if criteria.extract_snippets:
            for file_context in selected_context["files"]:
                file_path = Path(file_context["path"])
                try:
                    content = file_path.read_text(encoding='utf-8')
                    # Extract symbols for this file if symbol analyzer is available
                    symbols_to_pass = []
                    if self.symbol_analyzer:
                        try:
                            symbols_to_pass = self.symbol_analyzer.analyze_file_symbols(file_path)
                        except Exception:
                            symbols_to_pass = []
                    snippets = self._extract_snippets_from_content(
                        content,
                        type('RelevanceScore', (), {'composite': file_context.get('relevance_score', 0.5)})(),
                        criteria,
                        task_description,
                        symbols_to_pass
                    )
                    file_context["snippets"] = snippets
                    selected_context["snippets"].extend(snippets)
                except Exception:
                    # If we can't read the file for snippets, skip snippets for this file
                    pass

        return selected_context

    def _select_context_relevance_only(
        self,
        task_description: str,
        repository_metadata: Any,
        criteria: SelectionCriteria
    ) -> Dict[str, Any]:
        """
        Select context using only relevance engine (fallback when symbol analyzer unavailable).

        Args:
            task_description: Description of the current task
            repository_metadata: Repository metadata from Phase 3
            criteria: Selection criteria to use

        Returns:
            Dictionary containing selected context
        """
        selected_context = {
            "files": [],
            "symbols": [],
            "snippets": [],
            "repository_info": {},
        }

        # Get relevance scores for all files
        relevance_scores = self.relevance_engine.calculate_relevance_scores(
            task_description, repository_metadata
        )

        # Score and select files based on relevance alone
        file_scores = []
        for file_path, relevance_score in relevance_scores.items():
            if not self._is_within_workspace(file_path):
                continue

            base_score = relevance_score.composite

            # Only include files above minimum relevance threshold
            if base_score >= criteria.min_relevance_score:
                file_scores.append((file_path, base_score, relevance_score))

        # Sort by relevance score (descending)
        file_scores.sort(key=lambda x: x[1], reverse=True)

        # Apply maximum files limit
        max_files = criteria.max_files or 50
        if max_files > 0:
            file_scores = file_scores[:max_files]

        # Get detailed context for selected files
        for file_path, relevance_score, _ in file_scores:
            file_context = self._get_file_context_basic(
                file_path, relevance_score, criteria
            )
            if file_context:
                selected_context["files"].append(file_context)

        # Extract snippets from selected files
        if criteria.extract_snippets:
            for file_context in selected_context["files"]:
                file_path = Path(file_context["path"])
                try:
                    content = file_path.read_text(encoding='utf-8')
                    snippets = self._extract_snippets_from_content(
                        content,
                        type('RelevanceScore', (), {'composite': file_context.get('relevance_score', 0.5)})(),
                        criteria,
                        task_description
                    )
                    file_context["snippets"] = snippets
                    selected_context["snippets"].extend(snippets)
                except Exception:
                    # If we can't read the file for snippets, skip snippets for this file
                    pass

        return selected_context

    def _select_context_symbols_only(
        self,
        task_description: str,
        repository_metadata: Any,
        criteria: SelectionCriteria
    ) -> Dict[str, Any]:
        """
        Select context using only symbol analyzer (fallback when relevance engine unavailable).

        Args:
            task_description: Description of the current task
            repository_metadata: Repository metadata from Phase 3
            criteria: Selection criteria to use

        Returns:
            Dictionary containing selected context
        """
        selected_context = {
            "files": [],
            "symbols": [],
            "snippets": [],
            "repository_info": {},
        }

        # Get symbol information for all files
        file_symbols_map = {}
        structure_map = getattr(repository_metadata, 'structure_map', {})
        for dir_path, file_names in structure_map.items():
            for file_name in file_names:
                # Construct file path (simplified)
                if dir_path == "":
                    file_path = Path(file_name)
                else:
                    file_path = Path(dir_path) / file_name

                if self._is_within_workspace(file_path):
                    try:
                        symbols = self.symbol_analyzer.analyze_file_symbols(file_path)
                        file_symbols_map[file_path] = symbols
                    except Exception:
                        # If symbol analysis fails, continue with empty symbols
                        file_symbols_map[file_path] = []

        # Score each file based on symbol matches
        file_scores = []
        for file_path, symbols in file_symbols_map.items():
            # Calculate symbol relevance score
            symbol_score = self._calculate_symbol_relevance_bonus(
                symbols, task_description, criteria
            )

            # Only include files with sufficient symbol relevance
            if symbol_score >= criteria.min_relevance_score:
                file_scores.append((file_path, symbol_score, symbols))

        # Sort by symbol score (descending)
        file_scores.sort(key=lambda x: x[1], reverse=True)

        # Apply maximum files limit
        max_files = criteria.max_files or 50
        if max_files > 0:
            file_scores = file_scores[:max_files]

        # Get detailed context for selected files
        for file_path, symbol_score, symbols in file_scores:
            file_context = self._get_file_context_enhanced(
                file_path, symbol_score, symbols, criteria
            )
            if file_context:
                selected_context["files"].append(file_context)
                # Add symbols to global symbols list
                selected_context["symbols"].extend(
                    self._format_symbols_for_output(symbols)
                )

        # Extract snippets from selected files
        if criteria.extract_snippets:
            for file_context in selected_context["files"]:
                file_path = Path(file_context["path"])
                try:
                    content = file_path.read_text(encoding='utf-8')
                    snippets = self._extract_snippets_from_content(
                        content,
                        type('RelevanceScore', (), {'composite': file_context.get('relevance_score', 0.5)})(),
                        criteria,
                        task_description,
                        []  # We don't have easy access to symbols here without re-analyzing
                    )
                    file_context["snippets"] = snippets
                    selected_context["snippets"].extend(snippets)
                except Exception:
                    # If we can't read the file for snippets, skip snippets for this file
                    pass

        return selected_context

    def _extract_file_snippets(
        self,
        file_path: Path,
        relevance_score: Any,
        criteria: SelectionCriteria,
        task_description: str = "",
        symbols: List[Symbol] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract code snippets from a file.

        Args:
            file_path: Path to the file
            relevance_score: Relevance score for the file
            criteria: Selection criteria
            task_description: Description of the current task for relevance-guided extraction
            symbols: List of symbols in the file for symbol-aware extraction

        Returns:
            List of snippet dictionaries
        """
        try:
            if not file_path.is_file():
                return []

            content = file_path.read_text(encoding='utf-8')
            return self._extract_snippets_from_content(
                content, relevance_score, criteria, task_description, symbols or []
            )
        except Exception:
            return []

    def _extract_snippets_from_content(
        self,
        content: str,
        relevance_score: Any,
        criteria: SelectionCriteria,
        task_description: str = "",
        symbols: List[Symbol] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract code snippets from file content.

        Args:
            content: File content as string
            relevance_score: Relevance score for the file
            criteria: Selection criteria
            task_description: Description of the current task for relevance-guided extraction
            symbols: List of symbols in the file for symbol-aware extraction

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

        # Extract keywords from task description for relevance-guided extraction
        task_keywords = []
        if task_description:
            task_keywords = self._extract_keywords(task_description.lower())

        # If we have keywords or symbols, use enhanced relevance-guided extraction
        if task_keywords or (symbols and criteria.use_symbol_level_selection):
            # Score each line based on keyword matches and symbol proximity
            line_scores = [0.0] * total_lines

            # First, score based on task keywords
            if task_keywords:
                for i, line in enumerate(lines):
                    line_lower = line.lower()
                    # Count keyword matches in this line
                    matches = sum(1 for keyword in task_keywords if keyword in line_lower)
                    # Normalize by line length to avoid bias toward longer lines
                    if len(line) > 0:
                        line_scores[i] = matches / len(line)
                    else:
                        line_scores[i] = float(matches)  # For empty lines, just count matches

            # Then, add symbol-based relevance if symbols are available
            if symbols and criteria.use_symbol_level_selection:
                symbol_bonus_scores = self._calculate_symbol_line_relevance_bonus(
                    symbols, task_keywords, total_lines, criteria
                )
                # Combine keyword scores with symbol bonus (weighted by symbol_similarity_weight)
                for i in range(total_lines):
                    if task_keywords:
                        # If we have keyword scores, combine them with symbol bonus
                        keyword_score = line_scores[i]
                        symbol_bonus = symbol_bonus_scores[i]
                        # Weighted combination: keyword_score + (symbol_bonus * weight)
                        line_scores[i] = keyword_score + (symbol_bonus * criteria.symbol_similarity_weight)
                    else:
                        # If we only have symbols, use symbol bonus directly
                        line_scores[i] = symbol_bonus_scores[i]

            # If we found any relevance matches, use relevance-guided extraction
            if any(score > 0 for score in line_scores):
                if total_lines <= lines_per_snippet * max_snippets:
                    # Small file: evaluate all possible chunks and pick the best ones
                    chunk_size = lines_per_snippet
                    chunk_scores = []
                    for i in range(0, total_lines, chunk_size):
                        chunk_lines = lines[i:i + chunk_size]
                        if chunk_lines:
                            # Average score of lines in this chunk
                            chunk_score = sum(line_scores[i:i + len(chunk_lines)]) / len(chunk_lines)
                            chunk_scores.append((i, chunk_score, chunk_lines))

                    # Sort chunks by score (descending) and take the top ones
                    chunk_scores.sort(key=lambda x: x[1], reverse=True)
                    selected_chunks = chunk_scores[:max_snippets]

                    # Convert selected chunks to snippets with context window optimization
                    chunk_ranges = []
                    for start_idx, score, chunk_lines in selected_chunks:
                        end_idx = min(start_idx + len(chunk_lines) - 1, total_lines - 1)
                        chunk_ranges.append((start_idx, end_idx, score))

                    # Expand each range with context window (half of lines_per_snippet on each side)
                    context_window = max(1, (criteria.lines_per_snippet or 10) // 2)
                    expanded_ranges = []
                    for start_idx, end_idx, score in chunk_ranges:
                        expanded_start, expanded_end = self._expand_with_context_window(
                            start_idx, end_idx, total_lines, context_window
                        )
                        expanded_ranges.append((expanded_start, expanded_end, score))

                    # Merge overlapping/adjacent ranges
                    merged_ranges = self._merge_line_ranges([(start, end) for start, end, _ in expanded_ranges])

                    # Limit to max_snippets_per_file and create snippets
                    for i, (start_idx, end_idx) in enumerate(merged_ranges[:max_snippets]):
                        # For simplicity, we'll use the average score of the original chunks that contributed to this range
                        # In a more sophisticated implementation, we might want to preserve relevance scores better
                        snippet_content = "\n".join(lines[start_idx:end_idx + 1])
                        snippets.append({
                            "start_line": start_idx,
                            "end_line": end_idx,
                            "content": snippet_content,
                            "relevance": 0.5  # Placeholder - in a full implementation we'd preserve relevance better
                        })
                else:
                    # Large file: use relevance-guided sampling
                    # Create a probability distribution based on line scores
                    total_score = sum(line_scores)
                    if total_score > 0:
                        # Normalize to get probabilities
                        line_probabilities = [score / total_score for score in line_scores]
                    else:
                        # Fallback to uniform distribution if no relevance matches found
                        line_probabilities = [1.0 / total_lines] * total_lines

                    # Determine how many samples to take
                    # We want to ensure we get good coverage while focusing on high-relevance areas
                    num_samples = min(max_snippets * 3, total_lines // lines_per_snippet + 1)
                    if num_samples < max_snippets:
                        num_samples = max_snippets

                    # Select lines based on probability distribution (without replacement)
                    selected_indices = set()
                    attempts = 0
                    max_attempts = num_samples * 3  # Prevent infinite loop

                    while len(selected_indices) < num_samples and attempts < max_attempts:
                        # For determinism, select the highest scoring lines that haven't been chosen yet
                        # Create list of (index, score) pairs for unselected indices
                        unselected_scores = [(i, line_scores[i]) for i in range(total_lines) if i not in selected_indices]
                        if not unselected_scores:
                            break

                        # Sort by score descending and pick the best one
                        unselected_scores.sort(key=lambda x: x[1], reverse=True)
                        best_idx = unselected_scores[0][0]
                        selected_indices.add(best_idx)
                        attempts += 1

                    # If we didn't get enough samples, fill with uniform sampling
                    if len(selected_indices) < max_snippets:
                        # Add uniformly spaced indices that aren't already selected
                        interval = max(1, total_lines // max_snippets)
                        for i in range(0, total_lines, interval):
                            if len(selected_indices) >= max_snippets:
                                break
                            if i not in selected_indices:
                                selected_indices.add(i)

                    # Convert selected indices to snippets with context window optimization
                    selected_indices = sorted(list(selected_indices))

                    # Create initial ranges from selected indices (each index is a single line)
                    initial_ranges = [(idx, idx) for idx in selected_indices]

                    # Expand each range with context window (half of lines_per_snippet on each side)
                    context_window = max(1, (criteria.lines_per_snippet or 10) // 2)
                    expanded_ranges = []
                    for start_idx, end_idx in initial_ranges:
                        expanded_start, expanded_end = self._expand_with_context_window(
                            start_idx, end_idx, total_lines, context_window
                        )
                        expanded_ranges.append((expanded_start, expanded_end))

                    # Merge overlapping/adjacent ranges
                    merged_ranges = self._merge_line_ranges(expanded_ranges)

                    # Limit to max_snippets_per_file and create snippets
                    for i, (start_idx, end_idx) in enumerate(merged_ranges[:max_snippets]):
                        # Calculate average relevance for this snippet
                        snippet_score = sum(line_scores[start_idx:end_idx + 1]) / (end_idx - start_idx + 1)
                        snippet_content = "\n".join(lines[start_idx:end_idx + 1])
                        snippets.append({
                            "start_line": start_idx,
                            "end_line": end_idx,
                            "content": snippet_content,
                            "relevance": snippet_score
                        })
            else:
                # No relevance matches found - fall back to original behavior
                if total_lines <= lines_per_snippet * max_snippets:
                    # Small file, show everything in chunks
                    chunk_size = lines_per_snippet
                    chunk_ranges = []
                    for i in range(0, total_lines, chunk_size):
                        chunk_lines = lines[i:i + chunk_size]
                        if chunk_lines:
                            end_idx = min(i + len(chunk_lines) - 1, total_lines - 1)
                            chunk_ranges.append((i, end_idx, getattr(relevance_score, 'composite', 0.5) if relevance_score else 0.5))

                    # Expand each range with context window (half of lines_per_snippet on each side)
                    context_window = max(1, (criteria.lines_per_snippet or 10) // 2)
                    expanded_ranges = []
                    for start_idx, end_idx, score in chunk_ranges:
                        expanded_start, expanded_end = self._expand_with_context_window(
                            start_idx, end_idx, total_lines, context_window
                        )
                        expanded_ranges.append((expanded_start, expanded_end, score))

                    # Merge overlapping/adjacent ranges
                    merged_ranges = self._merge_line_ranges([(start, end) for start, end, _ in expanded_ranges])

                    # Limit to max_snippets_per_file and create snippets
                    for i, (start_idx, end_idx) in enumerate(merged_ranges[:max_snippets]):
                        snippet_content = "\n".join(lines[start_idx:end_idx + 1])
                        snippets.append({
                            "start_line": start_idx,
                            "end_line": end_idx,
                            "content": snippet_content,
                            "relevance": getattr(relevance_score, 'composite', 0.5) if relevance_score else 0.5
                        })
                else:
                    # Larger file, sample at regular intervals
                    interval = max(1, total_lines // (max_snippets * lines_per_snippet))
                    selected_indices = []
                    for i in range(0, total_lines, interval):
                        if len(selected_indices) >= max_snippets:
                            break
                        selected_indices.append(i)

                    # Convert selected indices to snippets with context window optimization
                    initial_ranges = [(idx, idx) for idx in selected_indices]

                    # Expand each range with context window (half of lines_per_snippet on each side)
                    context_window = max(1, (criteria.lines_per_snippet or 10) // 2)
                    expanded_ranges = []
                    for start_idx, end_idx in initial_ranges:
                        expanded_start, expanded_end = self._expand_with_context_window(
                            start_idx, end_idx, total_lines, context_window
                        )
                        expanded_ranges.append((expanded_start, expanded_end))

                    # Merge overlapping/adjacent ranges
                    merged_ranges = self._merge_line_ranges(expanded_ranges)

                    # Limit to max_snippets_per_file and create snippets
                    for i, (start_idx, end_idx) in enumerate(merged_ranges[:max_snippets]):
                        # For fallback, we use a default relevance score
                        snippet_content = "\n".join(lines[start_idx:end_idx + 1])
                        snippets.append({
                            "start_line": start_idx,
                            "end_line": end_idx,
                            "content": snippet_content,
                            "relevance": getattr(relevance_score, 'composite', 0.5) if relevance_score else 0.5
                        })
        else:
            # No task description, no keywords, and no symbols - use original behavior
            if total_lines <= lines_per_snippet * max_snippets:
                # Small file, show everything in chunks
                chunk_size = lines_per_snippet
                chunk_ranges = []
                for i in range(0, total_lines, chunk_size):
                    chunk_lines = lines[i:i + chunk_size]
                    if chunk_lines:
                        end_idx = min(i + len(chunk_lines) - 1, total_lines - 1)
                        chunk_ranges.append((i, end_idx, getattr(relevance_score, 'composite', 0.5) if relevance_score else 0.5))

                # Expand each range with context window (half of lines_per_snippet on each side)
                context_window = max(1, (criteria.lines_per_snippet or 10) // 2)
                expanded_ranges = []
                for start_idx, end_idx, score in chunk_ranges:
                    expanded_start, expanded_end = self._expand_with_context_window(
                        start_idx, end_idx, total_lines, context_window
                    )
                    expanded_ranges.append((expanded_start, expanded_end, score))

                # Merge overlapping/adjacent ranges
                merged_ranges = self._merge_line_ranges([(start, end) for start, end, _ in expanded_ranges])

                # Limit to max_snippets_per_file and create snippets
                for i, (start_idx, end_idx) in enumerate(merged_ranges[:max_snippets]):
                    snippet_content = "\n".join(lines[start_idx:end_idx + 1])
                    snippets.append({
                        "start_line": start_idx,
                        "end_line": end_idx,
                        "content": snippet_content,
                        "relevance": getattr(relevance_score, 'composite', 0.5) if relevance_score else 0.5
                    })
            else:
                # Larger file, sample at regular intervals
                interval = max(1, total_lines // (max_snippets * lines_per_snippet))
                selected_indices = []
                for i in range(0, total_lines, interval):
                    if len(selected_indices) >= max_snippets:
                        break
                    selected_indices.append(i)

                # Convert selected indices to snippets with context window optimization
                initial_ranges = [(idx, idx) for idx in selected_indices]

                # Expand each range with context window (half of lines_per_snippet on each side)
                context_window = max(1, (criteria.lines_per_snippet or 10) // 2)
                expanded_ranges = []
                for start_idx, end_idx in initial_ranges:
                    expanded_start, expanded_end = self._expand_with_context_window(
                        start_idx, end_idx, total_lines, context_window
                    )
                    expanded_ranges.append((expanded_start, expanded_end))

                # Merge overlapping/adjacent ranges
                merged_ranges = self._merge_line_ranges(expanded_ranges)

                # Limit to max_snippets_per_file and create snippets
                for i, (start_idx, end_idx) in enumerate(merged_ranges[:max_snippets]):
                    # For fallback, we use a default relevance score
                    snippet_content = "\n".join(lines[start_idx:end_idx + 1])
                    snippets.append({
                        "start_line": start_idx,
                        "end_line": end_idx,
                        "content": snippet_content,
                        "relevance": getattr(relevance_score, 'composite', 0.5) if relevance_score else 0.5
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