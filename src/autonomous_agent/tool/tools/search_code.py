"""Tool for searching code in the workspace."""

from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional
import asyncio
from pathlib import Path

from autonomous_agent.tool.interface import BaseTool, ToolSchema, ToolResult
from autonomous_agent.tool.errors import ToolError, ValidationError, WorkspaceViolationError


class SearchCodeTool(BaseTool):
    """Tool for searching code in the workspace."""

    def __init__(self):
        self._schema = ToolSchema(
            name="search_code",
            description="Search for code patterns in files",
            input_schema={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Regular expression pattern to search for"
                    },
                    "path": {
                        "type": "string",
                        "description": "Directory to search in (defaults to workspace root)",
                        "default": "."
                    },
                    "file_pattern": {
                        "type": "string",
                        "description": "Glob pattern to filter files (e.g., '*.py')",
                        "default": "*"
                    },
                    "ignore_case": {
                        "type": "boolean",
                        "description": "Whether to ignore case in search",
                        "default": False
                    },
                    "context_lines": {
                        "type": "integer",
                        "description": "Number of context lines to include before and after matches",
                        "default": 2,
                        "minimum": 0
                    },
                    "use_regex": {
                        "type": "boolean",
                        "description": "Whether to treat pattern as regex (if False, literal string search)",
                        "default": True
                    }
                },
                "required": ["pattern"],
                "additionalProperties": False
            },
            output_schema={
                "type": "object",
                "properties": {
                    "matches": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "file": {"type": "string"},
                                "line_number": {"type": "integer"},
                                "line": {"type": "string"},
                                "context_before": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "context_after": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "match_text": {"type": "string"}
                            }
                        },
                        "description": "List of matches with context"
                    },
                    "total_matches": {
                        "type": "integer",
                        "description": "Total number of matching lines"
                    },
                    "files_searched": {
                        "type": "integer",
                        "description": "Number of files searched"
                    }
                }
            },
            is_destructive=False,
            timeout_seconds=30
        )

    @property
    def name(self) -> str:
        return "search_code"

    @property
    def description(self) -> str:
        return "Search for code patterns in files"

    @property
    def schema(self) -> ToolSchema:
        return self._schema

    async def execute(self, tool_input: Dict[str, Any]) -> ToolResult:
        """Search for code patterns in files."""
        try:
            # Get parameters
            pattern = tool_input.get("pattern")
            search_path = tool_input.get("path", ".")
            file_pattern = tool_input.get("file_pattern", "*")
            ignore_case = tool_input.get("ignore_case", False)
            context_lines = tool_input.get("context_lines", 2)
            use_regex = tool_input.get("use_regex", True)

            # Validate pattern is provided
            if not pattern:
                return ToolResult(
                    success=False,
                    error=ValidationError(
                        "pattern is required",
                        tool_name=self.name
                    )
                )

            # Compile regex pattern if needed
            if use_regex:
                try:
                    flags = re.IGNORECASE if ignore_case else 0
                    regex_pattern = re.compile(pattern, flags)
                except re.error as e:
                    return ToolResult(
                        success=False,
                        error=ValidationError(
                            f"Invalid regular expression: {str(e)}",
                            tool_name=self.name
                        )
                    )
            else:
                # For literal search, we'll use string.find or similar
                search_pattern = pattern.lower() if ignore_case else pattern

            # Resolve search path
            full_search_path = Path(search_path).resolve()

            # Check if path exists
            if not full_search_path.exists():
                return ToolResult(
                    success=False,
                    error=ValidationError(
                        f"Search path '{search_path}' does not exist",
                        tool_name=self.name
                    )
                )

            # Check if path is a directory
            if not full_search_path.is_dir():
                return ToolResult(
                    success=False,
                    error=ValidationError(
                        f"Search path '{search_path}' is not a directory",
                        tool_name=self.name
                    )
                )

            # Search files
            matches = []
            files_searched = 0

            # Walk through directory
            for root, dirs, files in os.walk(full_search_path):
                # Skip hidden directories unless they match file_pattern
                # This is a simplified approach

                for filename in files:
                    # Apply file pattern filter
                    if not self._matches_pattern(filename, file_pattern):
                        continue

                    file_path = Path(root) / filename
                    files_searched += 1

                    try:
                        # Read file and search for pattern
                        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                            lines = f.readlines()

                        # Search each line
                        for line_num, line in enumerate(lines, 1):  # 1-indexed line numbers
                            line_content = line.rstrip('\n\r')
                            match_found = False
                            match_text = ""

                            if use_regex:
                                match = regex_pattern.search(line_content)
                                if match:
                                    match_found = True
                                    match_text = match.group(0)
                            else:
                                # Literal search
                                search_line = line_content.lower() if ignore_case else line_content
                                if search_pattern in search_line:
                                    match_found = True
                                    # Find the actual match text in original line
                                    idx = search_line.find(search_pattern)
                                    match_text = line_content[idx:idx + len(pattern)]

                            if match_found:
                                # Get context lines
                                context_before = []
                                context_after = []

                                # Get context before
                                start_idx = max(0, line_num - 1 - context_lines)
                                for i in range(start_idx, line_num - 1):
                                    if i < len(lines):
                                        context_before.append(lines[i].rstrip('\n\r'))

                                # Get context after
                                end_idx = min(len(lines), line_num + context_lines)
                                for i in range(line_num, end_idx):
                                    context_after.append(lines[i].rstrip('\n\r'))

                                # Calculate relative path
                                try:
                                    relative_path = file_path.relative_to(full_search_path)
                                except ValueError:
                                    # If we can't make it relative, use the full path
                                    relative_path = file_path

                                matches.append({
                                    "file": str(relative_path),
                                    "line_number": line_num,
                                    "line": line_content,
                                    "context_before": context_before,
                                    "context_after": context_after,
                                    "match_text": match_text
                                })
                    except Exception:
                        # Skip files that can't be read
                        continue

            # Sort matches by file and line number
            matches.sort(key=lambda x: (x["file"], x["line_number"]))

            return ToolResult(
                success=True,
                data={
                    "matches": matches,
                    "total_matches": len(matches),
                    "files_searched": files_searched
                }
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=ToolError(
                    f"Failed to search code: {str(e)}",
                    tool_name=self.name
                )
            )

    def _matches_pattern(self, filename: str, pattern: str) -> bool:
        """Simple pattern matching for file names."""
        import fnmatch
        return fnmatch.fnmatch(filename, pattern)