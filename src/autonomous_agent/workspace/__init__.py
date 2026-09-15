"""Workspace subsystem for the Autonomous Coding Agent."""
from .backend import FilesystemBackend, LocalFilesystemBackend, SymlinkPolicy
from .errors import *
from .manager import Workspace

__all__ = [
    "FilesystemBackend",
    "LocalFilesystemBackend",
    "SymlinkPolicy",
    "Workspace",
    "WorkspaceError",
    "WorkspaceFileAlreadyExistsError",
    "WorkspaceFileNotFoundError",
    "WorkspaceIOError",
    "WorkspaceIsADirectoryError",
    "WorkspaceNotADirectoryError",
    "WorkspaceRootDeletionError",
    "WorkspaceSecurityError",
]