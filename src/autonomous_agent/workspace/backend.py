"""
Filesystem backend abstraction for workspace operations.
"""
from __future__ import annotations

import os
import shutil
import tempfile
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any


class SymlinkPolicy(Enum):
    """Policy for handling symlinks during path resolution."""
    NEVER_FOLLOW = "never_follow"
    FOLLOW_IF_SAFE = "follow_if_safe"
    ALLOW_ALL = "allow_all"


class FilesystemBackend(ABC):
    """Abstract filesystem API confined to one configured workspace root."""

    def __init__(
        self,
        workspace_root: str,
        symlink_policy: SymlinkPolicy = SymlinkPolicy.FOLLOW_IF_SAFE,
    ):
        self.workspace_root = os.path.abspath(workspace_root)
        self.symlink_policy = SymlinkPolicy(symlink_policy)

        # Ensure workspace root exists
        if not os.path.exists(self.workspace_root):
            os.makedirs(self.workspace_root)
        elif not os.path.isdir(self.workspace_root):
            from autonomous_agent.errors.base import ErrorCode
            from autonomous_agent.workspace.errors import WorkspaceError
            raise WorkspaceError(
                f"Workspace root {self.workspace_root} does not exist or is not a directory",
                error_code=ErrorCode.WORKSPACE_INVALID,
            )

    @abstractmethod
    def read_file(self, path: str) -> bytes:
        """Read a file and return its contents as bytes."""
        raise NotImplementedError

    @abstractmethod
    def write_file(self, path: str, content: bytes, *, allow_overwrite: bool = False) -> None:
        """Write bytes to a file."""
        raise NotImplementedError

    @abstractmethod
    def create_file(self, path: str, content: bytes) -> None:
        """Create a new file with the given content."""
        raise NotImplementedError

    @abstractmethod
    def delete_file(self, path: str) -> None:
        """Delete a file."""
        raise NotImplementedError

    @abstractmethod
    def create_directory(
        self,
        path: str,
        *,
        parents: bool = False,
        exist_ok: bool = False,
    ) -> None:
        """Create a directory."""
        raise NotImplementedError

    @abstractmethod
    def delete_directory(self, path: str, *, recursive: bool = False) -> None:
        """Delete a directory."""
        raise NotImplementedError

    @abstractmethod
    def list_directory(self, path: str) -> list[dict[str, Any]]:
        """List contents of a directory."""
        raise NotImplementedError

    @abstractmethod
    def file_exists(self, path: str) -> bool:
        """Check if a file exists."""
        raise NotImplementedError

    @abstractmethod
    def directory_exists(self, path: str) -> bool:
        """Check if a directory exists."""
        raise NotImplementedError

    @abstractmethod
    def get_file_metadata(self, path: str) -> dict[str, Any]:
        """Get metadata for a file or directory."""
        raise NotImplementedError

    def resolve_path(self, path: str) -> str:
        """Resolve a path to an absolute path within the workspace.

        This is a convenience method that delegates to _confine_path.
        """
        return self._confine_path(path)

    @abstractmethod
    def _confine_path(self, user_path: str) -> str:
        """Confine a user-provided path to the workspace root.

        This method should:
        1. Convert relative paths to absolute paths relative to workspace root
        2. Validate that the resulting path is within the workspace root
        3. Handle symlinks according to the symlink policy
        4. Return the confined absolute path

        Args:
            user_path: A path provided by the user (may be relative or absolute)

        Returns:
            The confined absolute path

        Raises:
            WorkspaceSecurityError: If the path attempts to escape the workspace
            WorkspaceError: For other workspace-related errors
        """
        raise NotImplementedError


class LocalFilesystemBackend(FilesystemBackend):
    """Local backend with normalized, workspace-confined filesystem access.

    Existing symlinks and Windows junctions are resolved before the boundary
    check. The implementation is not an OS-level sandbox and does not provide
    complete protection from a concurrent attacker changing paths between
    validation and the underlying filesystem operation.
    """

    def _confine_path(self, user_path: str) -> str:
        """Confine a user-provided path to the workspace root."""
        # Convert to absolute path relative to workspace root if needed
        if os.path.isabs(user_path):
            target_path = user_path
        else:
            target_path = os.path.join(self.workspace_root, user_path)

        # Normalize the path
        target_path = os.path.normpath(target_path)

        # Handle symlinks according to policy
        if self.symlink_policy == SymlinkPolicy.NEVER_FOLLOW:
            # Check each component for symlinks
            parts = target_path.split(os.sep)
            # Skip empty parts (e.g., leading slash on Unix)
            for i, part in enumerate(parts):
                if not part:
                    continue
                # Build the path up to this component
                if os.path.isabs(target_path):
                    partial = os.path.join(os.path.sep, *parts[:i + 1]) if i > 0 else os.path.sep
                else:
                    partial = os.path.join(self.workspace_root, *parts[:i + 1])
                if os.path.islink(partial):
                    from autonomous_agent.errors.base import ErrorCode
                    from autonomous_agent.workspace.errors import WorkspaceSecurityError
                    raise WorkspaceSecurityError(
                        f"Symlink encountered in path at {partial} (symlink following disabled)",
                        error_code=ErrorCode.WORKSPACE_SYMLINK_ESCAPE,
                    )
            real_path = target_path
        elif self.symlink_policy == SymlinkPolicy.FOLLOW_IF_SAFE:
            try:
                real_path = os.path.realpath(target_path)
            except (OSError, RuntimeError) as e:
                from autonomous_agent.errors.base import ErrorCode
                from autonomous_agent.workspace.errors import WorkspaceSecurityError
                raise WorkspaceSecurityError(
                    f"Cannot resolve symlinks in path {user_path}: {e}",
                    error_code=ErrorCode.WORKSPACE_SYMLINK_ESCAPE,
                ) from e
        else:  # ALLOW_ALL
            try:
                real_path = os.path.realpath(target_path)
            except (OSError, RuntimeError) as e:
                from autonomous_agent.errors.base import ErrorCode
                from autonomous_agent.workspace.errors import WorkspaceSecurityError
                raise WorkspaceSecurityError(
                    f"Cannot resolve symlinks in path {user_path}: {e}",
                    error_code=ErrorCode.WORKSPACE_SYMLINK_ESCAPE,
                ) from e

        # Ensure the resolved path is within the workspace root
        # Use commonpath to avoid issues with trailing separators
        try:
            common = os.path.commonpath([self.workspace_root, real_path])
        except ValueError:
            # This can happen if one of the paths is empty (should not happen)
            from autonomous_agent.errors.base import ErrorCode
            from autonomous_agent.workspace.errors import WorkspaceSecurityError
            raise WorkspaceSecurityError(
                f"Path {user_path} resolves outside workspace root",
                error_code=ErrorCode.WORKSPACE_PATH_OUTSIDE,
            )

        if os.path.normcase(common) != os.path.normcase(self.workspace_root):
            from autonomous_agent.errors.base import ErrorCode
            from autonomous_agent.workspace.errors import WorkspaceSecurityError
            raise WorkspaceSecurityError(
                f"Path {user_path} resolves outside workspace root",
                error_code=ErrorCode.WORKSPACE_PATH_OUTSIDE,
            )

        return real_path

    def read_file(self, path: str) -> bytes:
        """Read a file and return its contents as bytes."""
        confined_path = self._confine_path(path)
        try:
            with open(confined_path, 'rb') as f:
                return f.read()
        except FileNotFoundError:
            from autonomous_agent.workspace.errors import WorkspaceFileNotFoundError
            raise WorkspaceFileNotFoundError(f"File not found: {path}")
        except IsADirectoryError:
            from autonomous_agent.workspace.errors import WorkspaceIsADirectoryError
            raise WorkspaceIsADirectoryError(f"Path is a directory: {path}")
        except PermissionError as e:
            from autonomous_agent.workspace.errors import (
                WorkspaceIOError,
                WorkspaceIsADirectoryError,
            )
            if os.path.isdir(confined_path):
                raise WorkspaceIsADirectoryError(f"Path is a directory: {path}")
            else:
                raise WorkspaceIOError(f"Permission denied reading file {path}: {e}") from e
        except OSError as e:
            from autonomous_agent.workspace.errors import WorkspaceIOError
            raise WorkspaceIOError(f"Error reading file {path}: {e}") from e

    def write_file(self, path: str, content: bytes, *, allow_overwrite: bool = False) -> None:
        """Write bytes to a file using atomic write."""
        confined_path = self._confine_path(path)

        # Check if file exists and we don't allow overwrite
        if not allow_overwrite and os.path.exists(confined_path):
            from autonomous_agent.workspace.errors import (
                WorkspaceFileAlreadyExistsError,
            )
            raise WorkspaceFileAlreadyExistsError(f"File already exists: {path}")

        # Check if parent is a file (not a directory)
        parent_dir = os.path.dirname(confined_path)
        if parent_dir and os.path.exists(parent_dir) and not os.path.isdir(parent_dir):
            from autonomous_agent.workspace.errors import WorkspaceNotADirectoryError
            raise WorkspaceNotADirectoryError(f"Parent path is not a directory: {parent_dir}")

        # Create parent directories if needed
        parent_dir = os.path.dirname(confined_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir)

        # Perform atomic write using temporary file
        try:
            with tempfile.NamedTemporaryFile(
                dir=parent_dir or self.workspace_root,
                delete=False
            ) as tmp_file:
                tmp_file.write(content)
                tmp_path = tmp_file.name

            # Atomic rename
            os.replace(tmp_path, confined_path)
        except Exception:
            # Clean up temp file on error
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
            raise

    def create_file(self, path: str, content: bytes) -> None:
        """Create a new file with the given content."""
        # This is essentially write_file with allow_overwrite=False
        self.write_file(path, content, allow_overwrite=False)

    def delete_file(self, path: str) -> None:
        """Delete a file."""
        confined_path = self._confine_path(path)

        try:
            # Prevent deletion of workspace root
            if os.path.samefile(confined_path, self.workspace_root):
                from autonomous_agent.workspace.errors import WorkspaceRootDeletionError
                raise WorkspaceRootDeletionError("Cannot delete workspace root directory")

            os.remove(confined_path)
        except FileNotFoundError:
            from autonomous_agent.workspace.errors import WorkspaceFileNotFoundError
            raise WorkspaceFileNotFoundError(f"File not found: {path}")
        except IsADirectoryError:
            from autonomous_agent.workspace.errors import WorkspaceIsADirectoryError
            raise WorkspaceIsADirectoryError(f"Path is a directory: {path}")
        except PermissionError as e:
            from autonomous_agent.workspace.errors import (
                WorkspaceIOError,
                WorkspaceIsADirectoryError,
            )
            if os.path.isdir(confined_path):
                raise WorkspaceIsADirectoryError(f"Path is a directory: {path}")
            else:
                raise WorkspaceIOError(f"Permission denied deleting file {path}: {e}") from e
        except OSError as e:
            from autonomous_agent.workspace.errors import WorkspaceIOError
            raise WorkspaceIOError(f"Error deleting file {path}: {e}") from e

    def create_directory(self, path: str, *, parents: bool = False, exist_ok: bool = False) -> None:
        """Create a directory."""
        confined_path = self._confine_path(path)

        try:
            if parents:
                os.makedirs(confined_path, exist_ok=exist_ok)
            else:
                if exist_ok:
                    if not os.path.exists(confined_path):
                        os.mkdir(confined_path)
                else:
                    os.mkdir(confined_path)
        except FileExistsError:
            if not exist_ok:
                # Check if it's actually a file
                if os.path.isfile(confined_path):
                    from autonomous_agent.workspace.errors import (
                        WorkspaceFileAlreadyExistsError,
                    )
                    raise WorkspaceFileAlreadyExistsError(f"File already exists: {path}")
                else:
                    # It's already a directory, which is not ok when exist_ok=False
                    from autonomous_agent.workspace.errors import (
                        WorkspaceFileAlreadyExistsError,
                    )
                    raise WorkspaceFileAlreadyExistsError(f"File already exists: {path}")
            # If exist_ok is True, we do nothing (already handled by os.makedirs or the check above)
        except PermissionError as e:
            from autonomous_agent.workspace.errors import WorkspaceIOError
            raise WorkspaceIOError(f"Permission denied creating directory {path}: {e}") from e
        except OSError as e:
            from autonomous_agent.workspace.errors import WorkspaceIOError
            raise WorkspaceIOError(f"Error creating directory {path}: {e}") from e

    def delete_directory(self, path: str, *, recursive: bool = False) -> None:
        """Delete a directory."""
        from autonomous_agent.workspace.errors import (
            WorkspaceFileNotFoundError,
            WorkspaceIOError,
            WorkspaceNotADirectoryError,
        )
        confined_path = self._confine_path(path)

        # Prevent deletion of workspace root
        try:
            if os.path.samefile(confined_path, self.workspace_root):
                from autonomous_agent.workspace.errors import WorkspaceRootDeletionError
                raise WorkspaceRootDeletionError("Cannot delete workspace root directory")
        except FileNotFoundError:
            # If the path doesn't exist, it's certainly not the workspace root
            pass

        try:
            if recursive:
                shutil.rmtree(confined_path)
            else:
                os.rmdir(confined_path)
        except FileNotFoundError:
            raise WorkspaceFileNotFoundError(f"Directory not found: {path}")
        except NotADirectoryError:
            raise WorkspaceNotADirectoryError(f"Path is not a directory: {path}")
        except PermissionError as e:
            raise WorkspaceIOError(f"Permission denied deleting directory {path}: {e}") from e
        except OSError as e:
            from autonomous_agent.workspace.errors import WorkspaceIOError
            raise WorkspaceIOError(f"Directory is not empty: {path}") from e

    def list_directory(self, path: str) -> list[dict[str, Any]]:
        """List contents of a directory."""
        confined_path = self._confine_path(path)

        try:
            entries = []
            for entry in os.scandir(confined_path):
                stat = entry.stat()
                entries.append({
                    "name": entry.name,
                    "path": os.path.join(path, entry.name),
                    "is_file": entry.is_file(),
                    "is_directory": entry.is_dir(),
                    "is_symlink": entry.is_symlink(),
                    "size": stat.st_size if entry.is_file() else 0,
                    "modified": stat.st_mtime,
                    "created": stat.st_ctime,
                    "permissions": stat.st_mode,
                })
            return entries
        except FileNotFoundError:
            from autonomous_agent.workspace.errors import WorkspaceFileNotFoundError
            raise WorkspaceFileNotFoundError(f"Directory not found: {path}")
        except NotADirectoryError:
            from autonomous_agent.workspace.errors import WorkspaceNotADirectoryError
            raise WorkspaceNotADirectoryError(f"Path is not a directory: {path}")
        except PermissionError as e:
            from autonomous_agent.workspace.errors import WorkspaceIOError
            raise WorkspaceIOError(f"Permission denied listing directory {path}: {e}") from e
        except OSError as e:
            from autonomous_agent.workspace.errors import WorkspaceIOError
            raise WorkspaceIOError(f"Error listing directory {path}: {e}") from e

    def file_exists(self, path: str) -> bool:
        """Check if a file exists."""
        from autonomous_agent.workspace.errors import WorkspaceSecurityError
        try:
            confined_path = self._confine_path(path)
            return os.path.isfile(confined_path)
        except WorkspaceSecurityError:
            return False

    def directory_exists(self, path: str) -> bool:
        """Check if a directory exists."""
        from autonomous_agent.workspace.errors import WorkspaceSecurityError
        try:
            confined_path = self._confine_path(path)
            return os.path.isdir(confined_path)
        except WorkspaceSecurityError:
            return False

    def get_file_metadata(self, path: str) -> dict[str, Any]:
        """Get metadata for a file or directory."""
        confined_path = self._confine_path(path)

        try:
            stat = os.stat(confined_path)
            return {
                "name": os.path.basename(confined_path),
                "path": path,
                "is_file": os.path.isfile(confined_path),
                "is_directory": os.path.isdir(confined_path),
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "created": stat.st_ctime,
                "permissions": stat.st_mode,
            }
        except FileNotFoundError:
            from autonomous_agent.workspace.errors import WorkspaceFileNotFoundError
            raise WorkspaceFileNotFoundError(f"File not found: {path}")
        except PermissionError as e:
            from ..errors import WorkspaceIOError
            raise WorkspaceIOError(f"Permission denied accessing file {path}: {e}") from e
        except OSError as e:
            from ..errors import WorkspaceIOError
            raise WorkspaceIOError(f"Error accessing file {path}: {e}") from e