"""
Unit tests for the Context Selector component.
"""
import tempfile
from pathlib import Path
from unittest.mock import Mock

from autonomous_agent.context_engineering import ContextSelector, SelectionCriteria
from autonomous_agent.repository_understanding import RelevanceEngine, RelevanceSignals


def test_selection_criteria_initialization():
    """Test SelectionCriteria initialization."""
    criteria = SelectionCriteria()

    assert criteria.max_files is None
    assert criteria.max_snippets_per_file is None
    assert criteria.lines_per_snippet is None
    assert criteria.min_relevance_score == 0.1
    assert criteria.extract_snippets == True
    assert criteria.include_structure == True
    assert criteria.planning_phase_weight == 1.0
    assert criteria.execution_phase_weight == 1.0
    assert criteria.verification_phase_weight == 1.0
    assert criteria.prefer_recent == True
    assert criteria.include_dependencies == True
    assert criteria.max_dependency_depth == 2


def test_selection_criteria_custom_values():
    """Test SelectionCriteria with custom values."""
    criteria = SelectionCriteria(
        max_files=10,
        max_snippets_per_file=3,
        lines_per_snippet=5,
        min_relevance_score=0.5,
        extract_snippets=False,
        include_structure=False,
        planning_phase_weight=2.0,
        execution_phase_weight=1.5,
        verification_phase_weight=0.5,
        prefer_recent=False,
        include_dependencies=False,
        max_dependency_depth=5
    )

    assert criteria.max_files == 10
    assert criteria.max_snippets_per_file == 3
    assert criteria.lines_per_snippet == 5
    assert criteria.min_relevance_score == 0.5
    assert criteria.extract_snippets == False
    assert criteria.include_structure == False
    assert criteria.planning_phase_weight == 2.0
    assert criteria.execution_phase_weight == 1.5
    assert criteria.verification_phase_weight == 0.5
    assert criteria.prefer_recent == False
    assert criteria.include_dependencies == False
    assert criteria.max_dependency_depth == 5


def test_context_selector_initialization():
    """Test ContextSelector initialization."""
    selector = ContextSelector()

    assert selector.relevance_engine is None
    assert isinstance(selector.default_criteria, SelectionCriteria)


def test_context_selector_with_relevance_engine():
    """Test ContextSelector with a relevance engine."""
    mock_relevance_engine = Mock(spec=RelevanceEngine)
    selector = ContextSelector(relevance_engine=mock_relevance_engine)

    assert selector.relevance_engine == mock_relevance_engine


def test_context_selector_default_criteria():
    """Test that ContextSelector provides default criteria."""
    selector = ContextSelector()
    criteria = selector.default_criteria

    assert isinstance(criteria, SelectionCriteria)
    assert criteria.min_relevance_score == 0.1


def test_selection_criteria_hash():
    """Test that SelectionCriteria can be hashed (for caching)."""
    criteria1 = SelectionCriteria(max_files=5, min_relevance_score=0.2)
    criteria2 = SelectionCriteria(max_files=5, min_relevance_score=0.2)
    criteria3 = SelectionCriteria(max_files=10, min_relevance_score=0.2)

    # Equal criteria should have equal hashes
    assert hash(criteria1) == hash(criteria2)

    # Different criteria should have different hashes (usually)
    # Note: Hash collisions are possible but unlikely with different values
    assert hash(criteria1) == hash(criteria2)  # These should be equal

    # Test that we can use them in a set/dict
    criteria_set = {criteria1, criteria2, criteria3}
    assert len(criteria_set) == 2  # criteria1 and criteria2 are the same


def test_context_selector_repr():
    """Test ContextSelector string representation."""
    selector = ContextSelector()
    repr_str = repr(selector)

    assert "ContextSelector" in repr_str
    assert "relevance_engine=None" in repr_str


if __name__ == "__main__":
    test_selection_criteria_initialization()
    test_selection_criteria_custom_values()
    test_context_selector_initialization()
    test_context_selector_with_relevance_engine()
    test_context_selector_default_criteria()
    test_selection_criteria_hash()
    test_context_selector_repr()
    print("All context selector tests passed!")