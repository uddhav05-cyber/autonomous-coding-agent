"""
Structured application error hierarchy for Autonomous Coding Agent.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional
from dataclasses import dataclass


class ErrorCode(str, Enum):
    """Error codes for the application."""
    # Configuration errors
    CONFIG_INVALID = "CONFIG_INVALID"
    CONFIG_MISSING = "CONFIG_MISSING"

    # Workspace errors
    WORKSPACE_INVALID = "WORKSPACE_INVALID"
    WORKSPACE_ACCESS_DENIED = "WORKSPACE_ACCESS_DENIED"
    WORKSPACE_NOT_FOUND = "WORKSPACE_NOT_FOUND"

    # Model errors
    MODEL_PROVIDER_INVALID = "MODEL_PROVIDER_INVALID"
    MODEL_API_ERROR = "MODEL_API_ERROR"
    MODEL_RATE_LIMITED = "MODEL_RATE_LIMITED"

    # Tool errors
    TOOL_INVALID = "TOOL_INVALID"
    TOOL_PERMISSION_DENIED = "TOOL_PERMISSION_DENIED"
    TOOL_TIMEOUT = "TOOL_TIMEOUT"
    TOOL_EXECUTION_FAILED = "TOOL_EXECUTION_FAILED"

    # Validation errors
    VALIDATION_FAILED = "VALIDATION_FAILED"

    # General errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"


class Retryability(str, Enum):
    """Whether an operation can be retried."""
    RETRYABLE = "retryable"
    NON_RETRYABLE = "non-retryable"


@dataclass
class AutonomousAgentError(Exception):
    """
    Base error class for the Autonomous Coding Agent.

    Attributes:
        error_code: Machine-readable error code
        message: Human-readable error message
        retryability: Whether the operation can be retried
        cause: Optional underlying exception
    """
    error_code: ErrorCode
    message: str
    retryability: Retryability = Retryability.NON_RETRYABLE
    cause: Optional[Exception] = None

    def __post_init__(self):
        if isinstance(self.error_code, str):
            self.error_code = ErrorCode(self.error_code)
        if isinstance(self.retryability, str):
            self.retryability = Retryability(self.retryability)

    def __str__(self) -> str:
        return f"[{self.error_code.value}] {self.message}"

    def __repr__(self) -> str:
        return (
            f"AutonomousAgentError("
            f"error_code={self.error_code!r}, "
            f"message={self.message!r}, "
            f"retryability={self.retryability!r}, "
            f"cause={self.cause!r}"
            f")"
        )


# Specific error types for common scenarios
class ConfigurationError(AutonomousAgentError):
    """Raised when configuration is invalid or missing."""
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.CONFIG_INVALID,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            error_code=error_code,
            message=message,
            retryability=Retryability.NON_RETRYABLE,
            cause=cause
        )


class WorkspaceError(AutonomousAgentError):
    """Raised when there are workspace-related issues."""
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.WORKSPACE_INVALID,
        cause: Optional[Exception] = None
    ):
        # Workspace errors might be retryable if it's a temporary access issue
        super().__init__(
            error_code=error_code,
            message=message,
            retryability=Retryability.RETRYABLE,
            cause=cause
        )


class ModelError(AutonomousAgentError):
    """Raised when there are model provider issues."""
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.MODEL_API_ERROR,
        cause: Optional[Exception] = None
    ):
        # Model errors might be retryable (rate limits, temporary failures)
        super().__init__(
            error_code=error_code,
            message=message,
            retryability=Retryability.RETRYABLE,
            cause=cause
        )


class ToolError(AutonomousAgentError):
    """Raised when there are tool execution issues."""
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.TOOL_EXECUTION_FAILED,
        cause: Optional[Exception] = None
    ):
        # Tool errors might be retryable depending on the cause
        super().__init__(
            error_code=error_code,
            message=message,
            retryability=Retryability.RETRYABLE,
            cause=cause
        )


class ValidationError(AutonomousAgentError):
    """Raised when validation fails."""
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.VALIDATION_FAILED,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            error_code=error_code,
            message=message,
            retryability=Retryability.NON_RETRYABLE,
            cause=cause
        )


class NotImplementedError(AutonomousAgentError):
    """Raised when functionality is not yet implemented."""
    def __init__(
        self,
        feature: str = "",
        message: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        if message is None:
            message = f"Not implemented: {feature}" if feature else "Not implemented"
        super().__init__(
            error_code=ErrorCode.NOT_IMPLEMENTED,
            message=message,
            retryability=Retryability.NON_RETRYABLE,
            cause=cause
        )
