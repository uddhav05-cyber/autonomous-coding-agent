"""Structured error definitions for the Controlled Tool System."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ToolError(Exception):
    """Base exception for all tool-related errors."""

    message: str
    error_type: str = "tool_error"
    retryable: bool = False
    tool_name: Optional[str] = None
    invocation_id: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.error_type:
            self.error_type = "tool_error"

    def __str__(self) -> str:
        return f"{self.error_type}: {self.message}"


@dataclass
class ToolNotFoundError(ToolError):
    """Raised when a requested tool is not found in the registry."""

    def __post_init__(self) -> None:
        self.error_type = "tool_not_found_error"
        self.retryable = False


@dataclass
class ValidationError(ToolError):
    """Raised when tool input validation fails."""

    def __post_init__(self) -> None:
        self.error_type = "validation_error"
        self.retryable = False


@dataclass
class PermissionDeniedError(ToolError):
    """Raised when tool execution is denied by policy."""

    def __post_init__(self) -> None:
        self.error_type = "permission_denied_error"
        self.retryable = False


@dataclass
class WorkspaceViolationError(ToolError):
    """Raised when tool attempts to access outside allowed workspace boundaries."""

    def __post_init__(self) -> None:
        self.error_type = "workspace_violation_error"
        self.retryable = False


@dataclass
class TimeoutError(ToolError):
    """Raised when tool execution exceeds the allowed time limit."""

    def __post_init__(self) -> None:
        self.error_type = "timeout_error"
        self.retryable = True  # Timeout errors are typically retryable


@dataclass
class ExecutionError(ToolError):
    """Raised when tool execution fails for unexpected reasons."""

    def __post_init__(self) -> None:
        self.error_type = "execution_error"
        self.retryable = False


@dataclass
class ConfirmationRequiredError(ToolError):
    """Raised when a destructive operation requires explicit confirmation."""

    def __post_init__(self) -> None:
        self.error_type = "confirmation_required_error"
        self.retryable = False


@dataclass
class ResourceLimitError(ToolError):
    """Raised when tool execution exceeds resource limits (memory, file size, etc.)."""

    def __post_init__(self) -> None:
        self.error_type = "resource_limit_error"
        self.retryable = False


@dataclass
class InternalToolError(ToolError):
    """Raised when an internal tool system error occurs."""

    def __post_init__(self) -> None:
        self.error_type = "internal_tool_error"
        self.retryable = False