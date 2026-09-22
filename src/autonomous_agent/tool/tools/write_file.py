"""Tool for writing files to the workspace."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional
import asyncio
from pathlib import Path

from autonomous_agent.tool.interface import BaseTool, ToolSchema, ToolResult
from autonomous_agent.tool.errors import ToolError, ValidationError, WorkspaceViolationError, ConfirmationRequiredError


class WriteFileTool(BaseTool):
    """Tool for writing files to the workspace."""

    def __init__(self):
        self._schema = ToolSchema(
            name="write_file",
            description="Write content to a file",
            input_schema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to write (relative to workspace)"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write to the file"
                    },
                    "mode": {
                        "type": "string",
                        "description": "Write mode: 'overwrite' or 'append'",
                        "enum": ["overwrite", "append"],
                        "default": "overwrite"
                    },
                    "create_dirs": {
                        "type": "boolean",
                        "description": "Whether to create parent directories if they don't exist",
                        "default": True
                    }
                },
                "required": ["file_path", "content"],
                "additionalProperties": False
            },
            output_schema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file that was written"
                    },
                    "size": {
                        "type": "integer",
                        "description": "Size of the file in bytes after writing"
                    },
                    "lines": {
                        "type": "integer",
                        "description": "Number of lines written"
                    },
                    "mode": {
                        "type": "string",
                        "description": "Write mode used"
                    }
                }
            },
            is_destructive=True,  # Writing files can be destructive
            requires_confirmation=True,
            timeout_seconds=10
        )

    @property
    def name(self) -> str:
        return "write_file"

    @property
    def description(self) -> str:
        return "Write content to a file"

    @property
    def schema(self) -> ToolSchema:
        return self._schema

    async def execute(self, tool_input: Dict[str, Any]) -> ToolResult:
        """Write content to a file."""
        try:
            # Get parameters
            file_path = tool_input.get("file_path")
            content = tool_input.get("content", "")
            mode = tool_input.get("mode", "overwrite")
            create_dirs = tool_input.get("create_dirs", True)

            # Validate required parameters
            if not file_path:
                return ToolResult(
                    success=False,
                    error=ValidationError(
                        "file_path is required",
                        tool_name=self.name
                    )
                )

            if content is None:
                return ToolResult(
                    success=False,
                    error=ValidationError(
                        "content is required",
                        tool_name=self.name
                    )
                )

            # Resolve the full path
            full_path = Path(file_path).resolve()

            # Check if file already exists (for confirmation warning)
            file_exists = full_path.exists()

            # Create parent directories if needed
            if create_dirs and not full_path.parent.exists():
                full_path.parent.mkdir(parents=True, exist_ok=True)

            # Determine write mode
            if mode == "overwrite":
                file_mode = 'w'
            elif mode == "append":
                file_mode = 'a'
            else:
                return ToolResult(
                    success=False,
                    error=ValidationError(
                        f"Invalid mode '{mode}'. Must be 'overwrite' or 'append'",
                        tool_name=self.name
                    )
                )

            # Write the file
            with open(full_path, file_mode, encoding='utf-8') as f:
                f.write(content)

            # Get file stats
            file_size = full_path.stat().st_size
            lines_written = len(content.splitlines())

            return ToolResult(
                success=True,
                data={
                    "file_path": str(full_path),
                    "size": file_size,
                    "lines": lines_written,
                    "mode": mode
                }
            )

        except PermissionError:
            return ToolResult(
                success=False,
                error=ValidationError(
                    f"Permission denied writing to '{file_path}'",
                    tool_name=self.name
                )
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=ToolError(
                    f"Failed to write file: {str(e)}",
                    tool_name=self.name
                )
            )