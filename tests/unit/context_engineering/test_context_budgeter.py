"""
Unit tests for the Context Budgeter component.
"""
from autonomous_agent.context_engineering import ContextBudgeter, BudgetAllocation


def test_budget_allocation_initialization():
    """Test BudgetAllocation initialization."""
    allocation = BudgetAllocation()

    assert isinstance(allocation.fixed_allocations, dict)
    assert isinstance(allocation.proportional_allocations, dict)
    assert isinstance(allocation.min_allocations, dict)
    assert isinstance(allocation.max_allocations, dict)
    assert allocation.enable_dynamic_reallocation == True
    assert allocation.planning_budget_multiplier == 1.0
    assert allocation.execution_budget_multiplier == 1.0
    assert allocation.verification_budget_multiplier == 1.0
    assert allocation.reserve_percentage == 0.1


def test_context_budgeter_initialization():
    """Test ContextBudgeter initialization."""
    budgeter = ContextBudgeter()

    assert isinstance(budgeter.default_allocation, BudgetAllocation)
    assert budgeter.default_allocation.reserve_percentage == 0.1


def test_context_budgeter_apply_budget():
    """Test applying budget to assembled context."""
    budgeter = ContextBudgeter()

    # Simple assembled context
    assembled_context = {
        "repository_context": {"metadata": {"project_type": "python"}},
        "working_context": {
            "files": [{"path": "test.py", "content": "print('hello')"}],
            "symbols": [{"name": "main", "type": "function"}],
            "snippets": [{"content": "print('hello')", "start_line": 1, "end_line": 1}]
        },
        "task_context": {"description": "Test task"},
        "history_context": {}
    }

    # Apply budget
    budgeted = budgeter.apply_budget(
        assembled_context=assembled_context,
        max_tokens=2000
    )

    # Should return a dictionary with the same structure
    assert isinstance(budgeted, dict)
    assert "repository_context" in budgeted
    assert "working_context" in budgeted
    assert "task_context" in budgeted
    assert "history_context" in budgeted

    # Should have budget info
    assert "_budget_info" in budgeted
    budget_info = budgeted["_budget_info"]
    assert "max_tokens" in budget_info
    assert "reserve_tokens" in budget_info
    assert "available_tokens" in budget_info
    assert "allocated_tokens" in budget_info
    assert "used_tokens" in budget_info


def test_context_budgeter_with_custom_allocation():
    """Test applying budget with custom allocation."""
    budgeter = ContextBudgeter()

    # Custom budget allocation
    custom_allocation = BudgetAllocation(
        fixed_allocations={
            "repository_context": 500,
            "task_context": 200
        },
        proportional_allocations={
            "working_context": 1.0
        },
        min_allocations={
            "repository_context": 100,
            "task_context": 50,
            "working_context": 100
        },
        max_allocations={
            "working_context": 1000
        },
        reserve_percentage=0.05
    )

    assembled_context = {
        "repository_context": {"metadata": {"test": "value"}},
        "working_context": {
            "files": [{"path": "test.py", "content": "x" * 500}],  # Large content
            "symbols": [],
            "snippets": []
        },
        "task_context": {"description": "Test task"},
        "history_context": {}
    }

    # Apply custom budget
    budgeted = budgeter.apply_budget(
        assembled_context=assembled_context,
        budget_allocation=custom_allocation,
        max_tokens=1000
    )

    # Should still return valid structure
    assert isinstance(budgeted, dict)
    assert "_budget_info" in budgeted

    # Check that budget info reflects our custom allocation
    budget_info = budgeted["_budget_info"]
    assert budget_info["max_tokens"] == 1000
    assert budget_info["reserve_percentage"] == 0.05  # Should be reflected in calculation


def test_context_budgeter_get_budget_recommendations():
    """Test getting budget recommendations."""
    budgeter = ContextBudgeter()

    context_usage = {
        "repository_context": 300,
        "working_context": 1200,
        "task_context": 100,
        "history_context": 50
    }

    recommendations = budgeter.get_budget_recommendations(
        context_usage=context_usage,
        total_tokens_used=1650,
        max_tokens=2000
    )

    assert isinstance(recommendations, dict)
    assert "current_utilization" in recommendations
    assert "is_over_budget" in recommendations
    assert "suggested_adjustments" in recommendations
    assert "warnings" in recommendations

    # Should not be over budget (1650 < 2000)
    assert recommendations["is_over_budget"] == False
    assert recommendations["current_utilization"] == 0.825  # 1650/2000


def test_context_budgeter_get_budget_recommendations_over_budget():
    """Test getting budget recommendations when over budget."""
    budgeter = ContextBudgeter()

    context_usage = {
        "repository_context": 800,
        "working_context": 1500,
        "task_context": 200,
        "history_context": 100
    }

    recommendations = budgeter.get_budget_recommendations(
        context_usage=context_usage,
        total_tokens_used=2600,  # Over budget
        max_tokens=2000
    )

    assert recommendations["is_over_budget"] == True
    assert recommendations["current_utilization"] == 1.3  # 2600/2000
    assert len(recommendations["warnings"]) > 0


def test_context_budgeter_repr():
    """Test ContextBudgeter string representation."""
    budgeter = ContextBudgeter()
    repr_str = repr(budgeter)

    assert "ContextBudgeter" in repr_str


if __name__ == "__main__":
    test_budget_allocation_initialization()
    test_context_budgeter_initialization()
    test_context_budgeter_apply_budget()
    test_context_budgeter_with_custom_allocation()
    test_context_budgeter_get_budget_recommendations()
    test_context_budgeter_get_budget_recommendations_over_budget()
    test_context_budgeter_repr()
    print("All context budgeter tests passed!")