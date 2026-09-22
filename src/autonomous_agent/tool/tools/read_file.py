"""Tool for reading files from the workspace."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional
import asyncio
from pathlib import Path

from autonomous_agent.tool.interface import BaseTool, ToolSchema, ToolResult
from autonomous_agent.tool.errors import ToolError, ValidationError, WorkspaceViolationError


class ReadFileTool(BaseTool):
    """Tool for reading files from the workspace."""

    def __init__(self):
        self._schema = ToolSchema(
            name="read_file",
            description="Read the contents of a file",
            input_schema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to read (relative to workspace)"
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Line number to start reading from (0-indexed)",
                        "default": 0,
                        "minimum": 0
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of lines to read",
                        "default": 0,  # 0 means no limit
                        "minimum": 0
                    }
                },
                "required": ["file_path"],
                "additionalProperties": False
            },
            output_schema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "File content"
                    },
                    "size": {
                        "type": "integer",
                        "description": "File size in bytes"
                    },
                    "lines": {
                        "type": "integer",
                        "description": "Number of lines in the file"
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Offset used for reading"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Limit used for reading"
                    }
                }
            },
            is_destructive=False,
            timeout_seconds=15
        )

    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return "Read the contents of a file"

    @property
    def schema(self) -> ToolSchema:
        return self._schema

    async def execute(self, tool_input: Dict[str, Any]) -> ToolResult:
        """Read the contents of a file."""
        try:
            # Get parameters
            file_path = tool_input.get("file_path")
            offset = tool_input.get("offset", 0)
            limit = tool_input.get("limit", 0)

            # Validate file_path is provided
            if not file_path:
                return ToolResult(
                    success=False,
                    error=ValidationError(
                        "file_path is required",
                        tool_name=self.name
                    )
                )

            # Resolve the full path
            full_path = Path(file_path).resolve()

            # Check if file exists
            if not full_path.exists():
                return ToolResult(
                    success=False,
                    error=ValidationError(
                        f"File '{file_path}' does not exist",
                        tool_name=self.name
                    )
                )

            # Check if it's actually a file
            if not full_path.is_file():
                return ToolResult(
                    success=False,
                    error=ValidationError(
                        f"'{file_path}' is not a file",
                        tool_name=self.name
                    )
                )

            # Get file size
            file_size = full_path.stat().st_size

            # Read the file
            lines = []
            with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                if offset > 0:
                    # Skip to offset
                    for _ in range(offset):
                        if f.readline() == '':
                            break  # End of file

                # Read lines
                line_count = 0
                for line in f:
                    if limit > 0 and line_count >= limit:
                        break
                    lines.append(line)
                    line_count += 1

            content = ''.join(lines)
            actual_lines = len(lines)

            return ToolResult(
                success=True,
                data={
                    "content": content,
                    "size": file_size,
                    "lines": actual_lines,
                    "offset": offset,
                    "limit": limit if limit > 0 else None
                }
            )

        except UnicodeDecodeError:
            # Try to read as binary if UTF-8 fails
            try:
                full_path = Path(file_path).resolve()
                with open(full_path, 'rb') as f:
                    if offset > 0:
                        # Skip to offset (approximate for binary)
                        f.seek(offset)

                    data = f.read()
                    if limit > 0:
                        # For binary, limit is approximate
                        # This is a simplification - real implementation would be more precise
                        pass

                    return ToolResult(
                        success=True,
                        data={
                            "content": data.decode('utf-8', errors='replace'),
                            "size": len(data),
                            "lines": data.count(b'\n'),
                            "offset": offset,
                            "limit": limit
                        }
                    )
            except Exception as e:
                return ToolResult(
                    success=False,
                    error=ToolError(
                        f"Failed to read file as binary: {str(e)}",
                        tool_name=self.name
                    )
                )
        except Exception as e:
            return ToolResult(
                success=False,
                error=ToolError(
                    f"Failed to read file: {str(e)}",
                    tool_name=self.name
                )
            )