"""Agent Orchestrator for the Autonomous Coding Agent.

This module provides the AgentOrchestrator class that coordinates the
autonomous coding-agent execution loop, managing the iterative process of
LLM reasoning, tool execution, and state updates.
"""
from __future__ import annotations

print("!!! MODULE LEVEL PRINT !!!")

import asyncio
import json
import os
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

from autonomous_agent.model_adapter.base import ModelAdapter
from autonomous_agent.model_adapter.types import ModelRequest, ModelResponse, ToolCall
from autonomous_agent.context_engineering.context_manager import ContextManager
from autonomous_agent.tool.interface import Tool, ToolResult
from autonomous_agent.tool.registry import ToolRegistry, get_global_registry
from autonomous_agent.tool.policy import ToolPolicyEngine, PermissionContext
from autonomous_agent.tool.executor import ToolExecutor
from autonomous_agent.workspace import Workspace
from autonomous_agent.tool.errors import (
    ToolError,
    ToolNotFoundError,
    ValidationError,
    PermissionDeniedError,
    WorkspaceViolationError,
    TimeoutError,
    ExecutionError,
    ConfirmationRequiredError,
    ResourceLimitError,
    InternalToolError
)
import json
import os
import hashlib


@dataclass
class ProgressMetrics:
    """Metrics for tracking progress of the agent orchestrator.

    Tracks meaningful progress indicators that are already available through
    the existing architecture, without duplicating Repository Understanding logic
    or introducing direct filesystem access.
    """
    # Current iteration metrics
    iteration: int = 0
    successful_tool_calls: int = 0
    failed_tool_calls: int = 0
    total_tool_calls: int = 0

    # Workspace change tracking (based on file count changes)
    workspace_file_count: int = 0
    workspace_file_count_delta: int = 0  # Change from previous iteration

    # Error tracking
    error_count: int = 0
    error_count_delta: int = 0  # Change from previous iteration

    # Success rate (ratio of successful to total tool calls)
    success_rate: float = 0.0

    # Historical data for trend calculation (bounded to prevent memory growth)
    _history: List['ProgressMetrics'] = field(default_factory=list)
    _max_history_size: int = 10  # Keep last 10 iterations for trend analysis

    def update(self,
               iteration: int,
               successful_tool_calls: int,
               failed_tool_calls: int,
               workspace_file_count: int,
               error_count: int) -> str:
        """Update progress metrics with current iteration data.

        Args:
            iteration: Current iteration number
            successful_tool_calls: Number of successful tool calls in this iteration
            failed_tool_calls: Number of failed tool calls in this iteration
            workspace_file_count: Current workspace file count
            error_count: Current error count
        Returns:
            "improving": Positive trend in success rate and/or workspace changes
            "stable": No significant change (no meaningful progress)
            "declining": Negative trend in success rate and/or increasing errors
        """
        # Get previous metrics if available
        prev_metrics = self._history[-1] if self._history else None

        # Calculate deltas - compare to 0 if no previous metrics
        prev_workspace_file_count = prev_metrics.workspace_file_count if prev_metrics else 0
        prev_error_count = prev_metrics.error_count if prev_metrics else 0
        workspace_file_count_delta = workspace_file_count - prev_workspace_file_count
        error_count_delta = error_count - prev_error_count

        # Calculate success rate
        total_tool_calls = successful_tool_calls + failed_tool_calls
        success_rate = successful_tool_calls / max(total_tool_calls, 1) if total_tool_calls > 0 else 0.0

        # Create new metrics instance
        new_metrics = ProgressMetrics(
            iteration=iteration,
            successful_tool_calls=successful_tool_calls,
            failed_tool_calls=failed_tool_calls,
            total_tool_calls=total_tool_calls,
            workspace_file_count=workspace_file_count,
            workspace_file_count_delta=workspace_file_count_delta,
            error_count=error_count,
            error_count_delta=error_count_delta,
            success_rate=success_rate,
            _max_history_size=self._max_history_size
        )
        new_metrics._history = self._history.copy()  # Copy existing history

        # Add to history and maintain bounded size
        self._history.append(new_metrics)
        if len(self._history) > self._max_history_size:
            self._history = self._history[-self._max_history_size:]

        # Update current instance with new values
        self.iteration = new_metrics.iteration
        self.successful_tool_calls = new_metrics.successful_tool_calls
        self.failed_tool_calls = new_metrics.failed_tool_calls
        self.total_tool_calls = new_metrics.total_tool_calls
        self.workspace_file_count = new_metrics.workspace_file_count
        self.workspace_file_count_delta = new_metrics.workspace_file_count_delta
        self.error_count = new_metrics.error_count
        self.error_count_delta = new_metrics.error_count_delta
        self.success_rate = new_metrics.success_rate

        return self.get_trend()

    def get_trend(self) -> str:
        """Calculate and return the current progress trend.

        Analyzes recent history to determine if progress is improving, stable, or declining
        based on success rate, workspace changes, and error trends.

        Returns:
            "improving": Positive trend in success rate and/or workspace changes
            "stable": No significant change (no meaningful progress)
            "declining": Negative trend in success rate and/or increasing errors
        """

        if len(self._history) < 3:
            # Not enough data for trend calculation
            return "stable"

        # Get recent history (last 3 entries)
        recent = self._history[-3:]

        # Calculate trends in key indicators
        success_rate_trend = recent[-1].success_rate - recent[0].success_rate
        workspace_change_trend = sum(m.workspace_file_count_delta for m in recent)
        error_trend = recent[-1].error_count - recent[0].error_count  # Negative is improving (errors decreasing)

        # Determine trend based on weighted factors
        # Success rate improvement is most important, then workspace changes, then error reduction
        improving_score = (
            success_rate_trend * 0.5 +  # Weight success rate highest
            (workspace_change_trend > 0) * 0.3 +  # Positive workspace change
            (-error_trend) * 0.2  # Negative error trend (errors decreasing)
        )

        declining_score = (
            -success_rate_trend * 0.5 +  # Success rate decreasing
            (workspace_change_trend < 0) * 0.3 +  # Negative workspace change
            error_trend * 0.2  # Positive error trend (errors increasing)
        )

        if improving_score > 0.2:
            return "improving"
        elif declining_score > 0.2:
            return "declining"
        else:
            return "stable"

    def get_current_stats(self) -> Dict[str, Any]:
        """Get current progress statistics.

        Returns:
            Dictionary containing current metrics
        """
        return {
            "iteration": self.iteration,
            "successful_tool_calls": self.successful_tool_calls,
            "failed_tool_calls": self.failed_tool_calls,
            "total_tool_calls": self.total_tool_calls,
            "workspace_file_count": self.workspace_file_count,
            "workspace_file_count_delta": self.workspace_file_count_delta,
            "error_count": self.error_count,
            "error_count_delta": self.error_count_delta,
            "success_rate": self.success_rate,
            "trend": self.get_trend()
        }

    def is_meaningful_progress(self) -> bool:
        """Determine if the current iteration represents meaningful progress.
        True if meaningful progress detected, False otherwise
        Meaningful progress is defined as:
        - Successful relevant tool operations (successful tool calls > 0)
        - OR relevant workspace changes (positive file count delta)
        - OR error reduction (negative error delta)

        Does NOT consider:
        - Repeated identical operations (captured by tool call patterns, but we're being conservative)
        - Failed operations
        - Unrelated changes
        - Changes that immediately regress

        """
        # Need at least one previous iteration to compare
        if len(self._history) < 2:
            # First iteration - consider it meaningful if we had any success
            return self.successful_tool_calls > 0

        prev = self._history[-1]

        # Check for meaningful progress indicators
        has_successful_operations = self.successful_tool_calls > 0
        has_positive_workspace_change = self.workspace_file_count_delta > 0
        has_error_reduction = self.error_count_delta < 0

        return has_successful_operations or has_positive_workspace_change or has_error_reduction

    def get_bounded_history(self) -> List[Dict[str, Any]]:
        """Get bounded history as a list of dictionaries for serialization.

        Returns:
            List of metric dictionaries representing bounded history
        """
        return [
            {
                "iteration": m.iteration,
                "successful_tool_calls": m.successful_tool_calls,
                "failed_tool_calls": m.failed_tool_calls,
                "total_tool_calls": m.total_tool_calls,
                "workspace_file_count": m.workspace_file_count,
                "workspace_file_count_delta": m.workspace_file_count_delta,
                "error_count": m.error_count,
                "error_count_delta": m.error_count_delta,
                "success_rate": m.success_rate
            }
            for m in self._history
        ]

    @classmethod
    def from_bounded_history(cls, history_data: List[Dict[str, Any]], max_history_size: int = 10) -> 'ProgressMetrics':
        """Create ProgressMetrics instance from bounded history data.

        Args:
            history_data: List of metric dictionaries
            max_history_size: Maximum size for history

        Returns:
            ProgressMetrics instance with restored history
        """
        if not history_data:
            return cls(_max_history_size=max_history_size)

        # Create instance
        instance = cls(_max_history_size=max_history_size)
        instance._history = []

        # Recreate metrics from history data
        for data in history_data:
            metrics = cls(
                iteration=data["iteration"],
                successful_tool_calls=data["successful_tool_calls"],
                failed_tool_calls=data["failed_tool_calls"],
                total_tool_calls=data["total_tool_calls"],
                workspace_file_count=data["workspace_file_count"],
                workspace_file_count_delta=data["workspace_file_count_delta"],
                error_count=data["error_count"],
                error_count_delta=data["error_count_delta"],
                success_rate=data["success_rate"],
                _max_history_size=max_history_size
            )
            instance._history.append(metrics)

        # Ensure we don't exceed max history size
        if len(instance._history) > max_history_size:
            instance._history = instance._history[-max_history_size:]

        # Set current metrics to the last entry if available
        if instance._history:
            last = instance._history[-1]
            instance.iteration = last.iteration
            instance.successful_tool_calls = last.successful_tool_calls
            instance.failed_tool_calls = last.failed_tool_calls
            instance.total_tool_calls = last.total_tool_calls
            instance.workspace_file_count = last.workspace_file_count
            instance.workspace_file_count_delta = last.workspace_file_count_delta
            instance.error_count = last.error_count
            instance.error_count_delta = last.error_count_delta
            instance.success_rate = last.success_rate

        return instance


class AgentState(Enum):
    """Possible states of the agent orchestrator."""
    PENDING = auto()      # Initial state, task not started
    RUNNING = auto()      # Agent is actively processing
    WAITING_FOR_TOOLS = auto()  # Waiting for tool execution results
    COMPLETED = auto()    # Task completed successfully
    FAILED = auto()       # Task failed due to error
    CANCELLED = auto()    # Task was cancelled by user
    TIMED_OUT = auto()    # Task exceeded time limit


@dataclass
class AgentOrchestratorState:
    """State representation for the agent orchestrator."""
    task_id: str = field(default_factory=lambda: str(uuid4()))
    task_description: str = ""
    current_iteration: int = 0
    max_iterations: int = 10
    state: AgentState = AgentState.PENDING

    # Execution tracking
    start_time: float = field(default_factory=time.time)
    last_activity_time: float = field(default_factory=time.time)
    total_tokens_used: int = 0
    total_tool_calls: int = 0

    # Context and execution history
    execution_history: List[Dict[str, Any]] = field(default_factory=list)
    tool_call_history: List[Dict[str, Any]] = field(default_factory=list)
    tool_result_history: List[Dict[str, Any]] = field(default_factory=list)

    # Error handling
    last_error: Optional[ToolError] = None
    error_count: int = 0
    consecutive_errors: int = 0

    # Retry and failure recovery
    max_consecutive_failures: int = 3
    retry_base_delay: float = 1.0  # seconds
    max_retry_delay: float = 30.0
    retry_multiplier: float = 2.0
    # Failure pattern tracking for advanced recovery
    failure_history: List[Dict[str, Any]] = field(default_factory=list)
    failure_type_counts: Dict[str, int] = field(default_factory=dict)
    alternative_approaches_attempted: List[str] = field(default_factory=list)

    # Progress detection
    stall_detection_iterations: int = 3
    last_progress_iteration: int = 0
    last_successful_tool_calls: int = 0
    last_workspace_file_count: int = 0
    # Progress metrics tracking (Phase 7.3.4.1)
    progress_metrics: ProgressMetrics = field(default_factory=ProgressMetrics)
    # Previous iteration counters for calculating per-iteration deltas
    prev_total_tool_calls: int = 0
    prev_error_count: int = 0
    prev_workspace_file_count: int = 0

    # Completion signals
    is_complete: bool = False
    completion_reason: str = ""
    final_response: str = ""

    # Safety and limits
    safety_violations: int = 0
    resource_warnings: List[str] = field(default_factory=list)


class AgentOrchestrator:
    """Coordinates the autonomous coding-agent execution loop.

    The orchestrator manages the iterative process of:
    1. Building prompts from context and task description
    2. Invoking the LLM via Model Adapter
    3. Parsing LLM responses for tool calls or reasoning
    4. Validating tool calls for safety and permissions
    5. Executing tools through the Tool System
    6. Updating context with results
    7. Evaluating task completion
    8. Handling errors, timeouts, and resource limits
    """

    def __init__(
        self,
        model_adapter: ModelAdapter,
        context_manager: ContextManager,
        tool_registry: ToolRegistry,
        tool_executor: ToolExecutor,
        workspace: Workspace,
        max_iterations: int = 10,
        iteration_timeout: float = 120.0,
        enable_metrics: bool = True,
        # Enhanced control parameters
        max_consecutive_failures: int = 3,
        retry_base_delay: float = 1.0,
        max_retry_delay: float = 30.0,
        retry_multiplier: float = 2.0,
        stall_detection_iterations: int = 3
    ):
        """Initialize the Agent Orchestrator.

        Args:
            model_adapter: Adapter for LLM interactions
            context_manager: Manager for context engineering
            tool_registry: Registry for available tools
            tool_executor: Executor for controlled tool execution
            workspace: Workspace boundary enforcement
            max_iterations: Maximum iterations before forced termination
            iteration_timeout: Timeout per iteration in seconds
            enable_metrics: Whether to collect execution metrics
            max_consecutive_failures: Maximum consecutive failures before termination
            retry_base_delay: Base delay for exponential backoff (seconds)
            max_retry_delay: Maximum delay for exponential backoff (seconds)
            retry_multiplier: Multiplier for exponential backoff
            stall_detection_iterations: Number of iterations with no progress to consider stalled
        """
        print("!!! AgentOrchestrator.__init__ called !!!")
        self.model_adapter = model_adapter
        self.context_manager = context_manager
        self.tool_registry = tool_registry
        self.tool_executor = tool_executor
        self.workspace = workspace
        self.max_iterations = max_iterations
        self.iteration_timeout = iteration_timeout
        self.enable_metrics = enable_metrics

        # Enhanced control parameters
        self.max_consecutive_failures = max_consecutive_failures
        self.retry_base_delay = retry_base_delay
        self.max_retry_delay = max_retry_delay
        self.retry_multiplier = retry_multiplier
        self.stall_detection_iterations = stall_detection_iterations

        # Internal state
        self._state: Optional[AgentOrchestratorState] = None
        self._cancelled: bool = False
        # Persistence and recovery
        self.persistence_dir = os.path.join(str(self.workspace.workspace_root), ".orchestrator_state")
        os.makedirs(self.persistence_dir, exist_ok=True)
        # TODO: Add cancellation token or event for graceful shutdown (we have a basic cancelled flag)

    def cancel(self) -> None:
        """Cancel the agent execution gracefully."""
        self._cancelled = True
    def _get_persistence_file_path(self, checkpoint_name: str = "latest") -> str:
        """Get the file path for a persistence checkpoint.

        Args:
            checkpoint_name: Name of the checkpoint

        Returns:
            Full path to the persistence file
        """
        # Sanitize checkpoint name to prevent directory traversal
        safe_name = "".join(c for c in checkpoint_name if c.isalnum() or c in ("-", "_", ".")).rstrip()
        if not safe_name:
            safe_name = "latest"
        return os.path.join(self.persistence_dir, f"{safe_name}.json")
    def _persist_state(self, checkpoint_name: str = "latest") -> None:
        """Persist the current orchestrator state to a file.

        Args:
            checkpoint_name: Name of the checkpoint
        """
        print(f"DEBUG: _persist_state called with checkpoint_name={checkpoint_name}")
        if self._state is None:
            print(f"DEBUG: _state is None, not persisting")
            return

        # Convert state to a dictionary, excluding non-serializable fields
        state_dict = {
            "task_id": self._state.task_id,
            "task_description": self._state.task_description,
            "current_iteration": self._state.current_iteration,
            "max_iterations": self._state.max_iterations,
            "state": self._state.state.name,  # Store enum name
            "start_time": self._state.start_time,
            "last_activity_time": self._state.last_activity_time,
            "total_tokens_used": self._state.total_tokens_used,
            "total_tool_calls": self._state.total_tool_calls,
            "execution_history": self._state.execution_history,
            "tool_call_history": self._state.tool_call_history,
            "tool_result_history": self._state.tool_result_history,
            "last_error": self._state.last_error.__dict__ if self._state.last_error else None,
            "error_count": self._state.error_count,
            "consecutive_errors": self._state.consecutive_errors,
            "max_consecutive_failures": self._state.max_consecutive_failures,
            "retry_base_delay": self._state.retry_base_delay,
            "max_retry_delay": self._state.max_retry_delay,
            "retry_multiplier": self._state.retry_multiplier,
            "stall_detection_iterations": self._state.stall_detection_iterations,
            "last_progress_iteration": self._state.last_progress_iteration,
            "last_successful_tool_calls": self._state.last_successful_tool_calls,
            "last_workspace_file_count": self._state.last_workspace_file_count,
            "is_complete": self._state.is_complete,
            "completion_reason": self._state.completion_reason,
            "final_response": self._state.final_response,
            "safety_violations": self._state.safety_violations,
            "resource_warnings": self._state.resource_warnings,
            "failure_history": self._state.failure_history,
            "failure_type_counts": self._state.failure_type_counts,
            "alternative_approaches_attempted": self._state.alternative_approaches_attempted,
            # Progress metrics tracking (Phase 7.3.4.1)
            "progress_metrics_history": self._state.progress_metrics.get_bounded_history(),
            "progress_metrics_max_size": self._state.progress_metrics._max_history_size,
            # Previous iteration counters for calculating per-iteration deltas
            "prev_total_tool_calls": self._state.prev_total_tool_calls,
            "prev_error_count": self._state.prev_error_count,
            "prev_workspace_file_count": self._state.prev_workspace_file_count
        }

        # Remove any potentially sensitive data (though none should be present)
        # We could add more filtering here if needed

        file_path = self._get_persistence_file_path(checkpoint_name)
        print(f"DEBUG: Persisting state to {file_path}")
        print(f"DEBUG: State dict keys: {list(state_dict.keys())}")
        try:
            with open(file_path, "w") as f:
                json.dump(state_dict, f, indent=2)
            print(f"DEBUG: State persisted successfully")
        except Exception as e:
            # Log error but don't crash the orchestrator
            print(f"DEBUG: Error persisting state: {e}")
            pass  # In production, we might want to log this
    def _recover_state(self, checkpoint_name: str = "latest") -> bool:
        """Recover orchestrator state from a persisted file.

        Args:
            checkpoint_name: Name of the checkpoint to recover

        Returns:
            True if recovery was successful, False otherwise
        """
        print(f"DEBUG: _recover_state called with checkpoint_name={checkpoint_name}")
        file_path = self._get_persistence_file_path(checkpoint_name)
        print(f"DEBUG: Looking for persistence file at {file_path}")
        if not os.path.exists(file_path):
            # Debug: File doesn't exist
            print(f"DEBUG: Persistence file does not exist at {file_path}")
            return False

        try:
            print(f"DEBUG: Reading persistence file from {file_path}")
            with open(file_path, "r") as f:
                state_dict = json.load(f)
            print(f"DEBUG: Loaded state dict: {state_dict}")

            # Validate the recovered state
            if not self._validate_recovered_state(state_dict):
                # Debug: Validation failed
                print(f"DEBUG: State validation failed")
                return False

            # Check task description match: if current task description is set (non-empty), it must match
            if self._state is not None and self._state.task_description and self._state.task_description != state_dict.get("task_description"):
                # Debug: Task description mismatch
                print(f"DEBUG: Task description mismatch: current='{self._state.task_description}', recovered='{state_dict.get('task_description')}'")
                return False

            # Reconstruct the state
            # We need to create a new AgentOrchestratorState instance
            # and populate it with the recovered data
            print(f"DEBUG: Reconstructing state from recovered data")
            recovered_state = AgentOrchestratorState(
                task_id=state_dict["task_id"],
                task_description=state_dict["task_description"],
                current_iteration=state_dict["current_iteration"],
                max_iterations=state_dict["max_iterations"],
                state=AgentState[state_dict["state"]],  # Convert enum name back to enum
                start_time=state_dict["start_time"],
                last_activity_time=state_dict["last_activity_time"],
                total_tokens_used=state_dict["total_tokens_used"],
                total_tool_calls=state_dict["total_tool_calls"],
                execution_history=state_dict["execution_history"],
                tool_call_history=state_dict["tool_call_history"],
                tool_result_history=state_dict["tool_result_history"],
                last_error=ToolError(**state_dict["last_error"]) if state_dict["last_error"] else None,
                error_count=state_dict["error_count"],
                consecutive_errors=state_dict["consecutive_errors"],
                max_consecutive_failures=state_dict["max_consecutive_failures"],
                retry_base_delay=state_dict["retry_base_delay"],
                max_retry_delay=state_dict["max_retry_delay"],
                retry_multiplier=state_dict["retry_multiplier"],
                stall_detection_iterations=state_dict["stall_detection_iterations"],
                last_progress_iteration=state_dict["last_progress_iteration"],
                last_successful_tool_calls=state_dict["last_successful_tool_calls"],
                last_workspace_file_count=state_dict["last_workspace_file_count"],
                is_complete=state_dict["is_complete"],
                completion_reason=state_dict["completion_reason"],
                final_response=state_dict["final_response"],
                safety_violations=state_dict["safety_violations"],
                resource_warnings=state_dict["resource_warnings"],
                failure_history=state_dict.get("failure_history", []),
                failure_type_counts=state_dict.get("failure_type_counts", {}),
                alternative_approaches_attempted=state_dict.get("alternative_approaches_attempted", []),
                # Progress metrics tracking (Phase 7.3.4.1)
                progress_metrics=ProgressMetrics.from_bounded_history(
                    state_dict.get("progress_metrics_history", []),
                    state_dict.get("progress_metrics_max_size", 10)
                ),
                # Previous iteration counters for calculating per-iteration deltas
                prev_total_tool_calls=state_dict.get("prev_total_tool_calls", 0),
                prev_error_count=state_dict.get("prev_error_count", 0),
                prev_workspace_file_count=state_dict.get("prev_workspace_file_count", 0)
            )

            print(f"DEBUG: Setting _state to recovered state")
            self._state = recovered_state
            print(f"DEBUG: Recovery successful")
            return True
        except Exception as e:
            # Recovery failed
            print(f"DEBUG: Exception during recovery: {e}")
            import traceback
            traceback.print_exc()
            return False
    def _validate_recovered_state(self, state_dict: dict) -> bool:
        """Validate recovered state dictionary.

        Args:
            state_dict: Dictionary containing state data

        Returns:
            True if state is valid, False otherwise
        """
        required_fields = [
            "task_id", "task_description", "current_iteration", "max_iterations",
            "state", "start_time", "last_activity_time", "total_tokens_used",
            "total_tool_calls", "execution_history", "tool_call_history",
            "tool_result_history", "last_error", "error_count", "consecutive_errors",
            "max_consecutive_failures", "retry_base_delay", "max_retry_delay",
            "retry_multiplier", "stall_detection_iterations", "last_progress_iteration",
            "last_successful_tool_calls", "last_workspace_file_count",
            "is_complete", "completion_reason", "final_response",
            "safety_violations", "resource_warnings"
        ]

        for field in required_fields:
            if field not in state_dict:
                return False

        # Additional validation
        if not isinstance(state_dict["task_id"], str):
            return False
        if not isinstance(state_dict["task_description"], str):
            return False
        if not isinstance(state_dict["current_iteration"], int) or state_dict["current_iteration"] < 0:
            return False
        if not isinstance(state_dict["max_iterations"], int) or state_dict["max_iterations"] <= 0:
            return False
        if state_dict["state"] not in [s.name for s in AgentState]:
            return False
        if not isinstance(state_dict["start_time"], (int, float)):
            return False
        if not isinstance(state_dict["last_activity_time"], (int, float)):
            return False
        if not isinstance(state_dict["total_tokens_used"], int) or state_dict["total_tokens_used"] < 0:
            return False
        if not isinstance(state_dict["total_tool_calls"], int) or state_dict["total_tool_calls"] < 0:
            return False
        if not isinstance(state_dict["execution_history"], list):
            return False
        if not isinstance(state_dict["tool_call_history"], list):
            return False
        if not isinstance(state_dict["tool_result_history"], list):
            return False
        if state_dict["last_error"] is not None and not isinstance(state_dict["last_error"], dict):
            return False
        if not isinstance(state_dict["error_count"], int) or state_dict["error_count"] < 0:
            return False
        if not isinstance(state_dict["consecutive_errors"], int) or state_dict["consecutive_errors"] < 0:
            return False
        if not isinstance(state_dict["max_consecutive_failures"], int) or state_dict["max_consecutive_failures"] <= 0:
            return False
        if not isinstance(state_dict["retry_base_delay"], (int, float)) or state_dict["retry_base_delay"] < 0:
            return False
        if not isinstance(state_dict["max_retry_delay"], (int, float)) or state_dict["max_retry_delay"] < 0:
            return False
        if not isinstance(state_dict["retry_multiplier"], (int, float)) or state_dict["retry_multiplier"] <= 0:
            return False
        if not isinstance(state_dict["stall_detection_iterations"], int) or state_dict["stall_detection_iterations"] < 0:
            return False
        if not isinstance(state_dict["last_progress_iteration"], int) or state_dict["last_progress_iteration"] < 0:
            return False
        if not isinstance(state_dict["last_successful_tool_calls"], int) or state_dict["last_successful_tool_calls"] < 0:
            return False
        if not isinstance(state_dict["last_workspace_file_count"], int) or state_dict["last_workspace_file_count"] < 0:
            return False
        if not isinstance(state_dict["is_complete"], bool):
            return False
        if not isinstance(state_dict["completion_reason"], str):
            return False
        if not isinstance(state_dict["final_response"], str):
            return False
        if not isinstance(state_dict["safety_violations"], int) or state_dict["safety_violations"] < 0:
            return False
        if not isinstance(state_dict["resource_warnings"], list):
            return False
        for warning in state_dict["resource_warnings"]:
            if not isinstance(warning, str):
                return False

        # Validate new fields for Phase 7.3.3
        if "failure_history" in state_dict:
            if not isinstance(state_dict["failure_history"], list):
                return False
            for failure in state_dict["failure_history"]:
                if not isinstance(failure, dict):
                    return False
                required_failure_fields = ["timestamp", "iteration", "error_type", "error_message", "is_retryable"]
                for field in required_failure_fields:
                    if field not in failure:
                        return False
                if not isinstance(failure["timestamp"], (int, float)):
                    return False
                if not isinstance(failure["iteration"], int) or failure["iteration"] < 0:
                    return False
                if not isinstance(failure["error_type"], str):
                    return False
                if not isinstance(failure["error_message"], str):
                    return False
                if not isinstance(failure["is_retryable"], bool):
                    return False

        if "failure_type_counts" in state_dict:
            if not isinstance(state_dict["failure_type_counts"], dict):
                return False
            for error_type, count in state_dict["failure_type_counts"].items():
                if not isinstance(error_type, str):
                    return False
                if not isinstance(count, int) or count < 0:
                    return False

        if "alternative_approaches_attempted" in state_dict:
            if not isinstance(state_dict["alternative_approaches_attempted"], list):
                return False
            for approach in state_dict["alternative_approaches_attempted"]:
                if not isinstance(approach, str):
                    return False

        # Validate progress metrics tracking fields (Phase 7.3.4.1)
        if "progress_metrics_history" in state_dict:
            if not isinstance(state_dict["progress_metrics_history"], list):
                return False
            for metric in state_dict["progress_metrics_history"]:
                if not isinstance(metric, dict):
                    return False
                # Check that each metric has the expected fields
                expected_fields = ["iteration", "successful_tool_calls", "failed_tool_calls", "total_tool_calls",
                                 "workspace_file_count", "workspace_file_count_delta", "error_count",
                                 "error_count_delta", "success_rate"]
                for field in expected_fields:
                    if field not in metric:
                        return False
                    if not isinstance(metric[field], (int, float)) and field != "success_rate":
                        return False
                    if field == "success_rate" and not isinstance(metric[field], (int, float)):
                        return False

        if "progress_metrics_max_size" in state_dict:
            if not isinstance(state_dict["progress_metrics_max_size"], int) or state_dict["progress_metrics_max_size"] <= 0:
                return False

        if "prev_total_tool_calls" in state_dict:
            if not isinstance(state_dict["prev_total_tool_calls"], int) or state_dict["prev_total_tool_calls"] < 0:
                return False

        if "prev_error_count" in state_dict:
            if not isinstance(state_dict["prev_error_count"], int) or state_dict["prev_error_count"] < 0:
                return False

        if "prev_workspace_file_count" in state_dict:
            if not isinstance(state_dict["prev_workspace_file_count"], int) or state_dict["prev_workspace_file_count"] < 0:
                return False

        return True

    async def execute_task(self, task_description: str) -> AgentOrchestratorState:
        """Execute a task using the agent orchestration loop.

        Args:
            task_description: Description of the task to accomplish

        Returns:
            Final agent state after task completion or termination
        """
        print(f"DEBUG: execute_task called with task_description={task_description}")
        # Attempt to recover state from latest checkpoint
        recovered = self._recover_state("latest")
        if recovered and self._state is not None and not self._state.is_complete and self._state.task_description == task_description:
            # Recovery successful and we have a valid, incomplete state for the same task
            # Update the last activity time to now to prevent immediate timeout
            self._state.last_activity_time = time.time()
            # Ensure the state is RUNNING
            if self._state.state != AgentState.RUNNING:
                self._state.state = AgentState.RUNNING
        else:
            # Initialize state
            # Initialize state with progress tracking fields
            self._state = AgentOrchestratorState(
                task_description=task_description,
                max_iterations=self.max_iterations,
                max_consecutive_failures=self.max_consecutive_failures,
                retry_base_delay=self.retry_base_delay,
                max_retry_delay=self.max_retry_delay,
                retry_multiplier=self.retry_multiplier,
                stall_detection_iterations=self.stall_detection_iterations,
                prev_total_tool_calls=0,
                prev_error_count=0,
                prev_workspace_file_count=0
            )
            self._state.state = AgentState.RUNNING
            self._state.start_time = time.time()
            self._state.last_activity_time = self._state.start_time

        try:
            # Main execution loop
            while not self._state.is_complete and self._state.current_iteration < self._state.max_iterations:
                iteration_start = time.time()

                # Check for overall timeout
                if time.time() - self._state.start_time > self.iteration_timeout:
                    self._state.state = AgentState.TIMED_OUT
                    self._state.is_complete = True
                    self._state.completion_reason = "Overall timeout exceeded"
                    break

                # Update iteration counter
                self._state.current_iteration += 1
                self._state.last_activity_time = time.time()

                # Execute one iteration
                await self._execute_iteration()

                # Check if we should continue
                if self._state.is_complete:
                    break

                # Check for stall
                if self._check_stall():
                    self._state.state = AgentState.FAILED
                    self._state.is_complete = True
                    self._state.completion_reason = "Stalled: no progress for too many iterations"
                    break

                # Check for cancellation
                if self._cancelled:
                    self._state.state = AgentState.CANCELLED
                    self._state.is_complete = True
                    self._state.completion_reason = "Task cancelled by user"
                    break

                # Small delay between iterations to prevent tight looping
                await asyncio.sleep(0.1)

        except Exception as e:
            # Handle unexpected errors
            self._state.state = AgentState.FAILED
            self._state.is_complete = True
            self._state.completion_reason = f"Unexpected error: {str(e)}"
            self._state.last_error = InternalToolError(
                f"Unexpected error in orchestrator: {str(e)}",
                tool_name="agent_orchestrator"
            )

        finally:
            print("DEBUG: Entering finally block")
            # Ensure we have a final state
            print(f"DEBUG: Finally block - is_complete: {self._state.is_complete if self._state else None}, current_iteration: {self._state.current_iteration if self._state else None}, max_iterations: {self._state.max_iterations if self._state else None}")
            if not self._state.is_complete:
                # Check if we reached max iterations
                if self._state.current_iteration >= self._state.max_iterations:
                    print(f"DEBUG: error_count = {self._state.error_count}")
                    # If we have errors when reaching max iterations, treat as failure
                    if self._state.error_count > 0:
                        self._state.state = AgentState.FAILED
                        self._state.is_complete = True
                        self._state.completion_reason = "Max iterations reached without completion"
                        print(f"DEBUG: Setting FAILED state due to max iterations reached with errors")
                    else:
                        self._state.state = AgentState.COMPLETED
                        self._state.is_complete = True
                        self._state.completion_reason = "Maximum iterations reached"
                        print(f"DEBUG: Setting COMPLETED state due to max iterations reached")
                else:
                    self._state.state = AgentState.FAILED
                    self._state.is_complete = True
                    if not self._state.completion_reason:
                        self._state.completion_reason = "Max iterations reached without completion"
                    print(f"DEBUG: Setting FAILED state due to not reaching max iterations")
        return self._state

    async def _execute_iteration(self) -> None:
        """Execute a single iteration of the agent loop with retry logic and progress tracking."""
        print("DEBUG: _execute_iteration called")
        if self._state is None:
            raise RuntimeError("Orchestrator state not initialized")

        # Retry loop for transient errors
        max_retries_per_iteration = 3
        for attempt in range(max_retries_per_iteration + 1):
            try:
                # Step 1: Build LLM prompt from current context and task description
                prompt = await self._build_prompt()

                # Step 2: Invoke LLM via Model Adapter
                model_request = ModelRequest(
                    prompt=prompt,
                    temperature=0.7,  # Could be made configurable
                    max_tokens=4000,  # Could be made configurable
                    tools=self._get_available_tools_schema()  # Provide tool definitions
                )

                # Get response from model adapter with timeout
                try:
                    model_response = await asyncio.wait_for(
                        self.model_adapter._generate(model_request),
                        timeout=30.0  # LLM response timeout
                    )
                except asyncio.TimeoutError:
                    raise TimeoutError("LLM response timeout", tool_name="model_adapter")

                # Update token usage
                if hasattr(model_response, 'usage') and model_response.usage:
                    self._state.total_tokens_used += getattr(model_response.usage, 'total_tokens', 0)

                # Step 3: Parse LLM response for tool calls or reasoning
                tool_calls = self._extract_tool_calls(model_response)
                reasoning_text = model_response.text.strip() if model_response.text else ""

                # Store execution history
                execution_record = {
                    "iteration": self._state.current_iteration,
                    "timestamp": time.time(),
                    "prompt_length": len(prompt),
                    "response_length": len(model_response.text) if model_response.text else 0,
                    "tool_calls_count": len(tool_calls),
                    "reasoning": reasoning_text[:200] + "..." if len(reasoning_text) > 200 else reasoning_text,
                    "state_at_start": self._state.state.name,
                    "retry_attempt": attempt,
                    "model_usage": {
                        "total_tokens": getattr(model_response.usage, 'total_tokens', 0) if hasattr(model_response, 'usage') and model_response.usage else 0
                    } if hasattr(model_response, 'usage') else None
                }
                self._state.execution_history.append(execution_record)

                # Step 4: If no tool calls, evaluate if we can complete based on reasoning
                if not tool_calls:
                    await self._evaluate_completion_from_reasoning(reasoning_text)
                    return

                # Step 5: Validate tool calls for safety and permissions
                validated_tool_calls = await self._validate_tool_calls(tool_calls)

                if not validated_tool_calls:
                    # No valid tool calls after validation, treat as completion attempt
                    await self._evaluate_completion_from_reasoning(
                        "No valid tool calls available after safety validation. "
                        "Considering task complete based on reasoning: " + reasoning_text
                    )
                    return

                # Step 6: Execute validated tool calls
                tool_results = await self._execute_tool_calls(validated_tool_calls)

                # Step 7: Process results and update context
                await self._process_tool_results(tool_results)

                # Step 8: Update execution history with results
                call_data = {}
                result_data = {}
                # Safely extract data from tool call and result for JSON serialization
                if hasattr(call, 'dict'):
                    try:
                        call_data = call.dict()
                    except Exception:
                        call_data = str(call)
                else:
                    call_data = str(call)

                if hasattr(result, 'dict'):
                    try:
                        result_data = result.dict()
                    except Exception:
                        result_data = str(result)
                else:
                    result_data = str(result)

                self._state.tool_call_history.extend([
                    {"call": call_data, "result": result_data}
                    for call, result in zip(validated_tool_calls, tool_results)
                ])

                # If we succeeded, update progress tracking and break out of retry loop
                self._update_progress(success=True)
                self._persist_state()
                return  # Success, exit the iteration

            except Exception as e:
                # If we have retries left and the error is retryable, wait and retry
                if attempt < max_retries_per_iteration and self._is_retryable_error(e):
                    delay = self._calculate_backoff_delay(attempt)
                    await asyncio.sleep(delay)
                    continue
                else:
                    # No more retries or non-retryable error, handle the error
                    self._state.error_count += 1
                    self._state.consecutive_errors += 1
                    self._state.last_error = ToolError(
                        f"Iteration {self._state.current_iteration} failed: {str(e)}",
                        tool_name="agent_orchestrator"
                    ) if not isinstance(e, ToolError) else e

                    # Record failure for pattern detection
                    self._record_failure(e, self._state.current_iteration)

                    # Update progress tracking for failed iteration
                    self._update_progress(success=False)
                    self._persist_state()

                    # Check for fundamental flaw that suggests we should try alternative approaches
                    if self._state.consecutive_errors >= self._state.max_consecutive_failures:
                        if self._detect_fundamental_flaw() and self._attempt_alternative_approach():
                            # We've detected a fundamental flaw and will try an alternative approach
                            # Don't fail yet - let the next iteration try the alternative approach
                            pass
                        else:
                            # Either no fundamental flaw detected or no alternative approaches left
                            self._state.state = AgentState.FAILED
                            self._state.is_complete = True
                            self._state.completion_reason = f"Too many consecutive errors: {self._state.consecutive_errors}"
                    return  # Exit the iteration (either failed or will be retried in next iteration if not complete)

        # If we exhausted all retries without success, the error has already been handled above
        # and we have returned. This point should not be reached, but just in case:
        if self._state is not None and not self._state.is_complete:
            self._state.state = AgentState.FAILED
            self._state.is_complete = True
            if not self._state.completion_reason:
                self._state.completion_reason = "Max retries exceeded without success"
            self._persist_state()

    def _is_retryable_error(self, error: Exception) -> bool:
        """Determine if an error is retryable at the orchestrator level.

        Args:
            error: The error to check

        Returns:
            True if the error is retryable, False otherwise
        """
        # Import error types locally to avoid circular imports
        from autonomous_agent.tool.errors import (
            TimeoutError,
            InternalToolError,
            ResourceLimitError
        )

        # Consider these errors as retryable
        if isinstance(error, (TimeoutError, InternalToolError, ResourceLimitError)):
            return True

        # Consider model-related transient errors as retryable
        # Note: We don't have direct access to model-specific errors here,
        # but we can check for common transient error messages if needed

        # By default, consider other errors as non-retryable
        return False

    def _calculate_backoff_delay(self, attempt: int) -> float:
        """Calculate delay for exponential backoff with jitter.

        Args:
            attempt: The current attempt number (0-based)

        Returns:
            Delay in seconds
        """
        import random
        base = min(
            self._state.retry_base_delay * (self._state.retry_multiplier ** attempt),
            self._state.max_retry_delay
        )
        # Add jitter to prevent thundering herd
        jitter = random.uniform(0, 0.1 * base)
        return base + jitter

    def _update_progress(self, success: bool) -> None:
        """Update progress tracking using ProgressMetrics.

        Args:
            success: Whether the current iteration was successful
        """
        print("!!! _update_progress called !!!")
        if self._state is None:
            return

        # Calculate current workspace file count
        try:
            if os.path.exists(str(self.workspace.workspace_root)):
                workspace_file_count = sum(len(files) for _, _, files in os.walk(str(self.workspace.workspace_root)))
            else:
                workspace_file_count = 0
        except Exception:
            # If we can't count files, use 0
            workspace_file_count = 0

        # Calculate per-iteration metrics by subtracting previous iteration's cumulative values
        successful_tool_calls = self._state.total_tool_calls - self._state.prev_total_tool_calls
        failed_tool_calls = self._state.error_count - self._state.prev_error_count
        workspace_file_count_delta = workspace_file_count - self._state.prev_workspace_file_count
        error_count_delta = self._state.error_count - self._state.prev_error_count

        # Update progress metrics
        self._state.progress_metrics.update(
            iteration=self._state.current_iteration,
            successful_tool_calls=successful_tool_calls,
            failed_tool_calls=failed_tool_calls,
            workspace_file_count=workspace_file_count,
            error_count=self._state.error_count
        )

        # Update previous values for next iteration
        self._state.prev_total_tool_calls = self._state.total_tool_calls
        self._state.prev_error_count = self._state.error_count
        self._state.prev_workspace_file_count = workspace_file_count

        # Update legacy fields for backward compatibility (will be deprecated in future phases)
        if success:
            self._state.last_progress_iteration = self._state.current_iteration
            self._state.last_successful_tool_calls = successful_tool_calls
            self._state.last_workspace_file_count = workspace_file_count

        # Debug print
        print(f"DEBUG: Iteration {self._state.current_iteration}, successful_tool_calls={successful_tool_calls}, total_tool_calls={self._state.total_tool_calls}, prev_total_tool_calls={self._state.prev_total_tool_calls}")

        # Debug print
        # print(f"DEBUG: Iteration {self._state.current_iteration}, successful_tool_calls={successful_tool_calls}, total_tool_calls={self._state.total_tool_calls}, prev_total_tool_calls={self._state.prev_total_tool_calls}")

    def _check_stall(self) -> bool:
        """Check if the orchestrator has stalled (no progress for too many iterations).

        Returns:
            True if stalled, False otherwise
        """
        if self._state is None:
            return False

        # Check if we've made progress in the last stall_detection_iterations iterations
        iterations_since_progress = self._state.current_iteration - self._state.last_progress_iteration
        return iterations_since_progress >= self._state.stall_detection_iterations

    async def _build_prompt(self) -> str:
        """Build LLM prompt from current context and task description.

        Returns:
            Formatted prompt for the LLM
        """
        if self._state is None:
            return ""

        # Get context from context manager
        context = self.context_manager.create_context_package(
            task_description=self._state.task_description
        )

        # Get context summary
        print(f"DEBUG: context_manager type: {type(self.context_manager)}")
        print(f"DEBUG: context type: {type(context)}")
        print(f"DEBUG: context has get_context_summary: {hasattr(context, "get_context_summary")}")
        context_summary = self.context_manager.get_context_summary(context)

        # Build prompt
        prompt = f"""Task: {self._state.task_description}

Current Iteration: {self._state.current_iteration}
Max Iterations: {self._state.max_iterations}

Context Summary:
{json.dumps(context_summary, indent=2)}

Available Tools:
{self._format_available_tools()}

Please provide the next steps to accomplish the task. If the task is complete, indicate so in your reasoning.
"""
        return prompt

    def _record_failure(self, error: Exception, iteration: int) -> None:
        """Record a failure for pattern detection and analysis.

        Args:
            error: The error that occurred
            iteration: The iteration number when the error occurred
        """
        if self._state is None:
            return

        # Record failure details
        failure_record = {
            "timestamp": time.time(),
            "iteration": iteration,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "is_retryable": self._is_retryable_error(error)
        }
        self._state.failure_history.append(failure_record)

        # Track failure type counts
        error_type = type(error).__name__
        if error_type in self._state.failure_type_counts:
            self._state.failure_type_counts[error_type] += 1
        else:
            self._state.failure_type_counts[error_type] = 1

        # Keep failure history bounded to prevent memory growth
        if len(self._state.failure_history) > 50:
            self._state.failure_history = self._state.failure_history[-50:]

    def _generate_alternative_approach(self, context: str) -> str:
        """Generate an alternative approach prompt based on failure patterns.

        Args:
            context: The current context summary

        Returns:
            Modified prompt encouraging alternative approaches
        """
        if self._state is None:
            return context

        # Analyze recent failures to suggest alternatives
        recent_failures = self._state.failure_history[-5:] if len(self._state.failure_history) >= 5 else self._state.failure_history

        # Generate alternative approach guidance
        alternative_guidance = "\n\nAlternative Approach Suggestion:\n"

        # Check for tool-related failures
        tool_errors = [f for f in recent_failures if "tool" in f["error_message"].lower() or
                      f["error_type"] in ["ToolError", "InternalToolError"]]
        if tool_errors:
            alternative_guidance += "- Previous tool executions have failed. Consider:\n"
            alternative_guidance += "  * Verifying tool parameters and inputs\n"
            alternative_guidance += "  * Trying different tools to accomplish the same goal\n"
            alternative_guidance += "  * Checking if required preconditions are met\n"

        # Check for timeout-related failures
        timeout_errors = [f for f in recent_failures if "timeout" in f["error_message"].lower()]
        if timeout_errors:
            alternative_guidance += "- Previous operations have timed out. Consider:\n"
            alternative_guidance += "  * Breaking down complex operations into smaller steps\n"
            alternative_guidance += "  * Using more efficient approaches or algorithms\n"
            alternative_guidance += "  * Checking for infinite loops or inefficient code\n"

        # Check for resource-related failures
        resource_errors = [f for f in recent_failures if "resource" in f["error_message"].lower() or
                          "limit" in f["error_message"].lower() or
                          f["error_type"] == "ResourceLimitError"]
        if resource_errors:
            alternative_guidance += "- Resource limits have been exceeded. Consider:\n"
            alternative_guidance += "  * Optimizing resource usage\n"
            alternative_guidance += "  * Requesting more resources if possible\n"
            alternative_guidance += "  * Reducing complexity or scale of operations\n"

        # Check for logic-related failures
        logic_errors = [f for f in recent_failures if "logic" in f["error_message"].lower() or
                       f["error_type"] in ["LogicError", "ValidationError"]]
        if logic_errors:
            alternative_guidance += "- Logic or validation errors have occurred. Consider:\n"
            alternative_guidance += "  * Reviewing assumptions and preconditions\n"
            alternative_guidance += "  * Checking input data validity\n"
            alternative_guidance += "  * Using more robust error handling\n"

        # If no specific patterns found, provide general guidance
        if not (tool_errors or timeout_errors or resource_errors or logic_errors):
            alternative_guidance += "- No specific failure patterns detected. Consider:\n"
            alternative_guidance += "  * Reviewing the overall approach and strategy\n"
            alternative_guidance += "  * Consulting documentation or best practices\n"
            alternative_guidance += "  * Seeking feedback or collaboration\n"

        return alternative_guidance

    def _get_available_tools_schema(self) -> List[Dict[str, Any]]:
        """Get the schema of all available tools for the LLM.

        Returns:
            List of tool schemas in format expected by LLM
        """
        schemas = []
        for tool_name in self.tool_registry.list_tools():
            tool = self.tool_registry.get(tool_name)
            if tool:
                schema = {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.schema.input_schema
                    }
                }
                schemas.append(schema)
        return schemas

    def _detect_fundamental_flaw(self) -> bool:
        """Detect if there is a fundamental flaw in the current approach based on failure patterns.

        Returns:
            True if a fundamental flaw is detected (indicating the approach should be changed),
            False otherwise
        """

    def _format_available_tools(self) -> str:
        """Format available tools for inclusion in prompts.

        Returns:
            Formatted string describing available tools
        """
        tool_descriptions = []
        for tool_name in self.tool_registry.list_tools():
            tool = self.tool_registry.get(tool_name)
            if tool:
                tool_descriptions.append(f"- {tool.name}: {tool.description}")

        return "\n".join(tool_descriptions) if tool_descriptions else "No tools available"

    def _extract_tool_calls(self, model_response: ModelResponse) -> List[ToolCall]:
        """Extract tool calls from model response.

        Args:
            model_response: Response from the LLM

        Returns:
            List of tool calls to execute
        """
        tool_calls = []

        # Check if response has tool_calls attribute (from ModelResponse)
        if hasattr(model_response, 'tool_calls') and model_response.tool_calls:
            tool_calls.extend(model_response.tool_calls)

        # Also check for tool calls in text format (parsing would be needed here)
        # For now, we'll rely on the structured tool_calls from ModelResponse

        return tool_calls

    async def _validate_tool_calls(self, tool_calls: List[ToolCall]) -> List[ToolCall]:
        """Validate tool calls for safety, permissions, and validity.

        Args:
            tool_calls: Tool calls to validate

        Returns:
            List of validated tool calls
        """
        if self._state is None:
            return []

        validated_calls = []
        permission_context = PermissionContext(
            user_id="autonomous_agent",
            session_id=self._state.task_id,
            workspace_path=str(self.workspace.workspace_root)
        )

        for tool_call in tool_calls:
            try:
                # Check if tool exists
                tool = self.tool_registry.get(tool_call.name)
                if not tool:
                    # Log invalid tool but don't fail the iteration
                    continue

                # Check permissions via policy engine
                permission_error = self.tool_policy_engine.check_permission(
                    tool_call.name, tool_call.arguments, permission_context
                )
                if permission_error:
                    # Log permission error but don't fail the iteration
                    continue

                # Validate input arguments against tool schema
                # We'll rely on the executor to do validation, but we can do a quick check here
                # For now, we'll assume the executor will handle validation

                # If all checks pass, add to validated calls
                validated_calls.append(tool_call)

            except Exception:
                # Skip invalid tool calls
                continue

        return validated_calls

    @property
    def tool_policy_engine(self) -> ToolPolicyEngine:
        """Get or create the tool policy engine."""
        if not hasattr(self, '_tool_policy_engine'):
            self._tool_policy_engine = ToolPolicyEngine(self.workspace)
        return self._tool_policy_engine

    async def _execute_tool_calls(self, tool_calls: List[ToolCall]) -> List[ToolResult]:
        """Execute validated tool calls.

        Args:
            tool_calls: Tool calls to execute

        Returns:
            List of tool execution results
        """
        if self._state is None:
            return []

        results = []
        for tool_call in tool_calls:
            try:
                # Get the tool instance
                tool = self.tool_registry.get(tool_call.name)
                if not tool:
                    results.append(ToolResult(
                        success=False,
                        error=ToolNotFoundError(
                            f"Tool '{tool_call.name}' not found",
                            tool_name=tool_call.name
                        )
                    ))
                    continue

                # Prepare tool input
                tool_input = tool_call.arguments if hasattr(tool_call, 'arguments') else {}

                # Execute the tool
                result = await self.tool_executor.execute(
                    tool=tool,
                    tool_input=tool_input
                )

                results.append(result)

                # Update counters
                if result.success:
                    self._state.total_tool_calls += 1
                else:
                    self._state.error_count += 1

            except Exception as e:
                results.append(ToolResult(
                    success=False,
                    error=ToolError(
                        f"Failed to execute tool {tool_call.name}: {str(e)}",
                        tool_name=tool_call.name
                    )
                ))
                self._state.error_count += 1

        return results

    async def _process_tool_results(self, tool_results: List[ToolResult]) -> None:
        """Process tool results and update context.

        Args:
            tool_results: Results from tool executions
        """
        if self._state is None:
            return

        # Process each result
        for i, result in enumerate(tool_results):
            # Store result in history
            result_record = {
                "iteration": self._state.current_iteration,
                "timestamp": time.time(),
                "tool_name": f"tool_{i}",  # In reality, we'd have the actual tool name
                "success": result.success,
                "has_error": result.error is not None,
                "data_type": type(result.data).__name__ if result.data is not None else "None"
            }
            self._state.tool_result_history.append(result_record)

            # If successful, consider updating context with the result
            # The context is updated via the workspace (tools write to workspace)
            # and the context manager will pick it up in the next iteration.
            # We don't need to do anything special here.

        # Check if any results indicate task completion
        # This would be domain-specific - for now, we'll rely on the LLM to decide

    async def _evaluate_completion_from_reasoning(self, reasoning: str) -> None:
        """Evaluate if the task is complete based on LLM reasoning.

        Args:
            reasoning: Reasoning text from the LLM
        """
        if self._state is None:
            return

        # Simple completion detection - in reality, this would be more sophisticated
        completion_indicators = [
            "task is complete",
            "task completed",
            "finished",
            "done",
            "accomplished",
            "goal achieved",
            "objective met",
            "no further action needed",
            "task successfully completed"
        ]

        reasoning_lower = reasoning.lower()
        for indicator in completion_indicators:
            if indicator in reasoning_lower:
                self._state.state = AgentState.COMPLETED
                self._state.is_complete = True
                self._state.completion_reason = "Task completed based on LLM reasoning"
                self._state.final_response = reasoning
                return

        # If we've reached max iterations, force completion
        if self._state.current_iteration >= self._state.max_iterations:
            self._state.state = AgentState.COMPLETED
            self._state.is_complete = True
            self._state.completion_reason = "Maximum iterations reached"
            self._state.final_response = reasoning

    def get_state(self) -> Optional[AgentOrchestratorState]:
        """Get the current state of the orchestrator.

        Returns:
            Current agent orchestrator state or None if not initialized
        """
        return self._state


# Convenience function for easy instantiation
def create_agent_orchestrator(
    model_adapter: ModelAdapter,
    context_manager: ContextManager,
    workspace: Workspace,
    max_iterations: int = 10
) -> AgentOrchestrator:
    """Create an AgentOrchestrator with default configuration.

    Args:
        model_adapter: Adapter for LLM interactions
        context_manager: Manager for context engineering
        workspace: Workspace boundary enforcement
        max_iterations: Maximum iterations before forced termination

    Returns:
        Configured AgentOrchestrator instance
    """
    # Get global tool registry and create executor/validator
    tool_registry = get_global_registry()

    # These would need to be properly initialized in a real implementation
    # For now, we'll create placeholder instances
    from autonomous_agent.tool.policy import ToolPolicyEngine
    from autonomous_agent.tool.validation import ToolValidator

    policy_engine = ToolPolicyEngine(workspace)
    validator = ToolValidator(workspace)
    tool_executor = ToolExecutor(policy_engine, validator, workspace)

    return AgentOrchestrator(
        model_adapter=model_adapter,
        context_manager=context_manager,
        tool_registry=tool_registry,
        tool_executor=tool_executor,
        workspace=workspace,
        max_iterations=max_iterations
    )
 
