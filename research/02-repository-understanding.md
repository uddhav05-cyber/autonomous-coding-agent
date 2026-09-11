# Repository Understanding

## How Should an Agent Discover a Repository?

Repository discovery involves identifying the boundaries, structure, and entry points of a codebase to operate on:

### Discovery Mechanisms
- **Workspace Boundaries**: Explicitly configured root directory or repository root
- **Version Control Metadata**: Using `.git/` or equivalent VCS directories to identify repository roots
- **Project Configuration Files**: Detecting `package.json`, `pom.xml`, `Cargo.toml`, `setup.py`, etc.
- **Language-specific Conventions**: Standard directory layouts (`src/`, `lib/`, `app/`, `cmd/`)
- **Build System Indicators**: Presence of `Makefile`, `CMakeLists.txt`, `build.gradle`, etc.
- **Documentation Hints**: `README*`, `LICENSE*`, `CONTRIBUTING*` files suggesting project roots
- **Explicit Specification**: User-provided repository path or clone URL

### Discovery Process
1. **Start Point**: Begin from user-specified path or current working directory
2. **Boundary Detection**: Traverse upward to find VCS root or project markers
3. **Validation**: Confirm presence of expected repository characteristics
4. **Mapping**: Create internal representation of repository structure
5. **Change Monitoring**: Watch for structural changes during agent operation

## How Should Relevant Files Be Identified?

Relevant file identification focuses on finding files most likely to require modification for a given task:

### Relevance Signals
- **Path Similarity**: Files in directories related to task domain (e.g., auth task → `auth/` directory)
- **Name Patterns**: Filename contains task-related terms (e.g., "login" in filename for authentication task)
- **Content Keywords**: File contents contain task-domain terminology
- **Dependency Relationships**: Files that import/export or are imported by known relevant files
- **Modification History**: Recently changed files in task-related areas
- **File Type Clues**: Specific extensions suggesting relevance (`.test*` for testing tasks)
- **Size Heuristics**: Smaller, focused files often more relevant than large monoliths

### Identification Techniques
- **Keyword Search**: Text search for task terminology across file contents
- **Directory Traversal**: Breadth/depth-first exploration from likely starting points
- **Dependency Graph Analysis**: Following import/require/include chains
- **Historical Analysis**: Using git blame/log to find recently modified related files
- **Structural Patterns**: Recognizing MVC, MVVM, layered architecture patterns
- **Configuration Following**: Tracing from config files to implementation files

## How Can Code Search Reduce Context Usage?

Effective code search minimizes the amount of code that needs to be loaded into the agent's context:

### Search-First Principles
- **Search Before Read**: Use search tools to locate specific code rather than reading entire files
- **Targeted Extraction**: Retrieve only matching lines with minimal surrounding context
- **Progressive Refinement**: Start broad, then narrow based on initial results
- **Result Ranking**: Prioritize matches by relevance signals (exact matches, path proximity, etc.)

### Search Optimization Strategies
- **Indexed Search**: Maintain searchable indices for fast retrieval (when available)
- **Language-aware Search**: Understand syntax to search within comments, strings, or code appropriately
- **Symbol-based Search**: Search for function/class names rather than text when possible
- **Dependency-aware Search**: Search within import/export hierarchies
- **Frequency Analysis**: Prioritize files where search terms appear frequently
- **Context Snippets**: Show minimal context around matches rather than full files

### Context Budget Management
- **Search Result Limits**: Constrain number of files/lines returned per search
- **Relevance Thresholding**: Filter results by match quality scores
- **Deduplication**: Avoid retrieving same code via multiple search paths
- **Incremental Loading**: Load more context only when initial results prove insufficient

## How Should Symbols and Dependencies Be Identified?

Understanding symbols (functions, classes, variables) and their dependencies is crucial for safe modifications:

### Symbol Identification
- **AST Parsing**: Use language-specific parsers to extract symbol definitions
- **Regex Fallbacks**: Simple pattern matching for unsupported languages
- **LSP Integration**: Use Language Server Protocol where available
- **Naming Conventions**: Identify symbols via common patterns (`getUser`, `UserController`)
- **Export Analysis**: Focus on publicly exported symbols for interface understanding
- **Definition Tracking**: Track where symbols are defined vs. used/declared

### Dependency Mapping
- **Static Analysis**: Analyze import/require/include statements
- **Dynamic Tracing**: Observe runtime dependencies (when feasible and safe)
- **Configuration Driven**: Dependencies specified in build/configuration files
- **Interface Contracts**: Extract interface definitions from type systems
- **Call Graph Construction**: Build graphs of function/method invocations
- **Data Flow Analysis**: Track how data moves between components

### Dependency Representation
- **Directional Edges**: A depends on B (A → B means A calls/uses B)
- **Weighted Relationships**: Frequency or importance of dependencies
- **Version Constraints**: Required versions or version ranges
- **Dependency Types**: Build-time, runtime, optional, peer dependencies
- **Circular Dependency Detection**: Identify and flag problematic cycles

## How Should Large Files Be Handled?

Large files present challenges for context consumption and processing efficiency:

### Size Thresholds
- **Warning Threshold**: Files > 500 lines warrant special handling
- **Processing Threshold**: Files > 1000 lines require active management
- **Hard Limit**: Files > 5000 lines should rarely be fully loaded

### Handling Strategies
- **Segmented Reading**: Read files in chunks with clear boundaries
- **Search-driven Extraction**: Only load sections matching search criteria
- **Structure-aware Parsing**: Extract functions/classes individually rather than whole files
- **Summary Generation**: Create high-level summaries of large files' purpose and structure
- **Difference Monitoring**: Track changes to large files without full reads
- **Viewport Concept**: Maintain sliding window of interest within large files

### Language-specific Approaches
- **Object-oriented**: Focus on class definitions and method signatures
- **Functional**: Extract function signatures and module exports/imports
- **Configuration**: Parse key-value sections rather than treating as text
- **Markup**: Extract component definitions or template structures
- **Generated Files**: Identify and handle machine-generated code specially

## How Should Generated Files Be Detected?

Generated files require special handling as they should not be manually modified:

### Detection Indicators
- **File Headers**: Comments indicating generation ("DO NOT EDIT", "Generated by")
- **Directory Conventions**: Located in `gen/`, `built/`, `dist/`, `target/` directories
- **File Patterns**: Matching templates like `*.generated.*`, `*.pb.go`
- **Lack of VCS History**: No meaningful git history or constant rewrites
- **Tool Specifications**: References to code generation tools in build files
- **Consistent Formatting**: Machine-consistent formatting unlike human-written code
- **Timestamp Patterns**: Recent timestamps correlating with build tool execution

### Handling Policies
- **Read-only Treatment**: Allow reading but prevent modification attempts
- **Regeneration Awareness**: Understand that edits will be lost on regeneration
- **Source Tracking**: Identify source templates or configuration that generates them
- **Modification Redirection**: Suggest modifying sources rather than generated output
- **Generation Process Integration**: Option to trigger regeneration after source changes
- **Documentation Links**: Point to documentation about the generation process

## How Should Binary Files Be Handled?

Binary files require different approaches than text-based source code:

### Binary File Detection
- **Extension Mapping**: Known binary extensions (`.png`, `.jpg`, `.exe`, `.so`, `.dll`)
- **Content Analysis**: Null bytes or high percentage of non-printable characters
- **MIME Type Detection**: File content analysis rather than extension reliance
- **Build Artifact Indicators**: Located in `bin/`, `dist/`, `target/` directories
- **Version Control Treatment**: Often marked as binary in VCS attributes

### Handling Strategies
- **Metadata Extraction**: Extract version info, build timestamps, etc. when possible
- **Reference Tracking**: Track where binaries are referenced in configuration/code
- **Build Process Understanding**: Know how binaries are produced from sources
- **Change Detection**: Use hashes or timestamps to detect changes rather than content diffs
- **Safety Boundaries**: Prevent attempts to edit or modify binary content directly
- **Alternative Interfaces**: Suggest modifying source/assets that produce binaries
- **Size Reporting**: Report file sizes rather than attempting content display

## Architectural Recommendations

Based on the research questions, a robust repository understanding system should:

1. **Implement multi-layered discovery** combining VCS metadata, project files, and conventions
2. **Use relevance scoring** combining path, name, content, and historical signals
3. **Prioritize search over reading** to minimize context usage with progressive refinement
4. **Employ language-aware symbol extraction** using ASTs, LSP, or robust fallbacks
5. **Build dependency maps** through static analysis and configuration tracing
6. **Apply size-based handling strategies** for large files with segmented approaches
7. **Detect generated files** through headers, directories, patterns, and VCS behavior
8. **Handle binary files** through detection, metadata extraction, and reference tracking
9. **Cache repository understanding** to avoid redundant discovery operations
10. **Provide change-aware updates** to maintain accurate repository models during agent operation

This approach enables the agent to efficiently understand repository contexts while minimizing unnecessary context consumption and focusing on the most relevant portions of the codebase for any given task.