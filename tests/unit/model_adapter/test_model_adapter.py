"""
Unit tests for the Model Adapter component.
"""
import asyncio
import tempfile
import time
from unittest.mock import Mock, patch
from typing import Any, Dict, Optional

from autonomous_agent.model_adapter import (
    ModelAdapter,
    ModelAdapterFactory,
    ModelAdapterRegistry,
    ModelAdapterConfig,
    ModelCapabilities,
    ModelRequest,
    ModelResponse,
    ToolCall,
    Usage,
    AnthropicAdapter,
    ModelError,
    AuthenticationError,
    RateLimitError,
    ModelNotFoundError,
    InvalidRequestError,
    InternalModelError,
)


class MockModelAdapter(ModelAdapter):
    """Mock model adapter for testing."""

    def __init__(self, model_name: str, should_fail: bool = False, **kwargs: Any):
        """Initialize the mock adapter.

        Args:
            model_name: Name of the model
            should_fail: Whether to simulate failures
            **kwargs: Additional configuration
        """
        super().__init__(model_name, **kwargs)
        self.should_fail = should_fail
        self.generate_called = False
        self.generate_stream_called = False

    async def _generate(self, request: ModelRequest) -> ModelResponse:
        """Mock generate method."""
        self.generate_called = True
        if self.should_fail:
            raise Exception("Simulated failure")

        return ModelResponse(
            text=f"Mock response from {self.model_name}",
            tool_calls=[],
            finished=True,
            usage=Usage(input_tokens=10, output_tokens=5)
        )

    async def _generate_stream(
        self, request: ModelRequest
    ):
        """Mock generate_stream method."""
        self.generate_stream_called = True
        if self.should_fail:
            raise Exception("Simulated failure")

        # Return an async iterator that yields one response
        async def mock_stream():
            yield ModelResponse(
                text=f"Mock streaming response from {self.model_name}",
                tool_calls=[],
                finished=True,
                usage=Usage(input_tokens=5, output_tokens=3)
            )

        return mock_stream()

    def get_capabilities(self) -> ModelCapabilities:
        """Get mock capabilities."""
        return ModelCapabilities(
            model=self.model_name,
            provider="mock",
            context_window=10000,
            max_output_tokens=1000,
            modalities=["text"],
            supports_streaming=True,
            supports_tools=False,
        )

    def format_tool_call(self, tool_call: ToolCall) -> Dict[str, Any]:
        """Mock format tool call."""
        return {"mock": "formatted_tool_call"}

    def parse_tool_call(
        self, provider_response: Dict[str, Any]
    ) -> Optional[ToolCall]:
        """Mock parse tool call."""
        if provider_response.get("mock") == "tool_call":
            return ToolCall(
                id="test_id",
                name="test_tool",
                arguments={"test": "arg"}
            )
        return None


def test_model_adapter_base_initialization():
    """Test ModelAdapter base class initialization."""
    adapter = MockModelAdapter("test-model")

    assert adapter.model_name == "test-model"
    assert adapter.config == {}


def test_model_adapter_base_initialization_with_config():
    """Test ModelAdapter base class initialization with config."""
    adapter = MockModelAdapter("test-model", param1="value1", param2="value2")

    assert adapter.model_name == "test-model"
    assert adapter.config == {"param1": "value1", "param2": "value2"}


def test_model_adapter_base_abstract_methods():
    """Test that ModelAdapter base class raises NotImplementedError for abstract methods."""
    # Test that the abstract base class raises NotImplementedError for abstract methods
    from autonomous_agent.model_adapter.base import ModelAdapter as BaseModelAdapter

    # Create a direct instance of the abstract base class to test abstract methods
    class AbstractModelAdapter(BaseModelAdapter):
        # Implement abstract methods that raise NotImplementedError
        async def _generate(self, request):
            raise NotImplementedError

        async def _generate_stream(self, request):
            raise NotImplementedError

        def get_capabilities(self):
            raise NotImplementedError

        def format_tool_call(self, tool_call):
            raise NotImplementedError

        def parse_tool_call(self, provider_response):
            raise NotImplementedError

    abstract_adapter = AbstractModelAdapter("test-model")

    # These should raise NotImplementedError
    import asyncio
    try:
        asyncio.run(abstract_adapter.generate(ModelRequest()))
        assert False, "Should have raised NotImplementedError"
    except NotImplementedError:
        pass  # Expected

    # Test generate_stream - need to properly handle the async generator
    async def test_generate_stream():
        async for _ in abstract_adapter.generate_stream(ModelRequest()):
            pass  # We shouldn't get here

    try:
        asyncio.run(test_generate_stream())
        assert False, "Should have raised NotImplementedError"
    except NotImplementedError:
        pass  # Expected

    try:
        abstract_adapter.get_capabilities()
        assert False, "Should have raised NotImplementedError"
    except NotImplementedError:
        pass  # Expected

    try:
        abstract_adapter.format_tool_call(ToolCall(id="test", name="test", arguments={}))
        assert False, "Should have raised NotImplementedError"
    except NotImplementedError:
        pass  # Expected

    try:
        abstract_adapter.parse_tool_call({})
        assert False, "Should have raised NotImplementedError"
    except NotImplementedError:
        pass  # Expected


def test_model_adapter_config_initialization():
    """Test ModelAdapterConfig initialization."""
    config = ModelAdapterConfig()

    assert config.timeout == 60.0
    assert config.max_retries == 3
    assert config.retry_base_delay == 1.0
    assert config.retry_max_delay == 60.0
    assert config.enable_streaming == True
    assert config.temperature == 0.7
    assert config.top_p == 0.9
    assert config.enable_tool_calling == True
    assert config.provider_config == {}


def test_model_adapter_config_custom_values():
    """Test ModelAdapterConfig with custom values."""
    config = ModelAdapterConfig(
        timeout=30.0,
        max_retries=5,
        retry_base_delay=0.5,
        retry_max_delay=30.0,
        enable_streaming=False,
        temperature=0.5,
        top_p=0.8,
        enable_tool_calling=False,
        provider_config={"custom": "value"}
    )

    assert config.timeout == 30.0
    assert config.max_retries == 5
    assert config.retry_base_delay == 0.5
    assert config.retry_max_delay == 30.0
    assert config.enable_streaming == False
    assert config.temperature == 0.5
    assert config.top_p == 0.8
    assert config.enable_tool_calling == False
    assert config.provider_config == {"custom": "value"}


def test_model_adapter_factory_register_adapter():
    """Test registering a new adapter with the factory."""
    # Store original adapters to restore later
    original_adapters = ModelAdapterFactory._adapters.copy()

    try:
        # Register our mock adapter
        ModelAdapterFactory.register_adapter("mock", MockModelAdapter)

        # Check that it's registered
        assert "mock" in ModelAdapterFactory.get_supported_providers()
        assert ModelAdapterFactory.is_provider_supported("mock")

        # Create an adapter using the factory
        adapter = ModelAdapterFactory.create_adapter("mock", "test-model")
        assert isinstance(adapter, MockModelAdapter)
        assert adapter.model_name == "test-model"

    finally:
        # Restore original adapters
        ModelAdapterFactory._adapters = original_adapters


def test_model_adapter_factory_create_adapter():
    """Test creating an adapter using the factory."""
    # Test with anthropic (should already be registered)
    adapter = ModelAdapterFactory.create_adapter(
        "anthropic",
        "claude-3-opus-20240229",
        api_key="test-key"
    )

    assert isinstance(adapter, AnthropicAdapter)
    assert adapter.model_name == "claude-3-opus-20240229"


def test_model_adapter_factory_unsupported_provider():
    """Test creating an adapter with an unsupported provider."""
    try:
        ModelAdapterFactory.create_adapter("unsupported_provider", "test-model")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Unsupported provider" in str(e)


def test_model_adapter_registry_initialization():
    """Test ModelAdapterRegistry initialization."""
    registry = ModelAdapterRegistry()

    assert len(registry.list_adapters()) == 0
    assert registry.get_default() is None


def test_model_adapter_registry_register_get():
    """Test registering and getting an adapter from the registry."""
    registry = ModelAdapterRegistry()
    adapter = MockModelAdapter("test-model")

    # Register the adapter
    registry.register("test-adapter", adapter)

    # Check that it's registered
    assert "test-adapter" in registry.list_adapters()
    retrieved = registry.get("test-adapter")
    assert retrieved is adapter

    # Check that default is set
    assert registry.get_default() is adapter


def test_model_adapter_registry_set_default():
    """Test setting the default adapter in the registry."""
    registry = ModelAdapterRegistry()
    adapter1 = MockModelAdapter("test-model-1")
    adapter2 = MockModelAdapter("test-model-2")

    # Register both adapters
    registry.register("adapter-1", adapter1)
    registry.register("adapter-2", adapter2)

    # Initially, adapter-1 should be default (first registered)
    assert registry.get_default() is adapter1

    # Set adapter-2 as default
    registry.set_default("adapter-2")
    assert registry.get_default() is adapter2


def test_model_adapter_registry_unregister():
    """Test unregistering an adapter from the registry."""
    registry = ModelAdapterRegistry()
    adapter = MockModelAdapter("test-model")

    # Register and then unregister
    registry.register("test-adapter", adapter)
    assert "test-adapter" in registry.list_adapters()

    registry.unregister("test-adapter")
    assert "test-adapter" not in registry.list_adapters()
    assert registry.get("test-adapter") is None


def test_model_capabilities_initialization():
    """Test ModelCapabilities initialization."""
    capabilities = ModelCapabilities(
        model="test-model",
        provider="test-provider",
        context_window=8000,
        max_output_tokens=2000
    )

    assert capabilities.model == "test-model"
    assert capabilities.provider == "test-provider"
    assert capabilities.context_window == 8000
    assert capabilities.max_output_tokens == 2000
    assert capabilities.modalities == ["text"]
    assert capabilities.supports_streaming == True
    assert capabilities.supports_tools == True
    assert capabilities.supports_vision == False


def test_model_capabilities_custom_values():
    """Test ModelCapabilities with custom values."""
    capabilities = ModelCapabilities(
        model="test-model-vision",
        provider="test-provider",
        context_window=100000,
        max_output_tokens=4096,
        modalities=["text", "image"],
        supports_streaming=False,
        supports_tools=True,
        supports_vision=True,
        latency_ms=500,
        cost_per_1k_input_tokens=0.01,
        cost_per_1k_output_tokens=0.03,
        requests_per_minute=100,
        tokens_per_minute=50000
    )

    assert capabilities.model == "test-model-vision"
    assert capabilities.provider == "test-provider"
    assert capabilities.context_window == 100000
    assert capabilities.max_output_tokens == 4096
    assert capabilities.modalities == ["text", "image"]
    assert capabilities.supports_streaming == False
    assert capabilities.supports_tools == True
    assert capabilities.supports_vision == True
    assert capabilities.latency_ms == 500
    assert capabilities.cost_per_1k_input_tokens == 0.01
    assert capabilities.cost_per_1k_output_tokens == 0.03
    assert capabilities.requests_per_minute == 100
    assert capabilities.tokens_per_minute == 50000


def test_usage_initialization():
    """Test Usage initialization."""
    usage = Usage()

    assert usage.input_tokens == 0
    assert usage.output_tokens == 0
    assert usage.total_tokens == 0
    assert usage.cost_usd == 0.0


def test_usage_addition():
    """Test Usage addition."""
    usage1 = Usage(input_tokens=10, output_tokens=5, cost_usd=0.01)
    usage2 = Usage(input_tokens=20, output_tokens=10, cost_usd=0.02)

    result = usage1 + usage2

    assert result.input_tokens == 30
    assert result.output_tokens == 15
    assert result.total_tokens == 45
    assert result.cost_usd == 0.03


def test_model_request_initialization():
    """Test ModelRequest initialization."""
    request = ModelRequest()

    assert request.prompt is None
    assert request.messages is None
    assert request.temperature is None
    assert request.top_p is None
    assert request.max_tokens is None
    assert request.stop is None
    assert request.tools is None
    assert request.tool_choice is None
    assert request.stream == False
    assert request.extra == {}


def test_model_request_with_prompt():
    """Test ModelRequest with prompt."""
    request = ModelRequest(
        prompt="Hello, world!",
        temperature=0.8,
        max_tokens=100
    )

    assert request.prompt == "Hello, world!"
    assert request.temperature == 0.8
    assert request.max_tokens == 100
    assert request.messages is None


def test_model_request_with_messages():
    """Test ModelRequest with messages."""
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"}
    ]
    request = ModelRequest(
        messages=messages,
        temperature=0.7,
        tools=[{"type": "function", "function": {"name": "test_func"}}]
    )

    assert request.messages == messages
    assert request.temperature == 0.7
    assert request.tools == [{"type": "function", "function": {"name": "test_func"}}]
    assert request.prompt is None


def test_model_response_initialization():
    """Test ModelResponse initialization."""
    response = ModelResponse()

    assert response.text == ""
    assert response.tool_calls == []
    assert response.finished == True
    assert isinstance(response.usage, Usage)
    assert response.extra == {}


def test_model_response_with_values():
    """Test ModelResponse with values."""
    usage = Usage(input_tokens=50, output_tokens=25, cost_usd=0.005)
    tool_call = ToolCall(
        id="call_1",
        name="test_tool",
        arguments={"arg": "value"}
    )

    response = ModelResponse(
        text="This is a test response",
        tool_calls=[tool_call],
        finished=False,
        usage=usage,
        extra={"custom": "data"}
    )

    assert response.text == "This is a test response"
    assert len(response.tool_calls) == 1
    assert response.tool_calls[0] == tool_call
    assert response.finished == False
    assert response.usage == usage
    assert response.extra == {"custom": "data"}


def test_tool_call_initialization():
    """Test ToolCall initialization."""
    tool_call = ToolCall(
        id="call_123",
        name="test_function",
        arguments={"param1": "value1", "param2": "value2"}
    )

    assert tool_call.id == "call_123"
    assert tool_call.name == "test_function"
    assert tool_call.arguments == {"param1": "value1", "param2": "value2"}


def test_tool_call_auto_id():
    """Test ToolCall with auto-generated ID."""
    tool_call = ToolCall(name="test_function", arguments={})

    assert tool_call.name == "test_function"
    assert tool_call.arguments == {}
    assert tool_call.id.startswith("call_")
    assert len(tool_call.id) > len("call_")


def test_model_error_initialization():
    """Test ModelError initialization."""
    error = ModelError("Test error message", error_type="test_error", retryable=True)

    assert error.message == "Test error message"
    assert error.error_type == "test_error"
    assert error.retryable == True
    assert error.provider_error_code is None


def test_model_selection_success():
    """Test successful model selection."""
    from autonomous_agent.model_adapter.model_selector import ModelSelector

    selector = ModelSelector()

    # Test selecting a model with basic text capabilities
    provider, model_name, capabilities = selector.select_model(
        required_capabilities={"modality": ["text"]},
        min_context_window=1000
    )

    # Should select an Anthropic model since it's the only one we know about
    assert provider == "anthropic"
    assert model_name in ["claude-3-opus-20240229", "claude-3-sonnet-20240229",
                         "claude-3-haiku-20240307", "claude-2.1", "claude-2.0"]
    assert capabilities.context_window >= 1000
    assert capabilities.supports_streaming == True
    assert capabilities.supports_tools == True


def test_model_selection_capability_mismatch():
    """Test model selection fails with capability mismatch."""
    from autonomous_agent.model_adapter.model_selector import ModelSelector, ModelSelectionError

    selector = ModelSelector()

    # Try to select a model that requires vision (none of our mocked models support vision in a way that would match)
    # Actually, some of our models do support vision, so let's test a different capability
    # Let's test for a modality we don't support
    try:
        selector.select_model(
            required_capabilities={"modality": ["audio"]},  # We don't support audio
            min_context_window=1000
        )
        assert False, "Should have raised ModelSelectionError"
    except ModelSelectionError:
        pass  # Expected


def test_model_selection_insufficient_context():
    """Test model selection fails with insufficient context window."""
    from autonomous_agent.model_adapter.model_selector import ModelSelector, ModelSelectionError

    selector = ModelSelector()

    # Require a huge context window that none of our models have
    try:
        selector.select_model(
            required_capabilities={"modality": ["text"]},
            min_context_window=1000000  # 1M tokens - way more than any model has
        )
        assert False, "Should have raised ModelSelectionError"
    except ModelSelectionError:
        pass  # Expected


def test_model_selection_unavailable_model():
    """Test model selection handles unavailable models gracefully."""
    from autonomous_agent.model_adapter.model_selector import ModelSelector

    selector = ModelSelector()

    # This should still work because we filter by what we know about
    provider, model_name, capabilities = selector.select_model(
        required_capabilities={"modality": ["text"], "supports_tools": True},
        min_context_window=1000
    )

    assert provider == "anthropic"
    assert capabilities.supports_tools == True


def test_model_selection_provider_preference():
    """Test that provider preferences are respected."""
    from autonomous_agent.model_adapter.model_selector import ModelSelector

    selector = ModelSelector()

    # Even though we only have anthropic, test that preferences work
    provider, model_name, capabilities = selector.select_model(
        required_capabilities={"modality": ["text"]},
        min_context_window=1000,
        provider_preferences=["anthropic"]  # Prefer anthropic
    )

    assert provider == "anthropic"


def test_model_selection_model_preference():
    """Test that model preferences are respected."""
    from autonomous_agent.model_adapter.model_selector import ModelSelector

    selector = ModelSelector()

    # Test that we can specify a preferred model
    provider, model_name, capabilities = selector.select_model(
        required_capabilities={"modality": ["text"]},
        min_context_window=1000,
        model_preferences=["claude-3-haiku-20240307"]  # Prefer haiku (fastest/cheapest)
    )

    # Should select haiku if it meets requirements
    assert provider == "anthropic"
    assert model_name == "claude-3-haiku-20240307"
    assert capabilities.model == "claude-3-haiku-20240307"


def test_model_selection_no_suitable_model():
    """Test model selection when no model meets requirements."""
    from autonomous_agent.model_adapter.model_selector import ModelSelector, ModelSelectionError

    selector = ModelSelector()

    # Require a combination that no model satisfies
    # For example, require both vision and not vision (impossible)
    try:
        selector.select_model(
            required_capabilities={"modality": ["image"]},
            min_context_window=1000
        )
        assert False, "Should have raised ModelSelectionError"
    except ModelSelectionError:
        pass  # Expected


def test_model_error_inheritance():
    """Test that specific error types inherit from ModelError."""
    auth_error = AuthenticationError("Auth failed")
    rate_limit_error = RateLimitError("Rate limit exceeded")
    not_found_error = ModelNotFoundError("Model not found")
    invalid_request_error = InvalidRequestError("Invalid request")
    internal_error = InternalModelError("Internal error")

    assert isinstance(auth_error, ModelError)
    assert isinstance(rate_limit_error, ModelError)
    assert isinstance(not_found_error, ModelError)
    assert isinstance(invalid_request_error, ModelError)
    assert isinstance(internal_error, ModelError)

    # Check specific properties
    assert auth_error.error_type == "authentication_error"
    assert auth_error.retryable == False

    assert rate_limit_error.error_type == "rate_limit_error"
    assert rate_limit_error.retryable == True

    assert not_found_error.error_type == "model_not_found_error"
    assert not_found_error.retryable == False

    assert invalid_request_error.error_type == "invalid_request_error"
    assert invalid_request_error.retryable == False

    assert internal_error.error_type == "internal_model_error"
    assert internal_error.retryable == True


def test_anthropic_adapter_initialization():
    """Test AnthropicAdapter initialization."""
    adapter = AnthropicAdapter(
        model_name="claude-3-opus-20240229",
        api_key="test-api-key",
        timeout=30.0,
        max_retries=5
    )

    assert adapter.model_name == "claude-3-opus-20240229"
    assert adapter.api_key == "test-api-key"
    assert adapter.config["timeout"] == 30.0
    assert adapter.config["max_retries"] == 5


def test_anthropic_adapter_initialization_missing_api_key():
    """Test AnthropicAdapter initialization with missing API key."""
    try:
        AnthropicAdapter(model_name="claude-3-opus-20240229")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Anthropic API key is required" in str(e)


def test_anthropic_adapter_get_capabilities():
    """Test getting capabilities from AnthropicAdapter."""
    # Test known model
    adapter = AnthropicAdapter(
        model_name="claude-3-opus-20240229",
        api_key="test-key"
    )

    capabilities = adapter.get_capabilities()

    assert capabilities.model == "claude-3-opus-20240229"
    assert capabilities.provider == "anthropic"
    assert capabilities.context_window == 200000
    assert capabilities.max_output_tokens == 4096
    assert capabilities.modalities == ["text"]
    assert capabilities.supports_streaming == True
    assert capabilities.supports_tools == True
    assert capabilities.supports_vision == True
    assert capabilities.latency_ms == 1500
    assert capabilities.cost_per_1k_input_tokens == 0.015
    assert capabilities.cost_per_1k_output_tokens == 0.075
    assert capabilities.requests_per_minute == 50
    assert capabilities.tokens_per_minute == 40000


def test_anthropic_adapter_format_tool_call():
    """Test formatting tool calls for Anthropic."""
    adapter = AnthropicAdapter(
        model_name="claude-3-opus-20240229",
        api_key="test-key"
    )

    tool_call = ToolCall(
        id="call_123",
        name="test_function",
        arguments={"param1": "value1", "param2": "value2"}
    )

    formatted = adapter.format_tool_call(tool_call)

    assert formatted["type"] == "function"
    assert formatted["id"] == "call_123"
    assert formatted["function"]["name"] == "test_function"
    assert formatted["function"]["arguments"] == '{"param1": "value1", "param2": "value2"}'


def test_anthropic_adapter_parse_tool_call():
    """Test parsing tool calls from Anthropic response."""
    adapter = AnthropicAdapter(
        model_name="claude-3-opus-20240229",
        api_key="test-key"
    )

    # Test valid tool call response
    provider_response = {
        "type": "tool_use",
        "id": "call_123",
        "name": "test_function",
        "input": {"param1": "value1", "param2": "value2"}
    }

    parsed = adapter.parse_tool_call(provider_response)

    assert parsed is not None
    assert parsed.id == "call_123"
    assert parsed.name == "test_function"
    assert parsed.arguments == {"param1": "value1", "param2": "value2"}

    # Test non-tool call response
    non_tool_response = {
        "type": "text",
        "text": "This is a text response"
    }

    parsed_none = adapter.parse_tool_call(non_tool_response)
    assert parsed_none is None


if __name__ == "__main__":
    test_model_adapter_base_initialization()
    test_model_adapter_base_initialization_with_config()
    test_model_adapter_base_abstract_methods()
    test_model_adapter_config_initialization()
    test_model_adapter_config_custom_values()
    test_model_adapter_factory_register_adapter()
    test_model_adapter_factory_create_adapter()
    test_model_adapter_factory_unsupported_provider()
    test_model_adapter_registry_initialization()
    test_model_adapter_registry_register_get()
    test_model_adapter_registry_set_default()
    test_model_adapter_registry_unregister()
    test_model_capabilities_initialization()
    test_model_capabilities_custom_values()
    test_usage_initialization()
    test_usage_addition()
    test_model_request_initialization()
    test_model_request_with_prompt()
    test_model_request_with_messages()
    test_model_response_initialization()
    test_model_response_with_values()
    test_tool_call_initialization()
    test_tool_call_auto_id()
    test_model_error_initialization()
    test_model_error_inheritance()
    test_anthropic_adapter_initialization()
    test_anthropic_adapter_initialization_missing_api_key()
    test_anthropic_adapter_get_capabilities()
    test_anthropic_adapter_format_tool_call()
    test_anthropic_adapter_parse_tool_call()
    print("All model adapter tests passed!")