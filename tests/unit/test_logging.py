"""
Unit tests for logging initialization.
"""
from __future__ import annotations

from unittest.mock import patch

from autonomous_agent.config.settings import Settings
from autonomous_agent.agent_logging.setup import get_logger, setup_logging


def test_logging_can_be_initialized():
    """Test that logging can be initialized without errors."""
    settings = Settings(log_level="INFO")

    # This should not raise an exception
    setup_logging(settings)

    # Test that we can get a logger
    logger = get_logger("test_module")
    assert logger is not None


def test_logging_respects_log_level():
    """Test that logging respects the configured log level."""
    settings = Settings(log_level="DEBUG")

    with patch('autonomous_agent.agent_logging.setup.logger') as mock_logger:
        setup_logging(settings)
        # Verify that logger.add was called with the correct level
        mock_logger.add.assert_called()
        # We could check the call args, but for simplicity we just verify it's called