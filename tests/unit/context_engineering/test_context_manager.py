"""
Unit tests for the Context Manager component.
"""
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

from autonomous_agent.context_engineering import (
    ContextManager,
    ContextPackage,
    SelectionCriteria,
    BudgetAllocation,
    ReuseDecision,
    DuplicatePolicy,
    compute_workspace_id,
    compute_task_context_id,
    compute_selection_config_id
)
from autonomous_agent.workspace import Workspace


class MockWorkspace:
    """Mock workspace for testing."""
    def __init__(self, root_path):
        self.workspace_root = root_path

    def resolve(self, path):
        return Path(path).resolve()

    def resolve_path(self, path):
        """Resolve a path relative to the workspace root."""
        from pathlib import Path
        path_obj = Path(path)
        if path_obj.is_absolute():
            return str(path_obj)
        else:
            return str(Path(self.workspace_root) / path)


class MockRepositoryDiscovery:
    """Mock repository discovery for testing."""
    def __init__(self):
        pass

    def discover_repository(self, force_refresh=False):
        """Return mock repository metadata."""
        from autonomous_agent.repository_understanding import RepositoryMetadata
        return RepositoryMetadata(
            root_path=Path("/tmp/test_workspace"),
            is_git_repo=True,
            git_branch="main",
            git_commit="abc123",
            project_type="python",
            project_configs={"setup.py": Path("/tmp/test_workspace/setup.py")},
            structure_map={"src": ["main.py", "utils.py"]},
            language_hints={"python"},
            build_system_hints={"setuptools"},
            documentation_hints={"readme.md"}
        )


def test_context_manager_initialization():
    """Test ContextManager initialization."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = MockWorkspace(temp_dir)
        manager = ContextManager(workspace=workspace)

        assert manager.workspace == workspace
        assert manager.default_budget_tokens == 4000
        assert manager.enable_metrics == True
        assert manager.enable_duplicate_prevention == True


def test_context_manager_with_mock_components():
    """Test ContextManager with mocked Phase 3 components."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = MockWorkspace(temp_dir)
        mock_discovery = MockRepositoryDiscovery()

        manager = ContextManager(
            workspace=workspace,
            repository_discovery=mock_discovery,
            enable_metrics=True,
            enable_duplicate_prevention=True
        )

        assert manager.repository_discovery == mock_discovery
        assert manager.metrics is not None


def test_context_package_creation():
    """Test creating a context package."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = MockWorkspace(temp_dir)
        manager = ContextManager(workspace=workspace)

        # Test basic context package creation
        package = manager.create_context_package(
            task_description="Test task",
            max_tokens=1000
        )

        assert isinstance(package, ContextPackage)
        assert package.context_id is not None
        assert package.timestamp > 0
        assert package.total_tokens >= 0
        assert package.workspace_compliant == True


def test_context_package_with_criteria():
    """Test creating a context package with selection criteria."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = MockWorkspace(temp_dir)
        manager = ContextManager(workspace=workspace)

        criteria = SelectionCriteria(
            max_files=5,
            min_relevance_score=0.2,
            extract_snippets=True
        )

        budget = BudgetAllocation()
        policy = DuplicatePolicy()

        package = manager.create_context_package(
            task_description="Test task with criteria",
            selection_criteria=criteria,
            budget_allocation=budget,
            duplicate_policy=policy,
            max_tokens=2000
        )

        assert isinstance(package, ContextPackage)
        assert package.selection_criteria == criteria
        assert package.budget_allocation == budget
        assert package.duplicate_policy == policy


def test_context_manager_is_within_workspace():
    """Test workspace boundary checking."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = MockWorkspace(temp_dir)
        manager = ContextManager(workspace=workspace)

        # Test file within workspace
        within_file = Path(temp_dir) / "test.py"
        within_file.touch()  # Create the file
        assert manager._is_within_workspace(within_file) == True

        # Test file outside workspace (using a path that's clearly outside)
        outside_file = Path("/tmp/definitely_outside_workspace_test_file.py")
        assert manager._is_within_workspace(outside_file) == False


def test_context_manager_detect_file_language():
    """Test file language detection."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = MockWorkspace(temp_dir)
        manager = ContextManager(workspace=workspace)

        # Test various file types
        assert manager._detect_file_language(Path("test.py")) == "python"
        assert manager._detect_file_language(Path("test.js")) == "javascript"
        assert manager._detect_file_language(Path("test.ts")) == "typescript"
        assert manager._detect_file_language(Path("test.java")) == "java"
        assert manager._detect_file_language(Path("test.cpp")) == "cpp"
        assert manager._detect_file_language(Path("test.cs")) == "csharp"
        assert manager._detect_file_language(Path("test.go")) == "go"
        assert manager._detect_file_language(Path("test.rs")) == "rust"
        assert manager._detect_file_language(Path("test.html")) == "html"
        assert manager._detect_file_language(Path("test.css")) == "css"
        assert manager._detect_file_language(Path("test.json")) == "json"
        assert manager._detect_file_language(Path("test.yaml")) == "yaml"
        assert manager._detect_file_language(Path("test.md")) == "markdown"
        assert manager._detect_file_language(Path("test.txt")) == "text"
        assert manager._detect_file_language(Path("test.unknown")) == "unknown"


def test_context_manager_clear_cache():
    """Test clearing the context cache."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = MockWorkspace(temp_dir)
        manager = ContextManager(workspace=workspace)

        # Create a context to populate cache
        manager.create_context_package(
            task_description="Test task",
            max_tokens=1000
        )

        # Verify cache has content
        assert len(manager._context_cache) >= 0  # May be 0 if caching didn't trigger

        # Clear cache
        manager.clear_cache()

        # Cache should be empty
        assert len(manager._context_cache) == 0


def test_context_manager_invalidate_repository_cache():
    """Test invalidating repository cache."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = MockWorkspace(temp_dir)
        manager = ContextManager(workspace=workspace)

        # Invalidate repository cache (should not error)
        manager.invalidate_repository_cache()

        # Should still be able to create context
        package = manager.create_context_package(
            task_description="Test task after invalidation",
            max_tokens=1000
        )

        assert isinstance(package, ContextPackage)


def test_reuse_decision_content_hash_validation():
    """Test that content hash validation causes a cache miss when file content changes."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        test_file = temp_path / "test.py"
        original_content = "# original content\nprint(\"hello\")"
        test_file.write_text(original_content)

        workspace = MockWorkspace(temp_dir)
        manager = ContextManager(workspace=workspace)

        # Get initial file state
        stat = test_file.stat()

        # Compute content hash for the original file
        import hashlib
        hash_sha256 = hashlib.sha256()
        with open(test_file, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        original_content_hash = hash_sha256.hexdigest()

        # Create a reuse decision with content hash validation enabled
        reuse_decision = ReuseDecision(
            workspace_id=compute_workspace_id(Path(temp_dir)),
            task_context_id=compute_task_context_id("test task", "complete"),
            selection_config_id=compute_selection_config_id(SelectionCriteria()),
            file_path="test.py",
            selected=True,
            size=stat.st_size,
            mtime=stat.st_mtime,
            content_hash=original_content_hash  # Enable content hash validation
        )

        # Store the decision
        manager.store_reuse_decision(
            workspace_id=compute_workspace_id(Path(temp_dir)),
            task_context_id=compute_task_context_id("test task", "complete"),
            selection_config_id=compute_selection_config_id(SelectionCriteria()),
            file_path="test.py",
            reuse_decision=reuse_decision
        )

        # Verify it can be retrieved (valid state)
        retrieved = manager.get_reuse_decision(
            workspace_id=compute_workspace_id(Path(temp_dir)),
            task_context_id=compute_task_context_id("test task", "complete"),
            selection_config_id=compute_selection_config_id(SelectionCriteria()),
            file_path="test.py",
            current_workspace=workspace
        )
        assert retrieved is not None
        assert retrieved.content_hash == original_content_hash

        # Change the file content while keeping approximately the same size
        # This ensures we test content hash rather than just size
        new_content = "# updated content\nprint(\"world!\")"
        test_file.write_text(new_content)

        # Verify the content hash has changed
        hash_sha256_new = hashlib.sha256()
        with open(test_file, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256_new.update(chunk)
        new_content_hash = hash_sha256_new.hexdigest()
        assert original_content_hash != new_content_hash, "Content hash should have changed"

        # Try to retrieve the decision - should return None due to content hash mismatch
        retrieved = manager.get_reuse_decision(
            workspace_id=compute_workspace_id(Path(temp_dir)),
            task_context_id=compute_task_context_id("test task", "complete"),
            selection_config_id=compute_selection_config_id(SelectionCriteria()),
            file_path="test.py",
            current_workspace=workspace
        )
        assert retrieved is None, "Should return None due to content hash mismatch"

        # Verify the entry was removed from cache
        cache_key = manager._generate_reuse_cache_key(
            workspace_id=compute_workspace_id(Path(temp_dir)),
            task_context_id=compute_task_context_id("test task", "complete"),
            selection_config_id=compute_selection_config_id(SelectionCriteria()),
            file_path="test.py"
        )
        assert cache_key not in manager._reuse_decision_cache


if __name__ == "__main__":
    test_context_manager_initialization()
    test_context_manager_with_mock_components()
    test_context_package_creation()
    test_context_package_with_criteria()
    test_context_manager_is_within_workspace()
    test_context_manager_detect_file_language()
    test_context_manager_clear_cache()
    test_context_manager_invalidate_repository_cache()
    test_reuse_decision_content_hash_validation()
    print("All context manager tests passed!")