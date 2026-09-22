"""Standard interface for all tools in the Controlled Tool System."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Protocol, runtime_checkable, Optional

from autonomous_agent.tool.errors import ToolError


@dataclass
class ToolResult:
    """Standard result returned by all tools."""

    success: bool
    data: Any = None
    error: Optional[ToolError] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self) -> None:
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ToolSchema:
    """Schema definition for tool input and output validation."""

    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    requires_confirmation: bool = False
    is_destructive: bool = False
    timeout_seconds: int = 30


@runtime_checkable
class Tool(Protocol):
    """Protocol that all tools must implement."""

    @property
    def name(self) -> str:
        """Unique identifier for the tool."""
        ...

    @property
    def description(self) -> str:
        """Human-readable description of what the tool does."""
        ...

    @property
    def schema(self) -> ToolSchema:
        """Schema defining input/output structure and tool properties."""
        ...

    async def execute(self, tool_input: Dict[str, Any]) -> ToolResult:
        """Execute the tool with the given input.

        Args:
            tool_input: Dictionary containing tool parameters

        Returns:
            ToolResult containing success status, data, or error information
        """
        ...


class BaseTool(ABC):
    """Abstract base class for all tools."""

    def __init__(self):
        self._schema: ToolSchema

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for the tool."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what the tool does."""
        pass

    @property
    @abstractmethod
    def schema(self) -> ToolSchema:
        """Schema defining input/output structure and tool properties."""
        pass

    @abstractmethod
    async def execute(self, tool_input: Dict[str, Any]) -> ToolResult:
        """Execute the tool with the given input.

        Args:
            tool_input: Dictionary containing tool parameters

        Returns:
            ToolResult containing success status, data, or error information
        """
        pass