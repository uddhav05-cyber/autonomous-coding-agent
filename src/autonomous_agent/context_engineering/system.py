"""
Context Engineering System for Autonomous Coding Agent.

This module provides the main ContextEngineeringSystem class that integrates
all context engineering components:
1. Context Selection
2. Context Budgeting
3. Context Assembly
4. Duplicate Prevention
5. Context Metrics

The system provides a unified interface for context engineering operations
while maintaining workspace boundary enforcement and security.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Callable
from uuid import uuid4

from .context_manager import ContextManager, ContextPackage
from .context_selector import SelectionCriteria
from .context_budgeter import BudgetAllocation
from .context_assembler import AssemblyResult
from .duplicate_preventer import DuplicatePolicy
from .context_metrics import MetricsReport
from autonomous_agent.repository_understanding import (
    RepositoryDiscovery,
    RepositoryMetadataManager,
    RelevanceEngine,
    CodeSearchModule,
    SymbolDependencyAnalyzer
)
from autonomous_agent.workspace import Workspace


@dataclass
class ContextEngineeringResult:
    """Result of a complete context engineering operation."""
    # Context package ready for LLM consumption
    context_package: ContextPackage

    # Assembly details
    assembly_result: AssemblyResult

    # Metrics from the operation
    operation_metrics: Dict[str, Any] = field(default_factory=dict)

    # System metadata
    timestamp: float = field(default_factory=time.time)
    operation_id: str = field(default_factory=lambda: str(uuid4()))
    total_operation_time_ms: float = 0.0

    def is_within_budget(self, max_tokens: int) -> bool:
        """Check if the context package is within token budget."""
        return self.context_package.is_within_budget(max_tokens)

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the context engineering result."""
        return {
            "operation_id": self.operation_id,
            "timestamp": self.timestamp,
            "total_operation_time_ms": self.total_operation_time_ms,
            "context_package": self.context_package.get_context_summary(),
            "assembly_result": self.assembly_result.get_summary(),
            "operation_metrics": self.operation_metrics.copy()
        }


class ContextEngineeringSystem:
    """
    Integrated Context Engineering System.

    This class combines all context engineering components into a
    cohesive system that provides:
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
        default_budget_tokens: int = 4000,
        default_selection_criteria: Optional[SelectionCriteria] = None,
        default_budget_allocation: Optional[BudgetAllocation] = None,
        default_duplicate_policy: Optional[DuplicatePolicy] = None
    ):
        """
        Initialize the integrated context engineering system.

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
            default_selection_criteria: Default selection criteria to use
            default_budget_allocation: Default budget allocation to use
            default_duplicate_policy: Default duplicate policy to use
        """
        self.workspace = workspace
        self.enable_metrics = enable_metrics
        self.enable_duplicate_prevention = enable_duplicate_prevention

        # Store Phase 3 components
        self.repository_discovery = repository_discovery
        self.metadata_manager = metadata_manager
        self.relevance_engine = relevance_engine
        self.search_module = search_module
        self.symbol_analyzer = symbol_analyzer

        # Set defaults
        self.default_selection_criteria = default_selection_criteria or SelectionCriteria()
        self.default_budget_allocation = default_budget_allocation or BudgetAllocation()
        self.default_duplicate_policy = default_duplicate_policy or DuplicatePolicy()
        self.default_budget_tokens = default_budget_tokens

        # Initialize the main context manager (which coordinates all subsystems)
        self.context_manager = ContextManager(
            workspace=workspace,
            repository_discovery=repository_discovery,
            metadata_manager=metadata_manager,
            relevance_engine=relevance_engine,
            search_module=search_module,
            symbol_analyzer=symbol_analyzer,
            enable_metrics=enable_metrics,
            enable_duplicate_prevention=enable_duplicate_prevention,
            default_budget_tokens=default_budget_tokens
        )

        # Initialize metrics collector if enabled
        if self.enable_metrics:
            self.metrics = self.context_manager.metrics  # Share the same metrics instance
        else:
            self.metrics = None

        # State tracking
        self._last_context_result: Optional[ContextEngineeringResult] = None

    def engineer_context(
        self,
        task_description: str,
        selection_criteria: Optional[SelectionCriteria] = None,
        budget_allocation: Optional[BudgetAllocation] = None,
        duplicate_policy: Optional[DuplicatePolicy] = None,
        max_tokens: Optional[int] = None,
        use_cache: bool = True
    ) -> ContextEngineeringResult:
        """
        Engineer context for the given task.

        This is the main entry point that coordinates all context engineering
        functions to produce an optimized context package ready for LLM consumption.

        Args:
            task_description: Description of the current task
            selection_criteria: Criteria for context selection
            budget_allocation: Allocation of token budget across context types
            duplicate_policy: Policy for handling duplicate context
            max_tokens: Maximum tokens allowed in context package
            use_cache: Whether to use cached results if available

        Returns:
            ContextEngineeringResult containing the engineered context
        """
        start_time = time.time()

        # Use defaults if not provided
        if selection_criteria is None:
            selection_criteria = self.default_selection_criteria
        if budget_allocation is None:
            budget_allocation = self.default_budget_allocation
        if duplicate_policy is None:
            duplicate_policy = self.default_duplicate_policy
        if max_tokens is None:
            max_tokens = self.default_budget_tokens

        # Delegate to the context manager (which does all the work)
        context_package = self.context_manager.create_context_package(
            task_description=task_description,
            selection_criteria=selection_criteria,
            budget_allocation=budget_allocation,
            duplicate_policy=duplicate_policy,
            max_tokens=max_tokens,
            use_cache=use_cache
        )

        # For the assembly result, we would need to capture it from the context manager
        # For now, we'll create a basic assembly result - in a full implementation,
        # the context manager would return this information
        assembly_result = AssemblyResult(
            assembly_id=f"asm_{int(time.time() * 1000)}",
            timestamp=time.time(),
            sources_used=["repository", "working"],
            file_count=len(context_package.working_context.get("files", [])) if context_package.working_context else 0,
            completeness_score=0.8,  # Placeholder - would be calculated in real implementation
            relevance_score=0.7,     # Placeholder - would be calculated in real implementation
            diversity_score=0.6      # Placeholder - would be calculated in real implementation
        )

        # Calculate operation time
        total_operation_time_ms = (time.time() - start_time) * 1000

        # Collect operation metrics
        operation_metrics = {}
        if self.metrics:
            metrics_report = self.metrics.get_report()
            operation_metrics = {
                "metrics_report": metrics_report.__dict__,
                "context_creation_time_ms": total_operation_time_ms * 0.7,  # Estimate
                "cache_hit_rate": metrics_report.cache_hit_rate,
                "token_usage": metrics_report.total_tokens_used,
                "average_relevance": metrics_report.average_relevance_score
            }

        # Create the final result
        result = ContextEngineeringResult(
            context_package=context_package,
            assembly_result=assembly_result,
            operation_metrics=operation_metrics,
            timestamp=time.time(),
            operation_id=str(uuid4()),
            total_operation_time_ms=total_operation_time_ms
        )

        # Update state tracking
        self._last_context_result = result

        return result

    def get_context_metrics(self) -> Optional[MetricsReport]:
        """
        Get context metrics if metrics collection is enabled.

        Returns:
            MetricsReport if metrics are enabled, None otherwise
        """
        if self.metrics:
            return self.metrics.get_report()
        return None

    def clear_all_caches(self) -> None:
        """Clear all caches in the system."""
        self.context_manager.clear_cache()
        if self.metrics:
            self.metrics.reset()

    def invalidate_context_cache(self) -> None:
        """Invalidate context cache when underlying data changes."""
        self.context_manager.clear_cache()
        if self.metrics:
            self.metrics.reset()

    def get_system_info(self) -> Dict[str, Any]:
        """
        Get information about the system and its components.

        Returns:
            Dictionary containing system information
        """
        return {
            "workspace_root": self.workspace.workspace_root,
            "context_manager": str(self.context_manager),
            "metrics_enabled": self.enable_metrics,
            "duplicate_prevention_enabled": self.enable_duplicate_prevention,
            "default_budget_tokens": self.default_budget_tokens,
            "has_repository_discovery": self.repository_discovery is not None,
            "has_metadata_manager": self.metadata_manager is not None,
            "has_relevance_engine": self.relevance_engine is not None,
            "has_search_module": self.search_module is not None,
            "has_symbol_analyzer": self.symbol_analyzer is not None,
            "last_operation_time": self._last_context_result.timestamp if self._last_context_result else None
        }

    def __repr__(self) -> str:
        return f"ContextEngineeringSystem(workspace='{self.workspace.workspace_root}', metrics_enabled={self.enable_metrics})"


def create_context_engineering_system(
    workspace_path: Optional[str] = None,
    repository_discovery: Optional[RepositoryDiscovery] = None,
    metadata_manager: Optional[RepositoryMetadataManager] = None,
    relevance_engine: Optional[RelevanceEngine] = None,
    search_module: Optional[CodeSearchModule] = None,
    symbol_analyzer: Optional[SymbolDependencyAnalyzer] = None,
    enable_metrics: bool = True,
    enable_duplicate_prevention: bool = True,
    default_budget_tokens: int = 4000,
    default_selection_criteria: Optional[SelectionCriteria] = None,
    default_budget_allocation: Optional[BudgetAllocation] = None,
    default_duplicate_policy: Optional[DuplicatePolicy] = None
) -> Tuple[Workspace, ContextEngineeringSystem]:
    """
    Create a complete context engineering system with workspace.

    Args:
        workspace_path: Optional workspace path. If None, uses workspace from settings.
        repository_discovery: Repository discovery component (Phase 3)
        metadata_manager: Metadata manager component (Phase 3)
        relevance_engine: Relevance engine component (Phase 3)
        search_module: Code search module (Phase 3)
        symbol_analyzer: Symbol and dependency analyzer (Phase 3)
        enable_metrics: Whether to collect and track metrics
        enable_duplicate_prevention: Whether to enable duplicate prevention
        default_budget_tokens: Default token budget for context packages
        default_selection_criteria: Default selection criteria to use
        default_budget_allocation: Default budget allocation to use
        default_duplicate_policy: Default duplicate policy to use

    Returns:
        Tuple of (Workspace, ContextEngineeringSystem) instances
    """
    from autonomous_agent.config.settings import Settings
    from autonomous_agent.workspace import Workspace

    # Get workspace
    if workspace_path is None:
        settings = Settings()
        workspace_path = settings.workspace_path

    workspace = Workspace(workspace_root=workspace_path)

    # Create the integrated system
    system = ContextEngineeringSystem(
        workspace=workspace,
        repository_discovery=repository_discovery,
        metadata_manager=metadata_manager,
        relevance_engine=relevance_engine,
        search_module=search_module,
        symbol_analyzer=symbol_analyzer,
        enable_metrics=enable_metrics,
        enable_duplicate_prevention=enable_duplicate_prevention,
        default_budget_tokens=default_budget_tokens,
        default_selection_criteria=default_selection_criteria,
        default_budget_allocation=default_budget_allocation,
        default_duplicate_policy=default_duplicate_policy
    )

    return workspace, system