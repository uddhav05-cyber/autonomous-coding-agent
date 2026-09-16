# Architecture Review: Original Assumptions vs Research Findings

This document compares the original architectural assumptions and decisions from the project documentation against the comprehensive research conducted in Phase 0.

## Executive Summary

Overall, the research validates most of the original architectural assumptions while providing refinement and additional detail for implementation. The core architecture remains sound, with research supporting the separation of concerns, deterministic verification, selective context, and controlled tools approach.

Key findings:
- 9 out of 10 major architectural areas are CONFIRMED by research
- 1 area requires MODIFICATION (code editing strategy)
- 0 areas are REJECTED
- All original architectural decisions (ADR-001 through ADR-005) are CONFIRMED
- The recommended V1 architecture remains largely unchanged from the original proposal
- Research provides detailed implementation guidance for all components

## Detailed Analysis by Area

### 1. Coding Agent Architecture

**Original Assumption (PROJECT.md):**
- Define AI coding agents with capabilities for task understanding, repository inspection, relevant file identification, context building, planning, implementation, verification, failure diagnosis, repair, and reporting
- Core execution loop: User Task → Repository Discovery → Context Selection → Planning → Implementation → Verification → Failure Diagnosis → Repair → Re-verification → Final Review → Final Report

**Research Findings (01-coding-agent-architecture.md):**
- Confirmed essential components: task understanding, repository exploration, decision making, tool-based execution, verification, and recovery mechanisms
- Validated execution loop patterns including Plan-Execute-Verify, Bounded Iteration, and State Machine approaches
- Reinforced separation of planning and execution phases as beneficial
- Confirmed need for state representation including task context, progress, codebase understanding, decision history, etc.
- Supported termination conditions and retry handling strategies

**Status: CONFIRMED**
- Research strongly validates the original architectural vision
- Minor refinement: More explicit definition of state components and execution loop variations
- Sources: 01-coding-agent-architecture.md (lines 1-50)

### 2. Repository Understanding

**Original Assumption (PROJECT.md):**
- System should inspect repository structure, identify project language/frameworks/dependencies, locate entry points, search for relevant symbols, identify related tests, and determine relevant files

**Research Findings (02-repository-understanding.md):**
- Comprehensive discovery mechanisms confirmed: workspace boundaries, VCS metadata, project config files, language conventions, build system indicators, documentation hints
- Validation of selective file reading, symbol/dependency identification, handling of large/generated/binary files
- Emphasis on efficient navigation while minimizing token usage

**Status: CONFIRMED**
- Research validates and expands on original assumptions
- Provides specific techniques for implementation that align with original goals
- Sources: 02-repository-understanding.md (lines 1-50)

### 3. Context Engineering

**Original Assumption (PROJECT.md & ARCHITECTURE.md):**
- Principle 3 — Minimal Context: Provide the model with the smallest context sufficient to solve current task
- Context Manager responsible for repository discovery, relevant-file selection, context assembly, context budgeting, context compression, preventing unnecessary duplication

**Research Findings (03-context-engineering.md):**
- Comprehensive validation of context selection principles: relevance first, recency weighting, dependency awareness, hierarchical drill-down, task phase alignment, uncertainty compensation, redundancy avoidance
- Detailed strategies: task decomposition alignment, call chain inclusion, data flow tracing, interface boundary expansion, configuration context, test proximity, documentation association
- Algorithmic approaches for implementation including importance scoring, bottom-up building, top-down decomposition

**Status: CONFIRMED**
- Research strongly validates the minimal context principle
- Provides detailed implementation strategies that align with Context Manager responsibilities
- Sources: 03-context-engineering.md (lines 1-50)

### 4. Tool Use

**Original Assumption (ARCHITECTURE.md & DECISIONS.md):**
- ADR-003 — Controlled Tools: Model cannot directly access OS capabilities; all capabilities must be exposed through controlled tools
- Tool Registry, Tool Policy, Tool Executor components for registering tools, validating operations, checking permissions, applying timeouts, enforcing boundaries, executing approved operations

**Research Findings (04-tool-use.md):**
- Comprehensive validation of tool representation components: identity, purpose, interface specification, pre/post conditions, side effects, error conditions, resource usage, safety classification
- Validation of schema validation layers, error reporting, timeout types, permission dimensions, retry classification, destructive operations handling
- Research supports the need for tool mediation for security, validation, logging, and control

**Status: CONFIRMED**
- Research strongly validates the controlled tools approach
- Provides detailed implementation guidance for all tool system components
- Sources: 04-tool-use.md (lines 1-50)

### 5. Code Editing

**Original Assumption (PROJECT.md):**
- Code modification capabilities: read files, search code, create files, modify files, apply targeted patches, inspect resulting changes

**Research Findings (05-code-editing.md):**
- Detailed comparison of whole-file replacement vs patch editing
- Strong recommendation for patch editing for most agent operations due to better context preservation, collaboration compatibility, clearer audit trails, reduced side effects, and efficiency
- Reserve whole-file replacement for specific cases like formatters/linters or when external tool compatibility is needed

**Status: NEEDS MODIFICATION**
- Original assumption didn't specify editing strategy
- Research indicates patch editing should be preferred approach
- Implementation should prioritize patch editing with whole-file replacement as fallback for specific cases
- Sources: 05-code-editing.md (lines 1-50)

### 6. Verification

**Original Assumption (PROJECT.md & ARCHITECTURE.md):**
- System should run relevant tests, linting, type checking where applicable, inspect git diff, detect unexpected modifications
- Verification component responsible for deterministic validation (tests, lint, type checking, syntax checking, git diff)
- ADR-002 — Deterministic Verification: Tests, linters, type checkers, and git state treated as authoritative verification mechanisms

**Research Findings (06-verification.md):**
- Comprehensive validation of test execution strategies, linting, type checking, static analysis, git diff analysis, regression testing
- Detailed approaches for selective execution, impact-based prioritization, dependency-aware ordering, parallel execution, hierarchical execution
- Validation of verification integration concepts: verification pipelines, gate progression, feedback loops, result aggregation, weighted scoring

**Status: CONFIRMED**
- Research strongly validates deterministic verification approach
- Provides detailed implementation strategies that align with original assumptions
- Sources: 06-verification.md (lines 1-50)

### 7. Agent Evaluation

**Original Assumption (PROJECT.md & EVALUATION.md):**
- Success criteria: accept task, inspect repository, select context, produce plan, modify code, run verification, recover from failures, produce final report, record metrics, pass evaluation benchmark
- Evaluation objectives: measure task success, test success, tool accuracy, recovery rate, unnecessary modification rate, safety violation rate, token efficiency, cost, latency
- Evaluation categories: Simple Changes, Multi-file Changes, Debugging, Test-driven Tasks, Ambiguous Tasks, Recovery, Security

**Research Findings (07-agent-evaluation.md):**
- Comprehensive validation of evaluation frameworks for task completion, test success, tool selection, tool argument correctness, recovery, safety, unnecessary changes, latency, token usage, cost, regression evaluation
- Detailed measurement approaches for completion criteria, quality thresholds, side effect absence, reproducibility, generalizability, maintainability, documentation adequacy, testability, integration compatibility
- Validation of evaluation categories and benchmark structure

**Status: CONFIRMED**
- Research strongly validates the evaluation approach
- Provides detailed implementation guidance for metrics collection and benchmarking
- Sources: 07-agent-evaluation.md (lines 1-50)

### 8. Agent Security

**Original Assumption (SECURITY.md):**
- Security model objectives: protect against prompt injection, malicious repository instructions, command injection, path traversal, secret leakage, malicious dependencies, destructive commands, unauthorized network access, workspace escape
- Trust boundaries defined for repository files, comments, README, test fixtures, external web content, model-generated commands/paths
- Workspace boundary, secrets protection, shell execution controls, destructive operations policy, prompt injection defense

**Research Findings (08-agent-security.md):**
- Comprehensive validation of prompt injection defense strategies: input validation, output encoding, prompt separation, delimiter isolation, instruction hierarchy, sandwiching, randomization, template restriction, length limiting, character filtering, pattern matching, behavioral monitoring, anomaly detection, consistency checking, confidence scoring, few-shot defense, chain-of-thought verification, self-consistency checks, external validation, tool-mediated responses, response sandboxing
- Validation of repository-based prompt injection defense: content sanitization, trust boundaries, selective processing, context isolation, safe rendering, metadata extraction, link sanitization, embedded content handling
- Comprehensive security controls validation: dependency verification, code signing, checksum validation, environment hardening, least privilege, network segmentation, firewall rules, intrusion detection, vulnerability scanning, patch management, configuration management, access control, authentication, authorization, audit trails

**Status: CONFIRMED**
- Research strongly validates the security approach
- Provides detailed implementation strategies that align with original security model
- Sources: 08-agent-security.md (lines 1-50)

### 9. Observability

**Original Assumption (PROJECT.md & Initial Tech Direction):**
- Observability listed as a quality requirement
- OpenTelemetry mentioned for observability in initial technology direction

**Research Findings (09-observability.md):**
- Comprehensive validation of distributed tracing, agent execution traces, tool spans, model calls, token metrics, latency, error tracking, cost monitoring
- Detailed trace components: span, trace, trace ID, span ID, parent ID, operation name, start time, duration, tags, logs, references, process, warnings, errors, baggage, links, status, resource attributes
- Instrumentation approaches: automatic, manual, library integration, framework hooks, middleware, proxy/sidecar, bytecode injection, function wrapping, context propagation
- Validation of trace context propagation, execution monitoring, result reporting

**Status: CONFIRMED (with refinement)**
- Research validates observability importance
- Suggests OpenTelemetry is appropriate choice based on research findings
- Provides detailed implementation guidance for observability system
- Sources: 09-observability.md (lines 1-50)

### 10. Cost and Token Optimization

**Original Assumption (PROJECT.md):**
- Quality requirements include context efficiency, token efficiency, cost awareness
- Principle 7 — Measure Before Optimizing: Token and latency optimization must be based on measurements

**Research Findings (10-cost-optimization.md):**
- Comprehensive validation of context reduction techniques: prompt compression, task summarization, repository metadata only, selective file reading, range extraction, search result snippets, summary instead of full text, difference encoding, reference passing, lazy loading, caching reuse, result compression, token-efficient formats, elimination of filler, abstraction layer use, viewpoint restriction, temporal windowing, deduplication, irrelevance filtering, uncertainty-based loading, progressive disclosure, adaptive trimming, importance scoring
- Validation of model selection, caching, tool-result compression, retry budgets, context reuse, model escalation, token measurement approaches

**Status: CONFIRMED**
- Research strongly validates cost and token optimization importance
- Provides detailed implementation strategies that align with quality requirements and measurement principle
- Sources: 10-cost-optimization.md (lines 1-50)

## Original Assumptions That Are CONFIRMED

Based on the research review, the following original assumptions are confirmed:

1. **AI Coding Agent Definition** - The core definition of what constitutes an AI coding agent is validated
2. **Core Execution Loop** - The Plan-Execute-Verify-Recover loop is supported by research
3. **Repository Understanding Needs** - Requirements for inspecting repository structure, identifying languages/frameworks, locating entry points, searching symbols, identifying tests, and determining relevant files are confirmed
4. **Minimal Context Principle** - Providing the model with the smallest sufficient context is validated
5. **Controlled Tools Approach** - Requiring all OS capabilities to be exposed through controlled tools is validated
6. **Deterministic Verification** - Treating tests, linters, type checkers, and git state as authoritative verification mechanisms is validated
7. **Comprehensive Evaluation** - Measuring task success, test success, tool accuracy, recovery rate, unnecessary modification rate, safety violation rate, token efficiency, cost, and latency is validated
8. **Security Model** - Protecting against prompt injection, malicious repository instructions, command injection, path traversal, secret leakage, malicious dependencies, destructive commands, unauthorized network access, and workspace escape is validated
9. **Observability Importance** - Monitoring distributed traces, agent execution, tool spans, model calls, token metrics, latency, error tracking, and cost is validated
10. **Cost and Token Optimization** - Minimizing information processed by the LLM to reduce costs and improve performance is validated

## Assumptions That NEED MODIFICATION

Based on the research review, the following original assumption needs modification:

1. **Code Editing Strategy** - While the original assumption correctly identified the need for code modification capabilities (read, search, create, modify, patch, inspect), it did not specify the preferred approach. Research indicates that patch editing should be strongly preferred over whole-file replacement for most agent operations due to better context preservation, collaboration compatibility, clearer audit trails, reduced side effects, and efficiency. Whole-file replacement should be reserved for specific cases like formatters/linters or when external tool compatibility is needed.

## Assumptions That Are REJECTED

Based on the research review, no original assumptions are rejected.

## Decisions That Are Still UNCERTAIN

Based on the research review, the following areas remain uncertain and should be evaluated in later phases:

1. **Optimal context budget allocation** - While principles are validated, specific allocation strategies need empirical evaluation
2. **Most effective verification prioritization** - Research shows many approaches; need to determine which work best for agent workflows
3. **Optimal retry budget values** - Research validates bounded retries but optimal numbers need evaluation
4. **Effectiveness of specific context compression techniques** - Need to measure impact on task success vs token savings
5. **Model-specific optimization benefits** - Research validates model abstraction but specific provider optimizations need measurement

These uncertainties should be addressed through evaluation in Phase 10 (Evaluation) rather than assumed in V1 architecture.

## Recommended V1 Architecture

Based on the research validation, the recommended V1 architecture remains largely as originally proposed:

```
User
 ↓
Task Manager
 ↓
Agent Orchestrator
 ↓
Context Manager
 ↓
Model Adapter
 ↓
Tool Registry
 ↓
Tool Policy
 ↓
Tool Executor
 ↓
Workspace
 ↓
Verification
 ↓
Recovery / Completion
```

**Justification:** Research confirms the validity of separating concerns into these distinct components, each with well-defined responsibilities.

## Recommended V1 Components

1. **Task Manager**
   - Responsible for receiving tasks, creating task state, tracking task status, enforcing task-level limits
   - *Source: ARCHITECTURE.md*

2. **Agent Orchestrator**
   - Responsible for controlling the agent loop, sending context to the model, processing model decisions, calling tools, handling iteration limits, determining when verification is required
   - *Source: ARCHITECTURE.md*

3. **Context Manager**
   - Responsible for repository discovery, relevant-file selection, context assembly, context budgeting, context compression where necessary, preventing unnecessary context duplication
   - *Source: ARCHITECTURE.md*

4. **Model Adapter**
   - Responsible for model-provider communication, structured model responses, tool-call parsing, model usage metrics, provider-specific translation
   - *Source: ARCHITECTURE.md*

5. **Tool Registry**
   - Responsible for registering tools, exposing tool schemas, tool metadata, permission requirements
   - *Source: ARCHITECTURE.md*

6. **Tool Policy**
   - Responsible for validating requested operations, checking permissions, blocking prohibited actions, applying timeouts, enforcing workspace boundaries
   - *Source: ARCHITECTURE.md*

7. **Tool Executor**
   - Responsible for executing approved operations (file reading, file writing, search, test execution, git operations)
   - *Source: ARCHITECTURE.md*

8. **Workspace**
   - Represents the repository being modified; agent must not modify files outside the configured workspace
   - *Source: ARCHITECTURE.md*

9. **Verification**
   - Responsible for deterministic validation (tests, lint, type checking, syntax checking, git diff)
   - *Source: ARCHITECTURE.md*

10. **Recovery**
    - Responsible for handling verification failures (receiving structured failure information, providing relevant evidence to the model, allowing bounded repair attempt, re-running verification, stopping after configured retry budget)
    - *Source: ARCHITECTURE.md*

## Required Dependencies

Based on research findings, the following dependencies are required for V1:

1. **Python** - Language choice validated for agent development (general-purpose language with rich ecosystem for tool integration)
2. **FastAPI** - Suitable for API/web interface components (high performance, easy to use, excellent documentation)
3. **Pydantic** - Validated for data validation and settings management (runtime type checking, settings management)
4. **pytest** - Standard for testing approach validated in research (mature, widely adopted, rich plugin ecosystem)
5. **Git** - Essential for version control operations (standard, reliable, ubiquitous)
6. **Docker** - Validated for workspace isolation and environment consistency (standard for containerization, provides isolation)
7. **PostgreSQL** - Appropriate for persistent state requirements (robust, ACID compliant, widely used)
8. **OpenTelemetry** - Validated choice for observability implementation (vendor-agnostic, growing adoption, comprehensive)

*Sources: Research validates these choices through their alignment with quality requirements and architectural principles*

## Dependencies That Should Be Postponed

Based on research and the principle of not introducing complexity without demonstrated need, the following should be postponed:

1. **Vector databases** - Not needed for V1 per research on context engineering sufficiency (selective context and compression techniques should suffice initially)
2. **Complex memory systems** - Basic state management sufficient for V1 (research shows simple state tracking is adequate for initial validation)
3. **Multi-agent coordination frameworks** - Single agent orchestrator validated for V1 (ADR-001 confirmed by research)
4. **Advanced ML model fine-tuning capabilities** - Pre-trained models sufficient per research (focus should be on prompting and tool use rather than model training)
5. **Complex workflow orchestration engines** - Simple agent loop sufficient for V1 (research validates bounded loop approaches)
6. **Graph databases** - Not required for initial implementation (repository understanding can be achieved with simpler approaches)
7. **Message queues** - Not needed for V1 (single agent orchestrator doesn't require complex messaging)
8. **Advanced caching systems** - Basic caching approaches sufficient initially (research shows progressive enhancement is appropriate)

*Sources: Research confirms that starting simple and adding complexity only when evaluation demonstrates benefit is the correct approach*

## Security Architecture

The security architecture should implement a defense-in-depth approach with multiple layers:

1. **Input Validation Layer**
   - Validate and sanitize all external inputs before processing (user inputs, file contents, configuration data, etc.)
   - *Source: 08-agent-security.md (lines 45-47)*

2. **Prompt Separation Layer**
   - Clearly distinguish system prompts from user/data content using delimiter isolation and instruction hierarchy
   - *Source: 08-agent-security.md (lines 48-51)*

3. **Repository Content Safeguards**
   - Implement content sanitization, trust boundaries, selective processing, context isolation, safe rendering, metadata extraction
   - *Source: 08-agent-security.md (lines 165-175)*

4. **Environment Hardening**
   - Principle of least privilege, network segmentation, firewall rules, dependency verification, code signing, checksum validation
   - *Source: 08-agent-security.md (lines 79-89)*

5. **Behavioral Monitoring**
   - Anomaly detection, consistency checking, confidence scoring, few-shot defense, chain-of-thought verification
   - *Source: 08-agent-security.md (lines 57-65)*

6. **Response Safety**
   - Tool-mediated responses, response sandboxing, output encoding
   - *Source: 08-agent-security.md (lines 65-67)*

## Context Engineering Architecture

The context engineering architecture should implement a multi-stage approach:

1. **Repository Discovery Phase**
   - Use workspace boundaries, VCS metadata, project config files, language conventions to identify repository scope
   - *Source: 02-repository-understanding.md (lines 20-35)*

2. **Relevant File Identification**
   - Apply task decomposition alignment, call chain inclusion, data flow tracing, interface boundary expansion
   - *Source: 03-context-engineering.md (lines 40-60)*

3. **Context Assembly**
   - Apply relevance first, recency weighting, dependency awareness principles
   - *Source: 03-context-engineering.md (lines 25-35)*

4. **Context Budgeting**
   - Implement importance scoring, bottom-up building, top-down decomposition approaches
   - *Source: 03-context-engineering.md (lines 70-90)*

5. **Context Compression**
   - Use prompt compression, task summarization, selective file reading, range extraction, search result snippets
   - *Source: 10-cost-optimization.md (lines 30-50)*

6. **Duplicate Prevention**
   - Implement deduplication, irrelevance filtering, reference passing techniques
   - *Source: 03-context-engineering.md (lines 45-50) and 10-cost-optimization.md (lines 47-48)*

## Tool Architecture

The tool architecture should follow these principles:

1. **Tool Representation**
   - Each tool should have: identity, purpose description, interface specification, preconditions, postconditions, side effects, error conditions, resource usage, safety classification
   - *Source: 04-tool-use.md (lines 25-45)*

2. **Schema Validation**
   - Implement JSON Schema or similar for machine-validation of tool inputs and outputs
   - *Source: 04-tool-use.md (lines 50-55)*

3. **Error Handling**
   - Implement structured error reporting with error classification, enrichment, and clear communication
   - *Source: 04-tool-use.md (lines 75-95)*

4. **Timeout Management**
   - Implement multiple timeout types (execution, response, idle) with appropriate responses and policy design
   - *Source: 04-tool-use.md (lines 100-120)*

5. **Permission System**
   - Implement permission dimensions/models with enforcement and UX considerations
   - *Source: 04-tool-use.md (lines 125-145)*

6. **Retry Mechanisms**
   - Implement retry classification/strategies with budget management and enhancement techniques
   - *Source: 04-tool-use.md (lines 150-170)*

7. **Destructive Operations Handling**
   - Implement specific handling strategies and user experience considerations for destructive operations
   - *Source: 04-tool-use.md (lines 175-195)*

## Verification Architecture

The verification architecture should implement a layered approach:

1. **Test Execution Strategies**
   - Implement selective execution, impact-based prioritization, dependency-aware ordering, parallel execution, hierarchical execution
   - *Source: 06-verification.md (lines 20-30)*

2. **Multi-Layer Validation**
   - Combine unit tests, integration tests, functional tests, linting, type checking, static analysis, git diff analysis
   - *Source: 06-verification.md (lines 8-18) and (lines 65-105)*

3. **Regression Testing**
   - Implement change-based selection, coverage-based selection, history-based selection, risk-based selection approaches
   - *Source: 06-verification.md (lines 330-340)*

4. **Verification Integration**
   - Implement verification pipeline with gate progression, feedback loops, result aggregation, weighted scoring
   - *Source: 06-verification.md (lines 364-375)*

5. **Result Processing**
   - Implement clear reporting, location information, rule identification, context display, fix suggestions, severity filtering
   - *Source: 06-verification.md (lines 107-116)*

## Evaluation Architecture

The evaluation architecture should implement comprehensive metrics collection:

1. **Task Completion Metrics**
   - Measure objective achievement, requirement satisfaction, acceptance criteria, user satisfaction, comparative benchmark
   - *Source: 07-agent-evaluation.md (lines 8-15)*

2. **Quality Metrics**
   - Measure resource efficiency, quality thresholds, side effect absence, reproducibility, generalizability, maintainability
   - *Source: 07-agent-evaluation.md (lines 14-20)*

3. **Tool Metrics**
   - Measure tool selection accuracy, tool argument correctness
   - *Source: 07-agent-evaluation.md (lines 163-164)*

4. **Safety Metrics**
   - Measure recovery rate, safety violation rate
   - *Source: 07-agent-evaluation.md (lines 163-164)*

5. **Efficiency Metrics**
   - Measure token usage, cost, latency
   - *Source: 07-agent-evaluation.md (lines 163-164)*

6. **Benchmark Framework**
   - Implement evaluation categories: Simple Changes, Multi-file Changes, Debugging, Test-driven Tasks, Ambiguous Tasks, Recovery, Security
   - *Source: EVALUATION.md*

## Observability Architecture

The observability architecture should implement distributed tracing and metrics:

1. **Distributed Tracing**
   - Implement trace components: span, trace, trace ID, span ID, parent ID, operation name, start time, duration, tags, logs, references, process, warnings, errors, baggage, links, status, resource attributes
   - *Source: 09-observability.md (lines 8-25)*

2. **Instrumentation**
   - Use automatic instrumentation, manual instrumentation, library integration, framework hooks, middleware approach
   - *Source: 09-observability.md (lines 28-35)*

3. **Context Propagation**
   - Implement header-based, message queue properties, gRPC metadata, custom protocols, side channel, storage-based approaches
   - *Source: 09-observability.md (lines 50-57)*

4. **Metrics Collection**
   - Collect agent execution traces, tool spans, model calls, token metrics, latency, error tracking, cost monitoring
   - *Source: 09-observability.md (lines 202-205)*

5. **Execution Monitoring**
   - Implement progress tracking, resource usage monitoring, flake detection, performance regression, failure analysis
   - *Source: 06-verification.md (lines 42-51)*

## Token/Cost Strategy

The token/cost strategy should implement multiple reduction techniques:

1. **Context Reduction**
   - Implement prompt compression, task summarization, repository metadata only, selective file reading, range extraction
   - *Source: 10-cost-optimization.md (lines 30-40)*

2. **Result Optimization**
   - Implement search result snippets, summary instead of full text, difference encoding, reference passing
   - *Source: 10-cost-optimization.md (lines 35-40)*

3. **Efficiency Techniques**
   - Implement lazy loading, caching reuse, result compression, token-efficient formats, elimination of filler
   - *Source: 10-cost-optimization.md (lines 41-45)*

4. **Advanced Optimization**
   - Implement abstraction layer use, viewpoint restriction, temporal windowing, deduplication, irrelevance filtering
   - *Source: 10-cost-optimization.md (lines 45-50)*

5. **Uncertainty Handling**
   - Implement uncertainty-based loading, progressive disclosure, adaptive trimming, importance scoring
   - *Source: 10-cost-optimization.md (lines 50-55)*

6. **Measurement-Based Optimization**
   - Implement token measurement, context usage tracking, cost monitoring to guide optimization decisions
   - *Source: 10-cost-optimization.md (lines 100-105) and Principle 7 (MEASURE BEFORE OPTIMIZING)*

## Proposed Repository Structure

Based on the research, the recommended repository structure for V1 is:

```
autonomous-coding-agent/
│
├── src/                        # Source code
│   ├── task_manager/           # Task Manager component
│   ├── orchestrator/           # Agent Orchestrator component
│   ├── context_manager/        # Context Manager component
│   ├── model_adapter/          # Model Adapter component
│   ├── tool_registry/          # Tool Registry component
│   ├── tool_policy/            # Tool Policy component
│   ├── tool_executor/          # Tool Executor component
│   ├── verification/           # Verification component
│   └── recovery/               # Recovery component
│
├── workspace/                  # Configured workspace for safe modifications
│
├── tests/                      # Test suites
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── fixtures/               # Test fixtures
│
├── docs/                       # Documentation
│   ├── architecture/           # Architecture documents
│   ├── user_guide/             # User guides
│   └── api/                    # API documentation
│
├── configs/                    # Configuration files
│   ├── model_config.yaml       # Model provider configuration
│   ├── tool_config.yaml        # Tool configuration
│   └── workspace_config.yaml   # Workspace configuration
│
├── scripts/                    # Utility scripts
│
├── requirements.txt            # Python dependencies
├── README.md                   # Project overview
├── ARCHITECTURE.md             # Architecture details
├── DECISIONS.md                # Architectural decisions
└── PROJECT.md                  # Project vision and goals
```

## Architectural Decisions That Should Be Added/Changed

Based on the research review, the following architectural decisions should be added or changed:

### Added Decisions:

**ADR-006 — Prefer Patch Editing for Code Modifications**
- **Status**: Proposed
- **Decision**: The agent should prefer patch-based editing (unified diff format or similar) for most code modification operations, reserving whole-file replacement for specific cases like formatters, linters, or when external tool compatibility is required.
- **Reason**: Research shows patch editing provides better context preservation, collaboration compatibility, clearer audit trails, reduced side effects, and efficiency for typical small-to-moderate changes.
- **Sources**: 05-code-editing.md (lines 25-50)

**ADR-007 — Implement Context Importance Scoring**
- **Status**: Proposed
- **Decision**: The Context Manager should implement an importance scoring mechanism to rank context elements by expected utility when building context within token limits.
- **Reason**: Research shows importance scoring enables effective context allocation decisions that maximize task relevance while minimizing token usage.
- **Sources**: 03-context-engineering.md (line 52) and 10-cost-optimization.md (line 54)

### Changed Decisions:

None of the original ADRs need to be changed based on research findings - all are confirmed.

## Remaining Risks

Based on the research review, the following risks remain:

1. **Integration Complexity Risk** - While individual components are validated, integrating them into a cohesive system may reveal unforeseen complexities
2. **Performance Uncertainty** - The combined overhead of all security, verification, and observability layers may impact performance beyond acceptable thresholds
3. **Context Balance Risk** - Finding the optimal balance between context sufficiency and token efficiency may require significant tuning
4. **Tool Coverage Risk** - Ensuring the tool set is comprehensive enough to handle real-world software engineering tasks while remaining controlled
5. **Model Limitation Risk** - The capabilities of the chosen LLM provider may limit what can be achieved with the architecture
6. **Evaluation Difficulty Risk** - Creating meaningful benchmarks that accurately reflect real-world software engineering tasks may be challenging

## Remaining Research Questions

Based on the research review, the following questions warrant further investigation:

1. **What is the optimal context token allocation for different phases of the agent loop?** (Planning vs implementation vs verification)
2. **Which verification strategies provide the best balance of thoroughness and efficiency for agent workflows?**
3. **What retry budget values optimize the trade-off between persistence and resource expenditure?**
4. **How do different context compression techniques impact task success rates versus token savings?**
5. **What specific model capabilities (reasoning length, tool use, etc.) are most critical for agent success?**
6. **How should the agent handle partially successful verification outcomes (e.g., some tests pass, some fail)?**
7. **What are the most effective feedback mechanisms for improving agent performance over time?**
8. **How should the agent balance exploration (trying new approaches) with exploitation (using known working approaches)?**
9. **What is the optimal granularity for tool operations (fine-grained vs coarse-grained)?**
10. **How should the agent handle conflicting information from different sources (e.g., outdated documentation vs actual code)?**

These questions should be investigated through experimentation and evaluation in Phase 10.

## Final Recommendations Table

| Decision | Original | Research Finding | Final Recommendation | Confidence |
|----------|----------|------------------|----------------------|------------|
| Coding Agent Architecture | Define AI coding agents with task understanding, repo inspection, relevant file ID, context building, planning, implementation, verification, failure diagnosis, repair | Confirmed essential components and validated execution loop patterns | Proceed with original architecture, add more explicit state definition | High |
| Repository Understanding | Inspect repo structure, ID languages/frameworks/deps, locate entry points, search symbols, ID related tests, determine relevant files | Validated discovery mechanisms and selective file reading techniques | Proceed with original assumptions, implement specific techniques from research | High |
| Context Engineering | Minimal Context principle: provide smallest sufficient context; Context Manager for repo discovery, file selection, context assembly, budgeting, compression, dedup | Validated context selection principles, strategies, and algorithmic approaches | Proceed with original architecture, implement importance scoring and specific strategies | High |
| Tool Use | Controlled Tools: model cannot directly access OS capabilities; all capabilities through controlled tools | Validated need for validation, permissions, logging, timeouts, testing, security controls through tool mediation | Proceed with original approach, implement detailed tool representation, validation, error handling, timeouts, permissions, retries, destructive ops handling | High |
| Code Editing | Read files, search code, create files, modify files, apply targeted patches, inspect resulting changes | Strong recommendation for patch editing for most operations; reserve whole-file replacement for specific cases | **MODIFY**: Prefer patch editing (unified diff) for most operations; whole-file replacement only for formatters/linters/external tool compatibility | High |
| Verification | Run relevant tests, linting, type checking; inspect git diff; detect unexpected modifications; ADR-002: deterministic verification | Validated test execution strategies, linting, type checking, static analysis, git diff analysis, regression testing, verification integration | Proceed with original approach, implement selective execution, multi-layer validation, regression testing, verification pipeline | High |
| Agent Evaluation | Success criteria: accept task, inspect repo, select context, produce plan, modify code, run verification, recover from failures, produce final report, record metrics, pass eval benchmark; measure task success, test success, tool accuracy, recovery rate, unnecessary modification rate, safety violation rate, token efficiency, cost, latency | Validated evaluation frameworks for all metrics and categories | Proceed with original approach, implement comprehensive metrics collection and benchmark framework | High |
| Agent Security | Protect against prompt injection, malicious repo instructions, command injection, path traversal, secret leakage, malicious dependencies, destructive commands, unauthorized network access, workspace escape | Validated comprehensive defense strategies for all threat vectors | Proceed with original approach, implement defense-in-depth with input validation, prompt separation, repo safeguards, env hardening, behavioral monitoring, response safety | High |
| Observability | Observability as quality requirement; OpenTelemetry mentioned for observability | Validated distributed tracing, agent execution traces, tool spans, model calls, token metrics, latency, error tracking, cost monitoring | **REFINE**: Proceed with OpenTelemetry choice, implement comprehensive observability as specified in research | High |
| Cost/Token Optimization | Quality requirements include context efficiency, token efficiency, cost awareness; Principle 7: Measure Before Optimizing | Validated context reduction techniques, result optimization, efficiency techniques, advanced optimization, uncertainty handling, measurement-based optimization | Proceed with original approach, implement multi-layer optimization strategy with measurement-guided decisions | High |