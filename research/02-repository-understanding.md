# Repository Understanding Research - Phase 3

## Phase 3 Objectives

The primary objective of Phase 3 is to implement a comprehensive repository understanding system that enables the autonomous coding agent to:
- Discover and map repository boundaries, structure, and entry points
- Identify relevant files for a given task using multiple relevance signals
- Perform efficient code search to minimize context usage
- Extract symbols and understand dependencies across the codebase
- Handle special file types (large, generated, binary) appropriately
- Build and maintain repository metadata for informed decision-making
- Operate within workspace boundaries while providing comprehensive codebase awareness

This phase establishes the foundation for context-aware operations by enabling the agent to understand what exists in the repository before determining what needs to be modified.

## Functional Requirements

### Repository Discovery
- Identify repository root using workspace boundaries, VCS metadata (.git/), and project configuration files
- Detect repository structure including standard directory layouts and language-specific conventions
- Recognize build system indicators, documentation hints, and explicit specifications
- Validate repository characteristics and monitor for structural changes during operation

### File Relevance Identification
- Determine file relevance based on path similarity to task domain
- Identify files through name patterns matching task terminology
- Detect content keywords related to the task domain
- Analyze dependency relationships (import/export chains)
- Consider modification history and file type clues
- Apply size heuristics to prioritize smaller, focused files

### Code Search and Context Efficiency
- Implement search-first principles: locate specific code before reading entire files
- Provide targeted extraction with minimal surrounding context
- Enable progressive refinement from broad to narrow searches
- Rank results by relevance signals (exact matches, path proximity, etc.)
- Apply search optimization strategies including indexed and language-aware search
- Manage context budget through result limits, relevance thresholding, and deduplication

### Symbol and Dependency Understanding
- Extract symbols using AST parsing, LSP integration, and regex fallbacks
- Identify symbols through naming conventions and export analysis
- Track symbol definitions vs. usage/declarations
- Map dependencies through static analysis, configuration tracing, and interface contracts
- Construct call graphs and perform data flow analysis
- Represent dependencies with directional edges, weighted relationships, and version constraints
- Detect and flag circular dependencies

### Special File Handling
- Handle large files through segmented reading, search-driven extraction, and structure-aware parsing
- Generate high-level summaries and maintain viewport concepts for large files
- Detect generated files via file headers, directory conventions, file patterns, VCS history, and tool specifications
- Handle binary files through extension mapping, content analysis, MIME type detection, and build artifact indicators
- Extract metadata, track references, understand build processes, and establish safety boundaries for special file types

### Repository Metadata
- Extract and maintain VCS metadata (branch, commit history, tags)
- Collect project metadata from configuration files (package.json, Cargo.toml, etc.)
- Track file system metadata (timestamps, sizes, permissions)
- Maintain symbol tables and dependency graphs
- Cache repository understanding to avoid redundant discovery operations
- Provide change-aware updates to maintain accurate repository models

## Technical Approach

### Discovery Mechanisms
The repository understanding system employs a multi-layered discovery approach:
1. **Workspace Boundary Validation**: Confirm operations remain within configured workspace root
2. **VCS Metadata Analysis**: Use .git/ directory to identify repository roots and extract metadata
3. **Project Configuration Scanning**: Detect standard files (package.json, setup.py, Cargo.toml, etc.) to understand project type and dependencies
4. **Convention-Based Detection**: Identify language-specific directory structures and build system indicators
5. **Documentation Correlation**: Use README, LICENSE, and CONTRIBUTING files to validate repository purpose
6. **Explicit Specification Handling**: Process user-provided repository paths or clone URLs

### Relevance Scoring Algorithm
File relevance is determined through a weighted scoring system combining:
- **Path Similarity Score**: Based on directory proximity to task-related paths
- **Name Pattern Score**: Filename matches to task terminology
- **Content Keyword Score**: Occurrence of task-domain terms in file contents
- **Dependency Score**: Centrality in import/export chains
- **Recency Score**: Based on modification history and git activity
- **File Type Score**: Preferences for certain extensions (.test, .spec, etc.)
- **Size Inversion Score**: Preference for smaller, focused files

### Code Search Optimization
To minimize context usage while maximizing search effectiveness:
- **Search Before Read**: Use search tools to locate code before loading files
- **Targeted Line Extraction**: Retrieve only matching lines with configurable context (default: 2 lines before/after)
- **Progressive Refinement**: Start with broad searches, narrow based on initial results
- **Result Relevance Ranking**: Prioritize exact matches, path proximity, and file type relevance
- **Search Optimization Techniques**:
  - Indexed search where available (using tools like ripgrep with --no-ignore-vcs)
  - Frequency analysis (prioritizing files with multiple term occurrences)
  - Context snippet generation (showing minimal context around matches)

### Symbol Extraction and Dependency Mapping
- **Multi-Language AST Parsing**: Use tree-sitter or language-specific parsers for accurate symbol extraction
- **LSP Integration**: Leverage Language Server Protocol where available for enhanced symbol resolution
- **Regex Fallbacks**: Robust pattern matching for unsupported or dynamically typed languages
- **Static Dependency Analysis**: Parse import/require/include statements to build dependency graphs
- **Configuration-Driven Dependencies**: Extract dependencies from build files (package.json, pom.xml, Cargo.toml, etc.)
- **Interface Contract Extraction**: Derive interface definitions from type systems when available
- **Call Graph Construction**: Build directed graphs of function/method invocations
- **Data Flow Analysis**: Track how data moves between components to identify critical paths

### Special File Type Handling
- **Large Files** (>1000 lines):
  - Segmented reading with configurable chunk sizes
  - Search-driven extraction to load only relevant sections
  - Structure-aware parsing to extract functions/classes individually
  - Automatic summary generation for files exceeding thresholds
  - Difference monitoring to track changes without full reads
  - Viewport maintenance for sliding window of interest

- **Generated Files**:
  - Header-based detection ("DO NOT EDIT", "Generated by" comments)
  - Directory convention matching (gen/, built/, dist/, target/)
  - File pattern matching (*.generated.*, *.pb.go)
  - VCS history analysis (lack of meaningful history, constant rewrites)
  - Tool specification detection (references in build files)
  - Formatting consistency analysis (machine vs. human patterns)
  - Timestamp pattern correlation with build tool execution

- **Binary Files**:
  - Extension mapping (.png, .jpg, .exe, .so, .dll)
  - Content analysis (null bytes, non-printable character percentage)
  - MIME type detection (content-based rather than extension-reliant)
  - Build artifact location detection (bin/, dist/, target/ directories)
  - VCS binary attribute detection
  - Metadata extraction (version info, build timestamps)
  - Reference tracking (where binaries are referenced in configuration/code)
  - Build process understanding (how binaries are produced from sources)
  - Change detection (hashes/timestamps rather than content diffs)
  - Safety boundaries (prevent direct editing attempts)
  - Alternative interfaces (suggest modifying sources/assets)
  - Size reporting (report file sizes rather than attempting content display)

## Architecture and Design

### Component Architecture
The repository understanding system consists of five primary components working in concert:

1. **Repository Discovery Module**
   - Responsible for identifying repository boundaries and structure
   - Implements multi-layered discovery mechanisms
   - Validates repository characteristics and monitors for changes
   - Outputs: Repository root path, structure map, VCS metadata

2. **Relevance Engine**
   - Calculates file relevance scores using multiple signals
   - Implements weighted scoring algorithm
   - Prioritizes files for agent attention
   - Outputs: Ranked file list with relevance scores

3. **Code Search Module**
   - Implements search-first, context-efficient search strategies
   - Provides targeted extraction with minimal context
   - Applies search optimization techniques
   - Outputs: Search results with location and context snippets

4. **Symbol and Dependency Analyzer**
   - Extracts symbols using AST parsers and LSP integration
   - Maps dependencies through static and configuration analysis
   - Constructs call graphs and performs data flow analysis
   - Detects special file types and applies appropriate handling
   - Outputs: Symbol tables, dependency graphs, special file classifications

5. **Repository Metadata Manager**
   - Extracts, caches, and maintains repository metadata
   - Manages VCS metadata, project metadata, and file system metadata
   - Implements caching strategies to avoid redundant operations
   - Provides change-aware updates for dynamic repositories
   - Outputs: Repository metadata cache, change notifications

### Data Flow
1. Repository Discovery Module identifies repository boundaries and structure
2. Relevance Engine scores all files based on task-specific relevance signals
3. Code Search Module locates specific code patterns with minimal context extraction
4. Symbol and Dependency Analyzer extracts symbols and maps relationships
5. Repository Metadata Manager maintains and updates repository understanding
6. All components feed into the Context Manager for context assembly

### Interface Design
- **Input**: Task description, workspace root, configuration parameters
- **Inter-component Communication**: Well-defined data structures for repository metadata, symbol tables, dependency graphs
- **Output**: Repository understanding package including file relevance rankings, search results, symbol information, dependency maps, and metadata
- **Error Handling**: Graceful degradation when specific mechanisms fail (e.g., fallback to regex when AST parsing unavailable)

## Dependencies and Technologies

### Core Dependencies
- **tree-sitter**: Modern incremental parsing library for accurate AST extraction across multiple languages (planned for future enhancement)
- **ripgrep**: Fast, regex-based search tool with git-ignore awareness for efficient code search
- **pygments**: Syntax highlighting and lexical analysis for language-aware search capabilities (planned for future enhancement)
- **GitPython**: Python library for Git repository interaction and metadata extraction
- **watchdog**: Cross-platform file system monitoring for change detection
- **chardet**: Character encoding detection for handling diverse file encodings
- **python-magic**: File type detection via MIME analysis for binary file identification
- **pathspez**: Path matching library for efficient glob pattern matching and path operations

### Optional/Enhancement Dependencies
- **LSP Clients**: Language-specific Language Protocol clients for enhanced symbol resolution (when available)
- **Semantic Search Libraries**: For embedding-based code search (sentence-transformers, faiss, etc.)
- **Graph Libraries**: NetworkX or similar for advanced dependency graph analysis
- **Caching Layer**: Redis or similar for distributed repository understanding caching (for multi-instance deployments)

### Version Constraints
All dependencies should use stable, actively maintained versions with attention to:
- Security update frequency
- Maintenance status and community support
- License compatibility (prefer MIT, Apache-2.0, or similar permissive licenses)
- Binary wheel availability for ease of installation
- Python version compatibility (targeting Python 3.9+)

## Security Considerations

### Repository Boundary Enforcement
- **Strict Path Validation**: All file operations confined to workspace root using resolved absolute paths
- **Symlink Protection**: Policies to prevent symlink-based workspace escape (NEVER_FOLLOW, FOLLOW_IF_SAFE)
- **Path Traversal Prevention**: Rigorous validation using os.path.commonpath to detect escape attempts
- **Repository Root Protection**: Prevention of attempts to delete or modify workspace root directory
- **Windows Junction Handling**: Special consideration for Windows junction points and reparse points

### Repository Content Safety
- **Content Validation**: Repository metadata extraction does not execute or evaluate discovered code
- **Safe Parsing**: AST parsing and LSP integration configured for analysis-only modes
- **Metadata Sanitization**: Extracted repository metadata sanitized before internal use
- **Binary File Protection**: Explicit prevention of attempts to edit or modify binary content
- **Generated File Awareness**: Clear identification and handling to prevent modification of generated outputs

### Information Disclosure Controls
- **Metadata Minimization**: Repository understanding collects only necessary metadata for agent operation
- **Access Logging**: Repository discovery and metadata access logged for audit trails
- **Error Message Sanitization**: Error messages avoid leaking sensitive repository structure information
- **Memory Safety**: Repository metadata cached securely with appropriate lifetime management
- **Concurrent Access Protection**: Thread-safe access to repository understanding data structures

### Threat Modeling and Mitigations
- **Malicious Repository Content**:
  - Threat: Repository containing code designed to exploit parsing/search mechanisms
  - Mitigation: Use well-tested, secure parsing libraries; implement timeouts on resource-intensive operations

- **Repository Structure Attacks**:
  - Threat: Deeply nested directories or circular symlinks designed to cause resource exhaustion
  - Mitigation: Depth limits on directory traversal; symlink cycle detection; resource quotas

- **Metadata Extraction Exploits**:
  - Threat: Malicious configuration files designed to exploit metadata parsers
  - Mitigation: Use secure parsers for configuration files (JSON, YAML, TOML); validate schema before processing

- **Denial of Service via Search**:
  - Threat: Complex regex patterns or large repositories designed to overwhelm search mechanisms
  - Mitigation: Timeout limits on search operations; result size limits; search complexity analysis

## Testing Strategy

### Unit Testing
- **Repository Discovery Module**:
  - Test workspace boundary validation with various path configurations
  - Verify VCS metadata extraction from mock .git/ directories
  - Test project configuration file detection and parsing
  - Validate convention-based detection for different language ecosystems

- **Relevance Engine**:
  - Test scoring algorithms with known file/task pairs
  - Validate weight adjustments and scoring boundaries
  - Test edge cases (empty repositories, single files, etc.)

- **Code Search Module**:
  - Test search accuracy with known patterns
  - Validate context extraction parameters
  - Test search optimization techniques (symbol-based, etc.)
  - Verify performance characteristics with large result sets

- **Symbol and Dependency Analyzer**:
  - Test AST parsing accuracy across supported languages
  - Validate LSP integration where available
  - Test dependency graph construction accuracy
  - Verify special file type detection and handling

- **Repository Metadata Manager**:
  - Test metadata extraction accuracy from various sources
  - Validate caching effectiveness and cache invalidation
  - Test change detection and notification mechanisms
  - Verify metadata persistence and recovery

### Integration Testing
- **End-to-End Repository Understanding**:
  - Test complete repository understanding pipeline with sample repositories
  - Validate integration between all five components
  - Test performance with repositories of varying sizes (small, medium, large)
  - Verify accuracy of relevance scoring against manual evaluation

- **Special File Type Handling**:
  - Test large file handling strategies with generated large files
  - Verify generated file detection accuracy
  - Test binary file identification and safety mechanisms
  - Validate metadata extraction from various file types

- **Workspace Boundary Security**:
  - Test prevention of path traversal attacks
  - Verify symlink protection effectiveness
  - Confirm workspace root protection mechanisms
  - Validate behavior with various path encoding attacks

### Performance Testing
- **Scalability Testing**:
  - Measure repository understanding time vs. repository size
  - Test memory usage growth with increasing repository size
  - Validate caching effectiveness for repeated operations
  - Measure impact of file system monitoring on performance

- **Concurrency Testing**:
  - Test thread safety of repository understanding components
  - Validate performance under concurrent access patterns
  - Verify resource cleanup and leak prevention

- **Regression Testing**:
  - Maintain benchmark repositories of known characteristics
  - Test against version control history to ensure consistent behavior
  - Validate performance characteristics across dependency updates

### Fixtures and Test Data
- **Repository Fixtures**:
  - Minimal repository: Single file, basic structure
  - Language-specific repositories: Python, JavaScript, Java, Rust projects
  - Framework-specific repositories: React, Django, Spring applications
  - Monorepo examples: Multi-package repositories with complex dependencies
  - Legacy codebases: Older projects with varied file types and structures

- **Special File Type Fixtures**:
  - Large files: Generated files exceeding 10K lines for testing handling strategies
  - Generated files: Protobuf outputs, compiled templates, minified assets
  - Binary files: Images, executables, libraries in various formats
  - Mixed repositories: Combinations of text, generated, and binary files

### Verification Criteria
A repository understanding implementation is considered complete when:
- All unit tests pass (>90% coverage)
- Integration tests demonstrate correct end-to-end functionality
- Performance meets defined thresholds (<100ms for small repos, <1s for medium repos)
- Security testing confirms boundary protection and threat mitigation
- Manual verification shows accurate relevance scoring and symbol extraction
- Change detection correctly identifies repository modifications
- Caching demonstrates significant performance improvements for repeated operations

## Implementation Scope

### In-Scope Components
1. **Repository Discovery Module**
   - Workspace boundary validation and enforcement
   - VCS metadata extraction (.git/ directory analysis)
   - Project configuration file detection and parsing
   - Language-specific convention recognition
   - Build system indicator detection
   - Documentation hint processing
   - Explicit repository specification handling
   - Repository change monitoring and validation

2. **Relevance Engine**
   - Multi-signal relevance scoring algorithm
   - Path similarity calculation
   - Name pattern matching
   - Content keyword extraction and scoring
   - Dependency relationship analysis
   - Modification history analysis
   - File type and size heuristic application
   - Score normalization and ranking

3. **Code Search Module**
   - Search-first methodology implementation
   - Targeted line extraction with configurable context
   - Progressive search refinement capabilities
   - Result relevance ranking system
   - Indexed search integration (ripgrep)
   - Language-aware search capabilities
   - Symbol-based search functionality
   - Dependency-aware search constraints
   - Frequency analysis prioritization
   - Context snippet generation

4. **Symbol and Dependency Analyzer**
   - Multi-language AST parsing (tree-sitter integration)
   - Language Server Protocol integration
   - Regex fallback mechanisms for unsupported languages
   - Import/export/require statement analysis
   - Configuration-driven dependency extraction
   - Interface contract derivation from type systems
   - Call graph construction and analysis
   - Data flow analysis implementation
   - Circular dependency detection
   - Special file type detection and classification

5. **Repository Metadata Manager**
   - VCS metadata extraction (branches, commits, tags, status)
   - Project metadata extraction (package.json, Cargo.toml, pom.xml, etc.)
   - File system metadata collection (timestamps, sizes, permissions)
   - Symbol table and dependency graph maintenance
   - Repository understanding caching mechanisms
   - Change detection and notification systems
   - Metadata persistence and recovery mechanisms
   - Memory-efficient storage strategies

### Out-of-Scope Components (Future Phases)
- **Advanced Code Intelligence**: Deep code understanding beyond symbol extraction (Phase 4+)
- **Dependency Resolution**: Automatic dependency installation and version conflict resolution (Phase 6+)
- **Build System Integration**: Direct invocation of build systems for verification (Phase 6+)
- **Deployment Understanding**: Understanding of deployment configurations and environments (Phase 8+)
- **Runtime Behavior Analysis**: Dynamic analysis of running applications (Phase 10+)
- **Cross-Repository Understanding**: Understanding of dependencies across multiple repositories (Phase 5+)
- **Machine Learning Models**: Training or fine-tuning of ML models for code understanding (Phase 12+)
- **Natural Language Repository Queries**: Advanced NLP interfaces for repository questioning (Phase 4+)

## Risks and Trade-offs

### Technical Risks
- **Performance Overhead**: Repository understanding operations may introduce latency
  - *Mitigation*: Implement caching, incremental updates, and background processing
  - *Trade-off*: Slightly increased memory usage for improved response times

- **Accuracy Limitations**: Heuristic-based relevance scoring may miss relevant files
  - *Mitigation*: Combine multiple signals and allow user feedback for tuning
  - *Trade-off*: Increased complexity vs. perfect accuracy

- **Language Support Gaps**: AST parsers may not be available for all languages
  - *Mitigation*: Robust fallback mechanisms using regex and LSP where available
  - *Trade-off*: Reduced accuracy for less common languages vs. broad language support

- **Resource Consumption**: Metadata maintenance and caching may consume significant resources
  - *Mitigation*: Implement size limits, LRU eviction, and selective caching strategies
  - *Trade-off*: Cache hit rates vs. memory usage

- **Concurrency Complexity**: Thread-safe access to shared repository understanding data
  - *Mitigation*: Use appropriate locking mechanisms and immutable data structures where possible
  - *Trade-off*: Development complexity vs. correctness and performance

### Operational Risks
- **Repository Size Scaling**: Performance may degrade significantly with very large repositories
  - *Mitigation*: Implement sampling strategies for initial scans and progressive refinement
  - *Trade-off*: Initial accuracy vs. scalability to enterprise-scale repositories

- **Initialization Delay**: First-time repository understanding may take noticeable time
  - *Mitigation*: Background initialization and progressive disclosure of results
  - *Trade-off*: Startup time vs. immediate full repository understanding

- **Change Tracking Overhead**: Continuous monitoring may impact file system performance
  - *Mitigation*: Adaptive polling rates and debouncing mechanisms
  - *Trade-off*: Change detection latency vs. file system impact

- **False Positives/Negatives in Special File Detection**:
  - *Mitigation*: Conservative detection policies with clear error recovery paths
  - *Trade-off*: Detection accuracy vs. blocking legitimate file operations

### Architectural Trade-offs
- **Depth vs. Breadth of Analysis**:
  - *Choice*: Prioritize broad repository understanding with targeted deep analysis
  - *Rationale*: Enables quick operation startup while allowing deep dives when needed

- **Real-time vs. Batch Processing**:
  - *Choice*: Hybrid approach with background batch processing and real-time critical updates
  - *Rationale*: Balances responsiveness with thoroughness

- **Centralized vs. Distributed Metadata**:
  - *Choice*: Centralized metadata with caching for performance
  - *Rationale*: Simplicity and consistency vs. scalability and fault tolerance

- **Precision vs. Recall in Relevance Scoring**:
  - *Choice*: Slightly favor precision to reduce context noise
  - *Rationale*: Better to miss some relevant files than to overwhelm context with irrelevant ones

### Dependencies on External Factors
- **Tool Availability**: Performance depends on quality of tree-sitter parsers, LSP servers, etc.
  - *Mitigation*: Abstract interfaces and fallback mechanisms
  - *Acceptable Risk*: External tool quality is generally good for major languages

- **File System Performance**: Performance depends on underlying file system speed
  - *Mitigation*: Minimize file system operations through caching and efficient algorithms
  - *Acceptable Risk*: Standard assumption in desktop/server environments

- **Git Repository Health**: Performance may degrade with corrupted or unusual Git repositories
  - *Mitigation*: Graceful degradation and timeout mechanisms
  - *Acceptable Risk*: Most repositories in practice are well-formed

## Recommended Implementation Plan

### Phase 3.1: Foundation and Discovery (Weeks 1-2)
**Objective**: Implement basic repository discovery and metadata extraction
- Implement Repository Discovery Module with workspace boundary validation
- Develop VCS metadata extraction from .git/ directories
- Create project configuration file detection and parsing system
- Implement basic repository structure mapping
- Add repository change detection and validation mechanisms
- Create initial Repository Metadata Manager for basic metadata storage
- **Deliverable**: Basic repository discovery capable of identifying repository roots and structure
- **Verification**: Unit tests for discovery components, integration tests with sample repositories

### Phase 3.2: Relevance and Search (Weeks 3-4)
**Objective**: Implement relevance scoring and code search capabilities to enable the agent to identify and retrieve the most relevant code artifacts for a given task while minimizing context usage.

#### Functional Requirements
- **Relevance Scoring Algorithm**: Implement a weighted scoring system combining multiple signals:
  - Path Similarity Score: Based on directory proximity to task-related paths
  - Name Pattern Score: Filename matches to task terminology (exact, partial, fuzzy)
  - Content Keyword Score: Occurrence of task-domain terms in file contents (weighted by frequency and location)
  - Dependency Score: Centrality in import/export chains and call graphs
  - Modification History Score: Based on git activity and recent changes
  - File Type Score: Preferences for certain extensions (.test, .spec, .md, etc.)
  - Size Inversion Score: Preference for smaller, focused files over large ones
- **Code Search Methodology**:
  - Search-first principles: locate specific code before reading entire files
  - Targeted line extraction: retrieve only matching lines with configurable context (default: 2 lines before/after)
  - Progressive refinement: start with broad searches, narrow based on initial results
  - Result relevance ranking: prioritize exact matches, path proximity, and file type relevance
- **Search Optimization Techniques**:
  - Indexed search integration (using tools like ripgrep with --no-ignore-vcs)
  - Language-aware search (understanding comments vs. code vs. strings)
  - Symbol-based search (searching for function/class names when possible)
  - Dependency-aware search (constrained to import/export hierarchies)
  - Frequency analysis (prioritizing files with multiple term occurrences)
  - Context snippet generation (showing minimal context around matches)

#### Technical Approach
The relevance and search system employs a pipeline architecture:
1. **Query Processing**: Parse and normalize the task description into search terms
2. **Signal Generation**: Compute individual relevance signals for each file
3. **Score Fusion**: Combine signals using weighted averaging (weights configurable per task type)
4. **Ranking and Filtering**: Sort files by composite score and apply relevance thresholds
5. **Search Execution**: For top-ranked files, perform targeted code search
6. **Result Compilation**: Extract context snippets and format results for consumption

#### Architecture and Design
- **Relevance Engine**: Central component that computes multi-signal relevance scores
- **Code Search Module**: Handles search execution and context extraction
- **Search Optimizer**: Applies domain-specific optimizations and caching strategies
- **Result Processor**: Formats and ranks search results for downstream consumption

#### Module and Interface Design
**Relevance Engine Interface**:
- Input: Task description, repository metadata from Stage 1
- Output: Relevance scores for all files in repository
- Methods:
  - `calculate_relevance_scores(task_query: str, metadata: RepositoryMetadata) -> Dict[Path, float]`
  - `update_signal_weights(task_type: str, weights: Dict[str, float])`

**Code Search Module Interface**:
- Input: Search query, file paths to search, context parameters
- Output: Search results with location and context snippets
- Methods:
  - `execute_search(query: str, file_paths: List[Path], context_lines: int) -> List[SearchResult]`
  - `extract_context(file_path: Path, line_number: int, context_lines: int) -> str`

#### Dependencies and Technology Evaluation
- **Required**:
  - ripgrep: Fast, regex-based search tool with git-ignore awareness (core search technology)
  - pathspez: Path matching library for efficient glob pattern and path operations
- **Recommended**:
  - Pygments: Syntax highlighting and lexical analysis for language-aware search
  - whoosh: Pure Python search library for fallback indexing capabilities
- **Evaluated Alternatives**:
  - ag (The Silver Searcher): Similar to ripgrep but less actively maintained
  - git-grep: Git-based search but limited to tracked files only
  - Elasticsearch: Overkill for local repository search, high resource usage

#### Security Considerations
- **Workspace Boundary Enforcement**: All search operations confined to workspace root using resolved absolute paths
- **Path Traversal Prevention**: Rigorous validation using os.path.commonpath to detect escape attempts
- **Search Query Sanitization**: Prevent injection attacks in regex patterns (timeout limits, pattern complexity analysis)
- **Information Disclosure Controls**: Search results limited to relevance-scored snippets, not full file contents unless explicitly requested

#### Testing Strategy
- **Unit Testing**:
  - Test scoring algorithms with known file/task pairs
  - Validate weight adjustments and scoring boundaries
  - Test search accuracy with known patterns and expected results
  - Verify context extraction parameters and edge cases
- **Integration Testing**:
  - Test end-to-end relevance scoring and search pipeline
  - Validate integration with Stage 1 discovery outputs
  - Test performance with repositories of varying sizes
- **Performance Testing**:
  - Measure search latency vs. repository size
  - Validate caching effectiveness for repeated searches
  - Benchmark different search optimization strategies

#### Implementation Scope
**Must Implement in Stage 2**:
- Multi-signal relevance scoring algorithm (7 core signals)
- Search-first methodology with targeted line extraction
- Progressive search refinement capabilities
- Result ranking and context snippet generation
- Integration of indexed search (ripgrep)
- Basic language-aware search capabilities

**Should Implement if Practical**:
- Symbol-based search (function/class name search)
- Dependency-aware search (import/export chain constrained search)
- Frequency analysis (multiple term occurrence boosting)
- Advanced caching strategies for search results

**Defer to Later Stages**:
- Semantic code search (embedding-based conceptual similarity)
- Natural language repository queries
- Machine learning for dynamic relevance weighting
- Cross-repository search capabilities

#### References
- Goldberg, D. (1991). What every computer scientist should know about floating-point arithmetic. ACM Computing Surveys.
- Gonzalez, R.C., & Woods, R.E. (2008). Digital Image Processing. Pearson Prentice Hall.
- Manning, C.D., Raghavan, P., & Schütze, H. (2008). Introduction to Information Retrieval. Cambridge University Press.
- Campbell, D. (2012). Understanding Ripgrep: A Practical Guide to Fast Code Search. O'Reilly Media.

#### Open Questions
1. **Optimal Signal Weighting**: How should relevance signal weights be dynamically adjusted based on task type and repository characteristics?
2. **Search Performance Thresholds**: What are acceptable latency thresholds for different repository sizes in interactive coding scenarios?
3. **Language Coverage Depth**: Which programming languages require specialized search handling beyond basic token matching?
### Phase 3.3: Symbol and Dependency Analysis (Weeks 5-6)
**Objective**: Implement symbol extraction and dependency mapping
- Develop Symbol and Dependency Analyzer with AST parsing capabilities
- Integrate tree-sitter for multi-language support
- Add Language Server Protocol integration where available
- Implement regex fallback mechanisms for unsupported languages
- Develop import/export/require statement analysis
- Add configuration-driven dependency extraction from build files
- Implement call graph construction and data flow analysis
- Add circular dependency detection and special file type classification
- **Deliverable**: Complete symbol extraction and dependency mapping capabilities
- **Verification**: Symbol extraction accuracy tests, dependency mapping validation, language support verification

### Phase 3.4: Special File Handling and Metadata Management (Weeks 7-8)
**Objective**: Implement special file handling and advanced metadata management
- Develop special file detection and handling for large files
- Implement segmented reading, search-driven extraction, and structure-aware parsing
- Add summary generation and viewport concepts for large files
- Develop generated file detection via headers, directories, patterns, and VCS analysis
- Implement binary file detection and safety mechanisms
- Develop metadata extraction, reference tracking, and build process understanding
- Enhance Repository Metadata Manager with caching and change-aware updates
- Add memory-efficient storage strategies and persistence mechanisms
- **Deliverable**: Complete special file handling and repository metadata management
- **Verification**: Special file handling accuracy tests, metadata management validation, performance benchmarks

### Phase 3.5: Integration, Optimization, and Security (Weeks 9-10)
**Objective**: Integrate components, optimize performance, and implement security
- Integrate all five components into cohesive repository understanding system
- Implement end-to-end data flow from discovery to metadata management
- Add security measures: path validation, symlink protection, repository boundary enforcement
- Implement error handling and graceful degradation mechanisms
- Optimize performance through caching, algorithmic improvements, and bottlenecks removal
- Add change notifications and incremental update capabilities
- Implement memory management and resource cleanup mechanisms
- **Deliverable**: Fully integrated, secure, and optimized repository understanding system
- **Verification**: End-to-end integration tests, security testing, performance benchmarks, stress testing

### Phase 3.6: Comprehensive Testing and Validation (Weeks 11-12)
**Objective**: Validate implementation against all requirements and prepare for handoff
- Execute comprehensive unit test suite (>90% coverage target)
- Run integration tests with diverse repository fixtures
- Conduct performance testing with repositories of various sizes
- Execute security testing for boundary protection and threat mitigation
- Validate special file handling accuracy and safety mechanisms
- Conduct usability testing with sample development tasks
- Prepare documentation and handoff materials for Context Manager team
- **Deliverable**: Validated, production-ready repository understanding system
- **Verification**: All test suites pass, performance meets thresholds, security validated, ready for Context Manager integration

## Success Criteria
Phase 3 is considered complete and ready for Phase 4 when:
1. All unit and integration tests pass with >90% code coverage
2. Performance benchmarks met: <100ms for small repos (<1K files), <1s for medium repos (1K-10K files)
3. Security testing confirms effective boundary protection and threat mitigation
4. Manual validation shows accurate relevance scoring, symbol extraction, and special file handling
5. Change detection correctly identifies repository modifications with minimal latency
6. Caching demonstrates >50% performance improvement for repeated operations on same repository
7. System demonstrates graceful degradation when individual components fail
8. Memory usage remains within reasonable bounds (<100MB for medium repositories)
9. Documentation is complete and handoff materials prepared for Context Manager team
10. No critical or high-severity defects remain unresolved

## Unresolved Questions and Future Considerations

### Short-Term Resolution (During Phase 3 Implementation)
1. **Optimal Relevance Weight Tuning**: While the relevance scoring framework is defined, the optimal weights for different task types may require empirical tuning during implementation
2. **Language Support Prioritization**: Determining which languages to prioritize for full AST parser support vs. fallback mechanisms
3. **Cache Invalidation Strategies**: Determining the most effective balance between cache freshness and resource usage
4. **Change Detection Granularity**: Deciding between file-level vs. block-level change detection for repository monitoring

### Medium-Term Considerations (Phase 4-6)
1. **Semantic Code Search**: Integration of embedding-based search for conceptual similarity beyond textual matching
2. **Cross-Repository Understanding**: Understanding of dependencies and relationships across multiple repositories
3. **Build System Integration**: Deeper integration with build systems for understanding compilation and test processes
4. **Runtime Behavior Correlation**: Linking static repository understanding with dynamic runtime behavior observations

### Long-Term Research Areas (Phase 7+)
1. **Machine Learning for Code Understanding**: Training or fine-tuning models specifically for code comprehension tasks
2. **Natural Language Repository Queries**: Advanced NLP interfaces allowing natural language questions about repository structure and content
3. **Predictive Change Impact Analysis**: Using repository understanding to predict the impact of potential changes before implementation
4. **Collaborative Repository Understanding**: Sharing and synchronizing repository understanding across multiple agents or users

## Conclusion

This research provides a comprehensive foundation for Phase 3 repository understanding implementation. The proposed architecture addresses all functional requirements while considering performance, security, and scalability trade-offs. The implementation plan delivers incremental value at each stage, allowing for early validation and course correction.

The repository understanding system will enable the autonomous coding agent to operate effectively within codebases by providing accurate, efficient, and safe comprehension of repository structure, content, and relationships. This foundation is essential for all subsequent phases, particularly context management, tool use, and code editing operations.

By following this research and implementation plan, Phase 3 will deliver a robust repository understanding capability that forms a critical component of the overall autonomous coding agent architecture.