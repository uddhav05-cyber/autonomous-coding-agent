"""
Typed configuration for Autonomous Coding Agent using Pydantic.
"""
from __future__ import annotations

import os
from typing import Literal, Optional
from pydantic import BaseModel, Field, validator


class ModelProviderConfig(BaseModel):
    """Model provider configuration placeholder."""
    provider: Literal["anthropic", "openai", "local"] = "anthropic"
    model_name: str = Field(default="claude-3-opus-20240229")
    api_key: Optional[str] = None  # Should be set via environment variable
    base_url: Optional[str] = None
    max_tokens: int = Field(default=4096, gt=0)
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)

    @validator("api_key", always=True)
    def _validate_api_key(cls, v):
        # Don't validate here - allow None for local models
        # Actual validation should happen when the model is used
        return v


class ExecutionLimits(BaseModel):
    """Execution limits for the agent."""
    max_iterations: int = Field(default=10, gt=0)
    max_tool_calls: int = Field(default=50, gt=0)
    max_context_tokens: int = Field(default=8000, gt=0)
    timeout_seconds: int = Field(default=300, gt=0)  # 5 minutes


class TimeoutConfig(BaseModel):
    """Timeout configuration."""
    tool_execution: int = Field(default=30, gt=0)  # seconds
    model_response: int = Field(default=60, gt=0)  # seconds
    verification: int = Field(default=120, gt=0)   # seconds


class Settings(BaseModel):
    """Application settings."""
    # Application environment
    environment: Literal["development", "testing", "production"] = Field(
        default="development"
    )

    # Log level
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO"
    )

    # Workspace path
    workspace_path: str = Field(default="./workspace")

    # Model provider configuration
    model_provider: ModelProviderConfig = Field(default_factory=ModelProviderConfig)

    # Execution limits
    execution_limits: ExecutionLimits = Field(default_factory=ExecutionLimits)

    # Timeout configuration
    timeouts: TimeoutConfig = Field(default_factory=TimeoutConfig)

    @validator("workspace_path")
    def _validate_workspace_path(cls, v):
        # Ensure it's a relative path or absolute path
        # Actual validation of whether it's a valid directory happens at runtime
        return v

    class Config:
        # Allow using environment variables
        env_prefix = "AUTONOMOUS_AGENT_"
        # Don't allow extra attributes
        extra = "forbid"
        # Use underscores for nested fields
        # e.g., AUTONOMOUS_AGENT_MODEL_PROVIDER_API_KEY
        # or AUTONOMOUS_AGENT_EXECUTION_LIMITS_MAX_ITERATIONS