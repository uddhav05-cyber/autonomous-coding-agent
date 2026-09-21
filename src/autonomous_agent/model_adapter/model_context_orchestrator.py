"""Phase 5 Context Engineering Integration.

Orchestrates the flow from task requirements to ModelRequest via:
Task → Model Selection → Context Manager → ModelRequest → Model Adapter
"""
from __future__ import annotations

from typing import Any

from autonomous_agent.context_engineering import ContextManager
from autonomous_agent.context_engineering.context_package import ContextPackage
from autonomous_agent.model_adapter import (
    ModelRequest,
    ModelSelector,
)


class ModelContextOrchestrator:
    """Orchestrates model selection and context engineering for Phase 5."""

    def __init__(
        self,
        context_manager: ContextManager,
        model_selector: ModelSelector | None = None,
    ):
        """Initialize the orchestrator.

        Args:
            context_manager: The ContextManager instance to use for context engineering
            model_selector: Optional ModelSelector instance. If not provided, creates a new one.
        """
        self.context_manager = context_manager
        self.model_selector = model_selector or ModelSelector()

    def create_model_request(
        self,
        task_description: str,
        required_capabilities: dict[str, Any],
        min_context_window: int = 0,
        provider_preferences: list[str] | None = None,
        model_preferences: list[str] | None = None,
        selection_criteria: Any | None = None,
        budget_allocation: Any | None = None,
        duplicate_policy: Any | None = None,
    ) -> ModelRequest:
        """Create a ModelRequest by orchestrating model selection and context engineering.

        Flow:
        1. Select best model based on requirements and preferences
        2. Get selected model's capabilities (especially context window)
        3. Use context window as max_tokens for ContextManager
        4. Create ContextPackage using ContextManager
        5. Convert ContextPackage to ModelRequest

        Args:
            task_description: Description of the current task
            required_capabilities: Dictionary of required capabilities
            min_context_window: Minimum required context window size in tokens
            provider_preferences: Ordered list of preferred providers
            model_preferences: Ordered list of preferred model names
            selection_criteria: Optional context selection criteria
            budget_allocation: Optional context budget allocation
            duplicate_policy: Optional duplicate prevention policy

        Returns:
            ModelRequest ready to be sent to a model adapter

        Raises:
            ModelSelectionError: If no suitable model is found
        """
        # Step 1: Select the best model
        provider, model_name, capabilities = self.model_selector.select_model(
            required_capabilities=required_capabilities,
            min_context_window=min_context_window,
            provider_preferences=provider_preferences,
            model_preferences=model_preferences,
        )

        # Step 2: Use the selected model's context window for context budgeting
        max_tokens = capabilities.context_window

        # Step 3: Create context package using the Context Manager
        context_package: ContextPackage = self.context_manager.create_context_package(
            task_description=task_description,
            selection_criteria=selection_criteria,
            budget_allocation=budget_allocation,
            duplicate_policy=duplicate_policy,
            max_tokens=max_tokens,
        )

        # Step 4: Convert context package to ModelRequest
        model_request = self._context_package_to_model_request(context_package)

        # Step 5: Add model information to the request for the adapter
        model_request.extra["selected_provider"] = provider
        model_request.extra["selected_model"] = model_name
        model_request.extra["model_capabilities"] = capabilities

        return model_request

    def _context_package_to_model_request(
        self, context_package: ContextPackage
    ) -> ModelRequest:
        """Convert a ContextPackage to a ModelRequest.

        Args:
            context_package: The context package to convert

        Returns:
            ModelRequest containing the context as a prompt
        """
        # For now, we'll create a simple prompt from the context
        # In a more sophisticated implementation, we might structure this better
        prompt_parts = []

        # Add task context if available
        if context_package.task_context:
            prompt_parts.append("Task Context:")
            for key, value in context_package.task_context.items():
                prompt_parts.append(f"- {key}: {value}")

        # Add working context if available
        if context_package.working_context:
            prompt_parts.append("\nWorking Context:")
            for key, value in context_package.working_context.items():
                prompt_parts.append(f"- {key}: {value}")

        # Add repository context if available
        if context_package.repository_context:
            prompt_parts.append("\nRepository Context:")
            for key, value in context_package.repository_context.items():
                prompt_parts.append(f"- {key}: {value}")

        # Add history context if available
        if context_package.history_context:
            prompt_parts.append("\nHistory Context:")
            for key, value in context_package.history_context.items():
                prompt_parts.append(f"- {key}: {value}")

        # Join all parts
        prompt = "\n".join(prompt_parts) if prompt_parts else ""

        # Create and return the ModelRequest
        return ModelRequest(
            prompt=prompt,
            # We don't set specific model parameters here - they can be overridden
            # by the caller if needed
        )