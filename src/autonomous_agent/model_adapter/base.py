"""Base interface for model adapters."""
from __future__ import annotations

import asyncio
import random
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Coroutine
from dataclasses import dataclass
from typing import Any

from autonomous_agent.model_adapter.types import (
    ModelCapabilities,
    ModelError,
    ModelRequest,
    ModelResponse,
    ToolCall,
    Usage,
)


class ModelAdapter(ABC):
    """Abstract base class for model adapters."""

    def __init__(self, model_name: str, **kwargs: Any):
        """Initialize the model adapter.

        Args:
            model_name: Name of the model to use
            **kwargs: Provider-specific configuration
        """
        self.model_name = model_name
        # For backward compatibility, store exactly what was passed in kwargs
        self.config = kwargs

        # Create a structured config object with defaults for internal use
        # Extract any 'config' sub-dictionary and merge with top-level kwargs
        config_dict = kwargs.get('config', {})
        # Start with default values, then override with config dict, then override with top-level kwargs
        # (but only for fields that exist in ModelAdapterConfig)
        default_values = {
            'timeout': 60.0,
            'max_retries': 3,
            'retry_base_delay': 1.0,
            'retry_max_delay': 60.0,
            'enable_streaming': True,
            'temperature': 0.7,
            'top_p': 0.9,
            'enable_tool_calling': True,
            'provider_config': {}
        }
        # Update with config dict
        default_values.update(config_dict)
        # Update with top-level kwargs, but only for known fields
        for key, value in kwargs.items():
            if key in default_values:
                default_values[key] = value
        self._structured_config = ModelAdapterConfig(**default_values)

    async def generate(
        self, request: ModelRequest
    ) -> ModelResponse:
        """Generate a response from the model with retry logic.

        Args:
            request: The model request

        Returns:
            The model response
        """
        last_exception = None
        for attempt in range(self._structured_config.max_retries + 1):
            try:
                return await self._generate(request)
            except ModelError as e:
                last_exception = e
                # Check if we should retry
                if not e.retryable or attempt == self._structured_config.max_retries:
                    # Don't retry non-retryable errors or if we've exhausted retries
                    raise
                # Calculate delay with exponential backoff and jitter
                delay = min(
                    self._structured_config.retry_base_delay * (2 ** attempt),
                    self._structured_config.retry_max_delay
                )
                # Add jitter to prevent thundering herd
                delay *= (0.5 + random.random() * 0.5)
                await asyncio.sleep(delay)
            # Re-raise any non-ModelError exceptions immediately (including NotImplementedError)
            # These indicate programming errors or unexpected issues that shouldn't be retried
            except Exception:
                raise

        # If we exhausted all retries, raise the last exception
        if last_exception:
            raise last_exception
        # This should never happen, but just in case
        raise RuntimeError("Unexpected state in retry logic")

    async def generate_stream(
        self, request: ModelRequest
    ) -> AsyncIterator[ModelResponse]:
        """Generate a streaming response from the model with retry logic.

        Args:
            request: The model request

        Yields:
            Model response chunks
        """
        last_exception = None
        for attempt in range(self._structured_config.max_retries + 1):
            try:
                # Await the _generate_stream call to get the async iterator
                async_iterator = await self._generate_stream(request)
                async for chunk in async_iterator:
                    yield chunk
                # If we successfully completed the stream, break out of retry loop
                return
            except ModelError as e:
                last_exception = e
                # Check if we should retry
                if not e.retryable or attempt == self._structured_config.max_retries:
                    # Don't retry non-retryable errors or if we've exhausted retries
                    raise
                # Calculate delay with exponential backoff and jitter
                delay = min(
                    self._structured_config.retry_base_delay * (2 ** attempt),
                    self._structured_config.retry_max_delay
                )
                # Add jitter to prevent thundering herd
                delay *= (0.5 + random.random() * 0.5)
                await asyncio.sleep(delay)
            # Re-raise any non-ModelError exceptions immediately (including NotImplementedError)
            # These indicate programming errors or unexpected issues that shouldn't be retried
            except Exception:
                raise

        # If we exhausted all retries, raise the last exception
        if last_exception:
            raise last_exception
        # This should never happen, but just in case
        raise RuntimeError("Unexpected state in retry logic")

    @abstractmethod
    async def _generate(
        self, request: ModelRequest
    ) -> ModelResponse:
        """Generate a response from the model (to be implemented by subclasses).

        Args:
            request: The model request

        Returns:
            The model response
        """

    @abstractmethod
    async def _generate_stream(
        self, request: ModelRequest
    ) -> Coroutine[Any, Any, AsyncIterator[ModelResponse]]:
        """Generate a streaming response from the model (to be implemented by subclasses).

        Args:
            request: The model request

        Yields:
            Model response chunks
        """

    @abstractmethod
    def get_capabilities(self) -> ModelCapabilities:
        """Get the capabilities of the model.

        Returns:
            Model capabilities
        """

    @abstractmethod
    def format_tool_call(self, tool_call: ToolCall) -> dict[str, Any]:
        """Format a tool call for the specific provider.

        Args:
            tool_call: The tool call to format

        Returns:
            Provider-specific tool call representation
        """

    @abstractmethod
    def parse_tool_call(
        self, provider_response: dict[str, Any]
    ) -> ToolCall | None:
        """Parse a tool call from the provider's response.

        Args:
            provider_response: The provider's response

        Returns:
            Parsed tool call or None if no tool call
        """

    def get_usage(self) -> Usage:
        """Get usage statistics for the adapter.

        Returns:
            Usage statistics
        """
        return Usage()


@dataclass
class ModelAdapterConfig:
    """Configuration for model adapters."""

    # Default timeout for requests (seconds)
    timeout: float = 60.0

    # Maximum number of retries
    max_retries: int = 3

    # Base delay for exponential backoff (seconds)
    retry_base_delay: float = 1.0

    # Maximum delay for exponential backoff (seconds)
    retry_max_delay: float = 60.0

    # Whether to enable streaming
    enable_streaming: bool = True

    # Default temperature
    temperature: float = 0.7

    # Default top_p
    top_p: float = 0.9

    # Whether to enable tool calling
    enable_tool_calling: bool = True

    # Provider-specific configuration
    provider_config: dict[str, Any] = None

    def __post_init__(self) -> None:
        if self.provider_config is None:
            self.provider_config = {}