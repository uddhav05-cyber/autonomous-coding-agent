"""Model Adapter for Autonomous Coding Agent."""
from autonomous_agent.model_adapter.base import ModelAdapter, ModelAdapterConfig
from autonomous_agent.model_adapter.factory import (
    ModelAdapterFactory,
    ModelAdapterRegistry,
)
from autonomous_agent.model_adapter.providers import AnthropicAdapter
from autonomous_agent.model_adapter.types import (
    AuthenticationError,
    InternalModelError,
    InvalidRequestError,
    ModelCapabilities,
    ModelError,
    ModelNotFoundError,
    ModelRequest,
    ModelResponse,
    RateLimitError,
    ToolCall,
    Usage,
)

__all__ = [
    "AnthropicAdapter",
    "AuthenticationError",
    "InternalModelError",
    "InvalidRequestError",
    "ModelAdapter",
    "ModelAdapterConfig",
    "ModelAdapterFactory",
    "ModelAdapterRegistry",
    "ModelCapabilities",
    "ModelError",
    "ModelNotFoundError",
    "ModelRequest",
    "ModelResponse",
    "RateLimitError",
    "ToolCall",
    "Usage",
]
