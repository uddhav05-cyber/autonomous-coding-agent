"""Model Adapter Factory and Registry."""
from __future__ import annotations

from typing import Any, ClassVar

from autonomous_agent.model_adapter.base import ModelAdapter
from autonomous_agent.model_adapter.providers import AnthropicAdapter


class ModelAdapterFactory:
    """Factory for creating model adapters."""

    # Registry of provider -> adapter class
    _adapters: ClassVar[dict[str, type[ModelAdapter]]] = {
        "anthropic": AnthropicAdapter,
        # Additional providers will be added here as they're implemented
        # "openai": OpenAIAdapter,
        # "google": GoogleAdapter,
        # "meta": MetaAdapter,
    }

    @classmethod
    def register_adapter(cls, provider: str, adapter_class: type[ModelAdapter]) -> None:
        """Register a new model adapter.

        Args:
            provider: Provider name (e.g., "anthropic", "openai")
            adapter_class: Adapter class to register
        """
        cls._adapters[provider.lower()] = adapter_class

    @classmethod
    def create_adapter(
        cls, provider: str, model_name: str, **kwargs: Any
    ) -> ModelAdapter:
        """Create a model adapter for the specified provider.

        Args:
            provider: Provider name (e.g., "anthropic", "openai")
            model_name: Name of the model to use
            **kwargs: Provider-specific configuration

        Returns:
            Model adapter instance

        Raises:
            ValueError: If the provider is not supported
        """
        provider_lower = provider.lower()
        if provider_lower not in cls._adapters:
            raise ValueError(
                f"Unsupported provider: {provider}. "
                f"Supported providers: {list(cls._adapters.keys())}"
            )

        adapter_class = cls._adapters[provider_lower]
        return adapter_class(model_name, **kwargs)

    @classmethod
    def get_supported_providers(cls) -> list[str]:
        """Get list of supported providers.

        Returns:
            List of supported provider names
        """
        return list(cls._adapters.keys())

    @classmethod
    def is_provider_supported(cls, provider: str) -> bool:
        """Check if a provider is supported.

        Args:
            provider: Provider name to check

        Returns:
            True if provider is supported, False otherwise
        """
        return provider.lower() in cls._adapters


class ModelAdapterRegistry:
    """Registry for managing model adapter instances."""

    def __init__(self):
        """Initialize the registry."""
        self._adapters: dict[str, ModelAdapter] = {}
        self._default_adapter: ModelAdapter | None = None

    def register(
        self, name: str, adapter: ModelAdapter, set_as_default: bool = False
    ) -> None:
        """Register a model adapter instance.

        Args:
            name: Name to register the adapter under
            adapter: Adapter instance to register
            set_as_default: Whether to set this as the default adapter
        """
        self._adapters[name] = adapter
        if set_as_default or self._default_adapter is None:
            self._default_adapter = adapter

    def get(self, name: str) -> ModelAdapter | None:
        """Get a registered model adapter.

        Args:
            name: Name of the adapter to retrieve

        Returns:
            Adapter instance or None if not found
        """
        return self._adapters.get(name)

    def get_default(self) -> ModelAdapter | None:
        """Get the default model adapter.

        Returns:
            Default adapter instance or None if not set
        """
        return self._default_adapter

    def set_default(self, name: str) -> None:
        """Set the default model adapter.

        Args:
            name: Name of the adapter to set as default

        Raises:
            KeyError: If the adapter is not registered
        """
        if name not in self._adapters:
            raise KeyError(f"Adapter '{name}' is not registered")
        self._default_adapter = self._adapters[name]

    def unregister(self, name: str) -> None:
        """Unregister a model adapter.

        Args:
            name: Name of the adapter to unregister
        """
        if name in self._adapters:
            del self._adapters[name]
            if self._default_adapter == self._adapters.get(name):
                self._default_adapter = None

    def list_adapters(self) -> list[str]:
        """List all registered adapter names.

        Returns:
            List of registered adapter names
        """
        return list(self._adapters.keys())

    def clear(self) -> None:
        """Clear all registered adapters."""
        self._adapters.clear()
        self._default_adapter = None