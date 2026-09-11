"""
Unit tests for package imports.
"""
from __future__ import annotations


def test_package_imports_successfully():
    """Test that the main package can be imported."""
    import autonomous_agent
    assert autonomous_agent is not None


def test_subpackages_import_successfully():
    """Test that subpackages can be imported."""
    from autonomous_agent import config, errors, logging, models
    assert config is not None
    assert errors is not None
    assert logging is not None
    assert models is not None


def test_settings_import():
    """Test that settings can be imported."""
    from autonomous_agent.config.settings import Settings
    assert Settings is not None


def test_error_imports():
    """Test that error classes can be imported."""
    from autonomous_agent.errors.base import (
        AutonomousAgentError,
        ConfigurationError,
        WorkspaceError,
        ModelError,
        ToolError,
        ValidationError,
        NotImplementedError
    )
    assert AutonomousAgentError is not None
    assert ConfigurationError is not None
    assert WorkspaceError is not None
    assert ModelError is not None
    assert ToolError is not None
    assert ValidationError is not None
    assert NotImplementedError is not None