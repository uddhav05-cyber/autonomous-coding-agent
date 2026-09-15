"""
Integration tests for the workspace subsystem.
"""
from __future__ import annotations

import os
import tempfile

import pytest

from autonomous_agent.workspace import Workspace
from autonomous_agent.workspace.errors import *


class TestWorkspaceIntegration:
    """Integration tests for the workspace subsystem."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def workspace(self, temp_workspace):
        """Create a workspace instance for testing."""
        workspace_path = os.path.join(temp_workspace, "integration_test_workspace")
        return Workspace(workspace_root=workspace_path)

    def test_full_file_lifecycle(self, workspace):
        """Test a complete file lifecycle: create, read, update, delete."""
        # Create a file
        original_content = b"Original content"
        workspace.create_file("lifecycle.txt", original_content)

        # Read the file
        content = workspace.read_file("lifecycle.txt")
        assert content == original_content

        # Update the file (with overwrite)
        updated_content = b"Updated content"
        workspace.write_file("lifecycle.txt", updated_content, allow_overwrite=True)

        # Read the updated file
        content = workspace.read_file("lifecycle.txt")
        assert content == updated_content

        # Delete the file
        workspace.delete_file("lifecycle.txt")

        # Verify file is gone
        assert not workspace.file_exists("lifecycle.txt")

    def test_text_file_lifecycle(self, workspace):
        """Test a complete text file lifecycle."""
        # Create a text file
        original_text = "Hello, 世界! 🌍"
        workspace.create_file_text("text_lifecycle.txt", original_text)

        # Read the file as text
        text = workspace.read_file_text("text_lifecycle.txt")
        assert text == original_text

        # Update the file
        updated_text = "Updated text: こんにちは"
        workspace.write_file_text("text_lifecycle.txt", updated_text, allow_overwrite=True)

        # Read the updated file
        text = workspace.read_file_text("text_lifecycle.txt")
        assert text == updated_text

        # Delete the file
        workspace.delete_file("text_lifecycle.txt")
        assert not workspace.file_exists("text_lifecycle.txt")

    def test_directory_operations(self, workspace):
        """Test directory creation, listing, and deletion."""
        # Create a nested directory structure
        workspace.create_directory("project/src", parents=True)
        workspace.create_directory("project/tests", parents=True)
        workspace.create_directory("project/docs", parents=True)

        # Create some files in the directories
        workspace.create_file_text("project/src/main.py", "# Main application\nprint('Hello')")
        workspace.create_file_text("project/src/utils.py", "# Utilities\n")
        workspace.create_file_text("project/tests/test_main.py", "# Tests\n")
        workspace.create_file_text("project/docs/README.md", "# Documentation\n")

        # List the project directory
        entries = workspace.list_directory("project")
        assert len(entries) == 3
        dir_names = {entry["name"] for entry in entries}
        assert dir_names == {"src", "tests", "docs"}

        # List the src directory
        src_entries = workspace.list_directory("project/src")
        assert len(src_entries) == 2
        src_file_names = {entry["name"] for entry in src_entries}
        assert src_file_names == {"main.py", "utils.py"}

        # Delete the entire project tree
        workspace.delete_directory("project", recursive=True)

        # Verify everything is gone
        assert not workspace.directory_exists("project")
        assert not workspace.file_exists("project/src/main.py")

    def test_file_metadata_operations(self, workspace):
        """Test file metadata operations."""
        # Create a file with known content
        test_content = b"Metadata test content"
        workspace.create_file("metadata_test.txt", test_content)

        # Get metadata
        metadata = workspace.get_file_metadata("metadata_test.txt")

        # Verify metadata contents
        assert metadata["name"] == "metadata_test.txt"
        assert metadata["is_file"] is True
        assert metadata["is_directory"] is False
        assert metadata["size"] == len(test_content)
        assert isinstance(metadata["modified"], (int, float))
        assert isinstance(metadata["created"], (int, float))
        assert isinstance(metadata["permissions"], int)

        # Create a directory and get its metadata
        workspace.create_directory("meta_dir")
        dir_metadata = workspace.get_file_metadata("meta_dir")
        assert dir_metadata["name"] == "meta_dir"
        assert dir_metadata["is_file"] is False
        assert dir_metadata["is_directory"] is True

    def test_nested_operations(self, workspace):
        """Test operations in deeply nested paths."""
        # Create a deeply nested file path
        deep_path = "very/deeply/nested/directory/structure/file.txt"
        test_content = b"Deep content"

        # Create the file (should create all intermediate directories)
        workspace.create_file(deep_path, test_content)

        # Verify the file exists
        assert workspace.file_exists(deep_path)

        # Read the file
        content = workspace.read_file(deep_path)
        assert content == test_content

        # Get metadata
        metadata = workspace.get_file_metadata(deep_path)
        assert metadata["is_file"] is True
        assert metadata["size"] == len(test_content)

        # List the parent directory
        parent_dir = "very/deeply/nested/directory/structure"
        entries = workspace.list_directory(parent_dir)
        assert len(entries) == 1
        assert entries[0]["name"] == "file.txt"

        # Delete the file
        workspace.delete_file(deep_path)
        assert not workspace.file_exists(deep_path)

        # Verify parent directory is now empty and can be deleted
        workspace.delete_directory(parent_dir)
        assert not workspace.directory_exists(parent_dir)

    def test_error_propagation(self, workspace):
        """Test that errors are properly propagated."""
        # Test file not found error
        with pytest.raises(WorkspaceFileNotFoundError):
            workspace.read_file("nonexistent.txt")

        # Test file already exists error
        workspace.create_file("exists.txt", b"content")
        with pytest.raises(WorkspaceFileAlreadyExistsError):
            workspace.create_file("exists.txt", b"other content")

        # Test is directory error
        workspace.create_directory("adir")
        with pytest.raises(WorkspaceIsADirectoryError):
            workspace.read_file("adir")

        # Test not directory error
        workspace.create_file("afile.txt", b"content")
        with pytest.raises(WorkspaceNotADirectoryError):
            workspace.delete_directory("afile.txt")

        # Test root deletion prevention
        with pytest.raises(WorkspaceRootDeletionError):
            workspace.delete_file(".")
        with pytest.raises(WorkspaceRootDeletionError):
            workspace.delete_directory("", recursive=True)

        # Test security error (path traversal)
        with pytest.raises(WorkspaceSecurityError):
            workspace.read_file("../../etc/passwd")

    def test_concurrent_operations_safe(self, workspace):
        """Test that basic concurrent-like operations don't corrupt state."""
        # Create multiple files
        for i in range(10):
            workspace.create_file(f"file_{i}.txt", f"Content {i}".encode())

        # Verify all files exist
        for i in range(10):
            assert workspace.file_exists(f"file_{i}.txt")

        # Read and verify content
        for i in range(10):
            content = workspace.read_file(f"file_{i}.txt")
            assert content == f"Content {i}".encode()

        # Update files
        for i in range(10):
            workspace.write_file(f"file_{i}.txt", f"Updated {i}".encode(), allow_overwrite=True)

        # Verify updates
        for i in range(10):
            content = workspace.read_file(f"file_{i}.txt")
            assert content == f"Updated {i}".encode()

        # Delete half the files
        for i in range(0, 10, 2):
            workspace.delete_file(f"file_{i}.txt")

        # Verify deletion
        for i in range(0, 10, 2):
            assert not workspace.file_exists(f"file_{i}.txt")
        for i in range(1, 10, 2):
            assert workspace.file_exists(f"file_{i}.txt")

    def test_workspace_isolation(self, temp_workspace):
        """Test that workspace properly isolates operations."""
        # Create two separate workspaces
        ws1_path = os.path.join(temp_workspace, "workspace1")
        ws2_path = os.path.join(temp_workspace, "workspace2")

        ws1 = Workspace(workspace_root=ws1_path)
        ws2 = Workspace(workspace_root=ws2_path)

        # Create a file in each workspace
        ws1.create_file("isolated.txt", b"Workspace 1 content")
        ws2.create_file("isolated.txt", b"Workspace 2 content")

        # Verify isolation
        ws1_content = ws1.read_file("isolated.txt")
        ws2_content = ws2.read_file("isolated.txt")

        assert ws1_content == b"Workspace 1 content"
        assert ws2_content == b"Workspace 2 content"
        assert ws1_content != ws2_content

        # Verify each workspace cannot see the other's files by trying to access with path traversal
        # This should fail due to security restrictions
        with pytest.raises(WorkspaceSecurityError):
            ws1.read_file("../workspace2/isolated.txt")

        with pytest.raises(WorkspaceSecurityError):
            ws2.read_file("../workspace1/isolated.txt")


if __name__ == "__main__":
    pytest.main([__file__])