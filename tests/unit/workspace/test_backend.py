"""
Unit tests for the LocalFilesystemBackend.
"""
from __future__ import annotations

import os
import tempfile

import pytest

from autonomous_agent.workspace.backend import LocalFilesystemBackend, SymlinkPolicy
from autonomous_agent.workspace.errors import *


class TestLocalFilesystemBackend:
    """Test the LocalFilesystemBackend class."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def backend(self, temp_workspace):
        """Create a backend instance for testing."""
        return LocalFilesystemBackend(temp_workspace)

    def test_init_creates_workspace_if_not_exists(self, temp_workspace):
        """Test that backend initialization creates workspace if it doesn't exist."""
        workspace_path = os.path.join(temp_workspace, "new_workspace")
        assert not os.path.exists(workspace_path)

        backend = LocalFilesystemBackend(workspace_path)
        assert os.path.isdir(workspace_path)
        assert backend.workspace_root == os.path.abspath(workspace_path)

    def test_init_fails_if_workspace_is_file(self, temp_workspace):
        """Test that backend initialization fails if workspace path is a file."""
        workspace_path = os.path.join(temp_workspace, "file.txt")
        with open(workspace_path, "w") as f:
            f.write("test")

        with pytest.raises(WorkspaceError, match="does not exist or is not a directory"):
            LocalFilesystemBackend(workspace_path)

    def test_confine_path_basic(self, backend, temp_workspace):
        """Test basic path confinement."""
        # Test relative path
        confined = backend._confine_path("test.txt")
        expected = os.path.join(temp_workspace, "test.txt")
        assert confined == expected

        # Test subdirectory path
        confined = backend._confine_path("subdir/test.txt")
        expected = os.path.join(temp_workspace, "subdir", "test.txt")
        assert confined == expected

    def test_confine_path_absolute(self, backend, temp_workspace):
        """Test confinement of absolute paths."""
        # Test absolute path within workspace
        abs_path = os.path.join(temp_workspace, "test.txt")
        confined = backend._confine_path(abs_path)
        assert confined == abs_path

        # Test absolute path outside workspace should raise error
        outside_path = "/tmp/outside.txt"
        with pytest.raises(WorkspaceSecurityError):
            backend._confine_path(outside_path)

    def test_confine_path_traversal_attempt(self, backend):
        """Test that path traversal attempts are blocked."""
        with pytest.raises(WorkspaceSecurityError):
            backend._confine_path("../../etc/passwd")

        with pytest.raises(WorkspaceSecurityError):
            backend._confine_path("subdir/../../outside.txt")

    def test_confine_path_empty(self, backend):
        """Test that empty paths resolve to workspace root."""
        result = backend._confine_path("")
        assert result == backend.workspace_root

    def test_string_symlink_policy_is_normalized(self, temp_workspace):
        """Test that string policies remain compatible with the public API."""
        backend = LocalFilesystemBackend(temp_workspace, "never_follow")
        assert backend.symlink_policy is SymlinkPolicy.NEVER_FOLLOW

    def test_confine_path_symlinks_never_follow(self, temp_workspace):
        """Test symlink handling with NEVER_FOLLOW policy."""
        # Create a symlink inside workspace pointing outside
        workspace_dir = os.path.join(temp_workspace, "workspace")
        os.makedirs(workspace_dir)

        outside_file = os.path.join(temp_workspace, "outside.txt")
        with open(outside_file, "w") as f:
            f.write("outside")

        symlink_path = os.path.join(workspace_dir, "link_to_outside")
        try:
            os.symlink(outside_file, symlink_path)
        except OSError as e:
            if e.winerror == 1314:
                pytest.skip("Skipping symlink test because required privilege is not held")
            else:
                raise

        backend = LocalFilesystemBackend(workspace_dir, SymlinkPolicy.NEVER_FOLLOW)

        # Should raise error when trying to access the symlink
        with pytest.raises(WorkspaceSecurityError, match="Symlink encountered"):
            backend._confine_path("link_to_outside")

    def test_confine_path_symlinks_follow_if_safe_within(self, temp_workspace):
        """Test symlink handling with FOLLOW_IF_SAFE policy for safe symlinks."""
        workspace_dir = os.path.join(temp_workspace, "workspace")
        os.makedirs(workspace_dir)

        # Create a symlink pointing to a file within workspace
        target_file = os.path.join(workspace_dir, "target.txt")
        with open(target_file, "w") as f:
            f.write("target")

        symlink_path = os.path.join(workspace_dir, "link_to_target")
        try:
            os.symlink(target_file, symlink_path)
        except OSError as e:
            if e.winerror == 1314:
                pytest.skip("Skipping symlink test because required privilege is not held")
            else:
                raise

        backend = LocalFilesystemBackend(workspace_dir, SymlinkPolicy.FOLLOW_IF_SAFE)

        # Should allow access and return the real path
        confined = backend._confine_path("link_to_target")
        assert confined == os.path.abspath(target_file)

    def test_confine_path_symlinks_follow_if_safe_outside_raises(self, temp_workspace):
        """Test symlink handling with FOLLOW_IF_SAFE policy for unsafe symlinks."""
        workspace_dir = os.path.join(temp_workspace, "workspace")
        os.makedirs(workspace_dir)

        # Create a symlink pointing to a file outside workspace
        outside_file = os.path.join(temp_workspace, "outside.txt")
        with open(outside_file, "w") as f:
            f.write("outside")

        symlink_path = os.path.join(workspace_dir, "link_to_outside")
        try:
            os.symlink(outside_file, symlink_path)
        except OSError as e:
            if e.winerror == 1314:
                pytest.skip("Skipping symlink test because required privilege is not held")
            else:
                raise

        backend = LocalFilesystemBackend(workspace_dir, SymlinkPolicy.FOLLOW_IF_SAFE)

        # Should raise error when trying to access the symlink
        with pytest.raises(WorkspaceSecurityError):
            backend._confine_path("link_to_outside")

    def test_read_file_success(self, backend, temp_workspace):
        """Test successful file reading."""
        test_file = os.path.join(temp_workspace, "test.txt")
        test_content = b"Hello, World!"
        with open(test_file, "wb") as f:
            f.write(test_content)

        content = backend.read_file("test.txt")
        assert content == test_content

    def test_read_file_not_found(self, backend):
        """Test reading a non-existent file."""
        with pytest.raises(WorkspaceFileNotFoundError):
            backend.read_file("nonexistent.txt")

    def test_read_file_is_directory(self, backend, temp_workspace):
        """Test reading a directory as if it were a file."""
        subdir = os.path.join(temp_workspace, "subdir")
        os.makedirs(subdir)

        with pytest.raises(WorkspaceIsADirectoryError):
            backend.read_file("subdir")

    def test_write_file_success(self, backend, temp_workspace):
        """Test successful file writing."""
        test_content = b"Hello, World!"
        backend.write_file("test.txt", test_content)

        # Verify file was written correctly
        with open(os.path.join(temp_workspace, "test.txt"), "rb") as f:
            assert f.read() == test_content

    def test_write_file_creates_parent_directories(self, backend):
        """Test that writing a file creates parent directories."""
        test_content = b"Hello, World!"
        backend.write_file("subdir/nested/test.txt", test_content)

        # Verify file and directories were created
        assert os.path.isfile(os.path.join(backend.workspace_root, "subdir", "nested", "test.txt"))
        assert os.path.isdir(os.path.join(backend.workspace_root, "subdir"))
        assert os.path.isdir(os.path.join(backend.workspace_root, "subdir", "nested"))

    def test_write_file_no_overwrite_by_default(self, backend, temp_workspace):
        """Test that writing does not overwrite by default."""
        test_file = os.path.join(temp_workspace, "test.txt")
        with open(test_file, "w") as f:
            f.write("original")

        with pytest.raises(WorkspaceFileAlreadyExistsError):
            backend.write_file("test.txt", b"new content")

        # Verify original content is unchanged
        with open(test_file, "r") as f:
            assert f.read() == "original"

    def test_write_file_with_overwrite(self, backend, temp_workspace):
        """Test that writing with allow_overwrite=True overwrites the file."""
        test_file = os.path.join(temp_workspace, "test.txt")
        with open(test_file, "w") as f:
            f.write("original")

        backend.write_file("test.txt", b"new content", allow_overwrite=True)

        # Verify content was overwritten
        with open(test_file, "rb") as f:
            assert f.read() == b"new content"

    def test_write_file_atomicity(self, backend, temp_workspace):
        """Test that file writing is atomic (uses temporary file)."""
        test_file = os.path.join(temp_workspace, "test.txt")

        # Write a large file to make timing easier to test
        large_content = b"x" * 10000
        backend.write_file("test.txt", large_content)

        # Verify file exists and has correct content
        assert os.path.isfile(test_file)
        with open(test_file, "rb") as f:
            assert f.read() == large_content

        # Verify no temporary file remains
        temp_file = test_file + ".tmp"
        assert not os.path.exists(temp_file)

    def test_create_file_success(self, backend, temp_workspace):
        """Test successful file creation."""
        test_content = b"Hello, World!"
        backend.create_file("test.txt", test_content)

        # Verify file was created correctly
        with open(os.path.join(temp_workspace, "test.txt"), "rb") as f:
            assert f.read() == test_content

    def test_create_file_fails_if_exists(self, backend, temp_workspace):
        """Test that creating a file fails if it already exists."""
        test_file = os.path.join(temp_workspace, "test.txt")
        with open(test_file, "w") as f:
            f.write("existing")

        with pytest.raises(WorkspaceFileAlreadyExistsError):
            backend.create_file("test.txt", b"new content")

    def test_delete_file_success(self, backend, temp_workspace):
        """Test successful file deletion."""
        test_file = os.path.join(temp_workspace, "test.txt")
        with open(test_file, "w") as f:
            f.write("to be deleted")

        assert os.path.exists(test_file)
        backend.delete_file("test.txt")
        assert not os.path.exists(test_file)

    def test_delete_file_not_found(self, backend):
        """Test deleting a non-existent file."""
        with pytest.raises(WorkspaceFileNotFoundError):
            backend.delete_file("nonexistent.txt")

    def test_delete_file_is_directory(self, backend, temp_workspace):
        """Test deleting a directory as if it were a file."""
        subdir = os.path.join(temp_workspace, "subdir")
        os.makedirs(subdir)

        with pytest.raises(WorkspaceIsADirectoryError):
            backend.delete_file("subdir")

    def test_delete_file_prevents_root_deletion(self, backend):
        """Test that deleting the workspace root is prevented."""
        with pytest.raises(WorkspaceRootDeletionError):
            backend.delete_file(".")

        with pytest.raises(WorkspaceRootDeletionError):
            backend.delete_file("")

    def test_create_directory_success(self, backend):
        """Test successful directory creation."""
        backend.create_directory("newdir")
        assert os.path.isdir(os.path.join(backend.workspace_root, "newdir"))

        # Test with parents
        backend.create_directory("parents/deep/dir", parents=True)
        assert os.path.isdir(os.path.join(backend.workspace_root, "parents", "deep", "dir"))

    def test_create_directory_exists_ok(self, backend):
        """Test creating a directory that already exists with exist_ok=True."""
        backend.create_directory("existing")
        # Should not raise
        backend.create_directory("existing", exist_ok=True)

        # But should raise if exist_ok=False
        with pytest.raises(WorkspaceFileAlreadyExistsError):
            backend.create_directory("existing", exist_ok=False)

    def test_create_directory_file_conflict(self, backend, temp_workspace):
        """Test creating a directory where a file exists with the same name."""
        test_file = os.path.join(temp_workspace, "conflict")
        with open(test_file, "w") as f:
            f.write("file")

        with pytest.raises(WorkspaceFileAlreadyExistsError):
            backend.create_directory("conflict")

    def test_delete_directory_success(self, backend, temp_workspace):
        """Test successful directory deletion."""
        # Create an empty directory
        test_dir = os.path.join(temp_workspace, "todelete")
        os.makedirs(test_dir)

        assert os.path.exists(test_dir)
        backend.delete_directory("todelete")
        assert not os.path.exists(test_dir)

    def test_delete_directory_recursive(self, backend, temp_workspace):
        """Test recursive directory deletion."""
        # Create a nested directory structure
        test_dir = os.path.join(temp_workspace, "todelete")
        os.makedirs(os.path.join(test_dir, "subdir", "deep"))
        test_file = os.path.join(test_dir, "subdir", "deep", "file.txt")
        with open(test_file, "w") as f:
            f.write("content")

        assert os.path.exists(test_dir)
        backend.delete_directory("todelete", recursive=True)
        assert not os.path.exists(test_dir)

    def test_delete_directory_not_empty_fails_without_recursive(self, backend, temp_workspace):
        """Test that deleting a non-empty directory fails without recursive=True."""
        test_dir = os.path.join(temp_workspace, "todelete")
        os.makedirs(test_dir)
        test_file = os.path.join(test_dir, "file.txt")
        with open(test_file, "w") as f:
            f.write("content")

        with pytest.raises(WorkspaceIOError, match="Directory is not empty"):
            backend.delete_directory("todelete")

    def test_delete_directory_not_found(self, backend):
        """Test deleting a non-existent directory."""
        with pytest.raises(WorkspaceFileNotFoundError):
            backend.delete_directory("nonexistent")

    def test_delete_directory_is_file(self, backend, temp_workspace):
        """Test deleting a file as if it were a directory."""
        test_file = os.path.join(temp_workspace, "file.txt")
        with open(test_file, "w") as f:
            f.write("content")

        with pytest.raises(WorkspaceNotADirectoryError):
            backend.delete_directory("file.txt")

    def test_delete_directory_prevents_root_deletion(self, backend):
        """Test that deleting the workspace root is prevented."""
        with pytest.raises(WorkspaceRootDeletionError):
            backend.delete_directory(".")

        with pytest.raises(WorkspaceRootDeletionError):
            backend.delete_directory("", recursive=True)

    def test_list_directory_success(self, backend, temp_workspace):
        """Test successful directory listing."""
        # Create test files and directories
        test_dir = os.path.join(temp_workspace, "testdir")
        os.makedirs(test_dir)

        # Create files
        with open(os.path.join(test_dir, "file1.txt"), "w") as f:
            f.write("content1")
        with open(os.path.join(test_dir, "file2.txt"), "w") as f:
            f.write("content2")

        # Create subdirectory
        os.makedirs(os.path.join(test_dir, "subdir"))

        # Create symlink
        try:
            os.symlink("file1.txt", os.path.join(test_dir, "link_to_file1"))
        except OSError as e:
            if e.winerror == 1314:
                pytest.skip("Skipping symlink test because required privilege is not held")
            else:
                raise

        # List directory
        entries = backend.list_directory("testdir")

        # Should have 4 entries: 2 files, 1 directory, 1 symlink
        assert len(entries) == 4

        # Check that we can find each entry by name
        names = {entry["name"] for entry in entries}
        assert names == {"file1.txt", "file2.txt", "subdir", "link_to_file1"}

        # Check file entries
        file_entries = [e for e in entries if e["is_file"]]
        assert len(file_entries) == 2

        # Check directory entry
        dir_entries = [e for e in entries if e["is_directory"]]
        assert len(dir_entries) == 1
        assert dir_entries[0]["name"] == "subdir"

        # Check symlink entry
        symlink_entries = [e for e in entries if e["is_symlink"]]
        assert len(symlink_entries) == 1
        assert symlink_entries[0]["name"] == "link_to_file1"

    def test_list_directory_not_found(self, backend):
        """Test listing a non-existent directory."""
        with pytest.raises(WorkspaceFileNotFoundError):
            backend.list_directory("nonexistent")

    def test_list_directory_is_file(self, backend, temp_workspace):
        """Test listing a file as if it were a directory."""
        test_file = os.path.join(temp_workspace, "file.txt")
        with open(test_file, "w") as f:
            f.write("content")

        with pytest.raises(WorkspaceNotADirectoryError):
            backend.list_directory("file.txt")

    def test_file_exists_true(self, backend, temp_workspace):
        """Test file_exists returns True for existing files."""
        test_file = os.path.join(temp_workspace, "exists.txt")
        with open(test_file, "w") as f:
            f.write("content")

        assert backend.file_exists("exists.txt") is True

    def test_file_exists_false(self, backend):
        """Test file_exists returns False for non-existent files."""
        assert backend.file_exists("nonexistent.txt") is False

    def test_file_exists_outside_workspace_returns_false(self, backend, temp_workspace):
        """Test that file_exists returns False for paths outside workspace (security)."""
        # Create a file outside the workspace
        outside_file = os.path.join(temp_workspace, "outside.txt")
        with open(outside_file, "w") as f:
            f.write("content")

        # Even though the file exists outside, it should return False for security
        # Note: This depends on how _confine_path is implemented
        # With our implementation, it should raise WorkspaceSecurityError which we catch and return False
        assert backend.file_exists("../outside.txt") is False

    def test_directory_exists_true(self, backend, temp_workspace):
        """Test directory_exists returns True for existing directories."""
        test_dir = os.path.join(temp_workspace, "existsdir")
        os.makedirs(test_dir)

        assert backend.directory_exists("existsdir") is True

    def test_directory_exists_false(self, backend):
        """Test directory_exists returns False for non-existent directories."""
        assert backend.directory_exists("nonexistentdir") is False

    def test_directory_exists_outside_workspace_returns_false(self, backend, temp_workspace):
        """Test that directory_exists returns False for paths outside workspace (security)."""
        # Create a directory outside the workspace
        outside_dir = os.path.join(temp_workspace, "outside")
        os.makedirs(outside_dir)

        # Even though the directory exists outside, it should return False for security
        assert backend.directory_exists("../outside") is False

    def test_get_file_metadata_success(self, backend, temp_workspace):
        """Test successful metadata retrieval."""
        test_file = os.path.join(temp_workspace, "metadata.txt")
        test_content = b"Hello, World!"
        with open(test_file, "wb") as f:
            f.write(test_content)

        metadata = backend.get_file_metadata("metadata.txt")

        assert metadata["name"] == "metadata.txt"
        assert metadata["is_file"] is True
        assert metadata["is_directory"] is False
        assert metadata["size"] == len(test_content)
        assert "modified" in metadata
        assert "created" in metadata
        assert "permissions" in metadata

    def test_get_file_metadata_directory(self, backend, temp_workspace):
        """Test metadata retrieval for a directory."""
        test_dir = os.path.join(temp_workspace, "metadatadir")
        os.makedirs(test_dir)

        metadata = backend.get_file_metadata("metadatadir")

        assert metadata["name"] == "metadatadir"
        assert metadata["is_file"] is False
        assert metadata["is_directory"] is True

    def test_get_file_metadata_not_found(self, backend):
        """Test metadata retrieval for non-existent path."""
        with pytest.raises(WorkspaceFileNotFoundError):
            backend.get_file_metadata("nonexistent.txt")

    def test_get_file_metadata_outside_workspace(self, backend, temp_workspace):
        """Test that get_file_metadata raises error for paths outside workspace."""
        outside_file = os.path.join(temp_workspace, "outside.txt")
        with open(outside_file, "w") as f:
            f.write("content")

        with pytest.raises(WorkspaceSecurityError):
            backend.get_file_metadata("../outside.txt")


if __name__ == "__main__":
    pytest.main([__file__])