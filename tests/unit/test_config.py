"""
Unit tests for configuration loading and validation.
"""
from __future__ import annotations

from pydantic import ValidationError as PydanticValidationError

from autonomous_agent.config.settings import (
    ExecutionLimits,
    ModelProviderConfig,
    Settings,
    TimeoutConfig,
)
from autonomous_agent.errors.base import (
    AutonomousAgentError,
    ConfigurationError,
    ErrorCode,
    ModelError,
    NotImplementedError,
    Retryability,
    ToolError,
    ValidationError,
    WorkspaceError,
)


def test_valid_configuration_loads():
    """Test that valid configuration loads correctly."""
    settings = Settings(
        environment="development",
        log_level="INFO",
        workspace_path="./workspace"
    )

    assert settings.environment == "development"
    assert settings.log_level == "INFO"
    assert settings.workspace_path == "./workspace"
    assert isinstance(settings.model_provider, ModelProviderConfig)
    assert isinstance(settings.execution_limits, ExecutionLimits)
    assert isinstance(settings.timeouts, TimeoutConfig)


def test_configuration_defaults_behave_correctly():
    """Test that default configuration values are correct."""
    settings = Settings()

    # Test defaults
    assert settings.environment == "development"
    assert settings.log_level == "INFO"
    assert settings.workspace_path == "./workspace"

    # Test model provider defaults
    assert settings.model_provider.provider == "anthropic"
    assert settings.model_provider.model_name == "claude-3-opus-20240229"
    assert settings.model_provider.max_tokens == 4096
    assert settings.model_provider.temperature == 0.0

    # Test execution limits defaults
    assert settings.execution_limits.max_iterations == 10
    assert settings.execution_limits.max_tool_calls == 50
    assert settings.execution_limits.max_context_tokens == 8000
    assert settings.execution_limits.timeout_seconds == 300

    # Test timeout defaults
    assert settings.timeouts.tool_execution == 30
    assert settings.timeouts.model_response == 60
    assert settings.timeouts.verification == 120


def test_environment_configuration_is_loaded_and_explicit_values_win(monkeypatch):
    """Test nested environment settings and programmatic precedence."""
    monkeypatch.setenv("AUTONOMOUS_AGENT_WORKSPACE_PATH", "./from-env")
    monkeypatch.setenv("AUTONOMOUS_AGENT_EXECUTION_LIMITS_MAX_ITERATIONS", "25")
    monkeypatch.setenv("AUTONOMOUS_AGENT_MODEL_PROVIDER_TEMPERATURE", "0.5")

    settings = Settings(workspace_path="./explicit")

    assert settings.workspace_path == "./explicit"
    assert settings.execution_limits.max_iterations == 25
    assert settings.model_provider.temperature == 0.5


def test_invalid_configuration_fails():
    """Test that invalid configuration fails validation."""
    # Test invalid environment
    try:
        Settings(environment="invalid")
        assert False, "Expected ValidationError but none was raised"
    except PydanticValidationError as e:
        # Check if it's a ValidationError from pydantic
        assert "ValidationError" in type(e).__name__
        # If we get here, it's some kind of ValidationError, which is what we want

    # Test invalid log level
    try:
        Settings(log_level="INVALID")
        assert False, "Expected ValidationError but none was raised"
    except PydanticValidationError as e:
        assert "ValidationError" in type(e).__name__

    # Test invalid max_tokens (must be > 0)
    try:
        Settings(model_provider={"max_tokens": 0})
        assert False, "Expected ValidationError but none was raised"
    except PydanticValidationError as e:
        assert "ValidationError" in type(e).__name__

    # Test invalid temperature (must be between 0 and 2)
    try:
        Settings(model_provider={"temperature": 3.0})
        assert False, "Expected ValidationError but none was raised"
    except PydanticValidationError as e:
        assert "ValidationError" in type(e).__name__

    # Test negative max_iterations
    try:
        Settings(execution_limits={"max_iterations": -1})
        assert False, "Expected ValidationError but none was raised"
    except PydanticValidationError as e:
        assert "ValidationError" in type(e).__name__


def test_error_contains_expected_metadata():
    """Test that errors contain expected metadata."""
    error = AutonomousAgentError(
        error_code=ErrorCode.CONFIG_INVALID,
        message="Test error message",
        retryability=Retryability.NON_RETRYABLE
    )

    assert error.error_code == ErrorCode.CONFIG_INVALID
    assert error.message == "Test error message"
    assert error.retryability == Retryability.NON_RETRYABLE
    assert error.cause is None

    # Test string representation
    error_str = str(error)
    assert "[CONFIG_INVALID]" in error_str
    assert "Test error message" in error_str


def test_specific_error_types():
    """Test specific error types."""
    # ConfigurationError
    config_error = ConfigurationError("Config error")
    assert config_error.error_code == ErrorCode.CONFIG_INVALID

    # WorkspaceError
    workspace_error = WorkspaceError("Workspace error")
    assert workspace_error.error_code == ErrorCode.WORKSPACE_INVALID
    assert workspace_error.retryability == Retryability.RETRYABLE

    # ModelError
    model_error = ModelError("Model error")
    assert model_error.error_code == ErrorCode.MODEL_API_ERROR
    assert model_error.retryability == Retryability.RETRYABLE

    # ToolError
    tool_error = ToolError("Tool error")
    assert tool_error.error_code == ErrorCode.TOOL_EXECUTION_FAILED
    assert tool_error.retryability == Retryability.RETRYABLE

    # ValidationError
    validation_error = ValidationError("Validation error")
    assert validation_error.error_code == ErrorCode.VALIDATION_FAILED
    assert validation_error.retryability == Retryability.NON_RETRYABLE

    # NotImplementedError
    not_impl_error = NotImplementedError(feature="Feature X")
    assert not_impl_error.error_code == ErrorCode.NOT_IMPLEMENTED
    assert "Not implemented: Feature X" in str(not_impl_error)
