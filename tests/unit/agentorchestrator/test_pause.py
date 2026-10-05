#!/usr/bin/env python3

import asyncio
from unittest.mock import MagicMock
from autonomous_agent.agentorchestrator import AgentOrchestrator, AgentState
from autonomous_agent.model_adapter.base import ModelAdapter
from autonomous_agent.context_engineering.context_manager import ContextManager
from autonomous_agent.tool.registry import ToolRegistry
from autonomous_agent.tool.executor import ToolExecutor
from autonomous_agent.workspace import Workspace
import tempfile
import os
import shutil

async def test_pause_functionality():
    """Test the pause functionality."""
    # Create mocks
    mock_model_adapter = MagicMock(spec=ModelAdapter)
    mock_context_manager = MagicMock(spec=ContextManager)
    mock_tool_registry = MagicMock(spec=ToolRegistry)
    mock_tool_executor = MagicMock(spec=ToolExecutor)
    mock_workspace = MagicMock(spec=Workspace)

    # Set up mocks
    mock_model_adapter._generate = MagicMock(return_value=MagicMock(text="Execute tool", tool_calls=[], usage=MagicMock(total_tokens=0)))
    mock_context_manager.create_context_package.return_value = MagicMock()
    mock_context_manager.get_context_summary = MagicMock(return_value={"total_tokens": 0})
    mock_tool_registry.list_tools.return_value = ["test_tool"]
    mock_tool = MagicMock()
    mock_tool.name = "test_tool"
    mock_tool_registry.get.return_value = mock_tool
    mock_tool_executor.execute.return_value = MagicMock(success=True, data=None, error=None)
    mock_workspace.workspace_root = tempfile.mkdtemp()

    # Create orchestrator
    orchestrator = AgentOrchestrator(
        model_adapter=mock_model_adapter,
        context_manager=mock_context_manager,
        tool_registry=mock_tool_registry,
        tool_executor=mock_tool_executor,
        workspace=mock_workspace,
        max_iterations=5
    )

    # Make iterations slow so we can pause
    async def slow_execute_iteration():
        await asyncio.sleep(0.2)  # Simulate work

    orchestrator._execute_iteration = slow_execute_iteration

    print("Starting task...")
    # Start the task in the background
    task = asyncio.create_task(orchestrator.execute_task("Test task for pausing"))

    # Give it a moment to start and complete first iteration
    await asyncio.sleep(0.3)  # Wait for first iteration to start loop again

    print(f"State before pause: {orchestrator._state.state if orchestrator._state else None}")

    # Pause the task
    print("Pausing task...")
    orchestrator.pause()

    # Give it a moment to pause
    await asyncio.sleep(0.1)

    print(f"State after pause: {orchestrator._state.state if orchestrator._state else None}")
    print(f"Paused flag: {orchestrator._paused}")

    # Verify it's paused
    assert orchestrator._state.state == AgentState.PAUSED
    assert orchestrator._paused == True

    # Resume the task
    print("Resuming task...")
    orchestrator.resume()

    # Give it a moment to resume
    await asyncio.sleep(0.1)

    print(f"State after resume: {orchestrator._state.state if orchestrator._state else None}")

    # Wait for completion
    print("Waiting for completion...")
    result_state = await task

    # Verify it completed after resume
    print(f"Final state: {result_state.state}")
    assert result_state.is_complete == True

    # Clean up
    shutil.rmtree(mock_workspace.workspace_root)

    print("Pause test passed!")

if __name__ == "__main__":
    asyncio.run(test_pause_functionality())