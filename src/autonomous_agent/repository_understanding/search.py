"""
Code Search Module for Repository Understanding.

This module provides code search functionality with ripgrep integration,
progressive refinement capabilities, and workspace boundary enforcement.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Set, Optional
import subprocess


@dataclass
class SearchResult:
    """Represents a single search result."""
    file_path: Path
    line_number: int
    line_content: str
    context_before: List[str]
    context_after: List[str]
    score: float


class CodeSearchModule:
    """
    Code search module with ripgrep integration and progressive refinement.

    Features:
    - Ripgrep-powered indexed search with Python fallback
    - Workspace boundary enforcement
    - Progressive search refinement
    - Configurable context extraction
    - Result ranking and scoring
    """

    def __init__(self, workspace):
        """
        Initialize the code search module.

        Args:
            workspace: Workspace object providing boundary information
        """
        self.workspace = workspace
        self._ripgrep_available = self._check_ripegrep_availability()

    def _check_ripegrep_availability(self) -> bool:
        """Check if ripgrep is available on the system."""
        try:
            subprocess.run(
                ["rg", "--version"],
                capture_output=True,
                check=True,
                timeout=5
            )
            return True
        except (subprocess.SubprocessError, FileNotFoundError, TimeoutError):
            return False

    def execute_search(
        self,
        query: str,
        file_paths: List[Path],
        context_lines: int = 2,
        use_regex: bool = False
    ) -> List[SearchResult]:
        """
        Execute a search operation.

        Args:
            query: Search query string
            file_paths: List of file paths to search within
            context_lines: Number of context lines to include before/after matches
            use_regex: Whether to treat query as regex pattern

        Returns:
            List of SearchResult objects sorted by relevance score
        """
        # Filter file paths to only include those within workspace
        safe_paths = self._get_safe_file_paths(file_paths)

        if not safe_paths:
            return []

        # Use ripgrep if available, otherwise fallback to Python implementation
        if self._ripgrep_available:
            try:
                return self._execute_ripegrep_search(
                    query, safe_paths, context_lines, use_regex
                )
            except Exception:
                # Fallback to Python implementation if ripgrep fails
                pass

        # Fallback to Python implementation
        return self._execute_fallback_search(
            query, safe_paths, context_lines, use_regex
        )

    def _execute_ripegrep_search(
        self,
        query: str,
        file_paths: List[Path],
        context_lines: int,
        use_regex: bool
    ) -> List[SearchResult]:
        """Execute search using ripgrep."""
        # Build ripgrep command
        cmd = ["rg"]

        # Add context lines
        cmd.extend(["-C", str(context_lines)])

        # Add file type filters if needed (optional optimization)
        # cmd.extend(["--type", "py"])  # Example for Python files

        # Add regex flag if needed
        if use_regex:
            cmd.extend(["--regexp", query])
        else:
            # Literal search
            cmd.extend(["--fixed-strings", query])

        # Add files to search
        cmd.extend([str(p) for p in file_paths])

        # Execute ripgrep
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        # Parse output
        if result.returncode == 0:
            return self._parse_ripegrep_output(
                result.stdout.splitlines(),
                set(str(p) for p in file_paths),
                context_lines,
                query
            )
        elif result.returncode == 1:
            # No matches found
            return []
        else:
            # Error occurred
            raise RuntimeError(f"Ripgrep failed: {result.stderr}")

    def _parse_ripegrep_output(
        self,
        lines: List[str],
        file_paths_set: Set[str],
        context_lines: int,
        query: str
    ) -> List[SearchResult]:
        """Parse ripgrep output into SearchResult objects."""
        results = []

        if not lines:
            return results

        # Parse ripgrep output format:
        # file_path:line_number:match_line
        # or with context: file_path:line_number-:context_line

        i = 0
        while i < len(lines):
            line = lines[i]

            # Skip empty lines (separators between matches)
            if not line.strip():
                i += 1
                continue

            # Check if this line starts a match record (contains first colon)
            if ':' in line and not line.startswith(' ') and not line.startswith('-'):
                # This could be a match line: file:line:content
                parts = line.split(':', 2)
                if len(parts) >= 3:
                    try:
                        file_path_str, line_num_str, match_line = parts
                        file_path = Path(file_path_str)
                        line_number = int(line_num_str)

                        # Validate file path is in our set and within workspace
                        if (str(file_path) in file_paths_set and
                            self._is_within_workspace(file_path)):

                            # Collect context lines before and after
                            context_before = []
                            context_after = []

                            # Look backwards for context lines (non-match lines)
                            j = i - 1
                            while j >= 0 and len(context_before) < context_lines:
                                context_line = lines[j]
                                # Stop if we hit another match or separator
                                if (':' in context_line and
                                    not context_line.startswith(' ') and
                                    not context_line.startswith('-') and
                                    context_line.count(':') >= 2):
                                    break
                                # Check if it's a context line (starts with - or contains line number with -)
                                if (context_line.startswith('-') or
                                    (':' in context_line and
                                     any(c.isdigit() for c in context_line.split(':')[1]) and
                                     '-' in context_line.split(':')[1])):
                                    context_before.insert(0, context_line[1:] if context_line.startswith('-') else context_line)
                                j -= 1

                            # Look forwards for context lines
                            j = i + 1
                            while j < len(lines) and len(context_after) < context_lines:
                                context_line = lines[j]
                                # Stop if we hit another match or separator
                                if (':' in context_line and
                                    not context_line.startswith(' ') and
                                    not context_line.startswith('-') and
                                    context_line.count(':') >= 2):
                                    break
                                # Check if it's a context line
                                if (context_line.startswith('-') or
                                    (':' in context_line and
                                     any(c.isdigit() for c in context_line.split(':')[1]) and
                                     '-' in context_line.split(':')[1])):
                                    context_after.append(context_line[1:] if context_line.startswith('-') else context_line)
                                j += 1

                            # Calculate relevance score
                            score = self._calculate_match_score(match_line, query, use_regex=False)

                            result = SearchResult(
                                file_path=file_path,
                                line_number=line_number,
                                line_content=match_line,
                                context_before=context_before,
                                context_after=context_after,
                                score=score
                            )
                            results.append(result)

                            # Move index past this match and its context
                            i = j
                            continue
                    except (ValueError, IndexError):
                        # If parsing fails, move to next line
                        pass

            i += 1

        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)
        return results

    def _execute_fallback_search(
        self,
        query: str,
        file_paths: List[Path],
        context_lines: int,
        use_regex: bool
    ) -> List[SearchResult]:
        """Fallback search implementation using Python's built-in file reading."""
        results = []

        # Prepare regex pattern if needed
        if use_regex:
            try:
                pattern = re.compile(query)
            except re.error:
                # Invalid regex, treat as literal
                pattern = re.compile(re.escape(query))
                use_regex = False
        else:
            # For literal search, escape regex special chars
            literal_query = re.escape(query)
            pattern = re.compile(literal_query, re.IGNORECASE)

        # Search each file
        for file_path in file_paths:
            # Ensure file is within workspace
            if not self._is_within_workspace(file_path):
                continue

            try:
                # Read file content
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                lines = content.splitlines()

                # Search each line
                for i, line in enumerate(lines):
                    line_num = i + 1  # 1-indexed line numbers

                    # Check for match
                    match_found = False
                    if use_regex:
                        match_found = bool(pattern.search(line))
                    else:
                        match_found = query.lower() in line.lower()

                    if match_found:
                        # Extract context
                        context_before = []
                        context_after = []

                        # Get context before
                        start_idx = max(0, i - context_lines)
                        context_before = lines[start_idx:i]

                        # Get context after
                        end_idx = min(len(lines), i + context_lines + 1)
                        context_after = lines[i+1:end_idx]

                        # Calculate basic relevance score (can be enhanced)
                        score = self._calculate_match_score(line, query, use_regex)

                        result = SearchResult(
                            file_path=file_path,
                            line_number=line_num,
                            line_content=line,
                            context_before=context_before,
                            context_after=context_after,
                            score=score
                        )
                        results.append(result)

            except (OSError, IOError, UnicodeDecodeError):
                # Skip unreadable files
                continue

        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)
        return results

    def _calculate_match_score(self, line: str, query: str, use_regex: bool) -> float:
        """
        Calculate a relevance score for a match.

        Args:
            line: The matched line
            query: The search query
            use_regex: Whether query is a regex pattern

        Returns:
            Score between 0.0 and 1.0
        """
        if use_regex:
            # For regex matches that we know succeeded, return a good score
            return 0.85

        # For literal search, calculate based on query term frequency in line
        query_lower = query.lower()
        line_lower = line.lower()

        # Count occurrences of query in line
        count = line_lower.count(query_lower)

        # Calculate base score from exact occurrences
        exact_score = min(count * 0.45, 0.6)  # Up to 0.6 for exact occurrences

        # Extract word components by splitting on non-alphabetic characters
        # This gives us alphabetic-only components, ignoring underscores and punctuation
        query_components = set([c for c in re.split(r'[^a-z]+', query_lower) if c])
        line_components = set([c for c in re.split(r'[^a-z]+', line_lower) if c])

        # Exact component matches
        exact_component_matches = len(query_components.intersection(line_components))
        exact_component_score = min(exact_component_matches * 0.3, 0.4)  # Up to 0.4 for exact component matches

        # Partial component matches (e.g., "auth" in "authenticate")
        partial_component_score = 0.0
        if exact_component_matches == 0 and len(query_components) > 0:
            for q_comp in query_components:
                for l_comp in line_components:
                    # Check if one is contained in the other
                    if len(q_comp) > 2 and len(l_comp) > 2:  # Only for reasonable length components
                        if q_comp in l_comp or l_comp in q_comp:
                            # Partial match - score based on overlap ratio
                            overlap = min(len(q_comp), len(l_comp))
                            max_len = max(len(q_comp), len(l_comp))
                            if max_len > 0:
                                partial_component_score = max(partial_component_score, overlap / max_len * 1.0)

        # Combine scores, ensuring we don't exceed 1.0
        total_score = min(
            exact_score + exact_component_score + partial_component_score,
            1.0
        )

        # Ensure we return a reasonable minimum for any kind of match
        if count > 0 or exact_component_matches > 0 or partial_component_score > 0:
            return max(total_score, 0.1)
        else:
            return 0.0

    def progressive_refinement_search(
        self,
        initial_query: str,
        file_paths: List[Path],
        context_lines: int = 2,
        max_iterations: int = 3
    ) -> List[SearchResult]:
        """
        Perform progressive refinement search: start broad, then narrow based on results.

        Args:
            initial_query: Starting search query
            file_paths: List of file paths to search within
            context_lines: Number of context lines to include
            max_iterations: Maximum number of refinement iterations

        Returns:
            List of SearchResult objects from final iteration
        """
        current_query = initial_query
        all_results = []

        for iteration in range(max_iterations):
            # Execute search with current query
            results = self.execute_search(
                query=current_query,
                file_paths=file_paths,
                context_lines=context_lines,
                use_regex=False
            )

            if not results:
                # No results found, break early
                break

            all_results = results

            # If we have results, try to refine the query based on context
            if iteration < max_iterations - 1:  # Don't refine on last iteration
                # Extract potential refinement terms from result contexts
                refinement_terms = self._extract_refinement_terms(results)
                if refinement_terms:
                    # Combine original query with refinement terms
                    current_query = f"{initial_query} {' '.join(refinement_terms[:3])}"
                else:
                    # No refinement terms found, break
                    break
            else:
                # Last iteration, keep results as is
                break

        return all_results

    def _extract_refinement_terms(self, results: List[SearchResult]) -> List[str]:
        """Extract potential refinement terms from search results."""
        # Collect words from context lines that might be relevant
        term_freq = {}
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'
        }

        # Analyze context from top results
        for result in results[:5]:  # Top 5 results
            # Check context before and after
            for context_line in result.context_before + result.context_after:
                words = re.findall(r'\b[a-zA-Z_]+\b', context_line.lower())
                for word in words:
                    if word not in stop_words and len(word) > 2:
                        term_freq[word] = term_freq.get(word, 0) + 1

        # Return terms sorted by frequency (descending)
        sorted_terms = sorted(term_freq.items(), key=lambda x: x[1], reverse=True)
        return [term for term, freq in sorted_terms if freq >= 2]  # At least 2 occurrences

    def _get_safe_file_paths(self, file_paths: List[Path]) -> List[Path]:
        """Filter file paths to only include those within workspace boundaries."""
        safe_paths = []
        for file_path in file_paths:
            if self._is_within_workspace(file_path):
                safe_paths.append(file_path)
        return safe_paths

    def _is_within_workspace(self, file_path: Path) -> bool:
        """Check if a file path is within the workspace boundaries."""
        try:
            # Convert to Path objects for comparison
            resolved_file = file_path.resolve()
            resolved_workspace = Path(self.workspace.workspace_root).resolve()

            # Check if file path is within workspace
            return resolved_workspace in resolved_file.parents or resolved_file == resolved_workspace
        except (OSError, ValueError):
            # If we can't resolve paths, be safe and exclude
            return False

    def extract_context(self, file_path: Path, line_number: int, context_lines: int = 2):
        """
        Extract context around a specific line in a file.

        Args:
            file_path: Path to the file
            line_number: 1-indexed line number to extract context around
            context_lines: Number of context lines to include before/after

        Returns:
            Tuple of (context_before, line_content, context_after)
        """
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            lines = content.splitlines()

            # Convert to 0-indexed
            idx = line_number - 1

            # Validate line number
            if idx < 0 or idx >= len(lines):
                return [], "", []

            # Get the line content
            line_content = lines[idx]

            # Get context before
            start_idx = max(0, idx - context_lines)
            context_before = lines[start_idx:idx]

            # Get context after
            end_idx = min(len(lines), idx + context_lines + 1)
            context_after = lines[idx+1:end_idx]

            return context_before, line_content, context_after
        except (OSError, IOError, UnicodeDecodeError):
            # Return empty values if file can't be read
            return [], "", ""


def create_code_search_system(workspace) -> CodeSearchModule:
    """
    Factory function to create a code search system.

    Args:
        workspace: Workspace object providing boundary information

    Returns:
        Configured CodeSearchModule instance
    """
    return CodeSearchModule(workspace)