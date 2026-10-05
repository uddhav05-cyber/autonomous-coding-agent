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

async def test_cancel_functionality():
    """Test the cancel functionality."""
    print("Testing cancel functionality...")

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

    # Make iterations slow so we can cancel
    async def slow_execute_iteration():
        await asyncio.sleep(0.2)  # Simulate work

    orchestrator._execute_iteration = slow_execute_iteration

    # Start the task
    task = asyncio.create_task(orchestrator.execute_task("Test task for cancelling"))

    # Give it a moment to start
    await asyncio.sleep(0.2)

    # Cancel the task
    orchestrator.cancel()

    # Wait for completion
    result_state = await task

    # Verify it was cancelled
    assert result_state.state == AgentState.CANCELLED
    assert orchestrator._cancelled == True

    # Clean up
    shutil.rmtree(mock_workspace.workspace_root)

    print("Cancel test passed!")

async def test_stop_after_iteration_functionality():
    """Test the stop-after-iteration functionality."""
    print("Testing stop-after-iteration functionality...")

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

    # Create orchestrator with max_iterations=5 (enough to test early stopping)
    orchestrator = AgentOrchestrator(
        model_adapter=mock_model_adapter,
        context_manager=mock_context_manager,
        tool_registry=mock_tool_registry,
        tool_executor=mock_tool_executor,
        workspace=mock_workspace,
        max_iterations=5  # Allow enough iterations to test early stopping
    )

    # Make iterations slow so we can set stop-after-iteration
    async def slow_execute_iteration():
        await asyncio.sleep(0.2)  # Simulate work

    orchestrator._execute_iteration = slow_execute_iteration

    # Start the task
    task = asyncio.create_task(orchestrator.execute_task("Test task for stop-after-iteration"))

    # Give it a moment to just start (before first iteration completes)
    await asyncio.sleep(0.05)  # Very short time - should be at start of first iteration

    # Set stop-after-iteration (should stop after current iteration completes)
    orchestrator.stop_after_iteration()

    # Wait for completion
    result_state = await task

    # Verify it stopped early (should have completed fewer than max_iterations)
    # Since we called stop_after_iteration() at the start, it should stop after first iteration
    # So we should see current_iteration == 1
    print(f"Stopped at iteration: {result_state.current_iteration}")
    assert result_state.current_iteration == 1
    assert orchestrator._stop_after_iteration == True

    # Clean up
    shutil.rmtree(mock_workspace.workspace_root)

    print("Stop-after-iteration test passed!")

async def test_pause_resume_state_preservation():
    """Test that pause/resume preserves state correctly."""
    print("Testing pause/resume state preservation...")

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

    # Track iterations
    iteration_count = 0
    original_execute_iteration = orchestrator._execute_iteration

    async def tracking_execute_iteration():
        nonlocal iteration_count
        iteration_count += 1
        await asyncio.sleep(0.2)  # Simulate work

    orchestrator._execute_iteration = tracking_execute_iteration

    # Start the task
    task = asyncio.create_task(orchestrator.execute_task("Test task for state preservation"))

    # Give it a moment to start and complete a few iterations
    await asyncio.sleep(0.6)  # Should complete ~3 iterations

    iterations_before_pause = iteration_count
    print(f"Iterations before pause: {iterations_before_pause}")

    # Pause the task
    orchestrator.pause()

    # Give it a moment to pause
    await asyncio.sleep(0.1)

    iterations_during_pause = iteration_count
    print(f"Iterations during pause: {iterations_during_pause}")

    # Verify no progress during pause
    assert iterations_during_pause == iterations_before_pause

    # Resume the task
    orchestrator.resume()

    # Give it a moment to continue
    await asyncio.sleep(0.6)  # Should complete ~3 more iterations

    iterations_after_resume = iteration_count
    print(f"Iterations after resume: {iterations_after_resume}")

    # Verify progress resumed
    assert iterations_after_resume > iterations_during_pause

    # Wait for completion
    result_state = await task

    # Verify it completed
    assert result_state.is_complete == True

    # Clean up
    shutil.rmtree(mock_workspace.workspace_root)

    print("Pause/resume state preservation test passed!")

async def run_all_tests():
    """Run all control tests."""
    await test_cancel_functionality()
    await test_stop_after_iteration_functionality()
    await test_pause_resume_state_preservation()
    print("\nAll control tests passed!")

if __name__ == "__main__":
    asyncio.run(run_all_tests())