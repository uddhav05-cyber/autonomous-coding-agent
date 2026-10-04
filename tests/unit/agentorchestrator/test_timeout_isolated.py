"""Isolated test for AgentOrchestrator timeout mechanism."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from autonomous_agent.agentorchestrator import AgentOrchestrator, AgentState
from autonomous_agent.model_adapter.base import ModelAdapter
from autonomous_agent.model_adapter.types import ModelRequest, ModelResponse
from autonomous_agent.context_engineering.context_manager import ContextManager
from autonomous_agent.tool.registry import ToolRegistry
from autonomous_agent.tool.executor import ToolExecutor
from autonomous_agent.workspace import Workspace


@pytest.mark.asyncio
async def test_timeout_mechanism_isolated():
    """Test that the orchestrator correctly times out when model generation exceeds iteration_timeout."""
    
    # Create minimal mocks
    mock_model_adapter = AsyncMock(spec=ModelAdapter)
    mock_context_manager = MagicMock(spec=ContextManager)
    mock_tool_registry = MagicMock(spec=ToolRegistry)
    mock_tool_executor = AsyncMock(spec=ToolExecutor)
    mock_workspace = MagicMock(spec=Workspace)
    
    # Set up workspace root
    mock_workspace.workspace_root = "/tmp/test_timeout_workspace"
    
    # Create orchestrator with short timeout
    orchestrator = AgentOrchestrator(
        model_adapter=mock_model_adapter,
        context_manager=mock_context_manager,
        tool_registry=mock_tool_registry,
        tool_executor=mock_tool_executor,
        workspace=mock_workspace,
        max_iterations=5,
        iteration_timeout=0.1  # 100ms timeout
    )
    
    # Create a model adapter that deliberately takes longer than the timeout
    async def slow_generate(*args, **kwargs):
        await asyncio.sleep(0.2)  # 200ms > 100ms timeout
        return MagicMock(text="Slow response", tool_calls=[], usage=MagicMock(total_tokens=0))
    
    # Assign the slow generator to the mock
    mock_model_adapter._generate = slow_generate
    
    # Execute task
    await orchestrator.execute_task("Test timeout task")
    
    # Print state details for debugging
    print(f"Orchestrator state:")
    print(f"  state: {orchestrator._state.state}")
    print(f"  completion_reason: {orchestrator._state.completion_reason}")
    print(f"  current_iteration: {orchestrator._state.current_iteration}")
    print(f"  max_iterations: {orchestrator._state.max_iterations}")
    
    # Assertions
    assert orchestrator._state is not None
    assert orchestrator._state.state == AgentState.TIMED_OUT
    assert orchestrator._state.completion_reason == "Overall timeout exceeded"
    
    # Clean up
    import shutil
    import os
    if os.path.exists("/tmp/test_timeout_workspace"):
        shutil.rmtree("/tmp/test_timeout_workspace", ignore_errors=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
