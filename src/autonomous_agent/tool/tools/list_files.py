"""Tool for listing files in the workspace."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
import asyncio
from pathlib import Path

from autonomous_agent.tool.interface import BaseTool, ToolSchema, ToolResult
from autonomous_agent.tool.errors import ToolError, ValidationError, WorkspaceViolationError


class ListFilesTool(BaseTool):
    """Tool for listing files in the workspace."""

    def __init__(self):
        self._schema = ToolSchema(
            name="list_files",
            description="List files and directories in the workspace",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path to list (defaults to workspace root)",
                        "default": "."
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "Whether to list files recursively",
                        "default": False
                    },
                    "include_hidden": {
                        "type": "boolean",
                        "description": "Whether to include hidden files and directories",
                        "default": False
                    },
                    "file_pattern": {
                        "type": "string",
                        "description": "Glob pattern to filter files (e.g., '*.py')",
                        "default": "*"
                    }
                },
                "additionalProperties": False
            },
            output_schema={
                "type": "object",
                "properties": {
                    "files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of file paths relative to workspace"
                    },
                    "directories": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of directory paths relative to workspace"
                    },
                    "count": {
                        "type": "integer",
                        "description": "Total number of items found"
                    }
                }
            },
            is_destructive=False,
            timeout_seconds=10
        )

    @property
    def name(self) -> str:
        return "list_files"

    @property
    def description(self) -> str:
        return "List files and directories in the workspace"

    @property
    def schema(self) -> ToolSchema:
        return self._schema

    async def execute(self, tool_input: Dict[str, Any]) -> ToolResult:
        """List files and directories in the workspace."""
        try:
            # Get parameters
            relative_path = tool_input.get("path", ".")
            recursive = tool_input.get("recursive", False)
            include_hidden = tool_input.get("include_hidden", False)
            file_pattern = tool_input.get("file_pattern", "*")

            # Validate path is within workspace
            # Note: In a real implementation, this would use the workspace abstraction
            # For now, we'll do basic path validation
            full_path = Path(relative_path).resolve()

            # Check if path exists
            if not full_path.exists():
                return ToolResult(
                    success=False,
                    error=ValidationError(
                        f"Path '{relative_path}' does not exist",
                        tool_name=self.name
                    )
                )

            # Check if path is a directory
            if not full_path.is_dir():
                return ToolResult(
                    success=False,
                    error=ValidationError(
                        f"Path '{relative_path}' is not a directory",
                        tool_name=self.name
                    )
                )

            # List files and directories
            files = []
            directories = []

            if recursive:
                # Walk recursively
                for root, dirs, filenames in os.walk(full_path):
                    # Filter directories
                    for dir_name in dirs:
                        dir_path = Path(root) / dir_name
                        relative_dir = dir_path.relative_to(full_path.parent)

                        # Skip hidden directories if not included
                        if not include_hidden and any(part.startswith('.') for part in relative_dir.parts):
                            continue

                        directories.append(str(relative_dir))

                    # Filter files
                    for filename in filenames:
                        file_path = Path(root) / filename
                        relative_file = file_path.relative_to(full_path.parent)

                        # Skip hidden files if not included
                        if not include_hidden and any(part.startswith('.') for part in relative_file.parts):
                            continue

                        # Apply file pattern filter
                        # Simple implementation - in reality would use proper glob matching
                        if file_pattern == "*" or self._matches_pattern(filename, file_pattern):
                            files.append(str(relative_file))
            else:
                # List only immediate contents
                for item in full_path.iterdir():
                    # Skip hidden items if not included
                    if not include_hidden and item.name.startswith('.'):
                        continue

                    relative_item = item.relative_to(full_path.parent)

                    if item.is_dir():
                        directories.append(str(relative_item))
                    elif item.is_file():
                        # Apply file pattern filter
                        if file_pattern == "*" or self._matches_pattern(item.name, file_pattern):
                            files.append(str(relative_item))

            # Sort results for consistent output
            files.sort()
            directories.sort()

            return ToolResult(
                success=True,
                data={
                    "files": files,
                    "directories": directories,
                    "count": len(files) + len(directories)
                }
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=ToolError(
                    f"Failed to list files: {str(e)}",
                    tool_name=self.name
                )
            )

    def _matches_pattern(self, filename: str, pattern: str) -> bool:
        """Simple pattern matching for file names."""
        # Convert glob pattern to regex
        if pattern == "*":
            return True

        # Very simple implementation - real implementation would use fnmatch or pathlib
        if "*" not in pattern and "?" not in pattern:
            return filename == pattern

        # For simplicity, we'll just do basic wildcard handling
        # In production, use proper glob matching
        import fnmatch
        return fnmatch.fnmatch(filename, pattern)