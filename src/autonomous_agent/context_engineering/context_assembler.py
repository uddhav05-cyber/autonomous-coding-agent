"""
Context Assembly for Autonomous Coding Agent.

This module provides context assembly mechanisms that combine selected
context from various sources into coherent packages suitable for LLM consumption.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import hashlib
import time

from .context_selector import SelectionCriteria
from .context_budgeter import BudgetAllocation
from .duplicate_preventer import DuplicatePolicy


@dataclass
class AssemblyResult:
    """Result of context assembly process."""
    # Assembled context organized by type
    repository_context: Dict[str, Any] = field(default_factory=dict)
    working_context: Dict[str, Any] = field(default_factory=dict)
    task_context: Dict[str, Any] = field(default_factory=dict)
    history_context: Dict[str, Any] = field(default_factory=dict)

    # Assembly metadata
    assembly_id: str = field(default_factory=lambda: hashlib.sha256(
        str(time.time()).encode()
    ).hexdigest()[:16])
    timestamp: float = field(default_factory=time.time)
    assembly_time_ms: float = 0.0

    # Source tracking
    sources_used: List[str] = field(default_factory=list)
    file_count: int = 0
    symbol_count: int = 0
    snippet_count: int = 0

    # Quality metrics
    completeness_score: float = 1.0  # How complete the assembly is (0.0 to 1.0)
    relevance_score: float = 0.0     # Average relevance of included items
    diversity_score: float = 0.0     # How diverse the selected context is

    def is_complete(self) -> bool:
        """Check if assembly is considered complete."""
        return self.completeness_score >= 0.8

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the assembly result."""
        return {
            "assembly_id": self.assembly_id,
            "timestamp": self.timestamp,
            "assembly_time_ms": self.assembly_time_ms,
            "sources_used": self.sources_used.copy(),
            "file_count": self.file_count,
            "symbol_count": self.symbol_count,
            "snippet_count": self.snippet_count,
            "completeness_score": self.completeness_score,
            "relevance_score": self.relevance_score,
            "diversity_score": self.diversity_score
        }


class ContextAssembler:
    """
    Context Assembler that combines selected context from various sources
    into coherent packages suitable for LLM consumption.

    This class provides:
    - Assembly of context from repository, working, task, and history sources
    - Context ordering and prioritization
    - Context compression and summarization where needed
    - Context validation and integrity checking
    - Assembly metadata and quality scoring
    """

    def __init__(self):
        """Initialize the Context Assembler."""
        pass

    def assemble_context(
        self,
        selected_context: Dict[str, Any],
        repository_metadata: Any,
        selection_criteria: Optional[SelectionCriteria] = None,
        budget_allocation: Optional[BudgetAllocation] = None,
        duplicate_policy: Optional[DuplicatePolicy] = None
    ) -> AssemblyResult:
        """
        Assemble context from selected items into a coherent package.

        Args:
            selected_context: Context items selected by the ContextSelector
            repository_metadata: Repository metadata from Phase 3
            selection_criteria: Criteria used for selection
            budget_allocation: Budget allocation for token limits
            duplicate_policy: Policy for duplicate handling

        Returns:
            AssemblyResult containing the assembled context
        """
        start_time = time.time()

        if selection_criteria is None:
            selection_criteria = SelectionCriteria()
        if budget_allocation is None:
            budget_allocation = BudgetAllocation()
        if duplicate_policy is None:
            duplicate_policy = DuplicatePolicy()

        # Initialize result
        result = AssemblyResult()

        # Assemble repository context
        result.repository_context = self._assemble_repository_context(
            selected_context, repository_metadata, selection_criteria
        )
        result.sources_used.append("repository")

        # Assemble working context (files, symbols, snippets)
        result.working_context = self._assemble_working_context(
            selected_context, selection_criteria
        )
        result.sources_used.append("working")
        result.file_count = len(result.working_context.get("files", []))
        result.symbol_count = len(result.working_context.get("symbols", []))
        result.snippet_count = len(result.working_context.get("snippets", []))

        # Assemble task context
        result.task_context = self._assemble_task_context(
            selected_context, selection_criteria
        )
        result.sources_used.append("task")

        # Assemble history context (would come from session in full implementation)
        result.history_context = self._assemble_history_context(
            selected_context, selection_criteria
        )
        if result.history_context:  # Only count if we actually have history
            result.sources_used.append("history")

        # Calculate quality metrics
        result.completeness_score = self._calculate_completeness_score(
            result, selection_criteria
        )
        result.relevance_score = self._calculate_relevance_score(
            selected_context
        )
        result.diversity_score = self._calculate_diversity_score(
            result.working_context
        )

        # Record assembly time
        result.assembly_time_ms = (time.time() - start_time) * 1000

        return result

    def _assemble_repository_context(
        self,
        selected_context: Dict[str, Any],
        repository_metadata: Any,
        selection_criteria: SelectionCriteria
    ) -> Dict[str, Any]:
        """
        Assemble repository-level context.

        Args:
            selected_context: Context items selected by the ContextSelector
            repository_metadata: Repository metadata from Phase 3
            selection_criteria: Selection criteria used

        Returns:
            Dictionary containing assembled repository context
        """
        repo_context = {
            "metadata": {},
            "structure_hints": {},
            "project_info": {}
        }

        # Extract repository information from selected context
        if "repository_info" in selected_context:
            repo_context["metadata"] = selected_context["repository_info"].copy()

        # Extract structural hints
        repo_context["structure_hints"] = self._extract_structure_hints(
            repository_metadata, selection_criteria
        )

        # Add project information
        repo_context["project_info"] = {
            "root_path": str(getattr(repository_metadata, 'root_path', '')),
            "is_git_repo": getattr(repository_metadata, 'is_git_repo', False),
            "git_branch": getattr(repository_metadata, 'git_branch', None),
            "git_commit": getattr(repository_metadata, 'git_commit', None),
            "project_type": getattr(repository_metadata, 'project_type', None),
            "language_hints": list(getattr(repository_metadata, 'language_hints', [])),
            "build_system_hints": list(getattr(repository_metadata, 'build_system_hints', [])),
            "documentation_hints": list(getattr(repository_metadata, 'documentation_hints', [])),
            "file_count_estimate": self._estimate_file_count(repository_metadata),
            "size_estimate": self._estimate_repository_size(repository_metadata)
        }

        return repo_context

    def _assemble_working_context(
        self,
        selected_context: Dict[str, Any],
        selection_criteria: SelectionCriteria
    ) -> Dict[str, Any]:
        """
        Assemble working context (files, symbols, snippets).

        Args:
            selected_context: Context items selected by the ContextSelector
            selection_criteria: Selection criteria used

        Returns:
            Dictionary containing assembled working context
        """
        working_context = {
            "files": [],
            "symbols": [],
            "snippets": [],
            "summary": {}
        }

        # Add selected files
        if "files" in selected_context:
            working_context["files"] = selected_context["files"].copy()

        # Add extracted symbols
        if "symbols" in selected_context:
            working_context["symbols"] = selected_context["symbols"].copy()

        # Add extracted snippets
        if "snippets" in selected_context:
            working_context["snippets"] = selected_context["snippets"].copy()

        # Add summary information
        working_context["summary"] = {
            "total_files": len(working_context["files"]),
            "total_symbols": len(working_context["symbols"]),
            "total_snippets": len(working_context["snippets"]),
            "languages_present": self._get_present_languages(working_context["files"]),
            "file_types_present": self._get_present_file_types(working_context["files"])
        }

        return working_context

    def _assemble_task_context(
        self,
        selected_context: Dict[str, Any],
        selection_criteria: SelectionCriteria
    ) -> Dict[str, Any]:
        """
        Assemble task-specific context.

        Args:
            selected_context: Context items selected by the ContextSelector
            selection_criteria: Selection criteria used

        Returns:
            Dictionary containing assembled task context
        """
        task_context = {
            "description": "",  # Would be provided by the task manager
            "objectives": [],
            "constraints": [],
            "requirements": [],
            "context_hints": {}
        }

        # In a full implementation, this would come from the task description
        # For now, we'll leave it mostly empty and let the caller fill it in

        # Add any task-specific hints from the selection process
        task_context["context_hints"] = {
            "selection_criteria_used": selection_criteria.__dict__,
            "context_assembly_timestamp": time.time()
        }

        return task_context

    def _assemble_history_context(
        self,
        selected_context: Dict[str, Any],
        selection_criteria: SelectionCriteria
    ) -> Dict[str, Any]:
        """
        Assemble history context from previous interactions.

        In a full implementation, this would come from session history.
        For this MVP, we'll return minimal context.

        Args:
            selected_context: Context items selected by the ContextSelector
            selection_criteria: Selection criteria used

        Returns:
            Dictionary containing assembled history context
        """
        # Placeholder for history context
        # In a full implementation, this would include:
        # - Previous task descriptions
        # - Previous context selections
        # - User feedback and corrections
        # - Learned patterns and preferences

        history_context = {
            "previous_tasks": [],
            "context_reuse_opportunities": [],
            "learned_patterns": {},
            "session_summary": {}
        }

        # For now, return minimal history context
        # This would be expanded in a full implementation with session tracking
        return history_context

    def _extract_structure_hints(
        self,
        repository_metadata: Any,
        selection_criteria: SelectionCriteria
    ) -> Dict[str, Any]:
        """
        Extract structural hints from repository metadata.

        Args:
            repository_metadata: Repository metadata from Phase 3
            selection_criteria: Selection criteria used

        Returns:
            Dictionary containing structural hints
        """
        hints = {
            "project_type": getattr(repository_metadata, 'project_type', None),
            "is_git_repo": getattr(repository_metadata, 'is_git_repo', False),
            "primary_languages": list(getattr(repository_metadata, 'language_hints', []))[:5],
            "build_systems": list(getattr(repository_metadata, 'build_system_hints', []))[:3],
            "documentation_types": list(getattr(repository_metadata, 'documentation_hints', []))[:3],
            "directory_structure": {},
            "file_organization": {}
        }

        # Add directory structure information if requested
        if selection_criteria.include_structure:
            structure_map = getattr(repository_metadata, 'structure_map', {})
            # Limit to avoid too much detail
            top_dirs = dict(list(structure_map.items())[:10])
            hints["directory_structure"] = {
                dir_path: {
                    "file_count": len(files),
                    "sample_files": files[:5] if len(files) > 5 else files,
                    "has_subdirectories": False  # Would need deeper inspection
                }
                for dir_path, files in top_dirs.items()
            }

            # Add file organization hints
            hints["file_organization"] = self._analyze_file_organization(structure_map)

        return hints

    def _analyze_file_organization(
        self,
        structure_map: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """
        Analyze file organization patterns in the repository.

        Args:
            structure_map: Directory to file mapping from repository metadata

        Returns:
            Dictionary containing file organization analysis
        """
        if not structure_map:
            return {"pattern": "unknown", "depth": 0, "breadth": 0}

        # Calculate basic statistics
        total_dirs = len(structure_map)
        total_files = sum(len(files) for files in structure_map.values())
        avg_files_per_dir = total_files / total_dirs if total_dirs > 0 else 0

        # Determine if structure is flat or hierarchical
        max_depth = self._calculate_max_depth(structure_map)

        organization = {
            "total_directories": total_dirs,
            "total_files": total_files,
            "average_files_per_directory": round(avg_files_per_dir, 2),
            "max_depth": max_depth,
            "structure_type": "flat" if max_depth <= 1 else "hierarchical",
            "distribution": "even" if avg_files_per_dir < 10 else "uneven"
        }

        return organization

    def _calculate_max_depth(
        self,
        structure_map: Dict[str, List[str]]
    ) -> int:
        """
        Calculate maximum directory depth in the structure map.

        Args:
            structure_map: Directory to file mapping

        Returns:
            Maximum depth found
        """
        max_depth = 0
        for dir_path in structure_map.keys():
            # Count path separators to estimate depth
            depth = dir_path.count('/') + dir_path.count('\\')
            max_depth = max(max_depth, depth)
        return max_depth

    def _get_present_languages(self, files: List[Dict[str, Any]]) -> List[str]:
        """
        Get list of programming languages present in the selected files.

        Args:
            files: List of file context dictionaries

        Returns:
            List of unique language identifiers
        """
        languages = set()
        for file_ctx in files:
            lang = file_ctx.get("language", "unknown")
            if lang != "unknown":
                languages.add(lang)
        return sorted(list(languages))

    def _get_present_file_types(self, files: List[Dict[str, Any]]) -> List[str]:
        """
        Get list of file types present in the selected files.

        Args:
            files: List of file context dictionaries

        Returns:
            List of unique file type identifiers
        """
        file_types = set()
        for file_ctx in files:
            file_path = file_ctx.get("path", "")
            if file_path:
                extension = Path(file_path).suffix.lower()
                if extension:
                    file_types.add(extension)
        return sorted(list(file_types))

    def _estimate_file_count(self, repository_metadata: Any) -> int:
        """
        Estimate total number of files in the repository.

        Args:
            repository_metadata: Repository metadata from Phase 3

        Returns:
            Estimated file count
        """
        structure_map = getattr(repository_metadata, 'structure_map', {})
        return sum(len(files) for files in structure_map.values())

    def _estimate_repository_size(self, repository_metadata: Any) -> Dict[str, Any]:
        """
        Estimate total size of the repository.

        Args:
            repository_metadata: Repository metadata from Phase 3

        Returns:
            Dictionary containing size estimates
        """
        # This would require actually reading files or having size metadata
        # For now, return placeholder values
        return {
            "estimated_size_mb": "unknown",
            "estimated_line_count": "unknown",
            "note": "Size estimation would require file system access"
        }

    def _calculate_completeness_score(
        self,
        result: AssemblyResult,
        selection_criteria: SelectionCriteria
    ) -> float:
        """
        Calculate completeness score for the assembly.

        Args:
            result: Assembly result to score
            selection_criteria: Selection criteria used

        Returns:
            Completeness score between 0.0 and 1.0
        """
        score = 1.0

        # Penalize for missing expected context types
        expected_sources = ["repository", "working", "task"]
        missing_sources = [
            source for source in expected_sources
            if source not in result.sources_used
        ]
        if missing_sources:
            score -= len(missing_sources) * 0.2  # 20% penalty per missing source

        # Penalize for extremely low counts when we expected more
        if selection_criteria.max_files and selection_criteria.max_files > 0:
            expected_min_files = max(1, selection_criteria.max_files // 10)  # Expect at least 10% of max
            if result.file_count < expected_min_files:
                score -= 0.3  # 30% penalty for having too few files

        # Penalize for zero symbols or snippets when we might expect them
        if result.symbol_count == 0 and result.file_count > 5:
            score -= 0.1  # Small penalty for no symbols in multi-file context

        if result.snippet_count == 0 and result.file_count > 3 and selection_criteria.extract_snippets:
            score -= 0.1  # Small penalty for no snippets when extraction was requested

        # Ensure score is in valid range
        return max(0.0, min(1.0, score))

    def _calculate_relevance_score(
        self,
        selected_context: Dict[str, Any]
    ) -> float:
        """
        Calculate average relevance score of selected context.

        Args:
            selected_context: Context items selected by the ContextSelector

        Returns:
            Average relevance score between 0.0 and 1.0
        """
        relevance_scores = []

        # Collect relevance scores from files
        for file_ctx in selected_context.get("files", []):
            relevance_obj = file_ctx.get("relevance_score")
            if relevance_obj and hasattr(relevance_obj, 'composite'):
                relevance_scores.append(relevance_obj.composite)
            elif isinstance(relevance_obj, (int, float)):
                relevance_scores.append(float(relevance_obj))

        # If we have scores, return the average
        if relevance_scores:
            return sum(relevance_scores) / len(relevance_scores)

        # If no specific scores, return a default based on selection
        # This indicates we used basic selection rather than relevance-based
        return 0.5  # Neutral score for basic selection

    def _calculate_diversity_score(
        self,
        working_context: Dict[str, Any]
    ) -> float:
        """
        Calculate diversity score of the working context.

        Args:
            working_context: Working context containing files, symbols, snippets

        Returns:
            Diversity score between 0.0 and 1.0
        """
        if not working_context:
            return 0.0

        diversity_factors = []

        # Language diversity
        languages = self._get_present_languages(working_context.get("files", []))
        if len(languages) > 1:
            language_diversity = min(1.0, len(languages) / 5.0)  # Normalize to 5 languages
            diversity_factors.append(language_diversity)
        elif len(languages) == 1:
            diversity_factors.append(0.5)  # Some diversity but not much
        else:
            diversity_factors.append(0.0)  # No language diversity

        # File type diversity
        file_types = self._get_present_file_types(working_context.get("files", []))
        if len(file_types) > 1:
            type_diversity = min(1.0, len(file_types) / 10.0)  # Normalize to 10 types
            diversity_factors.append(type_diversity)
        elif len(file_types) == 1:
            diversity_factors.append(0.4)
        else:
            diversity_factors.append(0.0)

        # Context type diversity (files vs symbols vs snippets)
        has_files = len(working_context.get("files", [])) > 0
        has_symbols = len(working_context.get("symbols", [])) > 0
        has_snippets = len(working_context.get("snippets", [])) > 0

        context_types_present = sum([has_files, has_symbols, has_snippets])
        if context_types_present > 1:
            type_diversity = context_types_present / 3.0  # Normalize to 3 types
            diversity_factors.append(type_diversity)
        else:
            diversity_factors.append(0.3 if context_types_present == 1 else 0.0)

        # Calculate average diversity
        if diversity_factors:
            return sum(diversity_factors) / len(diversity_factors)
        else:
            return 0.5  # Default middle value

    def __repr__(self) -> str:
        return f"ContextAssembler()"