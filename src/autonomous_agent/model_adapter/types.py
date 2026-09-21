"""Data types for the Model Adapter."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Union

import time


@dataclass
class ModelCapabilities:
    """Capabilities of a model."""

    # Model identifier
    model: str

    # Provider name
    provider: str

    # Context window size in tokens
    context_window: int

    # Maximum output tokens
    max_output_tokens: int

    # Supported modalities
    modalities: list[str] = field(default_factory=lambda: ["text"])

    # Whether the model supports streaming
    supports_streaming: bool = True

    # Whether the model supports tool/function calling
    supports_tools: bool = True

    # Whether the model supports vision/image input is supported
    supports_vision: bool = False

    # Performance characteristics (optional)
    latency_ms: int | None = None

    # Cost information (optional)
    cost_per_1k_input_tokens: float | None = None
    cost_per_1k_output_tokens: float | None = None

    # Rate limits (optional)
    requests_per_minute: int | None = None
    tokens_per_minute: int | None = None

    # Additional provider-specific capabilities
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class Usage:
    """Token usage statistics."""

    # Input tokens
    input_tokens: int = 0

    # Output tokens
    output_tokens: int = 0

    # Total tokens
    total_tokens: int = 0

    # Cost in USD
    cost_usd: float = 0.0

    def __post_init__(self):
        # Calculate total tokens
        self.total_tokens = self.input_tokens + self.output_tokens

    def __add__(self, other: Usage) -> Usage:
        """Add two usage objects together."""
        return Usage(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            cost_usd=self.cost_usd + other.cost_usd,
        )


@dataclass
class ModelRequest:
    """Request to send to a model."""

    # The prompt or messages to send
    prompt: str | None = None
    messages: list[dict[str, Any]] | None = None

    # Model parameters
    temperature: float | None = None
    top_p: float | None = None
    max_tokens: int | None = None
    stop: list[str] | None = None

    # Tool configuration
    tools: list[dict[str, Any]] | None = None
    tool_choice: Union[str, dict[str, Any]] | None = None

    # Whether to stream the response
    stream: bool = False

    # Additional provider-specific parameters
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelResponse:
    """Response from a model."""

    # The generated text
    text: str = ""

    # Tool calls if any
    tool_calls: list[ToolCall] = field(default_factory=list)

    # Whether the response is finished
    finished: bool = True

    # Usage statistics
    usage: Usage = field(default_factory=Usage)

    # Additional provider-specific fields
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolCall:
    """Represents a tool call from the model."""

    # Name of the tool to call
    name: str

    # Arguments to pass to the tool
    arguments: dict[str, Any]

    # Unique identifier for the tool call
    id: str = field(default_factory=lambda: f"call_{int(time.time() * 1000)}")

    def __post_init__(self) -> None:
        if not self.id:
            # Generate a simple ID if not provided
            self.id = f"call_{int(time.time() * 1000)}"


@dataclass
class ModelError(Exception):
    """Base exception for model adapter errors."""

    message: str
    error_type: str = "model_error"
    retryable: bool = False
    provider_error_code: str | None = None

    def __str__(self) -> str:
        return f"{self.error_type}: {self.message}"


@dataclass
class AuthenticationError(ModelError):
    """Authentication error."""

    def __post_init__(self) -> None:
        self.error_type = "authentication_error"
        self.retryable = False


@dataclass
class RateLimitError(ModelError):
    """Rate limit error."""

    def __post_init__(self) -> None:
        self.error_type = "rate_limit_error"
        self.retryable = True


@dataclass
class ModelNotFoundError(ModelError):
    """Model not found error."""

    def __post_init__(self) -> None:
        self.error_type = "model_not_found_error"
        self.retryable = False


@dataclass
class InvalidRequestError(ModelError):
    """Invalid request error."""

    def __post_init__(self) -> None:
        self.error_type = "invalid_request_error"
        self.retryable = False


@dataclass
class InternalModelError(ModelError):
    """Internal model error."""

    def __post_init__(self) -> None:
        self.error_type = "internal_model_error"
        self.retryable = True
