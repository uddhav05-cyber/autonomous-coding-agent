"""Permission and policy system for controlling tool access and execution."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from enum import Enum
import threading

from autonomous_agent.tool.errors import (
    PermissionDeniedError,
    WorkspaceViolationError,
    ConfirmationRequiredError,
    ToolError
)
from autonomous_agent.tool.interface import ToolSchema
from autonomous_agent.tool.validation import ToolValidator, ValidationLevel
from autonomous_agent.workspace import Workspace


class PermissionLevel(Enum):
    """Levels of permission for tool access."""
    NONE = 0          # No access
    READ = 1          # Read-only access
    WRITE = 2         # Read and write access
    EXECUTE = 3       # Full execution access
    ADMIN = 4         # Administrative access


class OperationType(Enum):
    """Types of operations that tools can perform."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    NETWORK = "network"
    SYSTEM = "system"


@dataclass
class ToolPolicy:
    """Policy definition for a specific tool."""
    
    tool_name: str
    permission_level: PermissionLevel = PermissionLevel.NONE
    allowed_operations: Set[OperationType] = field(default_factory=set)
    blocked_operations: Set[OperationType] = field(default_factory=set)
    max_execution_time: int = 30  # seconds
    max_memory_mb: int = 100      # megabytes
    require_confirmation: bool = False
    allowed_paths: List[str] = field(default_factory=list)  # Workspace-relative paths
    blocked_paths: List[str] = field(default_factory=list)  # Workspace-relative paths
    rate_limit_per_minute: int = 60
    validation_level: ValidationLevel = ValidationLevel.FULL
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PermissionContext:
    """Context information for permission checking."""
    
    user_id: str = "default"
    session_id: str = "default"
    workspace_path: str = ""
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    metadata: Dict[str, Any] = field(default_factory=dict)


class ToolPolicyEngine:
    """Engine for evaluating tool policies and permissions."""
    
    def __init__(self, workspace: Workspace):
        self.workspace = workspace
        self._policies: Dict[str, ToolPolicy] = {}
        self._usage_counts: Dict[str, List[float]] = {}  # tool_name -> [timestamps]
        self._lock = threading.RLock()
        
        # Set up default policies
        self._setup_default_policies()
    
    def _setup_default_policies(self) -> None:
        """Set up default policies for common tools."""
        # Default restrictive policy
        default_policy = ToolPolicy(
            tool_name="*",  # Wildcard for unspecified tools
            permission_level=PermissionLevel.NONE
        )
        self._policies["*"] = default_policy
    
    def set_policy(self, policy: ToolPolicy) -> None:
        """Set or update a tool policy.
        
        Args:
            policy: ToolPolicy to set
        """
        with self._lock:
            self._policies[policy.tool_name] = policy
    
    def get_policy(self, tool_name: str) -> ToolPolicy:
        """Get the policy for a specific tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            ToolPolicy for the tool (returns default policy if not found)
        """
        with self._lock:
            # Check for exact match first
            if tool_name in self._policies:
                return self._policies[tool_name]
            
            # Check for wildcard/default policy
            if "*" in self._policies:
                return self._policies["*"]
            
            # Return a default restrictive policy
            return ToolPolicy(
                tool_name=tool_name,
                permission_level=PermissionLevel.NONE,
                validation_level=ValidationLevel.FULL
            )
    
    def check_permission(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        context: PermissionContext
    ) -> Optional[ToolError]:
        """Check if the user has permission to execute the tool with given input.
        
        Args:
            tool_name: Name of the tool to check
            tool_input: Input parameters for the tool
            context: Permission context
            
        Returns:
            None if permission is granted, ToolError if denied
        """
        with self._lock:
            policy = self.get_policy(tool_name)
            
            # Check permission level
            if policy.permission_level == PermissionLevel.NONE:
                return PermissionDeniedError(
                    f"Permission denied for tool '{tool_name}'",
                    tool_name=tool_name
                )
            
            # For now, just return None (permission granted) for other checks
            # TODO: Implement full permission checking logic
            return None
