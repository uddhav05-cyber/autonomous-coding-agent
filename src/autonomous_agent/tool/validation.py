"""Validation system for tool inputs and execution constraints."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Callable
import json
import re
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta

from autonomous_agent.tool.errors import ValidationError, WorkspaceViolationError
from autonomous_agent.tool.interface import ToolSchema
from autonomous_agent.workspace import Workspace


class ValidationLevel(Enum):
    """Levels of validation to apply."""
    NONE = 0
    BASIC = 1
    SCHEMA = 2
    CONSTRAINTS = 3
    SAFETY = 4
    FULL = 5


@dataclass
class ValidationResult:
    """Result of a validation operation."""

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_error(self, error: str) -> None:
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: str) -> None:
        self.warnings.append(warning)


class ToolValidator:
    """Validates tool inputs and execution constraints."""

    def __init__(self, workspace: Workspace):
        self.workspace = workspace
        self._custom_validators: Dict[str, Callable[[Dict[str, Any]], ValidationResult]] = {}

    def register_custom_validator(self, tool_name: str, validator: Callable[[Dict[str, Any]], ValidationResult]) -> None:
        """Register a custom validator for a specific tool.

        Args:
            tool_name: Name of the tool to validate
            validator: Function that takes tool input and returns ValidationResult
        """
        self._custom_validators[tool_name] = validator

    def validate_input(
        self,
        tool_schema: ToolSchema,
        tool_input: Dict[str, Any],
        validation_level: ValidationLevel = ValidationLevel.FULL
    ) -> ValidationResult:
        """Validate tool input according to the specified level.

        Args:
            tool_schema: Schema defining expected input structure
            tool_input: Actual input to validate
            validation_level: Level of validation to perform

        Returns:
            ValidationResult indicating success or failure
        """
        result = ValidationResult(is_valid=True)

        if validation_level == ValidationLevel.NONE:
            return result

        # Basic validation - check for required fields
        if validation_level.value >= ValidationLevel.BASIC.value:
            self._validate_basic(tool_schema, tool_input, result)

        # Schema validation - JSON Schema validation
        if validation_level.value >= ValidationLevel.SCHEMA.value:
            self._validate_schema(tool_schema, tool_input, result)

        # Constraint validation - business logic constraints
        if validation_level.value >= ValidationLevel.CONSTRAINTS.value:
            self._validate_constraints(tool_schema, tool_input, result)

        # Safety validation - workspace boundaries, destructive ops, etc.
        if validation_level.value >= ValidationLevel.SAFETY.value:
            self._validate_safety(tool_schema, tool_input, result)

        # Custom validation - tool-specific validation logic
        if validation_level.value >= ValidationLevel.FULL.value:
            self._validate_custom(tool_schema.name, tool_input, result)

        return result

    def _validate_basic(self, tool_schema: ToolSchema, tool_input: Dict[str, Any], result: ValidationResult) -> None:
        """Perform basic validation - check required fields and types."""
        input_props = tool_schema.input_schema.get("properties", {})
        required_fields = tool_schema.input_schema.get("required", [])

        # Check required fields
        for field_name in required_fields:
            if field_name not in tool_input:
                result.add_error(f"Missing required field: {field_name}")

        # Check for unexpected fields if additionalProperties is False
        if not tool_schema.input_schema.get("additionalProperties", True):
            allowed_fields = set(input_props.keys()) | set(required_fields)
            actual_fields = set(tool_input.keys())
            unexpected = actual_fields - allowed_fields
            for field in unexpected:
                result.add_error(f"Unexpected field: {field}")

    def _validate_schema(self, tool_schema: ToolSchema, tool_input: Dict[str, Any], result: ValidationResult) -> None:
        """Perform JSON Schema validation."""
        # Simple type checking for common types
        input_props = tool_schema.input_schema.get("properties", {})

        for field_name, field_value in tool_input.items():
            if field_name in input_props:
                field_schema = input_props[field_name]
                expected_type = field_schema.get("type")

                if expected_type:
                    type_valid = self._check_type(field_value, expected_type)
                    if not type_valid:
                        result.add_error(
                            f"Field '{field_name}' must be of type {expected_type}, got {type(field_value).__name__}"
                        )

    def _validate_constraints(self, tool_schema: ToolSchema, tool_input: Dict[str, Any], result: ValidationResult) -> None:
        """Validate business logic constraints."""
        input_props = tool_schema.input_schema.get("properties", {})

        for field_name, field_value in tool_input.items():
            if field_name in input_props:
                field_schema = input_props[field_name]

                # Check minimum/maximum for numbers
                if "minimum" in field_schema and isinstance(field_value, (int, float)):
                    if field_value < field_schema["minimum"]:
                        result.add_error(
                            f"Field '{field_name}' must be >= {field_schema['minimum']}, got {field_value}"
                        )

                if "maximum" in field_schema and isinstance(field_value, (int, float)):
                    if field_value > field_schema["maximum"]:
                        result.add_error(
                            f"Field '{field_name}' must be <= {field_schema['maximum']}, got {field_value}"
                        )

                # Check minLength/maxLength for strings
                if "minLength" in field_schema and isinstance(field_value, str):
                    if len(field_value) < field_schema["minLength"]:
                        result.add_error(
                            f"Field '{field_name}' must be at least {field_schema['minLength']} characters long"
                        )

                if "maxLength" in field_schema and isinstance(field_value, str):
                    if len(field_value) > field_schema["maxLength"]:
                        result.add_error(
                            f"Field '{field_name}' must be at most {field_schema['maxLength']} characters long"
                        )

                # Check pattern for strings
                if "pattern" in field_schema and isinstance(field_value, str):
                    if not re.match(field_schema["pattern"], field_value):
                        result.add_error(
                            f"Field '{field_name}' must match pattern: {field_schema['pattern']}"
                        )

                # Check enum values
                if "enum" in field_schema:
                    if field_value not in field_schema["enum"]:
                        result.add_error(
                            f"Field '{field_name}' must be one of {field_schema['enum']}, got {field_value}"
                        )

    def _validate_safety(self, tool_schema: ToolSchema, tool_input: Dict[str, Any], result: ValidationResult) -> None:
        """Validate safety constraints including workspace boundaries."""
        # Check workspace boundaries for file paths
        path_fields = ["path", "file_path", "source", "destination", "directory"]

        for field_name in path_fields:
            if field_name in tool_input and isinstance(tool_input[field_name], str):
                path_value = tool_input[field_name]
                try:
                    # Normalize and check if path is within workspace
                    normalized_path = self.workspace.normalize_path(path_value)
                    if not self.workspace.is_within_boundary(normalized_path):
                        result.add_error(
                            f"Access to path '{path_value}' is outside allowed workspace boundaries"
                        )
                except Exception as e:
                    result.add_error(f"Invalid path '{path_value}': {str(e)}")

        # Check for destructive operations that require confirmation
        if tool_schema.is_destructive and not tool_schema.requires_confirmation:
            # This would normally be caught at policy level, but we can warn here
            result.add_warning(
                f"Tool '{tool_schema.name}' is marked as destructive but does not require confirmation"
            )

    def _validate_custom(self, tool_name: str, tool_input: Dict[str, Any], result: ValidationResult) -> None:
        """Apply custom validation logic for specific tools."""
        if tool_name in self._custom_validators:
            custom_result = self._custom_validators[tool_name](tool_input)
            if not custom_result.is_valid:
                result.is_valid = False
                result.errors.extend(custom_result.errors)
            result.warnings.extend(custom_result.warnings)

    def _check_type(self, value: Any, type_name: str) -> bool:
        """Check if a value matches the specified type."""
        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
            "null": type(None)
        }

        expected_type = type_map.get(type_name)
        if expected_type is None:
            return True  # Unknown type, assume valid

        return isinstance(value, expected_type)