"""Agent Orchestrator for the Autonomous Coding Agent.

This module provides the AgentOrchestrator class that coordinates the
autonomous coding-agent execution loop, managing the iterative process of
LLM reasoning, tool execution, and state updates.
"""

from __future__ import annotations

import asyncio
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

    # Progress detection
    stall_detection_iterations: int = 3
    last_progress_iteration: int = 0
    last_successful_tool_calls: int = 0
    last_workspace_file_count: int = 0

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
        # TODO: Add cancellation token or event for graceful shutdown (we have a basic cancelled flag)

    def cancel(self) -> None:
        """Cancel the agent execution gracefully."""
        self._cancelled = True

    async def execute_task(self, task_description: str) -> AgentOrchestratorState:
        """Execute a task using the agent orchestration loop.

        Args:
            task_description: Description of the task to accomplish

        Returns:
            Final agent state after task completion or termination
        """
        # Initialize state
        self._state = AgentOrchestratorState(
            task_description=task_description,
            max_iterations=self.max_iterations,
            max_consecutive_failures=self.max_consecutive_failures,
            retry_base_delay=self.retry_base_delay,
            max_retry_delay=self.max_retry_delay,
            retry_multiplier=self.retry_multiplier,
            stall_detection_iterations=self.stall_detection_iterations
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
            # Ensure we have a final state
            if not self._state.is_complete:
                self._state.state = AgentState.FAILED
                self._state.is_complete = True
                if not self._state.completion_reason:
                    self._state.completion_reason = "Max iterations reached without completion"

        return self._state

    async def _execute_iteration(self) -> None:
        """Execute a single iteration of the agent loop with retry logic and progress tracking."""
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
                    "reasoning": reasoning_text[:200] + "..." if len(reasoning_text) > 200 else reasoning_text
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
                self._state.tool_call_history.extend([
                    {"call": call.dict() if hasattr(call, 'dict') else str(call),
                     "result": result.dict() if hasattr(result, 'dict') else str(result)}
                    for call, result in zip(validated_tool_calls, tool_results)
                ])

                # If we succeeded, update progress tracking and break out of retry loop
                self._update_progress(success=True)
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

                    # Update progress tracking for failed iteration
                    self._update_progress(success=False)

                    # Check if we should terminate due to consecutive failures
                    if self._state.consecutive_errors >= self._state.max_consecutive_failures:
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
        """Update progress tracking for stall detection.

        Args:
            success: Whether the current iteration was successful
        """
        if self._state is None:
            return

        # Update last progress iteration if we had success
        if success:
            self._state.last_progress_iteration = self._state.current_iteration
            # Update workspace file count for progress detection
            try:
                # Count files in workspace (simplified)
                import os
                if os.path.exists(str(self.workspace.workspace_root)):
                    file_count = sum(len(files) for _, _, files in os.walk(str(self.workspace.workspace_root)))
                    self._state.last_workspace_file_count = file_count
                else:
                    self._state.last_workspace_file_count = 0
            except Exception:
                # If we can't count files, skip workspace tracking
                pass
        # Note: We don't update on failure, but we could track consecutive failures elsewhere

    def _check_stall(self) -> bool:
        """Check if the agent has stalled (no progress for too many iterations).

        Returns:
            True if stalled, False otherwise
        """
        if self._state is None:
            return False
        # If we haven't made any progress yet, we can't stall
        if self._state.last_progress_iteration == 0:
            return False
        iterations_since_progress = self._state.current_iteration - self._state.last_progress_iteration
        return iterations_since_progress >= self._state.stall_detection_iterations

    async def _build_prompt(self) -> str:
        """Build the LLM prompt from current context and task description.

        Returns:
            Formatted prompt string for the LLM
        """
        if self._state is None:
            raise RuntimeError("Orchestrator state not initialized")

        # Get context from context manager
        context_package = self.context_manager.create_context_package(
            task_description=self._state.task_description
        )
        context_summary = self.context_manager.get_context_summary(context_package)

        # Build prompt
        prompt_parts = [
            f"Task: {self._state.task_description}",
            "",
            "Context:",
            str(context_summary),  # We can format this better if needed
            "",
            "Instructions:",
            "You are an autonomous coding agent. Analyze the task and current context,",
            "then determine what actions to take. You can use available tools to",
            "investigate, modify, or create files as needed to complete the task.",
            "",
            "Available tools:",
            self._format_available_tools(),
            "",
            "Respond with either:",
            "1. Tool calls in the format: [tool_name](tool_arguments), or",
            "2. Reasoning about next steps if no tools are needed, or",
            "3. A final completion statement if the task is done.",
            "",
            f"Iteration: {self._state.current_iteration}/{self._state.max_iterations}",
            ""
        ]

        return "\n".join(prompt_parts)

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