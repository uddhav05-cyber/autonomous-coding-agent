"""Pytest configuration."""
import pytest

from autonomous_agent.config.settings import Settings


@pytest.fixture
def test_settings():
    """Provide test settings."""
    return Settings(
        environment="testing",
        log_level="DEBUG",
        workspace_path="./test_workspace"
    )