"""
Workspace manager providing a secure interface for file operations.
"""
from __future__ import annotations

import os
from typing import Any

from autonomous_agent.config.settings import Settings
from autonomous_agent.errors.base import ErrorCode

from .backend import FilesystemBackend, LocalFilesystemBackend, SymlinkPolicy
from .errors import WorkspaceError


class Workspace:
    """
    Workspace facade for file and directory operations within one bounded root.

    Relative and absolute paths are accepted, but every operation is delegated
    to a backend that normalizes the path, resolves links, and rejects paths
    outside the configured root. This boundary complements, but does not
    replace, OS sandboxing and command/tool policy controls.
    """

    def __init__(
        self,
        workspace_root: str | None = None,
        symlink_policy: SymlinkPolicy = SymlinkPolicy.FOLLOW_IF_SAFE,
        backend: FilesystemBackend | None = None,
    ):
        """
        Initialize the workspace manager.

        Args:
            workspace_root: The path to the workspace root. If None, uses the value from Settings.
            symlink_policy: Policy for handling symbolic links.
            backend: Optional backend to use. If None, creates a LocalFilesystemBackend.
        """
        # Get workspace root from settings if not provided
        if workspace_root is None:
            settings = Settings()
            workspace_root = settings.workspace_path

        # Convert to absolute path
        self.workspace_root = os.path.abspath(workspace_root)

        # Create backend if not provided
        if backend is None:
            self._backend = LocalFilesystemBackend(
                workspace_root=self.workspace_root,
                symlink_policy=symlink_policy
            )
        else:
            self._backend = backend
            self._backend.workspace_root = self.workspace_root

        # Ensure workspace root exists
        if not os.path.isdir(self.workspace_root):
            try:
                os.makedirs(self.workspace_root, exist_ok=True)
            except (PermissionError, OSError) as e:
                raise WorkspaceError(
                    f"Cannot create workspace root {self.workspace_root}: {e}",
                    error_code=ErrorCode.WORKSPACE_NOT_FOUND,
                ) from e

    # File reading operations
    def read_file(self, path: str) -> bytes:
        """
        Read file contents as bytes.

        Args:
            path: Path relative to workspace root or absolute path (will be confined).

        Returns:
            File contents as bytes.

        Raises:
            WorkspaceFileNotFoundError: If the file does not exist.
            WorkspaceIsADirectoryError: If the path points to a directory.
            WorkspaceSecurityError: If the path attempts to escape the workspace.
            WorkspaceIOError: If an I/O error occurs.
        """
        return self._backend.read_file(path)

    def read_file_text(self, path: str, encoding: str = "utf-8") -> str:
        """
        Read file contents as text.

        Args:
            path: Path relative to workspace root or absolute path (will be confined).
            encoding: Text encoding to use (default: utf-8).

        Returns:
            File contents as string.

        Raises:
            WorkspaceFileNotFoundError: If the file does not exist.
            WorkspaceIsADirectoryError: If the path points to a directory.
            WorkspaceSecurityError: If the path attempts to escape the workspace.
            WorkspaceIOError: If an I/O error occurs.
            UnicodeDecodeError: If the file cannot be decoded with the specified encoding.
        """
        content = self.read_file(path)
        return content.decode(encoding)

    # File writing operations
    def write_file(
        self,
        path: str,
        content: bytes,
        *,
        allow_overwrite: bool = False
    ) -> None:
        """
        Write file contents.

        Args:
            path: Path relative to workspace root or absolute path (will be confined).
            content: Content to write as bytes.
            allow_overwrite: Whether to overwrite an existing file (default: False).

        Raises:
            WorkspaceFileAlreadyExistsError: If the file exists and allow_overwrite is False.
            WorkspaceIsADirectoryError: If the path points to a directory.
            WorkspaceSecurityError: If the path attempts to escape the workspace.
            WorkspaceIOError: If an I/O error occurs.
        """
        self._backend.write_file(path, content, allow_overwrite=allow_overwrite)

    def write_file_text(
        self,
        path: str,
        content: str,
        *,
        encoding: str = "utf-8",
        allow_overwrite: bool = False
    ) -> None:
        """
        Write file contents as text.

        Args:
            path: Path relative to workspace root or absolute path (will be confined).
            content: Content to write as string.
            encoding: Text encoding to use (default: utf-8).
            allow_overwrite: Whether to overwrite an existing file (default: False).

        Raises:
            WorkspaceFileAlreadyExistsError: If the file exists and allow_overwrite is False.
            WorkspaceIsADirectoryError: If the path points to a directory.
            WorkspaceSecurityError: If the path attempts to escape the workspace.
            WorkspaceIOError: If an I/O error occurs.
        """
        encoded_content = content.encode(encoding)
        self.write_file(path, encoded_content, allow_overwrite=allow_overwrite)

    def create_file(self, path: str, content: bytes) -> None:
        """
        Create a new file; fails if file already exists.

        Args:
            path: Path relative to workspace root or absolute path (will be confined).
            content: Content to write as bytes.

        Raises:
            WorkspaceFileAlreadyExistsError: If the file already exists.
            WorkspaceIsADirectoryError: If the path points to a directory.
            WorkspaceSecurityError: If the path attempts to escape the workspace.
            WorkspaceIOError: If an I/O error occurs.
        """
        self._backend.create_file(path, content)

    def create_file_text(self, path: str, content: str, encoding: str = "utf-8") -> None:
        """
        Create a new text file; fails if file already exists.

        Args:
            path: Path relative to workspace root or absolute path (will be confined).
            content: Content to write as string.
            encoding: Text encoding to use (default: utf-8).

        Raises:
            WorkspaceFileAlreadyExistsError: If the file already exists.
            WorkspaceIsADirectoryError: If the path points to a directory.
            WorkspaceSecurityError: If the path attempts to escape the workspace.
            WorkspaceIOError: If an I/O error occurs.
        """
        encoded_content = content.encode(encoding)
        self._backend.create_file(path, encoded_content)

    # File deletion operations
    def delete_file(self, path: str) -> None:
        """
        Delete a file.

        Args:
            path: Path relative to workspace root or absolute path (will be confined).

        Raises:
            WorkspaceFileNotFoundError: If the file does not exist.
            WorkspaceIsADirectoryError: If the path points to a directory.
            WorkspaceRootDeletionError: If attempting to delete the workspace root.
            WorkspaceSecurityError: If the path attempts to escape the workspace.
            WorkspaceIOError: If an I/O error occurs.
        """
        self._backend.delete_file(path)

    # Directory operations
    def create_directory(
        self,
        path: str,
        *,
        parents: bool = False,
        exist_ok: bool = False
    ) -> None:
        """
        Create a directory.

        Args:
            path: Path relative to workspace root or absolute path (will be confined).
            parents: Whether to create parent directories (default: False).
            exist_ok: Whether to ignore if directory already exists (default: False).

        Raises:
            WorkspaceFileAlreadyExistsError: If the directory exists and exist_ok is False.
            WorkspaceFileAlreadyExistsError: If a file exists with the same name.
            WorkspaceSecurityError: If the path attempts to escape the workspace.
            WorkspaceIOError: If an I/O error occurs.
        """
        self._backend.create_directory(path, parents=parents, exist_ok=exist_ok)

    def delete_directory(self, path: str, *, recursive: bool = False) -> None:
        """
        Delete a directory.

        Args:
            path: Path relative to workspace root or absolute path (will be confined).
            recursive: Whether to delete directory contents recursively (default: False).

        Raises:
            WorkspaceFileNotFoundError: If the directory does not exist.
            WorkspaceNotADirectoryError: If the path points to a file.
            WorkspaceRootDeletionError: If attempting to delete the workspace root.
            WorkspaceIOError: If the directory is not empty and recursive is False.
            WorkspaceSecurityError: If the path attempts to escape the workspace.
            WorkspaceIOError: If an I/O error occurs.
        """
        self._backend.delete_directory(path, recursive=recursive)

    # Query operations
    def list_directory(self, path: str) -> list[dict[str, Any]]:
        """
        List directory entries.

        Args:
            path: Path relative to workspace root or absolute path (will be confined).

        Returns:
            List of dictionaries containing entry information.

        Raises:
            WorkspaceFileNotFoundError: If the directory does not exist.
            WorkspaceNotADirectoryError: If the path points to a file.
            WorkspaceSecurityError: If the path attempts to escape the workspace.
            WorkspaceIOError: If an I/O error occurs.
        """
        return self._backend.list_directory(path)

    def file_exists(self, path: str) -> bool:
        """
        Check if a file exists.

        Args:
            path: Path relative to workspace root or absolute path (will be confined).

        Returns:
            True if a file exists at the path, False otherwise.

        Note:
            Returns False for paths that would escape the workspace (for security).
        """
        return self._backend.file_exists(path)

    def directory_exists(self, path: str) -> bool:
        """
        Check if a directory exists.

        Args:
            path: Path relative to workspace root or absolute path (will be confined).

        Returns:
            True if a directory exists at the path, False otherwise.

        Note:
            Returns False for paths that would escape the workspace (for security).
        """
        return self._backend.directory_exists(path)

    def get_file_metadata(self, path: str) -> dict[str, Any]:
        """
        Get metadata for a file or directory.

        Args:
            path: Path relative to workspace root or absolute path (will be confined).

        Returns:
            Dictionary containing file metadata.

        Raises:
            WorkspaceFileNotFoundError: If the path does not exist.
            WorkspaceSecurityError: If the path attempts to escape the workspace.
            WorkspaceIOError: If an I/O error occurs.
        """
        return self._backend.get_file_metadata(path)

    # Properties
    @property
    def workspace_root(self) -> str:
        """Get the absolute path to the workspace root."""
        return self._workspace_root

    @workspace_root.setter
    def workspace_root(self, value: str) -> None:
        """Set the workspace root."""
        self._workspace_root = os.path.abspath(value)
        if hasattr(self, "_backend"):
            self._backend.workspace_root = self._workspace_root

    def resolve_path(self, path: str) -> str:
        """
        Resolve a path to its absolute form within the workspace.

        Args:
            path: Path to resolve (relative to workspace root or absolute).

        Returns:
            The absolute path confined to the workspace.

        Raises:
            WorkspaceSecurityError: If the path attempts to escape the workspace.
        """
        return self._backend._confine_path(path)