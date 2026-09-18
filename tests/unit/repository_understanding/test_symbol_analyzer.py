"""
Tests for the Symbol and Dependency Analyzer component.
"""
import tempfile
import os
from pathlib import Path
from autonomous_agent.repository_understanding import (
    Symbol,
    DependencyEdge,
    SpecialFileClassification,
    SymbolDependencyAnalyzer,
    create_symbol_dependency_analyzer
)


class MockWorkspace:
    """Mock workspace for testing."""
    def __init__(self, root_path):
        self.workspace_root = root_path


def test_symbol_creation():
    """Test creating a Symbol object."""
    symbol = Symbol(
        name="test_function",
        symbol_type="function",
        file_path=Path("/test/file.py"),
        line_number=10,
        column=0
    )

    assert symbol.name == "test_function"
    assert symbol.symbol_type == "function"
    assert symbol.file_path == Path("/test/file.py")
    assert symbol.line_number == 10
    assert symbol.column == 0
    assert symbol.is_definition == True  # Default value
    assert symbol.is_exported == False  # Default value
    assert symbol.is_imported == False  # Default value


def test_dependency_edge_creation():
    """Test creating a DependencyEdge object."""
    edge = DependencyEdge(
        source_file=Path("/test/source.py"),
        target_file=Path("/test/target.py"),
        dependency_type="import",
        symbol_name="test_module",
        line_number=5,
        weight=0.8
    )

    assert edge.source_file == Path("/test/source.py")
    assert edge.target_file == Path("/test/target.py")
    assert edge.dependency_type == "import"
    assert edge.symbol_name == "test_module"
    assert edge.line_number == 5
    assert edge.weight == 0.8
    assert edge.is_resolved == True  # Default value


def test_special_file_classification_creation():
    """Test creating a SpecialFileClassification object."""
    classification = SpecialFileClassification(
        file_path=Path("/test/file.py"),
        is_generated=True,
        is_large=False,
        is_binary=False,
        size_lines=50,
        size_bytes=1024,
        confidence=0.9,
        reasons=["Test reason"]
    )

    assert classification.file_path == Path("/test/file.py")
    assert classification.is_generated == True
    assert classification.is_large == False
    assert classification.is_binary == False
    assert classification.size_lines == 50
    assert classification.size_bytes == 1024
    assert classification.confidence == 0.9
    assert classification.reasons == ["Test reason"]


def test_create_symbol_dependency_analyzer():
    """Test creating a SymbolDependencyAnalyzer instance."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = MockWorkspace(temp_dir)
        analyzer = create_symbol_dependency_analyzer(workspace)

        assert isinstance(analyzer, SymbolDependencyAnalyzer)
        assert analyzer.workspace == workspace


def test_symbol_dependency_analyzer_init():
    """Test SymbolDependencyAnalyzer initialization."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = MockWorkspace(temp_dir)
        analyzer = SymbolDependencyAnalyzer(workspace)

        assert analyzer.workspace == workspace
        assert isinstance(analyzer._symbol_cache, dict)
        assert isinstance(analyzer._dependency_cache, dict)
        assert isinstance(analyzer._special_file_cache, dict)
        assert len(analyzer._symbol_cache) == 0
        assert len(analyzer._dependency_cache) == 0
        assert len(analyzer._special_file_cache) == 0


def test_is_within_workspace():
    """Test the _is_within_workspace method."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = MockWorkspace(temp_dir)
        analyzer = SymbolDependencyAnalyzer(workspace)

        # Test file within workspace
        file_within = Path(temp_dir) / "test.py"
        file_within.parent.mkdir(parents=True, exist_ok=True)
        file_within.touch()

        assert analyzer._is_within_workspace(file_within) == True

        # Test file outside workspace
        file_outside = Path("/outside/test.py")
        assert analyzer._is_within_workspace(file_outside) == False


def test_get_file_type():
    """Test the _get_file_type method."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = MockWorkspace(temp_dir)
        analyzer = SymbolDependencyAnalyzer(workspace)

        # Test various file types
        assert analyzer._get_file_type(Path("test.py")) == "python"
        assert analyzer._get_file_type(Path("test.js")) == "javascript"
        assert analyzer._get_file_type(Path("test.ts")) == "typescript"
        assert analyzer._get_file_type(Path("test.java")) == "java"
        assert analyzer._get_file_type(Path("test.go")) == "go"
        assert analyzer._get_file_type(Path("test.rb")) == "ruby"
        assert analyzer._get_file_type(Path("test.php")) == "php"
        assert analyzer._get_file_type(Path("test.unknown")) == "unknown"


def test_analyze_file_symbols_empty_file():
    """Test analyzing symbols in an empty file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = MockWorkspace(temp_dir)
        analyzer = SymbolDependencyAnalyzer(workspace)

        # Create an empty file
        empty_file = Path(temp_dir) / "empty.py"
        empty_file.touch()

        symbols = analyzer.analyze_file_symbols(empty_file)
        assert isinstance(symbols, list)
        assert len(symbols) == 0


def test_analyze_file_symbols_python_file():
    """Test analyzing symbols in a Python file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = MockWorkspace(temp_dir)
        analyzer = SymbolDependencyAnalyzer(workspace)

        # Create a Python file with some symbols
        python_file = Path(temp_dir) / "test.py"
        python_file.write_text("""
def hello_world():
    \"\"\"Say hello world.\"\"\"
    print("Hello, World!")

class TestClass:
    \"\"\"A test class.\"\"\"
    def method(self):
        pass

# Variable assignment
TEST_VARIABLE = 42
""")

        symbols = analyzer.analyze_file_symbols(python_file)
        assert isinstance(symbols, list)
        # Should find at least the function, class, and variable
        assert len(symbols) >= 3

        # Check that we found the function
        function_symbols = [s for s in symbols if s.name == "hello_world" and s.symbol_type == "function"]
        assert len(function_symbols) == 1

        # Check that we found the class
        class_symbols = [s for s in symbols if s.name == "TestClass" and s.symbol_type == "class"]
        assert len(class_symbols) == 1

        # Check that we found the variable
        variable_symbols = [s for s in symbols if s.name == "TEST_VARIABLE" and s.symbol_type == "variable"]
        assert len(variable_symbols) == 1


def test_analyze_file_dependencies():
    """Test analyzing dependencies in a file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = MockWorkspace(temp_dir)
        analyzer = SymbolDependencyAnalyzer(workspace)

        # Create a Python file with imports that can be resolved
        python_file = Path(temp_dir) / "test.py"
        python_file.write_text("""
import local_module
from . import submodule
""")

        # Create the imported files
        local_module_file = Path(temp_dir) / "local_module.py"
        local_module_file.write_text("# Local module\n")

        submodule_dir = Path(temp_dir) / "submodule"
        submodule_dir.mkdir()
        submodule_init_file = submodule_dir / "__init__.py"
        submodule_init_file.write_text("# Submodule init\n")

        dependencies = analyzer.analyze_file_dependencies(python_file)
        assert isinstance(dependencies, list)
        # Should find dependencies for the resolvable imports
        assert len(dependencies) >= 2

        # Check that we got DependencyEdge objects
        for dep in dependencies:
            assert isinstance(dep, DependencyEdge)
            assert dep.source_file == python_file


def test_classify_special_file():
    """Test classifying a special file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = MockWorkspace(temp_dir)
        analyzer = SymbolDependencyAnalyzer(workspace)

        # Create a regular file
        regular_file = Path(temp_dir) / "regular.py"
        regular_file.write_text("# Regular Python file\nprint('hello')\n")

        classification = analyzer.classify_special_file(regular_file)
        assert isinstance(classification, SpecialFileClassification)
        assert classification.file_path == regular_file
def test_build_dependency_graph():
    """Test building a dependency graph."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = MockWorkspace(temp_dir)
        analyzer = SymbolDependencyAnalyzer(workspace)

        # Create a couple of Python files
        file1 = Path(temp_dir) / "file1.py"
        file1.write_text("""
import os
""")

        file2 = Path(temp_dir) / "file2.py"
        file2.write_text("""
import sys
""")

        graph = analyzer.build_dependency_graph([file1, file2])
        assert isinstance(graph, dict)
        assert file1 in graph
        assert file2 in graph


def test_detect_circular_dependencies_no_circles():
    """Test detecting circular dependencies when there are none."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = MockWorkspace(temp_dir)
        analyzer = SymbolDependencyAnalyzer(workspace)

        # Create a couple of Python files with no circular imports
        file1 = Path(temp_dir) / "file1.py"
        file1.write_text("""
import os
""")

        file2 = Path(temp_dir) / "file2.py"
        file2.write_text("""
import sys
""")

        circles = analyzer.detect_circular_dependencies([file1, file2])
        assert isinstance(circles, list)
        # Should be no circles in this simple case
        assert len(circles) == 0


def test_clear_cache():
    """Test clearing the caches."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = MockWorkspace(temp_dir)
        analyzer = SymbolDependencyAnalyzer(workspace)

        # Add something to the caches
        analyzer._symbol_cache[Path("test")] = []
        analyzer._dependency_cache[Path("test")] = []
        analyzer._special_file_cache[Path("test")] = SpecialFileClassification(file_path=Path("test"))

        assert len(analyzer._symbol_cache) > 0
        assert len(analyzer._dependency_cache) > 0
        assert len(analyzer._special_file_cache) > 0

        # Clear the caches
        analyzer.clear_cache()

        assert len(analyzer._symbol_cache) == 0
        assert len(analyzer._dependency_cache) == 0
        assert len(analyzer._special_file_cache) == 0


if __name__ == "__main__":
    test_symbol_creation()
    test_dependency_edge_creation()
    test_special_file_classification_creation()
    test_create_symbol_dependency_analyzer()
    test_symbol_dependency_analyzer_init()
    test_is_within_workspace()
    test_get_file_type()
    test_analyze_file_symbols_empty_file()
    test_analyze_file_symbols_python_file()
    test_analyze_file_dependencies()
    test_classify_special_file()
    test_build_dependency_graph()
    test_detect_circular_dependencies_no_circles()
    test_clear_cache()
    print("All tests passed!")
