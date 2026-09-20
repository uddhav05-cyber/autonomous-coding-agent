"""
Context Engineering module for Autonomous Coding Agent.

This module provides context selection, budgeting, assembly, duplicate prevention,
and metrics capabilities for the autonomous coding agent, enabling it to
intelligently manage LLM context within token limits while providing the most
relevant information for coding tasks.
"""

from .context_manager import ContextManager, ContextPackage
from .context_selector import ContextSelector, SelectionCriteria
from .context_budgeter import ContextBudgeter, BudgetAllocation
from .context_assembler import ContextAssembler, AssemblyResult
from .duplicate_preventer import DuplicatePreventer, DuplicatePolicy
from .context_metrics import ContextMetrics, MetricsReport
from .system import (
    ContextEngineeringSystem,
    ContextEngineeringResult,
    create_context_engineering_system
)

__all__ = [
    "ContextManager",
    "ContextPackage",
    "ContextSelector",
    "SelectionCriteria",
    "ContextBudgeter",
    "BudgetAllocation",
    "ContextAssembler",
    "AssemblyResult",
    "DuplicatePreventer",
    "DuplicatePolicy",
    "ContextMetrics",
    "MetricsReport",
    "ContextEngineeringSystem",
    "ContextEngineeringResult",
    "create_context_engineering_system"
]