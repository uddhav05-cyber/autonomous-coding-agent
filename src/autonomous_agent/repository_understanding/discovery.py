"""
Repository Discovery Module for identifying repository boundaries and structure.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

from autonomous_agent.workspace import Workspace


@dataclass
class RepositoryMetadata:
    """Metadata about the discovered repository."""
    root_path: Path
    is_git_repo: bool = False
    git_branch: Optional[str] = None
    git_commit: Optional[str] = None
    project_type: Optional[str] = None  # e.g., "python", "javascript", "rust"
    project_configs: Dict[str, Path] = field(default_factory=dict)
    structure_map: Dict[str, List[str]] = field(default_factory=dict)  # dir -> [files]
    language_hints: Set[str] = field(default_factory=set)
    build_system_hints: Set[str] = field(default_factory=set)
    documentation_hints: Set[str] = field(default_factory=set)


class RepositoryDiscovery:
    """
    Discovers repository boundaries, structure, and basic metadata.

    This module implements the foundation for repository understanding by:
    - Validating workspace boundaries
    - Detecting VCS repositories (.git/)
    - Identifying project configuration files
    - Mapping basic repository structure
    - Detecting language, build system, and documentation hints
    """

    def __init__(self, workspace: Workspace, cache_ttl: float = 300.0):
        """
        Initialize the repository discovery module.

        Args:
            workspace: The workspace instance to operate within
            cache_ttl: Time-to-live for cached metadata in seconds (default: 5 minutes)
        """
        self.workspace = workspace
        self._cache: Optional[RepositoryMetadata] = None
        self._cache_valid = False
        self._cache_ttl = cache_ttl
        self._cache_timestamp: float = 0.0

    def _is_cache_valid(self) -> bool:
        """Check if the discovery cache is still valid based on time."""
        if not self._cache_valid or self._cache is None:
            return False
        return (time.time() - self._cache_timestamp) < self._cache_ttl

    def discover_repository(self, force_refresh: bool = False) -> RepositoryMetadata:
        """
        Discover and return repository metadata.

        Args:
            force_refresh: If True, bypass cache and perform fresh discovery

        Returns:
            RepositoryMetadata containing discovered repository information
        """
        if not force_refresh and self._is_cache_valid():
            return self._cache

        # Perform fresh discovery
        metadata = self._perform_discovery()

        # Cache the results
        self._cache = metadata
        self._cache_valid = True
        self._cache_timestamp = time.time()

        return metadata

    def _perform_discovery(self) -> RepositoryMetadata:
        """
        Perform the actual repository discovery process.

        Returns:
            RepositoryMetadata with discovery results
        """
        workspace_root = Path(self.workspace.workspace_root).resolve()

        # Initialize metadata
        metadata = RepositoryMetadata(root_path=workspace_root)

        # Validate we're working within a proper directory
        if not workspace_root.exists() or not workspace_root.is_dir():
            raise ValueError(f"Workspace root does not exist or is not a directory: {workspace_root}")

        # Detect VCS repository (specifically Git for now)
        self._detect_git_repository(workspace_root, metadata)

        # Detect project configuration files
        self._detect_project_configs(workspace_root, metadata)

        # Detect language hints from file extensions and configs
        self._detect_language_hints(workspace_root, metadata)

        # Detect build system hints
        self._detect_build_system_hints(workspace_root, metadata)

        # Detect documentation hints
        self._detect_documentation_hints(workspace_root, metadata)

        # Build basic structure map (limited depth for performance)
        self._build_structure_map(workspace_root, metadata, max_depth=3)

        return metadata

    def _detect_git_repository(self, root_path: Path, metadata: RepositoryMetadata) -> None:
        """
        Detect if the repository is a Git repository and extract basic Git metadata.

        Args:
            root_path: The repository root path to check
            metadata: The RepositoryMetadata object to update
        """
        git_dir = root_path / ".git"
        if git_dir.exists() and git_dir.is_dir():
            metadata.is_git_repo = True

            # Try to extract basic Git information
            try:
                # Get current branch
                head_file = git_dir / "HEAD"
                if head_file.exists():
                    head_content = head_file.read_text().strip()
                    if head_content.startswith("ref: refs/heads/"):
                        metadata.git_branch = head_content.split("/")[-1]
                    elif len(head_content) == 40:  # Direct commit hash (detached HEAD)
                        metadata.git_commit = head_content

                # Get latest commit hash if we don't have it yet
                if not metadata.git_commit:
                    # Try to read from FETCH_HEAD or look for a simple way to get HEAD commit
                    # For now, we'll leave this as a placeholder for more advanced Git integration
                    pass

            except (OSError, IOError):
                # If we can't read Git info, that's okay - we still know it's a Git repo
                pass

    def _detect_project_configs(self, root_path: Path, metadata: RepositoryMetadata) -> None:
        """
        Detect project configuration files and identify project type.

        Args:
            root_path: The repository root path to search
            metadata: The RepositoryMetadata object to update
        """
        # Common project configuration files by type
        config_patterns = {
            "python": ["setup.py", "pyproject.toml", "requirements.txt", "Pipfile", "poetry.lock"],
            "javascript": ["package.json", "yarn.lock", "package-lock.json", "npm-shrinkwrap.json"],
            "typescript": ["tsconfig.json", "jsconfig.json"],
            "rust": ["Cargo.toml", "Cargo.lock"],
            "java": ["pom.xml", "build.gradle", "build.gradle.kts"],
            "go": ["go.mod", "go.sum"],
            "ruby": ["Gemfile", "Gemfile.lock", "rakefile"],
            "php": ["composer.json", "composer.lock"],
            "csharp": ["*.csproj", "*.sln", "packages.config"],
        }

        # Check for each pattern
        for project_type, patterns in config_patterns.items():
            for pattern in patterns:
                # Handle glob patterns
                if "*" in pattern:
                    matches = list(root_path.glob(pattern))
                    if matches:
                        metadata.project_type = project_type
                        metadata.project_configs[project_type] = matches[0]
                        break
                else:
                    config_file = root_path / pattern
                    if config_file.exists() and config_file.is_file():
                        metadata.project_type = project_type
                        metadata.project_configs[project_type] = config_file
                        break

            # If we found a project type, we can stop checking others for efficiency
            # (though in reality a repo might have multiple, we'll pick the first strong signal)
            if metadata.project_type:
                break

    def _detect_language_hints(self, root_path: Path, metadata: RepositoryMetadata) -> None:
        """
        Detect programming language hints from file extensions.

        Args:
            root_path: The repository root path to search
            metadata: The RepositoryMetadata object to update
        """
        # Common file extensions to language mapping
        extension_to_language = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",
            ".rs": "rust",
            ".java": "java",
            ".go": "go",
            ".rb": "ruby",
            ".php": "php",
            ".cs": "csharp",
            ".cpp": "cpp",
            ".c": "c",
            ".h": "c",
            ".hpp": "cpp",
        }

        # Scan a limited number of files to detect languages (performance consideration)
        files_checked = 0
        max_files_to_check = 100

        for file_path in root_path.rglob("*"):
            if files_checked >= max_files_to_check:
                break

            if file_path.is_file():
                suffix = file_path.suffix.lower()
                if suffix in extension_to_language:
                    metadata.language_hints.add(extension_to_language[suffix])

                files_checked += 1

    def _detect_build_system_hints(self, root_path: Path, metadata: RepositoryMetadata) -> None:
        """
        Detect build system hints from common build files.

        Args:
            root_path: The repository root path to search
            metadata: The RepositoryMetadata object to update
        """
        build_files = {
            "Makefile": "make",
            "makefile": "make",
            "CMakeLists.txt": "cmake",
            "configure": "autotools",
            "build.xml": "ant",
            "build.gradle": "gradle",
            "build.gradle.kts": "gradle_kts",
            "pom.xml": "maven",
            "Gruntfile.js": "grunt",
            "gulpfile.js": "gulp",
            "webpack.config.js": "webpack",
            "rollup.config.js": "rollup",
            "vite.config.js": "vite",
            "next.config.js": "nextjs",
            "nest-cli.json": "nest",
        }

        for build_file, build_system in build_files.items():
            if (root_path / build_file).exists():
                metadata.build_system_hints.add(build_system)

    def _detect_documentation_hints(self, root_path: Path, metadata: RepositoryMetadata) -> None:
        """
        Detect documentation hints from common documentation files.

        Args:
            root_path: The repository root path to search
            metadata: The RepositoryMetadata object to update
        """
        doc_files = {
            "README.md": "markdown",
            "README": "text",
            "README.rst": "rst",
            "README.txt": "text",
            "LICENSE": "license",
            "LICENSE.md": "markdown",
            "CONTRIBUTING.md": "markdown",
            "CONTRIBUTING": "text",
            "CHANGELOG.md": "markdown",
            "CHANGELOG": "text",
            "docs/": "documentation_directory",
        }

        for doc_file, doc_type in doc_files.items():
            doc_path = root_path / doc_file
            if doc_path.exists():
                metadata.documentation_hints.add(doc_type)

    def _build_structure_map(self, root_path: Path, metadata: RepositoryMetadata, max_depth: int = 3) -> None:
        """
        Build a basic map of the repository structure.

        Args:
            root_path: The repository root path to map
            metadata: The RepositoryMetadata object to update
            max_depth: Maximum depth to traverse (for performance)
        """
        def _should_skip_dir(dir_path: Path) -> bool:
            """Determine if a directory should be skipped during traversal."""
            skip_dirs = {
                ".git", ".svn", ".hg",  # VCS directories
                "__pycache__", ".pytest_cache", "__pycache__",  # Python cache
                "node_modules", "bower_components",  # JS dependencies
                "target", "build", "dist", "out",  # Build outputs
                ".idea", ".vscode", ".DS_Store",  # IDE/OS files
                "coverage", ".coverage",  # Coverage reports
                "logs", "log",  # Logs
            }
            return dir_path.name in skip_dirs

        def _map_directory(current_path: Path, current_depth: int) -> None:
            """Recursively map directory structure."""
            if current_depth > max_depth:
                return

            try:
                items = list(current_path.iterdir())
            except (OSError, PermissionError):
                # Skip directories we can't read
                return

            # Separate files and directories
            files = [item.name for item in items if item.is_file() and not _should_skip_dir(item)]
            dirs = [item for item in items if item.is_dir() and not _should_skip_dir(item)]

            # Store files at this level
            relative_path = str(current_path.relative_to(root_path))
            if relative_path == ".":
                relative_path = ""
            metadata.structure_map[relative_path] = sorted(files)

            # Recursively map subdirectories
            for dir_path in dirs:
                _map_directory(dir_path, current_depth + 1)

        # Start mapping from the root
        _map_directory(root_path, 0)

    def invalidate_cache(self) -> None:
        """Invalidate the cached repository metadata."""
        self._cache_valid = False
        self._cache = None

    def is_cache_valid(self) -> bool:
        """Check if the cached metadata is still valid."""
        return self._cache_valid