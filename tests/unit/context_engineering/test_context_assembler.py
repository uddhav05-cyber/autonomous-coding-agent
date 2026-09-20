"""
Unit tests for the Context Assembler component.
"""
import time
from pathlib import Path
from autonomous_agent.context_engineering import (
    ContextAssembler,
    AssemblyResult,
    SelectionCriteria,
    BudgetAllocation,
    DuplicatePolicy
)


def test_assembly_result_initialization():
    """Test AssemblyResult initialization."""
    result = AssemblyResult()

    assert result.assembly_id is not None
    assert len(result.assembly_id) > 0
    assert result.timestamp > 0
    assert result.assembly_time_ms >= 0
    assert isinstance(result.sources_used, list)
    assert result.file_count == 0
    assert result.symbol_count == 0
    assert result.snippet_count == 0
    assert result.completeness_score == 1.0
    assert result.relevance_score == 0.0
    assert result.diversity_score == 0.0


def test_assembly_result_is_complete():
    """Test AssemblyResult is_complete method."""
    result = AssemblyResult()

    assert result.is_complete() == True  # Default completeness is 1.0

    # Test with low completeness
    result.completeness_score = 0.5
    assert result.is_complete() == False

    # Test with high completeness
    result.completeness_score = 0.9
    assert result.is_complete() == True


def test_assembly_result_get_summary():
    """Test AssemblyResult get_summary method."""
    result = AssemblyResult(
        assembly_id="test123",
        timestamp=1234567890.0,
        assembly_time_ms=50.0,
        sources_used=["repository", "working"],
        file_count=5,
        symbol_count=10,
        snippet_count=3,
        completeness_score=0.85,
        relevance_score=0.75,
        diversity_score=0.65
    )

    summary = result.get_summary()

    assert summary["assembly_id"] == "test123"
    assert summary["timestamp"] == 1234567890.0
    assert summary["assembly_time_ms"] == 50.0
    assert summary["sources_used"] == ["repository", "working"]
    assert summary["file_count"] == 5
    assert summary["symbol_count"] == 10
    assert summary["snippet_count"] == 3
    assert summary["completeness_score"] == 0.85
    assert summary["relevance_score"] == 0.75
    assert summary["diversity_score"] == 0.65


def test_context_assembler_initialization():
    """Test ContextAssembler initialization."""
    assembler = ContextAssembler()

    assert isinstance(assembler, ContextAssembler)


def test_context_assembler_assemble_context():
    """Test assembling context."""
    assembler = ContextAssembler()

    # Simple selected context
    selected_context = {
        "files": [
            {
                "path": "/tmp/test.py",
                "relative_path": "test.py",
                "relevance_score": type('MockScore', (), {'composite': 0.8})(),
                "content": "print('hello world')",
                "size_bytes": 19,
                "line_count": 1,
                "language": "python",
                "items_for_dedup": ["path:/tmp/test.py", "content_hash:abc123"]
            }
        ],
        "symbols": [],
        "snippets": [],
        "repository_info": {
            "root_path": "/tmp",
            "is_git_repo": True,
            "git_branch": "main",
            "project_type": "python"
        }
    }

    # Mock repository metadata
    class MockRepositoryMetadata:
        def __init__(self):
            self.root_path = Path("/tmp")
            self.is_git_repo = True
            self.git_branch = "main"
            self.git_commit = "abc123"
            self.project_type = "python"
            self.project_configs = {"setup.py": Path("/tmp/setup.py")}
            self.structure_map = {"src": ["main.py"]}
            self.language_hints = {"python"}
            self.build_system_hints = {"setuptools"}
            self.documentation_hints = {"readme.md"}

    repository_metadata = MockRepositoryMetadata()
    selection_criteria = SelectionCriteria()
    budget_allocation = BudgetAllocation()
    duplicate_policy = DuplicatePolicy()

    # Assemble context
    result = assembler.assemble_context(
        selected_context=selected_context,
        repository_metadata=repository_metadata,
        selection_criteria=selection_criteria,
        budget_allocation=budget_allocation,
        duplicate_policy=duplicate_policy
    )

    # Should return an AssemblyResult
    assert isinstance(result, AssemblyResult)
    assert result.assembly_id is not None
    assert result.timestamp > 0
    assert result.assembly_time_ms >= 0
    assert isinstance(result.sources_used, list)
    assert result.file_count >= 0
    assert result.symbol_count >= 0
    assert result.snippet_count >= 0
    assert 0.0 <= result.completeness_score <= 1.0
    assert 0.0 <= result.relevance_score <= 1.0
    assert 0.0 <= result.diversity_score <= 1.0


def test_context_assembler_calculate_completeness_score():
    """Test calculating completeness score."""
    assembler = ContextAssembler()

    # Test with complete result
    result = AssemblyResult(
        sources_used=["repository", "working", "task"],
        file_count=5,
        symbol_count=3,
        snippet_count=2
    )
    criteria = SelectionCriteria(max_files=10)

    score = assembler._calculate_completeness_score(result, criteria)
    assert 0.0 <= score <= 1.0

    # Test with missing sources
    result_incomplete = AssemblyResult(
        sources_used=["repository"],  # Missing working and task
        file_count=0,
        symbol_count=0,
        snippet_count=0
    )

    score_incomplete = assembler._calculate_completeness_score(result_incomplete, criteria)
    assert score_incomplete < score  # Should be lower due to missing sources


def test_context_assembler_calculate_relevance_score():
    """Test calculating relevance score."""
    assembler = ContextAssembler()

    # Test with relevance scores present
    selected_context = {
        "files": [
            {
                "relevance_score": type('MockScore', (), {'composite': 0.8})()
            },
            {
                "relevance_score": type('MockScore', (), {'composite': 0.6})()
            },
            {
                "relevance_score": type('MockScore', (), {'composite': 0.9})()
            }
        ]
    }

    score = assembler._calculate_relevance_score(selected_context)
    expected = (0.8 + 0.6 + 0.9) / 3  # 0.766...
    assert abs(score - expected) < 0.01

    # Test with no relevance scores
    selected_context_no_scores = {
        "files": [
            {"relevance_score": None},
            {"relevance_score": "invalid"}
        ]
    }

    score_no_scores = assembler._calculate_relevance_score(selected_context_no_scores)
    assert score_no_scores == 0.5  # Default fallback score


def test_context_assembler_calculate_diversity_score():
    """Test calculating diversity score."""
    assembler = ContextAssembler()

    # Test with diverse files
    working_context = {
        "files": [
            {"language": "python", "path": "test1.py"},
            {"language": "javascript", "path": "test2.js"},
            {"language": "java", "path": "test3.java"}
        ],
        "symbols": [{"name": "func1", "type": "function"}],
        "snippets": [{"content": "code snippet"}]
    }

    score = assembler._calculate_diversity_score(working_context)
    assert 0.0 <= score <= 1.0
    # Should be reasonably high due to multiple languages and context types

    # Test with no diversity
    working_context_none = {
        "files": [],
        "symbols": [],
        "snippets": []
    }

    score_none = assembler._calculate_diversity_score(working_context_none)
    assert score_none == 0.0  # No diversity at all


def test_context_assembler_extract_structure_hints():
    """Test extracting structure hints."""
    assembler = ContextAssembler()

    class MockRepositoryMetadata:
        def __init__(self):
            self.project_type = "python"
            self.is_git_reo = True
            self.language_hints = {"python", "javascript"}
            self.build_system_hints = {"setuptools"}
            self.documentation_hints = {"readme.md", "changelog.txt"}
            self.structure_map = {
                "src": ["main.py", "utils.py"],
                "tests": ["test_main.py"],
                "docs": ["readme.md"]
            }

    repository_metadata = MockRepositoryMetadata()
    selection_criteria = SelectionCriteria(include_structure=True)

    hints = assembler._extract_structure_hints(repository_metadata, selection_criteria)

    assert "project_type" in hints
    assert "is_git_repo" in hints
    assert "primary_languages" in hints
    assert "build_systems" in hints
    assert "documentation_types" in hints
    assert "directory_structure" in hints

    # Check that we got the expected languages
    assert "python" in hints["primary_languages"]
    assert "javascript" in hints["primary_languages"]


def test_context_assembler_repr():
    """Test ContextAssembler string representation."""
    assembler = ContextAssembler()
    repr_str = repr(assembler)

    assert "ContextAssembler" in repr_str


if __name__ == "__main__":
    test_assembly_result_initialization()
    test_assembly_result_is_complete()
    test_assembly_result_get_summary()
    test_context_assembler_initialization()
    test_context_assembler_assemble_context()
    test_context_assembler_calculate_completeness_score()
    test_context_assembler_calculate_relevance_score()
    test_context_assembler_calculate_diversity_score()
    test_context_assembler_extract_structure_hints()
    test_context_assembler_repr()
    print("All context assembler tests passed!")