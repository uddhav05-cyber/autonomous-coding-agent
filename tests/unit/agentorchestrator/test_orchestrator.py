"""Unit tests for the Agent Orchestrator."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from autonomous_agent.agentorchestrator import AgentOrchestrator, AgentOrchestratorState, AgentState
from autonomous_agent.model_adapter.base import ModelAdapter
from autonomous_agent.context_engineering.context_manager import ContextManager
from autonomous_agent.tool.registry import ToolRegistry
from autonomous_agent.tool.executor import ToolExecutor
from autonomous_agent.workspace import Workspace
from autonomous_agent.tool.errors import ToolError


@pytest.fixture
def mock_model_adapter():
    """Create a mock model adapter."""
    mock = AsyncMock(spec=ModelAdapter)
    mock._generate = AsyncMock(return_value=MagicMock(text="Test response", tool_calls=[], usage=MagicMock(total_tokens=0)))
    return mock


@pytest.fixture
def mock_context_manager():
    """Create a mock context manager."""
    mock = MagicMock(spec=ContextManager)
    mock.create_context_package.return_value = MagicMock()
    mock.get_context_summary = MagicMock(return_value={"total_tokens": 0})
    return mock


@pytest.fixture
def mock_tool_registry():
    """Create a mock tool registry."""
    mock = MagicMock(spec=ToolRegistry)
    mock.list_tools.return_value = []
    mock.get.return_value = None
    return mock


@pytest.fixture
def mock_tool_executor():
    """Create a mock tool executor."""
    mock = AsyncMock(spec=ToolExecutor)
    mock.execute = AsyncMock(return_value=MagicMock(success=True, data=None, error=None))
    return mock


@pytest.fixture
def mock_workspace():
    """Create a mock workspace."""
    return MagicMock(spec=Workspace)


@pytest.fixture
def orchestrator(mock_model_adapter, mock_context_manager, mock_tool_registry, mock_tool_executor, mock_workspace):
    """Create an orchestrator instance with mocks."""
    return AgentOrchestrator(
        model_adapter=mock_model_adapter,
        context_manager=mock_context_manager,
        tool_registry=mock_tool_registry,
        tool_executor=mock_tool_executor,
        workspace=mock_workspace,
        max_iterations=2
    )


@pytest.mark.asyncio
async def test_execute_task_initialization(orchestrator, mock_model_adapter, mock_context_manager):
    """Test that execute_task initializes the state correctly."""
    task_description = "Test task"
    await orchestrator.execute_task(task_description)

    assert orchestrator._state is not None
    assert orchestrator._state.task_description == task_description
    assert orchestrator._state.state == AgentState.COMPLETED  # After execution completes via max iterations
    assert orchestrator._state.current_iteration == 2

    # Check that context manager was called to create context package each iteration
    assert mock_context_manager.create_context_package.call_count == orchestrator.max_iterations
    mock_context_manager.create_context_package.assert_called_with(task_description=task_description)


@pytest.mark.asyncio
async def test_execute_task_iteration_count(orchestrator, mock_model_adapter):
    """Test that the iteration count is incremented correctly."""
    # Set up the mock to return a response that will cause the loop to continue until max_iterations
    mock_model_adapter._generate.return_value = MagicMock(text="Continue", tool_calls=[], usage=MagicMock(total_tokens=0))

    await orchestrator.execute_task("Test task")

    assert orchestrator._state.current_iteration == orchestrator.max_iterations


@pytest.mark.asyncio
async def test_execute_task_completion_from_reasoning(orchestrator, mock_model_adapter):
    """Test that the task completes when the LLM indicates completion."""
    # Set up the mock to return a response with completion reasoning
    mock_model_adapter._generate.return_value = MagicMock(text="Task is complete", tool_calls=[], usage=MagicMock(total_tokens=0))

    await orchestrator.execute_task("Test task")

    assert orchestrator._state.state == AgentState.COMPLETED
    assert orchestrator._state.completion_reason == "Task completed based on LLM reasoning"
    assert orchestrator._state.final_response == "Task is complete"


@pytest.mark.asyncio
async def test_execute_task_max_iterations(orchestrator, mock_model_adapter):
    """Test that the task stops after max iterations."""
    # Set up the mock to return a response that never indicates completion
    mock_model_adapter._generate.return_value = MagicMock(text="Continue", tool_calls=[], usage=MagicMock(total_tokens=0))

    await orchestrator.execute_task("Test task")

    assert orchestrator._state.state == AgentState.COMPLETED  # Because we force completion at max iterations
    assert orchestrator._state.completion_reason == "Maximum iterations reached"
    assert orchestrator._state.current_iteration == orchestrator.max_iterations


@pytest.mark.asyncio
async def test_execute_task_timeout(orchestrator, mock_model_adapter):
    """Test that the task respects the overall timeout."""
    # Set a short timeout for the orchestrator
    orchestrator.iteration_timeout = 0.1  # 100 ms

    # Set up the mock to delay the response
    async def delayed_generate(*args, **kwargs):
        await asyncio.sleep(0.2)  # Longer than the timeout
        return MagicMock(text="Delayed response", tool_calls=[], usage=MagicMock(total_tokens=0))

    mock_model_adapter._generate = delayed_generate

    await orchestrator.execute_task("Test task")

    assert orchestrator._state.state == AgentState.TIMED_OUT
    assert orchestrator._state.completion_reason == "Overall timeout exceeded"


@pytest.mark.asyncio
async def test_execute_task_error_handling(orchestrator, mock_model_adapter):
    """Test that the orchestrator handles unexpected errors."""
    # Set up the mock to raise an exception
    mock_model_adapter._generate.side_effect = Exception("Test error")

    await orchestrator.execute_task("Test task")

    assert orchestrator._state.state == AgentState.FAILED
    assert orchestrator._state.completion_reason == "Max iterations reached without completion"
    assert orchestrator._state.error_count == 2
    assert orchestrator._state.last_error is not None
    assert isinstance(orchestrator._state.last_error, ToolError)
    assert "Test error" in str(orchestrator._state.last_error)
