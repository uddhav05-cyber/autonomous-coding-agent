"""
Workspace-specific error hierarchy for the Autonomous Coding Agent.
"""
from __future__ import annotations

from autonomous_agent.errors.base import AutonomousAgentError, ErrorCode, Retryability


class WorkspaceError(AutonomousAgentError):
    """Base error for all workspace-related issues."""
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.WORKSPACE_INVALID,
        cause: Exception | None = None,
        retryability: Retryability = Retryability.NON_RETRYABLE,
    ):
        super().__init__(
            error_code=error_code,
            message=message,
            retryability=retryability,
            cause=cause,
        )


class WorkspaceSecurityError(WorkspaceError):
    """Raised when a workspace security violation is detected (e.g., path traversal, symlink escape)."""
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.WORKSPACE_PATH_INVALID,
        cause: Exception | None = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            cause=cause,
            retryability=Retryability.NON_RETRYABLE,
        )


class WorkspaceFileNotFoundError(WorkspaceError):
    """Raised when a file is expected to exist but does not."""
    def __init__(
        self,
        message: str,
        cause: Exception | None = None,
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.WORKSPACE_FILE_NOT_FOUND,
            cause=cause,
            retryability=Retryability.NON_RETRYABLE,
        )


class WorkspaceFileAlreadyExistsError(WorkspaceError):
    """Raised when attempting to create a file that already exists."""
    def __init__(
        self,
        message: str,
        cause: Exception | None = None,
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.WORKSPACE_FILE_ALREADY_EXISTS,
            cause=cause,
            retryability=Retryability.NON_RETRYABLE,
        )


class WorkspaceIsADirectoryError(WorkspaceError):
    """Raised when a file operation is expected to operate on a file but a directory is provided."""
    def __init__(
        self,
        message: str,
        cause: Exception | None = None,
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.WORKSPACE_IS_DIRECTORY,
            cause=cause,
            retryability=Retryability.NON_RETRYABLE,
        )


class WorkspaceNotADirectoryError(WorkspaceError):
    """Raised when a directory operation is expected to operate on a directory but a file is provided."""
    def __init__(
        self,
        message: str,
        cause: Exception | None = None,
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.WORKSPACE_NOT_DIRECTORY,
            cause=cause,
            retryability=Retryability.NON_RETRYABLE,
        )


class WorkspaceRootDeletionError(WorkspaceError):
    """Raised when an attempt is made to delete the workspace root directory."""
    def __init__(
        self,
        message: str,
        cause: Exception | None = None,
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.WORKSPACE_ROOT_DELETION,
            cause=cause,
            retryability=Retryability.NON_RETRYABLE,
        )


class WorkspaceIOError(WorkspaceError):
    """Raised when an I/O operation fails (e.g., permission denied, disk full)."""
    def __init__(
        self,
        message: str,
        cause: Exception | None = None,
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.WORKSPACE_IO_ERROR,
            cause=cause,
            retryability=Retryability.RETRYABLE,  # I/O errors might be transient
        )
