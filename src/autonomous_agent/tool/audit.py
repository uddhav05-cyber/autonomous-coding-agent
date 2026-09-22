"""Audit logging system for tool invocations."""

from __future__ import annotations

from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import threading
from enum import Enum


class AuditLevel(Enum):
    """Levels of audit logging."""
    NONE = 0
    BASIC = 1
    FULL = 2


@dataclass
class AuditEntry:
    """Single audit log entry."""

    timestamp: str
    tool_name: str
    invocation_id: str
    user_id: str
    session_id: str
    status: str  # success, failure, error
    safety_classification: str  # safe, warning, dangerous
    duration_ms: float
    input_summary: Dict[str, Any] = field(default_factory=dict)
    output_summary: Dict[str, Any] = field(default_factory=dict)
    error_info: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=field(default_factory=dict))


class ToolAuditLogger:
    """Logs tool invocations for audit and security tracking."""

    def __init__(self, audit_level: AuditLevel = AuditLevel.BASIC):
        self.audit_level = audit_level
        self._log_buffer: List[AuditEntry] = []
        self._lock = threading.RLock()
        self._invocation_counter = 0

    def log_invocation(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        tool_result: Any,  # ToolResult
        invocation_id: str,
        user_id: str = "default",
        session_id: str = "default",
        safety_classification: str = "safe",
        duration_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a tool invocation.

        Args:
            tool_name: Name of the tool that was invoked
            tool_input: Input parameters provided to the tool
            tool_result: Result of the tool execution
            invocation_id: Unique identifier for this invocation
            user_id: User who initiated the invocation
            session_id: Session identifier
            safety_classification: Safety classification of the operation
            duration_ms: Execution duration in milliseconds
            metadata: Additional metadata to log
        """
        if self.audit_level == AuditLevel.NONE:
            return

        with self._lock:
            # Create audit entry
            entry = AuditEntry(
                timestamp=datetime.now().isoformat(),
                tool_name=tool_name,
                invocation_id=invocation_id,
                user_id=user_id,
                session_id=session_id,
                status="success" if getattr(tool_result, 'success', False) else "failure",
                safety_classification=safety_classification,
                duration_ms=duration_ms,
                metadata=metadata or {}
            )

            # Add input summary based on audit level
            if self.audit_level.value >= AuditLevel.BASIC.value:
                entry.input_summary = self._summarize_input(tool_input)

            # Add output summary based on audit level
            if self.audit_level.value >= AuditLevel.FULL.value:
                entry.output_summary = self._summarize_output(tool_result)

            # Add error information if present
            if hasattr(tool_result, 'error') and tool_result.error is not None:
                entry.error_info = {
                    "error_type": getattr(tool_result.error, 'error_type', 'unknown'),
                    "message": str(tool_result.error)
                }

            # Add to buffer
            self._log_buffer.append(entry)

            # Keep buffer size reasonable
            if len(self._log_buffer) > 1000:
                self._log_buffer = self._log_buffer[-500:]  # Keep last 500 entries

    def _summarize_input(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of tool input for audit logging."""
        summary = {}

        # Don't log sensitive information
        sensitive_keys = {
            'password', 'secret', 'key', 'token', 'auth', 'credential',
            'content', 'patch_content'  # These might be large
        }

        for key, value in tool_input.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                # For sensitive fields, just log type and length/size
                if isinstance(value, str):
                    summary[key] = f"<string:{len(value)} chars>"
                elif isinstance(value, (list, tuple)):
                    summary[key] = f"<{type(value).__name__}:{len(value)} items>"
                elif isinstance(value, dict):
                    summary[key] = f"<dict:{len(value)} keys>"
                else:
                    summary[key] = f"<{type(value).__name__}>"
            else:
                # For non-sensitive fields, log the value directly (if small)
                if isinstance(value, str) and len(value) > 100:
                    summary[key] = value[:100] + "..."
                else:
                    summary[key] = value

        return summary

    def _summarize_output(self, tool_result: Any) -> Dict[str, Any]:
        """Create a summary of tool output for audit logging."""
        summary = {}

        if hasattr(tool_result, 'success'):
            summary['success'] = tool_result.success

        if hasattr(tool_result, 'data') and tool_result.data is not None:
            # Summarize the data
            data = tool_result.data
            if isinstance(data, dict):
                summary['data_keys'] = list(data.keys())
                summary['data_type'] = 'dict'
            elif isinstance(data, (list, tuple)):
                summary['data_count'] = len(data)
                summary['data_type'] = type(data).__name__
            elif isinstance(data, str):
                summary['data_length'] = len(data)
                summary['data_preview'] = data[:100] + ("..." if len(data) > 100 else "")
            else:
                summary['data_value'] = str(data)[:200]  # Truncate long values
                summary['data_type'] = type(data).__name__

        if hasattr(tool_result, 'error') and tool_result.error is not None:
            summary['error_present'] = True
            summary['error_type'] = getattr(tool_result.error, 'error_type', 'unknown')
        else:
            summary['error_present'] = False

        return summary

    def get_recent_logs(self, limit: int = 100) -> List[AuditEntry]:
        """Get recent audit log entries.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of recent audit entries
        """
        with self._lock:
            return self._log_buffer[-limit:] if self._log_buffer else []

    def clear_logs(self) -> None:
        """Clear the audit log buffer."""
        with self._lock:
            self._log_buffer.clear()

    def get_log_count(self) -> int:
        """Get the number of logged entries.

        Returns:
            Number of audit log entries
        """
        with self._lock:
            return len(self._log_buffer)