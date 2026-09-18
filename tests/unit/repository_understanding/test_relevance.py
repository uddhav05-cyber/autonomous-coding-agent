"""
Unit tests for the Relevance Engine module.
"""
from __future__ import annotations

import tempfile
import os
from pathlib import Path

import pytest

from autonomous_agent.repository_understanding import RelevanceEngine
from autonomous_agent.workspace import Workspace


class TestRelevanceEngine:
    """Test the RelevanceEngine class."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def workspace(self, temp_workspace):
        """Create a workspace instance for testing."""
        workspace_path = os.path.join(temp_workspace, "test_workspace")
        os.makedirs(workspace_path, exist_ok=True)
        return Workspace(workspace_root=workspace_path)

    @pytest.fixture
    def relevance_engine(self, workspace):
        """Create a RelevanceEngine instance for testing."""
        return RelevanceEngine(workspace)

    def test_init_with_workspace(self, workspace):
        """Test that RelevanceEngine initializes correctly with a workspace."""
        engine = RelevanceEngine(workspace)
        assert engine.workspace == workspace
        assert isinstance(engine.weights, RelevanceEngine.RelevanceWeights)

    def test_extract_task_terms(self, relevance_engine):
        """Test extraction of task terms from query."""
        task_query = "Fix the bug in the user authentication service"
        terms = relevance_engine._extract_task_terms(task_query)

        # Should extract meaningful terms and filter out stop words
        assert "fix" in terms
        assert "bug" in terms
        assert "user" in terms
        assert "authentication" in terms
        assert "service" in terms

        # Should filter out stop words
        assert "the" not in terms
        assert "in" not in terms

    def test_calculate_path_similarity(self, relevance_engine):
        """Test path similarity calculation."""
        # Create a temporary directory structure
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace_path = Path(tmpdir) / "test_workspace"
            workspace_path.mkdir()

            # Create test file structure
            src_dir = workspace_path / "src"
            src_dir.mkdir()
            auth_dir = src_dir / "auth"
            auth_dir.mkdir()
            service_file = auth_dir / "service.py"
            service_file.write_text("# Authentication service\n")

            # Create workspace and relevance engine
            workspace = Workspace(workspace_root=str(workspace_path))
            engine = RelevanceEngine(workspace)

            # Test path similarity for auth-related task
            task_terms = ["auth", "service"]
            score = engine._calculate_path_similarity(
                service_file, task_terms, None  # metadata not needed for this test
            )

            # Should have high score since path contains both terms
            assert score > 0.5

    def test_calculate_name_pattern(self, relevance_engine):
        """Test name pattern calculation."""
        # Create a temporary file
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "auth_service.py"
            file_path.write_text("# Authentication service\n")

            workspace = Workspace(workspace_root=str(tmpdir))
            engine = RelevanceEngine(workspace)

            # Test exact match
            task_terms = ["auth", "service"]
            score = engine._calculate_name_pattern(file_path, task_terms)
            assert score > 0.7  # Should be high for good match

            # Test partial match
            task_terms = ["authentication"]
            score = engine._calculate_name_pattern(file_path, task_terms)
            assert score > 0.3  # Should have some score for partial match

            # Test no match
            task_terms = ["database", "query"]
            score = engine._calculate_name_pattern(file_path, task_terms)
            assert score < 0.3  # Should be low for no match

    def test_calculate_file_type(self, relevance_engine):
        """Test file type scoring."""
        # Create test files of different types
        with tempfile.TemporaryDirectory() as tmpdir:
            # Python file
            py_file = Path(tmpdir) / "test.py"
            py_file.write_text("# Python file\n")

            # Text file
            txt_file = Path(tmpdir) / "test.txt"
            txt_file.write_text("Text file\n")

            # Binary-like file (we'll treat as unknown)
            bin_file = Path(tmpdir) / "test.bin"
            bin_file.write_bytes(b"\x00\x01\x02\x03")

            workspace = Workspace(workspace_root=str(tmpdir))
            engine = RelevanceEngine(workspace)

            # Python file should get high score
            py_score = engine._calculate_file_type(py_file, [])
            assert py_score > 0.8

            # Text file should get moderate score
            txt_score = engine._calculate_file_type(txt_file, [])
            assert 0.3 < txt_score < 0.7

            # Unknown binary type should get low score
            bin_score = engine._calculate_file_type(bin_file, [])
            assert bin_score < 0.5

    def test_calculate_size_inversion(self, relevance_engine):
        """Test size inversion scoring."""
        # Create test files of different sizes
        with tempfile.TemporaryDirectory() as tmpdir:
            # Tiny file
            tiny_file = Path(tmpdir) / "tiny.py"
            tiny_file.write_text("# Tiny\n")

            # Small file
            small_file = Path(tmpdir) / "small.py"
            small_file.write_text("# Small file\n" * 10)

            # Large file
            large_file = Path(tmpdir) / "large.py"
            large_file.write_text("# Large file\n" * 1000)

            workspace = Workspace(workspace_root=str(tmpdir))
            engine = RelevanceEngine(workspace)

            # Tiny file should get highest score
            tiny_score = engine._calculate_size_inversion(tiny_file)
            assert tiny_score == 1.0

            # Small file should get high score
            small_score = engine._calculate_size_inversion(small_file)
            assert small_score >= 0.9

            # Large file should get lower score
            large_score = engine._calculate_size_inversion(large_file)
            assert large_score <= 0.4

    def test_update_signal_weights(self, relevance_engine):
        """Test updating signal weights."""
        # Store original weights
        original_path_weight = relevance_engine.weights.path_similarity

        # Update weights
        new_weights = {
            "path_similarity": 0.5,
            "name_pattern": 0.3,
            "content_keyword": 0.2
        }
        relevance_engine.update_signal_weights("test_task", new_weights)

        # Check that weights were updated
        assert relevance_engine.weights.path_similarity == 0.5
        assert relevance_engine.weights.name_pattern == 0.3
        assert relevance_engine.weights.content_keyword == 0.2

        # Other weights should remain unchanged (default values)
        assert relevance_engine.weights.dependency == 0.15
        assert relevance_engine.weights.modification_history == 0.10

    def test_get_top_files(self, relevance_engine):
        """Test getting top-ranked files."""
        # Create test scores
        scores = {
            Path("file1.py"): 0.9,
            Path("file2.py"): 0.7,
            Path("file3.py"): 0.5,
            Path("file4.py"): 0.2,
            Path("file5.py"): 0.1,
        }

        # Get top 3 files with threshold 0.3
        top_files = relevance_engine.get_top_files(scores, limit=3, threshold=0.3)

        # Should return top 3 files above threshold
        assert len(top_files) == 3
        assert top_files[0][0] == Path("file1.py")
        assert top_files[0][1] == 0.9
        assert top_files[1][0] == Path("file2.py")
        assert top_files[1][1] == 0.7
        assert top_files[2][0] == Path("file3.py")
        assert top_files[2][1] == 0.5

        # Files below threshold should be excluded
        assert Path("file4.py") not in [f[0] for f in top_files]
        assert Path("file5.py") not in [f[0] for f in top_files]


if __name__ == "__main__":
    pytest.main([__file__])