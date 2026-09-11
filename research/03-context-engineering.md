# Context Engineering

## How Should Context Be Selected?

Context selection involves choosing the most relevant information to present to the LLM for a given task while staying within token limits:

### Selection Principles
- **Relevance First**: Prioritize information directly related to the current task objective
- **Recency Weighting**: Favor recently accessed or modified information
- **Dependency Awareness**: Include prerequisites and dependents of target code
- **Hierarchical Drill-down**: Start broad, then narrow to specifics as needed
- **Task Phase Alignment**: Different contexts for planning vs execution vs verification
- **Uncertainty Compensation**: Provide more context when confidence is low
- **Redundancy Avoidance**: Prevent duplicate or substantially similar information

### Selection Strategies
- **Task Decomposition Alignment**: Map context needs to specific subtasks
- **Call Chain Inclusion**: Include functions called by and calling target functions
- **Data Flow Tracing**: Follow data inputs/outputs relevant to the modification
- **Interface Boundary Expansion**: Include relevant interface definitions and implementations
- **Configuration Context**: Include relevant config files that affect target behavior
- **Test Proximity**: Consider test files that exercise the code being modified
- **Documentation Association**: Link to relevant comments, docstrings, or external docs

### Algorithmic Approaches
- **Relevance Scoring**: Weighted combination of textual, structural, and historical signals
- **Graph-based Expansion**: Start from seed nodes, expand through dependency/import graphs
- **Attention Mimicking**: Simulate attention mechanisms to identify important contexts
- **Budget-aware Selection**: Greedy or dynamic programming approaches to maximize relevance within limits
- **Iterative Refinement**: Begin with minimal context, expand based on LLM requests or uncertainty

## How Can Unnecessary Context Be Avoided?

Minimizing unnecessary context improves focus, reduces cost, and decreases hallucination risk:

### Sources of Unnecessary Context
- **Verbosity**: Reading entire files when only small portions are needed
- **Redundancy**: Duplicate information accessible through multiple paths
- **Irrelevance**: Information not connected to current task objectives
- **Staleness**: Outdated information that doesn't reflect current state
- **Noise**: Comments, formatting, or boilerplate that doesn't contribute to understanding
- **Over-scoping**: Including broader system context when local changes suffice

### Avoidance Techniques
- **Precision Extraction**: Use search and extraction to get only needed lines/ranges
- **Deduplication Tracking**: Maintain awareness of already-provided context to prevent repeats
- **Relevance Thresholding**: Filter out low-scoring contextual elements
- **Change-based Filtering**: Focus on recently modified or likely-to-be-modified code
- **Abstraction Layer Use**: Work at appropriate levels of abstraction (API vs implementation)
- **Viewpoint Restriction**: Limit to caller/callee perspectives when appropriate
- **Temporal Windowing**: Limit historical context to relevant time periods
- **Layer Separation**: Separate concerns (UI logic from business logic from data access)

### Context Hygiene Practices
- **Regular Pruning**: Periodically review and remove outdated context
- **Explicit Boundaries**: Define clear context limits for different operations
- **Reference Tracking**: Track what context has been provided to avoid loops
- **Usage Analysis**: Monitor which context elements are actually used by the LLM
- **Feedback Loops**: Allow LLM to request additional context rather than assuming needs

## How Should Context Budgets Work?

Context budgets manage the finite token capacity of LLMs across different operational needs:

### Budget Components
- **Base Context**: Essential system instructions, agent architecture, tool descriptions
- **Task Context**: User request, success criteria, constraints, and background
- **Repository Context**: Discovered structure, metadata, and navigation aids
- **Working Context**: Current focus files, symbols, and immediate dependencies
- **History Context**: Recent actions, observations, and intermediate results
- **Verification Context**: Test suites, lint configurations, and validation criteria
- **Buffer Reserve**: Emergency capacity for unexpected needs or clarifications

### Budget Allocation Strategies
- **Fixed Partitioning**: Pre-allocate percentages to each context type
- **Priority-based Allocation**: Fill high-priority contexts first, trickle down
- **Dynamic Rebalancing**: Shift allocation based on current phase and needs
- **Demand-responsive**: Allocate based on demonstrated usage patterns
- **Phase-aware Budgeting**: Different allocations for planning vs execution vs verification
- **Task Complexity Scaling**: Adjust budgets based on estimated task difficulty

### Budget Monitoring and Enforcement
- **Real-time Tracking**: Monitor token usage as context is assembled
- **Predictive Estimating**: Estimate costs before adding context
- **Graceful Degradation**: Remove least important context when over budget
- **User Notification**: Alert when approaching limits or requiring trade-offs
- **Budget Adjustment**: Allow user to modify allocations based on observed needs
- **Historical Baselines**: Use past performance to inform future allocations

## How Should Long Files Be Summarized?

Summarization enables understanding of large files without consuming excessive context:

### Summarization Approaches
- **Structural Summaries**: Focus on file organization, classes, functions, and interfaces
- **Purpose-driven Summaries**: Explain what the file does and why it exists
- **Interface Summaries**: Document exported/imported symbols and their contracts
- **Change-centric Summaries**: Focus on recent modifications and evolution
- **Dependency Summaries**: Highlight what the file uses and what uses it
- **Quality Attribute Summaries**: Note performance, security, or concurrency characteristics
- **Hybrid Approaches**: Combine multiple summary types based on file type and task

### Summarization Techniques
- **Extractive Summarization**: Select key sentences or passages that best represent content
- **Abstractive Summarization**: Generate new text that captures essential meaning
- **Template-based Summarization**: Fill in predefined sections about purpose, structure, etc.
- **Metadata Enhancement**: Augment summaries with file metrics, timestamps, and authorship
- **Multi-level Summaries**: Provide different detail levels (high-level overview to detailed outline)
- **Difference Highlighting**: Focus on what changed from previous versions or baselines

### Implementation Considerations
- **Language-awareness**: Use language-specific parsers for better structural understanding
- **Prompt Engineering**: Craft effective prompts for abstractive summarization when needed
- **Quality Validation**: Verify summaries don't omit critical information
- **Incremental Updates**: Update summaries when files change rather than regenerating
- **Task-specific Tailoring**: Adjust summary focus based on current task objectives
- **Caching Strategies**: Store summaries to avoid recomputation for unchanged files

## When Should the Agent Expand Context?

Context expansion should be driven by demonstrated need rather than speculative preparation:

### Expansion Triggers
- **LLM Request**: Explicit requests for more information from the language model
- **Uncertainty Signals**: LLM expresses doubt, asks clarifying questions, or provides low-confidence answers
- **Failed Attempts**: Actions based on current context fail or produce unexpected results
- **Missing References**: LLM refers to symbols, files, or concepts not in current context
- **Incomplete Understanding**: LLM summaries or explanations show gaps in comprehension
- **Verification Failures**: Tests or checks fail due to lack of contextual understanding
- **Tool Requirements**: Specific tools need additional context to operate effectively

### Expansion Strategies
- **Targeted Expansion**: Provide only the specific information requested or needed
- **Progressive Disclosure**: Expand in stages, evaluating usefulness at each step
- **Related Context Inclusion**: When expanding for X, also include closely related Y and Z
- **Alternative Presentation**: Offer different ways to consume the same information (summary vs detail)
- **Cross-reference Provision**: Help LLM connect new context to existing knowledge
- **Expansion Justification**: Briefly explain why additional context is being provided
- **Rollback Capability**: Ability to retract expansion if proven unnecessary

### Expansion Boundaries
- **Maximum Expansion Limits**: Prevent runaway context growth
- **Relevance Decay**: Diminish returns on increasingly distant context
- **Cost Awareness**: Consider token cost against expected benefit
- **Diminishing Returns**: Stop when additional context provides minimal new value
- **Task Drift Prevention**: Avoid expanding into areas unrelated to current objectives
- **User Control**: Allow users to set expansion preferences or require approval

## How Should Previous Tool Results Be Reused?

Reusing tool results avoids redundant work and builds upon established knowledge:

### Result Classification
- **Factual Results**: Objective information unlikely to change (file contents, directory listings)
- **Derivative Results**: Computed or analyzed information (search results, dependency graphs)
- **Temporal Results**: Time-sensitive information that may change (running processes, network states)
- **Experimental Results**: Outcomes of trials or attempts (patch applications, test runs)
- **State-changing Results**: Results that modify the environment (file writes, command executions)
- **Diagnostic Results**: Information about system health or problems (error messages, performance metrics)

### Reuse Policies by Result Type
- **Factual Results**: Safe to reuse until explicit invalidation or time-based expiry
- **Derivative Results**: Reuse with validation that inputs haven't changed significantly
- **Temporal Results**: Short reuse windows or require revalidation before use
- **Experimental Results**: Reuse as historical data but not as predictive guarantees
- **State-changing Results**: Generally not reusable as they represent past states
- **Diagnostic Results**: Reuse for trend analysis but verify current state independently

### Reuse Mechanisms
- **Result Caching**: Store results with metadata for future retrieval
- **Dependency Tracking**: Know what inputs produced each result to validate freshness
- **Version Association**: Link results to specific file/content versions or timestamps
- **Invalidation Strategies**: Define when results become stale (time, file changes, etc.)
- **Result Chaining**: Build new results upon previous ones when appropriate
- **Confidence Scoring**: Indicate reliability of reused results based on age and volatility
- **Transparent Sourcing**: Clearly indicate when information is reused vs freshly obtained

### Reuse Optimization
- **Pre-fetching**: Anticipate likely needed results and prepare them in advance
- **Batch Processing**: Execute similar tool calls together for efficiency
- **Incremental Updates**: Update results based on changes rather than recomputing
- **Result Specialization**: Create task-specific variants of general results
- **Lossy Compression**: Store summaries or key points when full fidelity unnecessary
- **Sharing Across Tasks**: Reuse results when working on related or similar tasks

## How Should Duplicate Context Be Avoided?

Preventing duplicate context preserves precious token capacity for novel information:

### Sources of Duplication
- **Multiple Access Paths**: Same information reachable via different routes (different search terms, traversal paths)
- **Overlapping Extractions**: Adjacent or overlapping ranges from the same file
- **Redundant Summaries**: Multiple summaries covering similar ground
- **Historical Repetition**: Re-presenting information already seen in previous steps
- **Template Similarity**: Boilerplate code or standard patterns appearing in multiple places
- **Import/Export Duplication**: Seeing both definition and usage of the same symbol
- **Test Redundancy**: Multiple tests exercising the same code paths

### Detection Techniques
- **Content Hashing**: Use cryptographic hashes to identify identical content
- **Similarity Thresholding**: Flag substantially similar content using text similarity metrics
- **Structural Equivalence**: Detect same functions/classes accessed via different paths
- **Coverage Analysis**: Track what percentage of new context overlaps with existing
- **Semantic Deduplication**: Identify functionally equivalent code despite syntactic differences
- **Namespace Qualification**: Distinguish between same-named entities in different modules
- **Version Awareness**: Recognize when seeing different versions of the same entity

### Prevention Strategies
- **Seen Tracking**: Maintain record of already-provided context (by hash, path, or identifier)
- **Access Path Coordination**: Prefer consistent paths to information to reduce variation
- **Range Merging**: Combine overlapping or adjacent extractions into single ranges
- **Summary Consolidation**: Merge related summaries rather than maintaining multiple
- **Timeline Awareness**: Avoid re-presenting chronological sequences unnecessarily
- **Abstraction Lifting**: Move to higher abstraction levels where duplicates converge
- **User-guided Deduplication**: Allow users to identify and eliminate redundancies
- **Canonical Selection**: Choose one representative when multiple equivalents exist

### Management Approaches
- **Incremental Deduplication**: Check for duplicates as each context element is added
- **Batch Deduplication**: Process accumulated context to remove duplicates
- **Real-time Filtering**: Prevent duplicates from entering context in the first place
- **Post-compaction**: Periodically review and compress context to eliminate duplicates
- **Hierarchical Organization**: Structure context to make duplicates apparent
- **Quality Metrics**: Track duplicate ratio as a context quality indicator
- **Recovery Strategies**: Have fallback plans when over-aggressive deduplication removes needed context

## Architectural Recommendations

Based on the research questions, a robust context engineering system should:

1. **Implement principled context selection** combining relevance, recency, dependency, and task alignment
2. **Deploy multi-layered duplication avoidance** using content hashing, similarity detection, and structural awareness
3. **Establish dynamic context budgeting** with phase-aware allocation, real-time monitoring, and graceful degradation
4. **Create intelligent summarization capabilities** tailored to file types, tasks, and multiple detail levels
5. **Define clear context expansion triggers** driven by LLM requests, uncertainty signals, and verification needs
6. **Build robust tool result reuse systems** with classification-sensitive policies, caching, and dependency tracking
7. **Implement comprehensive duplicate prevention** through seen tracking, access coordination, and canonical selection
8. **Provide context quality metrics** to monitor effectiveness and guide improvements
9. **Enable user oversight and control** over context decisions with visibility into selection rationale
10. **Design for incremental evolution** allowing context strategies to improve based on empirical feedback

This approach ensures the agent maintains optimal contextual awareness—providing the LLM with precisely what it needs to make good decisions while avoiding the pitfalls of context overload, redundancy, and wasted resources.