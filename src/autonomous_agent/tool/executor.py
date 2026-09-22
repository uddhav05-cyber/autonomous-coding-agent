"""Controlled tool executor with timeout handling, result capture, and error management."""

from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, Optional, Callable
from dataclasses import dataclass

from autonomous_agent.tool.interface import Tool, ToolResult, ToolSchema
from autonomous_agent.tool.errors import (
    ToolError, TimeoutError, ExecutionError, InternalToolError,
    ValidationError, PermissionDeniedError, WorkspaceViolationError
)
from autonomous_agent.tool.validation import ToolValidator
from autonomous_agent.tool.policy import ToolPolicyEngine, PermissionContext


@dataclass
class ExecutionConfig:
    """Configuration for tool execution."""

    timeout_seconds: int = 30
    validation_level: int = 2  # ValidationLevel.FULL equivalent
    enable_timing: bool = True
    capture_output: bool = True
    cleanup_on_error: bool = True


class ToolExecutor:
    """Executes tools with controlled execution, timeout handling, and error management."""

    def __init__(
        self,
        policy_engine: ToolPolicyEngine,
        validator: ToolValidator,
        workspace: Any  # Workspace instance
    ):
        self.policy_engine = policy_engine
        self.validator = validator
        self.workspace = workspace
        self._execution_stats: Dict[str, Dict[str, Any]] = {}

    async def execute(
        self,
        tool: Tool,
        tool_input: Dict[str, Any],
        config: Optional[ExecutionConfig] = None
    ) -> ToolResult:
        """Execute a tool with controlled execution.

        Args:
            tool: Tool instance to execute
            tool_input: Input parameters for the tool
            config: Execution configuration

        Returns:
            ToolResult containing execution outcome
        """
        if config is None:
            config = ExecutionConfig()

        start_time = time.time() if config.enable_timing else None
        tool_name = tool.name

        try:
            # Step 1: Validate input
            validation_result = await self._validate_input(tool, tool_input, config)
            if not validation_result.is_valid:
                return ToolResult(
                    success=False,
                    error=ValidationError(
                        f"Input validation failed for tool '{tool_name}': {', '.join(validation_result.errors)}",
                        tool_name=tool_name
                    )
                )

            # Step 2: Check permissions
            permission_context = PermissionContext(
                workspace_path=str(self.workspace.root_path)
            )
            permission_error = self.policy_engine.check_permission(
                tool_name, tool_input, permission_context
            )
            if permission_error:
                return ToolResult(
                    success=False,
                    error=permission_error
                )

            # Step 3: Execute with timeout
            tool_result = await self._execute_with_timeout(tool, tool_input, config)

            # Step 4: Post-process result
            if config.enable_timing and start_time is not None:
                execution_time = time.time() - start_time
                if tool_result.metadata is None:
                    tool_result.metadata = {}
                tool_result.metadata["execution_time_seconds"] = execution_time

                # Update execution statistics
                self._update_execution_stats(tool_name, execution_time, tool_result.success)

            return tool_result

        except Exception as e:
            # Handle unexpected errors
            if config.cleanup_on_error:
                await self._cleanup_on_error(tool, tool_input)

            return ToolResult(
                success=False,
                error=InternalToolError(
                    f"Internal tool executor error: {str(e)}",
                    tool_name=tool_name
                )
            )

    async def _validate_input(
        self,
        tool: Tool,
        tool_input: Dict[str, Any],
        config: ExecutionConfig
    ) -> Any:  # Returns ValidationResult
        """Validate tool input using the validator."""
        # Convert int validation level to ValidationLevel enum
        validation_level_map = {
            0: 0,   # NONE
            1: 1,   # BASIC
            2: 2,   # SCHEMA
            3: 3,   # CONSTRAINTS
            4: 4,   # SAFETY
            5: 5    # FULL
        }
        validation_level_enum = validation_level_map.get(
            config.validation_level,
            4  # Default to SAFETY
        )

        # Import ValidationLevel here to avoid circular imports
        from autonomous_agent.tool.validation import ValidationLevel
        validation_level = ValidationLevel(validation_level_enum)

        return self.validator.validate_input(tool.schema, tool_input, validation_level)

    async def _execute_with_timeout(
        self,
        tool: Tool,
        tool_input: Dict[str, Any],
        config: ExecutionConfig
    ) -> ToolResult:
        """Execute the tool with timeout handling."""
        try:
            # Execute the tool with timeout
            result = await asyncio.wait_for(
                tool.execute(tool_input),
                timeout=config.timeout_seconds
            )
            return result
        except asyncio.TimeoutError:
            raise TimeoutError(
                f"Tool '{tool.name}' execution exceeded timeout of {config.timeout_seconds} seconds",
                tool_name=tool.name
            )
        except Exception as e:
            # Re-raise tool-specific errors, wrap others
            if isinstance(e, ToolError):
                raise
            else:
                raise ExecutionError(
                    f"Tool '{tool.name}' execution failed: {str(e)}",
                    tool_name=tool.name
                ) from e

    async def _cleanup_on_error(self, tool: Tool, tool_input: Dict[str, Any]) -> None:
        """Perform cleanup operations after a tool error."""
        # This is a placeholder for tool-specific cleanup logic
        # In a more advanced implementation, tools could register cleanup callbacks
        pass

    def _update_execution_stats(self, tool_name: str, execution_time: float, success: bool) -> None:
        """Update execution statistics for a tool."""
        if tool_name not in self._execution_stats:
            self._execution_stats[tool_name] = {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "total_time": 0.0,
                "avg_time": 0.0,
                "min_time": float('inf'),
                "max_time": 0.0
            }

        stats = self._execution_stats[tool_name]
        stats["total_executions"] += 1
        stats["total_time"] += execution_time

        if success:
            stats["successful_executions"] += 1
        else:
            stats["failed_executions"] += 1

        if execution_time < stats["min_time"]:
            stats["min_time"] = execution_time
        if execution_time > stats["max_time"]:
            stats["max_time"] = execution_time

        stats["avg_time"] = stats["total_time"] / stats["total_executions"]

    def get_execution_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get execution statistics for all tools."""
        return self._execution_stats.copy()

    def reset_execution_stats(self) -> None:
        """Reset execution statistics."""
        self._execution_stats.clear()