"""
Unit tests for the Code Search Module.
"""
from __future__ import annotations

import tempfile
import os
from pathlib import Path

import pytest

from autonomous_agent.repository_understanding import CodeSearchModule, SearchResult
from autonomous_agent.workspace import Workspace


class TestCodeSearchModule:
    """Test the CodeSearchModule class."""

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
    def search_module(self, workspace):
        """Create a CodeSearchModule instance for testing."""
        return CodeSearchModule(workspace)

    def test_init_with_workspace(self, workspace):
        """Test that CodeSearchModule initializes correctly with a workspace."""
        module = CodeSearchModule(workspace)
        assert module.workspace == workspace
        # ripgrep availability depends on system, but object should be created
        assert hasattr(module, '_ripgrep_available')

    def test_is_within_workspace(self, search_module):
        """Test workspace boundary checking."""
        # Use the workspace from the search_module
        workspace_path = Path(search_module.workspace.workspace_root)

        # Create test file inside workspace
        inside_file = workspace_path / "inside.py"
        inside_file.write_text("# Inside file\n")

        # Create test file outside workspace
        outside_file = Path(tempfile.gettempdir()) / "outside.py"
        outside_file.write_text("# Outside file\n")

        # Test file inside workspace
        assert search_module._is_within_workspace(inside_file) is True

        # Test file outside workspace
        assert search_module._is_within_workspace(outside_file) is False

    def test_extract_context(self, search_module):
        """Test context extraction around a line."""
        # Use the workspace from the search_module
        workspace_path = Path(search_module.workspace.workspace_root)

        # Create test file
        test_file = workspace_path / "test.py"
        test_content = """def func1():
    return 1

def func2():
    x = 2
    return x

def func3():
    return 3
"""
        test_file.write_text(test_content)

        # Test extracting context around line 5 (the "x = 2" line)
        context_before, line_content, context_after = search_module.extract_context(
            test_file, line_number=5, context_lines=1
        )

        # Should get one line before, the line itself, and one line after
        assert len(context_before) == 1
        assert context_before[0].strip() == "def func2():"
        assert line_content.strip() == "x = 2"
        assert len(context_after) == 1
        assert context_after[0].strip() == "return x"

    def test_calculate_match_score(self, search_module):
        """Match score calculation tests."""
        # Exact match should get high score
        score = search_module._calculate_match_score("def authenticate_user():", "authenticate_user", False)
        assert score > 0.8

        # Partial match should get lower score
        score = search_module._calculate_match_score("def user_auth():", "authenticate", False)
        assert 0.3 < score < 0.8

        # No match should get low score
        score = search_module._calculate_match_score("def calculate_total():", "authenticate", False)
        assert score < 0.3

        # Regex match should get high score
        score = search_module._calculate_match_score("def authenticate_user():", r"def \w+_user\(\):", True)
        assert score > 0.8

    def test_get_safe_file_paths(self, search_module):
        """Test filtering of safe file paths."""
        # Use the workspace from the search_module
        workspace_path = Path(search_module.workspace.workspace_root)

        # Create test files
        inside_file = workspace_path / "inside.py"
        inside_file.write_text("# Inside\n")

        outside_file = Path(tempfile.gettempdir()) / "outside.py"
        outside_file.write_text("# Outside\n")

        # Test filtering
        all_files = [inside_file, outside_file]
        safe_files = search_module._get_safe_file_paths(all_files)

        # Should only return the inside file
        assert len(safe_files) == 1
        assert safe_files[0] == inside_file


if __name__ == "__main__":
    pytest.main([__file__])