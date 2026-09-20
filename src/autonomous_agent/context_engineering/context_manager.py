"""
Context Manager for Autonomous Coding Agent.

This module provides the main ContextManager class that coordinates context
selection, budgeting, assembly, duplicate prevention, and metrics to provide
optimal LLM context within token limits.
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from uuid import uuid4

from .context_selector import SelectionCriteria
from .context_budgeter import BudgetAllocation, ContextBudgeter
from .context_assembler import AssemblyResult
from .duplicate_preventer import DuplicatePolicy
from autonomous_agent.repository_understanding import (
    RepositoryMetadata,
    RepositoryDiscovery,
    RepositoryMetadataManager,
    RelevanceEngine,
    CodeSearchModule,
    SymbolDependencyAnalyzer
)
from autonomous_agent.workspace import Workspace


@dataclass
class ContextPackage:
    """A package of context ready for LLM consumption."""
    # Context content organized by type and source
    repository_context: Dict[str, Any] = field(default_factory=dict)
    working_context: Dict[str, Any] = field(default_factory=dict)
    task_context: Dict[str, Any] = field(default_factory=dict)
    history_context: Dict[str, Any] = field(default_factory=dict)

    # Metadata about the context package
    context_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: float = field(default_factory=time.time)
    total_tokens: int = 0
    token_breakdown: Dict[str, int] = field(default_factory=dict)

    # Tracking information
    sources_used: List[str] = field(default_factory=list)
    selection_criteria: Optional[SelectionCriteria] = None
    budget_allocation: Optional[BudgetAllocation] = None
    duplicate_policy: Optional[DuplicatePolicy] = None

    # Validation and security
    workspace_compliant: bool = True
    content_sanitized: bool = False
    validation_passed: bool = True

    def is_within_budget(self, max_tokens: int) -> bool:
        """Check if context package is within token budget."""
        return self.total_tokens <= max_tokens

    def get_context_summary(self) -> Dict[str, Any]:
        """Get a summary of the context package."""
        return {
            "context_id": self.context_id,
            "timestamp": self.timestamp,
            "total_tokens": self.total_tokens,
            "token_breakdown": self.token_breakdown.copy(),
            "sources_used": self.sources_used.copy(),
            "workspace_compliant": self.workspace_compliant,
            "validation_passed": self.validation_passed
        }


class ContextManager:
    """
    Main Context Manager that coordinates all context engineering functions.

    This class provides:
    - Context selection using relevance signals from Phase 3
    - Token budgeting and enforcement
    - Context assembly from multiple sources
    - Duplicate prevention and detection
    - Context metrics and tracking
    - Workspace boundary enforcement and security
    """

    def __init__(
        self,
        workspace: Workspace,
        repository_discovery: Optional[RepositoryDiscovery] = None,
        metadata_manager: Optional[RepositoryMetadataManager] = None,
        relevance_engine: Optional[RelevanceEngine] = None,
        search_module: Optional[CodeSearchModule] = None,
        symbol_analyzer: Optional[SymbolDependencyAnalyzer] = None,
        enable_metrics: bool = True,
        enable_duplicate_prevention: bool = True,
        default_budget_tokens: int = 4000
    ):
        """
        Initialize the Context Manager.

        Args:
            workspace: The workspace instance for boundary enforcement
            repository_discovery: Repository discovery component (Phase 3)
            metadata_manager: Metadata manager component (Phase 3)
            relevance_engine: Relevance engine component (Phase 3)
            search_module: Code search module (Phase 3)
            symbol_analyzer: Symbol and dependency analyzer (Phase 3)
            enable_metrics: Whether to collect and track metrics
            enable_duplicate_prevention: Whether to enable duplicate prevention
            default_budget_tokens: Default token budget for context packages
        """
        self.workspace = workspace
        self.repository_discovery = repository_discovery
        self.metadata_manager = metadata_manager
        self.relevance_engine = relevance_engine
        self.search_module = search_module
        self.symbol_analyzer = symbol_analyzer
        self.enable_metrics = enable_metrics
        self.enable_duplicate_prevention = enable_duplicate_prevention
        self.default_budget_tokens = default_budget_tokens

        # Initialize subsystems
        if self.enable_metrics:
            from .context_metrics import ContextMetrics
            self.metrics = ContextMetrics()
        else:
            self.metrics = None

        if self.enable_duplicate_prevention:
            from .duplicate_preventer import DuplicatePreventer
            self.duplicate_preventer = DuplicatePreventer()
        else:
            self.duplicate_preventer = None

        # Cache for performance optimization
        self._context_cache: Dict[str, ContextPackage] = {}
        self._max_cache_size = 100

        # State tracking
        self._last_repository_metadata: Optional[RepositoryMetadata] = None
        self._last_context_package: Optional[ContextPackage] = None

    def create_context_package(
        self,
        task_description: str,
        selection_criteria: Optional[SelectionCriteria] = None,
        budget_allocation: Optional[BudgetAllocation] = None,
        duplicate_policy: Optional[DuplicatePolicy] = None,
        max_tokens: Optional[int] = None,
        use_cache: bool = True
    ) -> ContextPackage:
        """
        Create a context package for the given task.

        This is the main entry point that coordinates all context engineering
        functions to produce an optimized context package.

        Args:
            task_description: Description of the current task
            selection_criteria: Criteria for context selection
            budget_allocation: Allocation of token budget across context types
            duplicate_policy: Policy for handling duplicate context
            max_tokens: Maximum tokens allowed in context package
            use_cache: Whether to use cached results if available

        Returns:
            ContextPackage containing assembled context within constraints
        """
        start_time = time.time()

        # Use defaults if not provided
        if selection_criteria is None:
            selection_criteria = SelectionCriteria()
        if budget_allocation is None:
            budget_allocation = BudgetAllocation()
        if duplicate_policy is None:
            duplicate_policy = DuplicatePolicy()
        if max_tokens is None:
            max_tokens = self.default_budget_tokens

        # Check cache if enabled
        cache_key = self._generate_cache_key(
            task_description, selection_criteria, budget_allocation,
            duplicate_policy, max_tokens
        )
        if use_cache and cache_key in self._context_cache:
            cached_package = self._context_cache[cache_key]
            # Validate cache is still fresh
            if self._is_cache_valid(cached_package):
                if self.metrics:
                    self.metrics.record_cache_hit()
                return cached_package

        if self.metrics:
            self.metrics.record_cache_miss()

        # Step 1: Get latest repository understanding from Phase 3
        repository_metadata = self._get_repository_understanding()

        # Step 2: Select relevant context based on criteria and relevance
        selected_context = self._select_context(
            task_description, repository_metadata, selection_criteria
        )

        # Step 3: Apply duplicate prevention if enabled
        if self.enable_duplicate_prevention and self.duplicate_preventer:
            selected_context = self.duplicate_preventer.remove_duplicates(
                selected_context, duplicate_policy
            )
            if self.metrics:
                duplicates_removed = len(selected_context.get("all_items", [])) - len(selected_context.get("unique_items", []))
                self.metrics.record_duplicate_detection(
                    duplicates_detected=duplicates_removed,
                    duplicates_removed=duplicates_removed,
                    tokens_saved=0
                )

        # Step 4: Assemble context from selected items
        assembled_context = self._assemble_context(
            selected_context, repository_metadata, selection_criteria
        )

        # Step 5: Apply context budgeting
        budgeted_context = self._apply_budgeting(
            assembled_context, budget_allocation, max_tokens
        )

        # Step 6: Validate and sanitize context for security
        validated_context = self._validate_and_sanitize_context(
            budgeted_context
        )

        # Step 7: Create final context package
        context_package = self._create_context_package(
            task_description, validated_context, selection_criteria,
            budget_allocation, duplicate_policy, max_tokens,
            start_time
        )

        # Step 8: Update metrics
        if self.metrics:
            self.metrics.record_context_creation(
                context_package, time.time() - start_time
            )

        # Step 9: Cache the result if enabled
        if use_cache:
            self._cache_context_package(cache_key, context_package)

        # Step 10: Update state tracking
        self._last_context_package = context_package
        self._last_repository_metadata = repository_metadata

        return context_package

    def _get_repository_understanding(self) -> RepositoryMetadata:
        """Get the latest repository understanding from Phase 3 components."""
        if not self.repository_discovery:
            # Return basic metadata if discovery not available
            return RepositoryMetadata(
                root_path=self.workspace.workspace_root,
                is_git_repo=False
            )

        # Get fresh metadata from discovery
        metadata = self.repository_discovery.discover_repository(
            force_refresh=False
        )

        # Enhance with additional information if managers are available
        if self.metadata_manager:
            # The metadata manager could enhance the metadata further
            # For now, we use the raw discovery metadata
            pass

        return metadata

    def _select_context(
        self,
        task_description: str,
        repository_metadata: RepositoryMetadata,
        selection_criteria: SelectionCriteria
    ) -> Dict[str, Any]:
        """
        Select relevant context based on task description and repository metadata.

        This method uses the Phase 3 relevance engine and other signals to
        identify the most relevant files, symbols, and code snippets.
        """
        selected_context = {
            "files": [],
            "symbols": [],
            "code_snippets": [],
            "repository_info": {},
            "all_items": []  # For duplicate tracking
        }

        # If we have a relevance engine, use it to score files
        if self.relevance_engine and self.repository_discovery:
            try:
                # Get relevance scores for all files in the repository
                relevance_scores = self.relevance_engine.calculate_relevance_scores(
                    task_description, repository_metadata
                )

                # Select top files based on relevance scores and criteria
                max_files = selection_criteria.max_files or 50
                sorted_files = sorted(
                    relevance_scores.items(),
                    key=lambda x: x[1].composite,
                    reverse=True
                )[:max_files]

                for file_path, relevance_score in sorted_files:
                    # Only include files above minimum relevance threshold
                    if (relevance_score.composite >=
                        selection_criteria.min_relevance_score):

                        # Check if file is within workspace boundaries
                        if self._is_within_workspace(file_path):
                            file_context = self._get_file_context(
                                file_path, relevance_score, selection_criteria
                            )
                            if file_context:
                                selected_context["files"].append(file_context)
                                selected_context["all_items"].extend(
                                    file_context.get("items_for_dedup", [])
                                )

            except Exception as e:
                # If relevance scoring fails, fall back to basic discovery
                pass

        # If no relevance engine or it failed, use basic file discovery
        if not selected_context["files"]:
            selected_context["files"] = self._get_basic_file_context(
                repository_metadata, selection_criteria
            )

        # Extract repository information for context
        selected_context["repository_info"] = {
            "root_path": str(repository_metadata.root_path),
            "is_git_repo": repository_metadata.is_git_repo,
            "git_branch": repository_metadata.git_branch,
            "git_commit": repository_metadata.git_commit,
            "project_type": repository_metadata.project_type,
            "language_hints": list(repository_metadata.language_hints),
            "build_system_hints": list(repository_metadata.build_system_hints),
            "documentation_hints": list(repository_metadata.documentation_hints)
        }

        return selected_context

    def _get_file_context(
        self,
        file_path: Path,
        relevance_score: Any,
        selection_criteria: SelectionCriteria
    ) -> Optional[Dict[str, Any]]:
        """
        Get context information for a specific file.

        This method extracts relevant information from a file based on
        relevance score and selection criteria.
        """
        try:
            # Check if file exists and is readable
            if not file_path.is_file():
                return None

            # Read file content (respecting workspace boundaries)
            if not self._is_within_workspace(file_path):
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
                "relative_path": str(file_path.relative_to(
                    self.workspace.workspace_root
                )) if file_path.is_relative_to(self.workspace.workspace_root)
                else str(file_path),
                "relevance_score": relevance_score,
                "content": content,
                "size_bytes": len(content.encode('utf-8')),
                "line_count": len(content.splitlines()),
                "language": self._detect_file_language(file_path),
                "items_for_dedup": []  # Will be populated for duplicate detection
            }

            # Extract symbols and dependencies if analyzer is available
            if self.symbol_analyzer:
                try:
                    symbols = self.symbol_analyzer.analyze_file_symbols(file_path)
                    dependencies = self.symbol_analyzer.analyze_file_dependencies(
                        file_path
                    )
                    file_context["symbols"] = [
                        {
                            "name": s.name,
                            "type": s.symbol_type,
                            "line_start": s.line_start,
                            "line_end": s.line_end
                        }
                        for s in symbols
                    ]
                    file_context["dependencies"] = [
                        {
                            "symbol": d.symbol_name,
                            "type": d.dependency_type,
                            "resolved": d.resolved
                        }
                        for d in dependencies
                    ]
                except Exception:
                    # If symbol analysis fails, continue without it
                    pass

            # Extract relevant code snippets based on relevance
            if selection_criteria.extract_snippets and relevance_score:
                snippets = self._extract_relevant_snippets(
                    content, relevance_score, selection_criteria
                )
                file_context["snippets"] = snippets

            # Prepare items for duplicate detection
            file_context["items_for_dedup"] = self._prepare_items_for_dedup(
                file_context
            )

            return file_context

        except Exception:
            # If any error occurs, skip this file
            return None

    def _get_basic_file_context(
        self,
        repository_metadata: RepositoryMetadata,
        selection_criteria: SelectionCriteria
    ) -> List[Dict[str, Any]]:
        """
        Get basic file context when relevance engine is not available.

        This method provides a fallback that uses basic repository discovery
        to get file information.
        """
        files_context = []

        # Get files from structure map
        structure_map = repository_metadata.structure_map
        max_files = selection_criteria.max_files or 20

        file_count = 0
        for dir_path, file_names in structure_map.items():
            if file_count >= max_files:
                break

            # Construct full directory path
            if dir_path == "":
                dir_path_obj = repository_metadata.root_path
            else:
                dir_path_obj = repository_metadata.root_path / dir_path

            # Check if directory is within workspace
            if not self._is_within_workspace(dir_path_obj):
                continue

            for file_name in file_names:
                if file_count >= max_files:
                    break

                file_path = dir_path_obj / file_name

                # Skip if not a file or not within workspace
                if not file_path.is_file() or not self._is_within_workspace(file_path):
                    continue

                try:
                    content = file_path.read_text(encoding='utf-8')
                    file_context = {
                        "path": str(file_path),
                        "relative_path": str(file_path.relative_to(
                            self.workspace.workspace_root
                        )) if file_path.is_relative_to(self.workspace.workspace_root)
                        else str(file_path),
                        "content": content,
                        "size_bytes": len(content.encode('utf-8')),
                        "line_count": len(content.splitlines()),
                        "language": self._detect_file_language(file_path),
                        "items_for_dedup": []
                    }

                    # Prepare items for duplicate detection
                    file_context["items_for_dedup"] = self._prepare_items_for_dedup(
                        file_context
                    )

                    files_context.append(file_context)
                    file_count += 1

                except (UnicodeDecodeError, OSError):
                    # Skip unreadable files
                    continue

        return files_context

    def _extract_relevant_snippets(
        self,
        content: str,
        relevance_score: Any,
        selection_criteria: SelectionCriteria
    ) -> List[Dict[str, Any]]:
        """
        Extract relevant code snippets from file content.

        This method uses relevance signals to identify the most relevant
        portions of a file to include in the context.
        """
        snippets = []

        lines = content.splitlines()
        total_lines = len(lines)

        if total_lines == 0:
            return snippets

        # Simple approach: extract lines around areas of high relevance
        # In a more sophisticated implementation, this would use
        # the specific relevance signals to target relevant areas

        # For now, extract a sample of lines based on file size
        max_snippets = selection_criteria.max_snippets_per_file or 5
        lines_per_snippet = selection_criteria.lines_per_snippet or 10

        # Calculate sample interval
        if total_lines <= lines_per_snippet * max_snippets:
            # Small file, show everything
            snippet_lines = [(i, line) for i, line in enumerate(lines)]
        else:
            # Larger file, sample at intervals
            interval = max(1, total_lines // (max_snippets * lines_per_snippet))
            snippet_lines = []
            for i in range(0, total_lines, interval):
                snippet_lines.extend([
                    (j, lines[j]) for j in range(
                        i, min(i + lines_per_snippet, total_lines)
                    )
                ])
                if len(snippet_lines) >= max_snippets * lines_per_snippet:
                    break

        # Group lines into snippets
        current_snippet = []
        current_start_line = None

        for line_num, line_content in snippet_lines:
            if current_start_line is None:
                current_start_line = line_num
            current_snippet.append(line_content)

            # End snippet if we've reached the limit or gap
            if (len(current_snippet) >= lines_per_snippet or
                (snippet_lines and
                 snippet_lines.index((line_num, line_content)) + 1 < len(snippet_lines) and
                 snippet_lines[snippet_lines.index((line_num, line_content)) + 1][0] > line_num + 1)):

                if current_snippet:
                    snippets.append({
                        "start_line": current_start_line,
                        "end_line": current_start_line + len(current_snippet) - 1,
                        "content": "\n".join(current_snippet),
                        "relevance_weight": getattr(relevance_score, 'composite', 0.5)
                        if relevance_score else 0.5
                    })
                    current_snippet = []
                    current_start_line = None

        # Don't forget the last snippet
        if current_snippet and current_start_line is not None:
            snippets.append({
                "start_line": current_start_line,
                "end_line": current_start_line + len(current_snippet) - 1,
                "content": "\n".join(current_snippet),
                "relevance_weight": getattr(relevance_score, 'composite', 0.5)
                if relevance_score else 0.5
            })

        return snippets[:max_snippets]

    def _prepare_items_for_dedup(self, file_context: Dict[str, Any]) -> List[str]:
        """
        Prepare items from file context for duplicate detection.

        This method extracts strings that can be hashed and compared
        to detect duplicate context.
        """
        items = []

        # Add file path
        items.append(f"path:{file_context.get('path', '')}")

        # Add file content hash for exact duplicate detection
        content = file_context.get('content', '')
        if content:
            content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            items.append(f"content_hash:{content_hash}")

        # Add snippet hashes for snippet-level duplicate detection
        snippets = file_context.get('snippets', [])
        for i, snippet in enumerate(snippets):
            snippet_content = snippet.get('content', '')
            if snippet_content:
                snippet_hash = hashlib.sha256(
                    snippet_content.encode('utf-8')
                ).hexdigest()
                items.append(f"snippet_{i}_hash:{snippet_hash}")

        # Add symbol information if available
        symbols = file_context.get('symbols', [])
        for symbol in symbols:
            symbol_key = f"symbol:{symbol.get('name', '')}:{symbol.get('type', '')}"
            items.append(symbol_key)

        return items

    def _assemble_context(
        self,
        selected_context: Dict[str, Any],
        repository_metadata: RepositoryMetadata,
        selection_criteria: SelectionCriteria
    ) -> Dict[str, Any]:
        """
        Assemble selected context into a coherent structure.

        This method organizes the selected context into logical groups
        and prepares it for budgeting and final assembly.
        """
        assembled = {
            "repository_context": {
                "metadata": selected_context.get("repository_info", {}),
                "structure_hints": self._extract_structure_hints(
                    repository_metadata, selection_criteria
                )
            },
            "working_context": {
                "files": selected_context.get("files", []),
                "symbols": [],
                "snippets": []
            },
            "task_context": {
                "description": "",  # Will be filled by caller
                "requirements": []
            },
            "history_context": {},  # Would be filled from session history
            "all_items_for_dedup": []
        }

        # Collect all items for duplicate tracking
        for file_context in selected_context.get("files", []):
            assembled["all_items_for_dedup"].extend(
                file_context.get("items_for_dedup", [])
            )

            # Extract symbols and snippets for working context
            assembled["working_context"]["symbols"].extend(
                file_context.get("symbols", [])
            )
            assembled["working_context"]["snippets"].extend(
                file_context.get("snippets", [])
            )

        return assembled

    def _extract_structure_hints(
        self,
        repository_metadata: RepositoryMetadata,
        selection_criteria: SelectionCriteria
    ) -> Dict[str, Any]:
        """
        Extract structural hints from repository metadata.

        This method provides high-level structural information about
        the repository that can be useful for context understanding.
        """
        hints = {
            "project_type": repository_metadata.project_type,
            "is_git_repo": repository_metadata.is_git_repo,
            "primary_languages": list(repository_metadata.language_hints)[:5],
            "build_systems": list(repository_metadata.build_system_hints)[:3],
            "documentation_types": list(repository_metadata.documentation_hints)[:3]
        }

        # Add directory structure summary if requested
        if selection_criteria.include_structure:
            structure_map = repository_metadata.structure_map
            # Limit to top-level directories to avoid too much detail
            top_dirs = dict(list(structure_map.items())[:10])
            hints["structure_sample"] = {
                dir_path: len(files) for dir_path, files in top_dirs.items()
            }

        return hints

    def _apply_budgeting(
        self,
        assembled_context: Dict[str, Any],
        budget_allocation: BudgetAllocation,
        max_tokens: int
    ) -> Dict[str, Any]:
        """
        Apply token budgeting to the assembled context.

        This method allocates tokens to different context types and
        truncates or summarizes content to fit within the budget.
        """
        if not self.enable_metrics or not self.metrics:
            # Simple budgeting without metrics tracking
            return self._simple_budgeting(
                assembled_context, budget_allocation, max_tokens
            )

        # Use the budgeter subsystem for sophisticated budgeting
        context_budgeter = ContextBudgeter()
        return context_budgeter.apply_budget(
            assembled_context, budget_allocation, max_tokens
        )

    def _simple_budgeting(
        self,
        assembled_context: Dict[str, Any],
        budget_allocation: BudgetAllocation,
        max_tokens: int
    ) -> Dict[str, Any]:
        """
        Simple token budgeting implementation.

        This is a fallback budgeting method that proportionally
        allocates tokens based on the budget allocation percentages.
        """
        # Calculate token allocation for each context type
        allocations = {}
        remaining_budget = max_tokens

        # Handle fixed allocations first
        for context_type, allocation in budget_allocation.fixed_allocations.items():
            allocated = min(allocation.tokens, remaining_budget)
            allocations[context_type] = allocated
            remaining_budget -= allocated

        # Handle proportional allocations
        proportional_types = [
            ct for ct, alloc in budget_allocation.proportional_allocations.items()
            if ct not in allocations
        ]

        if proportional_types and remaining_budget > 0:
            total_weight = sum(
                budget_allocation.proportional_allocations[ct].weight
                for ct in proportional_types
            )

            if total_weight > 0:
                for context_type in proportional_types:
                    weight = budget_allocation.proportional_allocations[
                        context_type
                    ].weight
                    proportional_share = weight / total_weight
                    allocated = int(
                        remaining_budget * proportional_share
                    )
                    allocations[context_type] = allocated

        # Apply allocations to truncate/summarize content
        budgeted_context = {}
        for context_type, context_content in assembled_context.items():
            if context_type in allocations:
                max_tokens_for_type = allocations[context_type]
                budgeted_context[context_type] = self._truncate_to_tokens(
                    context_content, max_tokens_for_type
                )
            else:
                # No allocation for this type, include minimal info
                budgeted_context[context_type] = self._get_minimal_context(
                    context_content
                )

        return budgeted_context

    def _truncate_to_tokens(
        self,
        content: Any,
        max_tokens: int
    ) -> Any:
        """
        Truncate content to fit within token limit.

        This method estimates token count and truncates content
        to stay within the specified limit.
        """
        # Simple token estimation: ~4 characters per token for English text
        # This is a rough approximation - in practice, we'd use a proper tokenizer
        chars_per_token = 4
        max_chars = max_tokens * chars_per_token

        if isinstance(content, str):
            if len(content) <= max_chars:
                return content
            else:
                # Truncate and add indicator
                truncated = content[:max_chars]
                # Try to break at a word boundary
                last_space = truncated.rfind(' ')
                if last_space > max_chars * 0.8:  # Only if we don't lose too much
                    truncated = truncated[:last_space]
                return truncated + "\n\n[...content truncated due to token limits...]"

        elif isinstance(content, list):
            # Truncate list proportionally
            if not content:
                return content

            # Estimate tokens per item (this is simplified)
            if len(content) <= 10:  # Small list, show all or none
                # Estimate total tokens
                estimated_tokens = len(str(content)) // chars_per_token
                if estimated_tokens <= max_tokens:
                    return content
                else:
                    # Show fewer items
                    max_items = max(1, len(content) * max_tokens // estimated_tokens)
                    return content[:max_items]
            else:
                # For larger lists, show first N items
                # Estimate based on first item
                if content:
                    first_item_tokens = len(str(content[0])) // chars_per_token
                    if first_item_tokens > 0:
                        max_items = max(1, max_tokens // first_item_tokens)
                        return content[:max_items]
                return content[:max(1, max_tokens // 10)]  # Fallback

        elif isinstance(content, dict):
            # Truncate dictionary by limiting number of keys
            if not content:
                return content

            # Estimate tokens per key-value pair
            if len(content) <= 10:  # Small dict
                estimated_tokens = len(str(content)) // chars_per_token
                if estimated_tokens <= max_tokens:
                    return content
                else:
                    # Show fewer items
                    max_items = max(1, len(content) * max_tokens // estimated_tokens)
                    items = list(content.items())[:max_items]
                    return dict(items)
            else:
                # For larger dicts, show first N items
                if content:
                    first_pair_tokens = len(str(list(content.items())[0])) // chars_per_token
                    if first_pair_tokens > 0:
                        max_items = max(1, max_tokens // first_pair_tokens)
                        items = list(content.items())[:max_items]
                        return dict(items)
                return dict(list(content.items())[:max(1, max_tokens // 10)])

        # For other types, return as-is (hopefully they're small)
        return content

    def _get_minimal_context(self, content: Any) -> Any:
        """
        Get minimal context representation for types with no allocation.

        This method provides a minimal representation when a context
        type receives no token allocation.
        """
        if isinstance(content, str):
            if len(content) <= 100:
                return content
            return content[:100] + "...[truncated]"
        elif isinstance(content, list):
            if len(content) <= 3:
                return content
            return content[:3] + [f"+{len(content)-3} more items..."]
        elif isinstance(content, dict):
            if len(content) <= 3:
                return content
            items = list(content.items())[:3]
            result = dict(items)
            result[f"+{len(content)-3} more keys..."] = ""
            return result
        else:
            return str(content)[:100] + "...[truncated]" if content else None

    def _validate_and_sanitize_context(
        self,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate and sanitize context for security and compliance.

        This method ensures that the context:
        - Does not contain files outside the workspace
        - Is free from potential prompt injection attempts
        - Does not expose sensitive information
        - Complies with workspace security policies
        """
        validated = {
            "repository_context": {},
            "working_context": {},
            "task_context": {},
            "history_context": {},
            "validation_errors": [],
            "warnings": []
        }

        # Validate each context type
        for context_type in ["repository_context", "working_context",
                           "task_context", "history_context"]:
            if context_type in context:
                validated[context_type] = self._validate_context_type(
                    context[context_type], context_type
                )

        # Check overall workspace compliance
        workspace_compliant = len(validated.get("validation_errors", [])) == 0

        # Add validation metadata
        validated["_validation"] = {
            "workspace_compliant": workspace_compliant,
            "validation_passed": len(validated.get("validation_errors", [])) == 0,
            "validation_errors": validated.get("validation_errors", []),
            "warnings": validated.get("warnings", []),
            "sanitized": len(validated.get("warnings", [])) > 0
        }

        return validated

    def _validate_context_type(
        self,
        context_data: Any,
        context_type: str
    ) -> Any:
        """
        Validate a specific type of context data.

        This method applies type-specific validation rules.
        """
        if isinstance(context_data, dict):
            validated_dict = {}
            for key, value in context_data.items():
                # Validate the key (should be safe strings)
                safe_key = self._make_safe_string(str(key))
                # Recursively validate the value
                validated_value = self._validate_context_type(value, f"{context_type}.{key}")
                validated_dict[safe_key] = validated_value
            return validated_dict

        elif isinstance(context_data, list):
            validated_list = []
            for item in context_data:
                validated_item = self._validate_context_type(item, f"{context_type}_item")
                validated_list.append(validated_item)
            return validated_list

        elif isinstance(context_data, str):
            return self._sanitize_string(context_data)

        else:
            # For other types (int, float, bool, None), return as-is
            return context_data

    def _make_safe_string(self, s: str) -> str:
        """
        Make a string safe for use as a key or identifier.

        This method removes or replaces potentially problematic characters.
        """
        # Keep only alphanumeric, underscore, hyphen, and dot
        import re
        safe = re.sub(r'[^a-zA-Z0-9_.\-]', '_', s)
        # Ensure it doesn't start with a number or special character
        if safe and (safe[0].isdigit() or safe[0] in '._-'):
            safe = '_' + safe
        return safe or "empty"

    def _sanitize_string(self, s: str) -> str:
        """
        Sanitize a string to prevent potential security issues.

        This method attempts to remove or neutralize content that
        could be used for prompt injection or other attacks.
        """
        if not s:
            return s

        # List of potentially dangerous patterns
        dangerous_patterns = [
            # Potential prompt injection attempts
            r"(?i)\s*system\s*:",  # "System:" attempts to change role
            r"(?i)\s*assistant\s*:",  # "Assistant:" attempts to change role
            r"(?i)\s*user\s*:",  # "User:" attempts to change role
            r"(?i)\s*<\|.*?\|>",  # Special tokens like <|endoftext|>
            r"(?i)\s*\[INST\]",  # Instruction markers
            r"(?i)\s*\[/INST\]",
            # Potential code execution attempts
            r"(?i)exec\s*\(",  # exec() calls
            r"(?i)eval\s*\(",  # eval() calls
            r"(?i)__import__\s*\(",  # __import__ calls
            # Potential file system escapes
            r"\.\.(/|\\)",  # Directory traversal attempts
            # Potential script tags (if HTML/XML content might appear)
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            # Potential SQL injection (less likely but possible)
            r"(?i)union\s+select",
            r"(?i)drop\s+table",
        ]

        sanitized = s
        warnings = []

        for pattern in dangerous_patterns:
            import re
            matches = re.findall(pattern, sanitized)
            if matches:
                warnings.append(f"Potential security pattern detected: {pattern}")
                # Replace with safe placeholder
                sanitized = re.sub(
                    pattern,
                    f"[SECURITY_FILTERED:{len(matches)}]",
                    sanitized,
                    flags=re.IGNORECASE
                )

        # If we found and filtered anything, we should warn
        if warnings and hasattr(self, '_validation_warnings'):
            self._validation_warnings.extend(warnings)

        return sanitized

    def _is_within_workspace(self, file_path: Path) -> bool:
        """
        Check if a file path is within the workspace boundaries.

        This method enforces workspace security by ensuring that
        no context is sourced from outside the approved workspace.
        """
        try:
            if isinstance(file_path, str):
                file_path = Path(file_path)

            resolved_file = file_path.resolve()
            resolved_workspace = Path(self.workspace.workspace_root).resolve()

            # Check if file is within or equal to workspace root
            return (
                resolved_workspace in resolved_file.parents or
                resolved_file == resolved_workspace
            )
        except (OSError, ValueError):
            # If we can't resolve the path, err on the side of safety
            return False

    def _detect_file_language(self, file_path: Path) -> str:
        """
        Detect the programming language of a file.

        This method uses file extension and content heuristics
        to determine the likely programming language.
        """

        # Extension-based detection
        extension = file_path.suffix.lower()
        extension_map = {
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
            ".markdown": "markdown",
            ".rst": "restructuredtext",
            ".txt": "text",
            ".sql": "sql",
            ".dockerfile": "dockerfile",
            ".gitignore": "gitignore",
            ".gitattributes": "gitattributes"
        }

        if extension in extension_map:
            return extension_map[extension]

        # Check for special filenames
        filename = file_path.name.lower()
        special_files = {
            "dockerfile": "dockerfile",
            "makefile": "make",
            "gnumakefile": "make",
            "kfile": "make",
            "makefile": "make",
            "rakefile": "ruby",
            "gemfile": "ruby",
            "vagrantfile": "ruby",
            "berksfile": "ruby",
            "podfile": "ruby",
            "fastfile": "ruby",
            "appfile": "ruby",
            "jenkinsfile": "jenkins",
            " puppet": "puppet",
            "cheffile": "ruby",
            "rakefile": "ruby"
        }

        if filename in special_files:
            return special_files[filename]

        # Default to unknown
        return "unknown"

    def _generate_cache_key(
        self,
        task_description: str,
        selection_criteria: SelectionCriteria,
        budget_allocation: BudgetAllocation,
        duplicate_policy: DuplicatePolicy,
        max_tokens: int
    ) -> str:
        """
        Generate a cache key for context package results.

        This method creates a deterministic key based on the input
        parameters to enable caching of similar requests.
        """
        # Create a string representation of all parameters
        key_parts = [
            f"task:{hashlib.sha256(task_description.encode()).hexdigest()[:16]}",
            f"criteria:{selection_criteria.__hash__() if hasattr(selection_criteria, '__hash__') else hash(str(selection_criteria))}",
            f"budget:{budget_allocation.__hash__() if hasattr(budget_allocation, '__hash__') else hash(str(budget_allocation))}",
            f"policy:{duplicate_policy.__hash__() if hasattr(duplicate_policy, '__hash__') else hash(str(duplicate_policy))}",
            f"tokens:{max_tokens}",
            f"workspace:{self.workspace.workspace_root}"
        ]

        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()

    def _is_cache_valid(self, cached_package: ContextPackage) -> bool:
        """
        Check if a cached context package is still valid.

        This method determines whether a cached context package
        is still fresh enough to be used.
        """
        # Check basic age - cached contexts should not be too old
        age = time.time() - cached_package.timestamp
        max_age = 300  # 5 minutes max age for context cache

        if age > max_age:
            return False

        # Check if repository metadata has changed significantly
        if (self._last_repository_metadata and
            cached_package.context_id != "unknown"):  # Skip validation for unknown IDs
            try:
                # For now, we'll use a simple timestamp check
                # In a more sophisticated version, we'd check for actual changes
                repository_age = time.time() - getattr(
                    self._last_repository_metadata, '_cache_timestamp', time.time()
                )
                if repository_age > 60:  # Repository metadata older than 1 minute
                    return False
            except AttributeError:
                # If we can't check repository age, be conservative
                pass

        return True

    def _cache_context_package(
        self,
        key: str,
        context_package: ContextPackage
    ) -> None:
        """
        Cache a context package for future use.

        This method stores context packages in an LRU-like cache
        to avoid recomputing similar requests.
        """
        # Add to cache
        self._context_cache[key] = context_package

        # Enforce cache size limit
        if len(self._context_cache) > self._max_cache_size:
            # Remove oldest entries (simple FIFO for now)
            # In production, we'd use a proper LRU implementation
            keys_to_remove = list(self._context_cache.keys())[:len(self._context_cache) - self._max_cache_size]
            for old_key in keys_to_remove:
                del self._context_cache[old_key]

    def get_context_metrics(self) -> Optional['MetricsReport']:
        """
        Get context metrics if metrics collection is enabled.

        Returns:
            MetricsReport if metrics are enabled, None otherwise
        """
        if self.metrics:
            from .context_metrics import MetricsReport
            return self.metrics.get_report()
        return None

    def clear_cache(self) -> None:
        """Clear the internal context cache."""
        self._context_cache.clear()
        if self.metrics:
            self.metrics.reset()

    def invalidate_repository_cache(self) -> None:
        """Invalidate cached context when repository changes."""
        self.clear_cache()
        self._last_repository_metadata = None
        self._last_context_package = None

    def _create_context_package(
        self,
        task_description: str,
        validated_context: Dict[str, Any],
        selection_criteria: SelectionCriteria,
        budget_allocation: BudgetAllocation,
        duplicate_policy: DuplicatePolicy,
        max_tokens: int,
        start_time: float
    ) -> ContextPackage:
        """
        Create a final context package from the validated context.

        Args:
            task_description: Description of the current task
            validated_context: Context that has been validated and sanitized
            selection_criteria: Criteria used for context selection
            budget_allocation: Budget allocation used
            duplicate_policy: Duplicate policy used
            max_tokens: Maximum tokens allowed
            start_time: Start time of context creation process

        Returns:
            ContextPackage containing the final context
        """
        # Extract context components
        repository_context = validated_context.get("repository_context", {})
        working_context = validated_context.get("working_context", {})
        task_context = validated_context.get("task_context", {})
        history_context = validated_context.get("history_context", {})

        # Calculate total tokens (estimate if not already calculated)
        total_tokens = validated_context.get("_budget_info", {}).get("used_tokens", 0)
        if total_tokens == 0:
            # Fallback: estimate token count
            import hashlib
            chars_per_token = 4
            total_content = str(repository_context) + str(working_context) + str(task_context) + str(history_context)
            total_tokens = len(total_content) // chars_per_token

        # Create token breakdown
        token_breakdown = {
            "repository_context": len(str(repository_context)) // 4,
            "working_context": len(str(working_context)) // 4,
            "task_context": len(str(task_context)) // 4,
            "history_context": len(str(history_context)) // 4
        }

        # Determine sources used
        sources_used = []
        if repository_context:
            sources_used.append("repository")
        if working_context:
            sources_used.append("working")
        if task_context:
            sources_used.append("task")
        if history_context:
            sources_used.append("history")

        # Create and return the context package
        return ContextPackage(
            repository_context=repository_context,
            working_context=working_context,
            task_context=task_context,
            history_context=history_context,
            context_id=str(uuid4()),
            timestamp=time.time(),
            total_tokens=total_tokens,
            token_breakdown=token_breakdown,
            sources_used=sources_used,
            selection_criteria=selection_criteria,
            budget_allocation=budget_allocation,
            duplicate_policy=duplicate_policy,
            workspace_compliant=validated_context.get("_validation", {}).get("workspace_compliant", True),
            content_sanitized=validated_context.get("_validation", {}).get("sanitized", False),
            validation_passed=len(validated_context.get("_validation", {}).get("validation_errors", [])) == 0
        )

    def __repr__(self) -> str:
        return f"ContextManager(workspace='{self.workspace.workspace_root}', metrics_enabled={self.enable_metrics})"