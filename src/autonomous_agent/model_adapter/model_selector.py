"""Model Selection Foundation for Phase 5.

Provides deterministic model selection based on capabilities and requirements.
"""
from __future__ import annotations

from typing import Any

from autonomous_agent.model_adapter import (
    ModelAdapterFactory,
    ModelAdapterRegistry,
    ModelCapabilities,
    ModelError,
)


class ModelSelectionError(ModelError):
    """Error raised when model selection fails."""

    def __post_init__(self) -> None:
        self.error_type = "model_selection_error"
        self.retryable = False


class ModelSelector:
    """Deterministic model selector based on capabilities and requirements."""

    def __init__(self, registry: ModelAdapterRegistry | None = None):
        """Initialize the model selector.

        Args:
            registry: Optional registry of model adapter instances.
                     If not provided, uses the factory to create adapters on demand.
        """
        self.registry = registry or ModelAdapterRegistry()

    def select_model(
        self,
        required_capabilities: dict[str, Any],
        min_context_window: int = 0,
        provider_preferences: list[str] | None = None,
        model_preferences: list[str] | None = None,
    ) -> tuple[str, str, ModelCapabilities]:
        """Select the best model based on requirements and preferences.

        Args:
            required_capabilities: Dictionary of required capabilities.
                                 Supported keys: modality, supports_streaming,
                                 supports_tools, supports_vision, etc.
            min_context_window: Minimum required context window size in tokens.
            provider_preferences: Ordered list of preferred providers.
            model_preferences: Ordered list of preferred model names.

        Returns:
            Tuple of (provider, model_name, ModelCapabilities) for the selected model.

        Raises:
            ModelSelectionError: If no suitable model is found.
        """
        # Get all available providers from the factory
        available_providers = ModelAdapterFactory.get_supported_providers()

        # Apply provider preferences - filter to only preferred providers if specified
        if provider_preferences:
            available_providers = [
                p for p in provider_preferences if p in available_providers
            ]
            # If none of the preferred providers are available, fall back to all
            if not available_providers:
                available_providers = ModelAdapterFactory.get_supported_providers()

        candidates: list[tuple[str, str, ModelCapabilities]] = []

        # Check each provider for available models
        for provider in available_providers:
            # Get the adapter class for this provider
            adapter_class = ModelAdapterFactory._adapters.get(provider.lower())
            if not adapter_class:
                continue

            # For each provider, we need to check what models are available
            # Since we don't have a registry of all possible models, we'll check
            # the adapter's known capabilities (if it exposes them) or create
            # a temporary adapter to get capabilities for known models

            # Try to get known models from the adapter class if available
            known_models = self._get_known_models_for_provider(adapter_class, provider)

            # If we can't get known models, we'll have to skip this provider
            # In a real implementation, this would come from configuration
            if not known_models:
                continue
            # Check each known model
            for model_name in known_models:
                try:
                    # Create a temporary adapter to get capabilities
                    adapter = ModelAdapterFactory.create_adapter(
                        provider, model_name, api_key="dummy-key"
                    )
                    capabilities = adapter.get_capabilities()

                    # Check if model meets requirements
                    if self._meets_requirements(
                        capabilities, required_capabilities, min_context_window
                    ):
                        candidates.append((provider, model_name, capabilities))
                except Exception:  # Skip models that fail to initialize (e.g., missing API keys during testing)
                    # Skip models that fail to initialize
                    continue

            # If we have candidates from this provider, we can break early
            # since we're going through providers in preference order
            if candidates:
                break

        if not candidates:
            raise ModelSelectionError(
                f"No suitable model found for requirements: "
                f"required_capabilities={required_capabilities}, "
                f"min_context_window={min_context_window}, "
                f"provider_preferences={provider_preferences}, "
                f"model_preferences={model_preferences}"
            )

        # Sort candidates by preferences
        def _candidate_score(candidate: tuple[str, str, ModelCapabilities]) -> tuple[int, int]:
            provider, model_name, _ = candidate

            # Provider preference score (lower is better)
            provider_score = 0
            if provider_preferences:
                try:
                    provider_score = provider_preferences.index(provider)
                except ValueError:
                    provider_score = len(provider_preferences)  # Not in preferences

            # Model preference score (lower is better)
            model_score = 0
            if model_preferences:
                try:
                    model_score = model_preferences.index(model_name)
                except ValueError:
                    model_score = len(model_preferences)  # Not in preferences

            return (provider_score, model_score)

        # Sort by provider preference first, then model preference
        candidates.sort(key=_candidate_score)

        # Return the best candidate
        provider, model_name, capabilities = candidates[0]
        return provider, model_name, capabilities

    def _get_known_models_for_provider(
        self, adapter_class: Any, provider: str
    ) -> list[str]:
        """Get known model names for a provider from the adapter class.

        Args:
            adapter_class: The adapter class for the provider
            provider: Provider name

        Returns:
            List of known model names for the provider
        """
        # For AnthropicAdapter, we know the models from the capabilities map
        if provider.lower() == "anthropic" and hasattr(adapter_class, '_CAPABILITIES_MAP'):
            return list(adapter_class._CAPABILITIES_MAP.keys())

        # For other providers, we would need similar implementation
        # For now, return empty list to skip providers we don't know about
        return []

    def _meets_requirements(
        self,
        capabilities: ModelCapabilities,
        required_capabilities: dict[str, Any],
        min_context_window: int,
    ) -> bool:
        """Check if a model's capabilities meet the requirements.

        Args:
            capabilities: The model's capabilities
            required_capabilities: Dictionary of required capabilities
            min_context_window: Minimum required context window

        Returns:
            True if capabilities meet all requirements, False otherwise
        """
        # Check context window
        if capabilities.context_window < min_context_window:
            return False

        # Check each required capability
        for key, required_value in required_capabilities.items():
            if key == "modality":
                # Check if at least one required modality is supported
                if not any(mod in capabilities.modalities for mod in required_value):
                    return False
            elif key == "supports_streaming":
                if capabilities.supports_streaming != required_value:
                    return False
            elif key == "supports_tools":
                if capabilities.supports_tools != required_value:
                    return False
            elif key == "supports_vision":
                if capabilities.supports_vision != required_value:
                    return False
            elif hasattr(capabilities, key):
                # Check other boolean attributes
                actual_value = getattr(capabilities, key)
                if actual_value != required_value:
                    return False
            # For unsupported keys, we ignore them (they might be in extra)

        return True