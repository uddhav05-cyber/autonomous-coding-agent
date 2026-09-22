"""Controlled Tool System for the autonomous coding agent.

This system provides secure access to operating-system capabilities through
validated, permission-checked, timed, and logged interfaces.

The tool system sits between Model Adapter (Phase 5) and Workspace (Phase 2):
LLM → Model Adapter → Tool Registry → Tool Policy → Tool Executor → Workspace
"""

from __future__ import annotations

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

from autonomous_agent.tool.interface import (
    Tool,
    BaseTool,
    ToolResult,
    ToolSchema
)

from autonomous_agent.tool.registry import (
    ToolRegistry,
    get_global_registry
)

from autonomous_agent.tool.validation import (
    ToolValidator,
    ValidationLevel
)

from autonomous_agent.tool.policy import (
    ToolPolicyEngine,
    PermissionContext,
    PermissionLevel,
    OperationType,
    ToolPolicy
)

from autonomous_agent.tool.executor import (
    ToolExecutor,
    ExecutionConfig
)

from autonomous_agent.tool.audit import (
    ToolAuditLogger,
    AuditLevel,
    AuditEntry
)

# Import the initial tools
from autonomous_agent.tool.tools.list_files import ListFilesTool
from autonomous_agent.tool.tools.read_file import ReadFileTool
from autonomous_agent.tool.tools.search_code import SearchCodeTool
from autonomous_agent.tool.tools.write_file import WriteFileTool
from autonomous_agent.tool.tools.apply_patch import ApplyPatchTool

__all__ = [
    # Errors
    "ToolError",
    "ToolNotFoundError",
    "ValidationError",
    "PermissionDeniedError",
    "WorkspaceViolationError",
    "TimeoutError",
    "ExecutionError",
    "ConfirmationRequiredError",
    "ResourceLimitError",
    "InternalToolError",

    # Interface
    "Tool",
    "BaseTool",
    "ToolResult",
    "ToolSchema",

    # Registry
    "ToolRegistry",
    "get_global_registry",

    # Validation
    "ToolValidator",
    "ValidationLevel",

    # Policy
    "ToolPolicyEngine",
    "PermissionContext",
    "PermissionLevel",
    "OperationType",
    "ToolPolicy",

    # Executor
    "ToolExecutor",
    "ExecutionConfig",

    # Audit
    "ToolAuditLogger",
    "AuditLevel",
    "AuditEntry",

    # Initial Tools
    "ListFilesTool",
    "ReadFileTool",
    "SearchCodeTool",
    "WriteFileTool",
    "ApplyPatchTool"
]