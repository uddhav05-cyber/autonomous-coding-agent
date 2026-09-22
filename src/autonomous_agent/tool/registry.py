"""Central tool registry for managing tool registration and lookup."""

from __future__ import annotations

from typing import Dict, Optional, Type
import threading

from autonomous_agent.tool.interface import Tool, ToolSchema
from autonomous_agent.tool.errors import ToolNotFoundError, InternalToolError


class ToolRegistry:
    """Registry for managing tool instances and metadata."""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._schemas: Dict[str, ToolSchema] = {}
        self._lock = threading.RLock()

    def register(self, tool: Tool) -> None:
        """Register a tool instance.

        Args:
            tool: Tool instance to register

        Raises:
            ValueError: If a tool with the same name is already registered
        """
        with self._lock:
            if tool.name in self._tools:
                raise ValueError(f"Tool '{tool.name}' is already registered")

            self._tools[tool.name] = tool
            self._schemas[tool.name] = tool.schema

    def unregister(self, tool_name: str) -> bool:
        """Unregister a tool by name.

        Args:
            tool_name: Name of the tool to unregister

        Returns:
            True if tool was found and removed, False otherwise
        """
        with self._lock:
            if tool_name in self._tools:
                del self._tools[tool_name]
                del self._schemas[tool_name]
                return True
            return False

    def get(self, tool_name: str) -> Tool:
        """Get a tool by name.

        Args:
            tool_name: Name of the tool to retrieve

        Returns:
            Tool instance

        Raises:
            ToolNotFoundError: If tool is not found
        """
        with self._lock:
            tool = self._tools.get(tool_name)
            if tool is None:
                raise ToolNotFoundError(
                    f"Tool '{tool_name}' not found in registry",
                    tool_name=tool_name
                )
            return tool

    def get_schema(self, tool_name: str) -> ToolSchema:
        """Get the schema for a tool by name.

        Args:
            tool_name: Name of the tool

        Returns:
            ToolSchema for the tool

        Raises:
            ToolNotFoundError: If tool is not found
        """
        with self._lock:
            schema = self._schemas.get(tool_name)
            if schema is None:
                raise ToolNotFoundError(
                    f"Tool '{tool_name}' not found in registry",
                    tool_name=tool_name
                )
            return schema

    def list_tools(self) -> list[str]:
        """List all registered tool names.

        Returns:
            List of registered tool names
        """
        with self._lock:
            return list(self._tools.keys())

    def tool_exists(self, tool_name: str) -> bool:
        """Check if a tool is registered.

        Args:
            tool_name: Name of the tool to check

        Returns:
            True if tool exists, False otherwise
        """
        with self._lock:
            return tool_name in self._tools

    def clear(self) -> None:
        """Clear all registered tools."""
        with self._lock:
            self._tools.clear()
            self._schemas.clear()


# Global registry instance
_global_registry: Optional[ToolRegistry] = None
_registry_lock = threading.Lock()


def get_global_registry() -> ToolRegistry:
    """Get the global tool registry instance.

    Returns:
        Global ToolRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        with _registry_lock:
            if _global_registry is None:
                _global_registry = ToolRegistry()
    return _global_registry