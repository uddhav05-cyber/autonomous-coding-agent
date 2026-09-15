"""
Unit tests for the Workspace manager.
"""
from __future__ import annotations

import os
import tempfile

import pytest

from autonomous_agent.workspace import SymlinkPolicy, Workspace
from autonomous_agent.workspace.errors import *


class TestWorkspace:
    """Test the Workspace class."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def workspace(self, temp_workspace):
        """Create a workspace instance for testing."""
        workspace_path = os.path.join(temp_workspace, "test_workspace")
        return Workspace(workspace_root=workspace_path)

    def test_init_uses_settings_when_no_root_provided(self, monkeypatch, temp_workspace):
        """Test that Workspace uses Settings when no workspace_root is provided."""
        # Set environment variable for settings
        monkeypatch.setenv("AUTONOMOUS_AGENT_WORKSPACE_PATH", temp_workspace)

        # Create workspace without specifying root
        workspace = Workspace()
        assert workspace.workspace_root == os.path.abspath(temp_workspace)

    def test_init_creates_workspace_if_not_exists(self, temp_workspace):
        """Test that Workspace initialization creates workspace if it doesn't exist."""
        workspace_path = os.path.join(temp_workspace, "new_workspace")
        assert not os.path.exists(workspace_path)

        workspace = Workspace(workspace_root=workspace_path)
        assert os.path.isdir(workspace_path)
        assert workspace.workspace_root == os.path.abspath(workspace_path)

    def test_read_file_delegates_to_backend(self, workspace, temp_workspace):
        """Test that read_file delegates to the backend."""
        test_file = os.path.join(workspace.workspace_root, "test.txt")
        test_content = b"Hello, World!"
        with open(test_file, "wb") as f:
            f.write(test_content)

        content = workspace.read_file("test.txt")
        assert content == test_content

    def test_read_file_text_delegates_to_backend(self, workspace, temp_workspace):
        """Test that read_file_text delegates to the backend."""
        test_file = os.path.join(workspace.workspace_root, "test.txt")
        test_content = "Hello, World!"
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_content)

        content = workspace.read_file_text("test.txt")
        assert content == test_content

    def test_write_file_delegates_to_backend(self, workspace, temp_workspace):
        """Test that write_file delegates to the backend."""
        test_content = b"Hello, World!"
        workspace.write_file("test.txt", test_content)

        # Verify file was written correctly
        with open(os.path.join(workspace.workspace_root, "test.txt"), "rb") as f:
            assert f.read() == test_content

    def test_write_file_text_delegates_to_backend(self, workspace, temp_workspace):
        """Test that write_file_text delegates to the backend."""
        test_content = "Hello, World!"
        workspace.write_file_text("test.txt", test_content)

        # Verify file was written correctly
        with open(os.path.join(workspace.workspace_root, "test.txt"), "r", encoding="utf-8") as f:
            assert f.read() == test_content

    def test_create_file_delegates_to_backend(self, workspace, temp_workspace):
        """Test that create_file delegates to the backend."""
        test_content = b"Hello, World!"
        workspace.create_file("test.txt", test_content)

        # Verify file was created correctly
        with open(os.path.join(workspace.workspace_root, "test.txt"), "rb") as f:
            assert f.read() == test_content

    def test_create_file_text_delegates_to_backend(self, workspace, temp_workspace):
        """Test that create_file_text delegates to the backend."""
        test_content = "Hello, World!"
        workspace.create_file_text("test.txt", test_content)

        # Verify file was created correctly
        with open(os.path.join(workspace.workspace_root, "test.txt"), "r", encoding="utf-8") as f:
            assert f.read() == test_content

    def test_delete_file_delegates_to_backend(self, workspace, temp_workspace):
        """Test that delete_file delegates to the backend."""
        test_file = os.path.join(workspace.workspace_root, "test.txt")
        with open(test_file, "w") as f:
            f.write("to be deleted")

        assert os.path.exists(test_file)
        workspace.delete_file("test.txt")
        assert not os.path.exists(test_file)

    def test_create_directory_delegates_to_backend(self, workspace):
        """Test that create_directory delegates to the backend."""
        workspace.create_directory("newdir")
        assert os.path.isdir(os.path.join(workspace.workspace_root, "newdir"))

    def test_delete_directory_delegates_to_backend(self, workspace, temp_workspace):
        """Test that delete_directory delegates to the backend."""
        # Create a directory to delete inside the workspace root
        test_dir = os.path.join(workspace.workspace_root, "todelete")
        os.makedirs(test_dir)

        assert os.path.exists(test_dir)
        workspace.delete_directory("todelete")
        assert not os.path.exists(test_dir)

    def test_list_directory_delegates_to_backend(self, workspace, temp_workspace):
        """Test that list_directory delegates to the backend."""
        # Create test content inside the workspace root
        test_dir = os.path.join(workspace.workspace_root, "testdir")
        os.makedirs(test_dir)
        with open(os.path.join(test_dir, "file.txt"), "w") as f:
            f.write("content")

        entries = workspace.list_directory("testdir")
        assert len(entries) == 1
        assert entries[0]["name"] == "file.txt"

    def test_file_exists_delegates_to_backend(self, workspace, temp_workspace):
        """Test that file_exists delegates to the backend."""
        test_file = os.path.join(workspace.workspace_root, "exists.txt")
        with open(test_file, "w") as f:
            f.write("content")

        assert workspace.file_exists("exists.txt") is True
        assert workspace.file_exists("nonexistent.txt") is False

    def test_directory_exists_delegates_to_backend(self, workspace, temp_workspace):
        """Test that directory_exists delegates to the backend."""
        test_dir = os.path.join(workspace.workspace_root, "existsdir")
        os.makedirs(test_dir)

        assert workspace.directory_exists("existsdir") is True
        assert workspace.directory_exists("nonexistentdir") is False

    def test_get_file_metadata_delegates_to_backend(self, workspace, temp_workspace):
        """Test that get_file_metadata delegates to the backend."""
        test_file = os.path.join(workspace.workspace_root, "metadata.txt")
        with open(test_file, "w") as f:
            f.write("content")

        metadata = workspace.get_file_metadata("metadata.txt")
        assert metadata["name"] == "metadata.txt"
        assert metadata["is_file"] is True

    def test_resolve_path_delegates_to_backend(self, workspace, temp_workspace):
        """Test that resolve_path delegates to the backend."""
        resolved = workspace.resolve_path("test.txt")
        expected = os.path.join(workspace.workspace_root, "test.txt")
        assert resolved == expected

    def test_workspace_root_property(self, workspace, temp_workspace):
        """Test the workspace_root property."""
        assert workspace.workspace_root == os.path.abspath(os.path.join(temp_workspace, "test_workspace"))

        # Test setting the property
        new_root = os.path.join(temp_workspace, "new_root")
        workspace.workspace_root = new_root
        assert workspace.workspace_root == os.path.abspath(new_root)

    def test_symlink_policy_configuration(self, temp_workspace):
        """Test that symlink policy can be configured."""
        workspace_neverspace = Workspace(
            workspace_root=os.path.join(temp_workspace, "test"),
            symlink_policy=SymlinkPolicy.NEVER_FOLLOW
        )
        assert workspace_neverspace._backend.symlink_policy == SymlinkPolicy.NEVER_FOLLOW

        workspace_followspace = Workspace(
            workspace_root=os.path.join(temp_workspace, "test"),
            symlink_policy=SymlinkPolicy.FOLLOW_IF_SAFE
        )
        assert workspace_followspace._backend.symlink_policy == SymlinkPolicy.FOLLOW_IF_SAFE


if __name__ == "__main__":
    pytest.main([__file__])