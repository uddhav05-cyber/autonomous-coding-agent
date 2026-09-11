# Coding Agent Architecture

## What Constitutes an AI Coding Agent?

An AI coding agent is a software system that uses large language models (LLMs) to autonomously perform software engineering tasks. Unlike simple code generators, coding agents:

1. **Understand task requirements** in natural language
2. **Explore and comprehend** existing codebases
3. **Make decisions** about what changes to make
4. **Execute changes** through controlled tool use
5. **Verify their work** using tests and other validation
6. **Recover from failures** through iterative repair
7. **Operate within defined boundaries** (workspace, permissions, etc.)

Key characteristics that distinguish coding agents from LLMs or simple assistants:
- **Agency**: Ability to initiate and persist in goal-directed behavior
- **Tool use**: Capacity to interact with development tools (editors, terminals, version control)
- **Feedback loops**: Mechanisms to observe results and adjust behavior
- **State maintenance**: Tracking of progress, context, and decision history
- **Boundary awareness**: Understanding of operational limits and safety constraints

## Common Agent Execution Loops

Several execution loop patterns have emerged in AI agent architectures:

### 1. ReAct (Reasoning + Acting) Loop
- **Reason**: Analyze current state and task progress
- **Act**: Select and execute appropriate tools
- **Observe**: Process results and update understanding
- Repeat until task completion or termination condition

### 2. Plan-Execute-Verify Loop
- **Plan**: Create detailed implementation plan based on task analysis
- **Execute**: Carry out planned actions using available tools
- **Verify**: Check correctness of executed actions
- **Repair**: If verification fails, diagnose and fix issues
- Repeat planning-execution-verification cycles as needed

### 3. Bounded Iteration Loop
- Fixed number of iterations or time budget
- Each iteration makes progress toward goal
- Early termination if goal achieved
- Graceful degradation when budget exhausted

### 4. State Machine Loop
- Defined states (e.g., IDLE, PLANNING, EXECUTING, VERIFYING, REPAIRING)
- Transitions triggered by events or conditions
- Clear entry/exit actions for each state
- Termination when reaching SUCCESS or FAILURE state

## Separation of Planning and Execution

Effective coding agents separate planning from execution to improve reliability and reduce cognitive load on the LLM:

### Planning Phase Responsibilities
- Task decomposition into manageable subtasks
- Identification of affected components and dependencies
- Risk assessment and mitigation strategies
- Resource estimation and timeline projection
- Creation of detailed, actionable implementation steps
- Consideration of alternative approaches and trade-offs

### Execution Phase Responsibilities
- Precise implementation of planned actions
- Tool selection and parameterization
- Error handling and recovery during execution
- Progress tracking and status reporting
- Adherence to safety constraints and boundaries
- Documentation of actual changes made

### Benefits of Separation
- Reduced token consumption during execution (less reasoning needed)
- Improved reliability through deterministic execution of well-defined plans
- Better error isolation (planning vs execution errors)
- Enhanced verifiability (can check if execution matched plan)
- Enables different optimization strategies for each phase

## State Representation

Effective state management is crucial for agent coherence and long-term task persistence:

### Essential State Components
- **Task Context**: Original user request, success criteria, constraints
- **Progress Tracking**: Completed steps, current focus, remaining work
- **Codebase Understanding**: File mappings, symbol tables, dependency graphs
- **Decision History**: Choices made, alternatives considered, rationale
- **Tool Usage Log**: Commands executed, results obtained, timing
- **Verification Results**: Test outcomes, lint issues, type errors
- **Resource Metrics**: Token usage, time elapsed, API calls made
- **Error State**: Failure details, retry counts, diagnostic information

### State Storage Approaches
- **In-memory**: Fast access, volatile (suitable for short sessions)
- **File-based**: Persistent, shareable, queryable (JSON, SQLite)
- **Database**: Structured querying, relationships, scaling (PostgreSQL, Redis)
- **Hybrid**: Active state in memory, checkpoints to persistent storage

### State Update Principles
- **Atomicity**: State updates should be complete and consistent
- **Auditability**: All state changes should be traceable
- **Efficiency**: Minimize overhead of state maintenance
- **Relevance**: Discard or compress irrelevant historical data

## Termination Conditions

Coding agents should have clear, predictable termination conditions:

### Success-Based Termination
- All verification criteria met (tests passing, lint clean, etc.)
- User-specified goals achieved
- Implementation satisfies acceptance criteria
- No further actionable items remain

### Failure-Based Termination
- Retry budget exhausted after repeated verification failures
- Unrecoverable error detected (permission denied, missing dependency)
- Safety violation attempted or detected
- Resource limits exceeded (time, tokens, cost)

### User-Controlled Termination
- Explicit stop command from user
- Timeout reached without completion
- User requests intervention or redirection
- Pause/resume functionality for long-running tasks

### Graceful Degradation
- Partial completion when full success unattainable
- Clear reporting of what was accomplished vs. remaining
- Preservation of useful work artifacts
- Actionable feedback for user to continue manually

## Retry Handling Strategies

Effective retry mechanisms balance persistence with resource awareness:

### Retry Classification
- **Transient Failures**: Network blips, temporary resource contention
- **Correctable Errors**: Syntax mistakes, simple logical flaws
- **Environmental Issues**: Missing dependencies, configuration problems
- **Fundamental Flaws**: Misunderstood requirements, architectural mismatches

### Retry Policies
- **Fixed Interval**: Constant delay between retries (simple but inefficient)
- **Exponential Backoff**: Increasing delays to avoid overwhelming systems
- **Jitter Addition**: Randomization to prevent thundering herd problems
- **Circuit Breaker**: Temporary cessation after repeated failures

### Retry Budget Allocation
- **Per-operation limits**: Maximum attempts for specific tool calls
- **Per-phase limits**: Attempts allocated to planning, execution, verification
- **Global limits**: Overall attempt ceiling for entire task
- **Adaptive allocation**: Dynamic adjustment based on failure patterns

### Retry Enhancement Techniques
- **Failure analysis**: Modify approach based on error patterns
- **Context enrichment**: Provide additional information for retry attempts
- **Alternative approaches**: Try different methods when one repeatedly fails
- **Escalation paths**: Involve different tools or techniques after threshold

## Failure Representation

Structured failure representation enables effective diagnosis and recovery:

### Failure Taxonomy
- **Syntax Errors**: Invalid code that won't parse or compile
- **Semantic Errors**: Code that parses but doesn't behave correctly
- **Logic Errors**: Correct syntax/semantics but wrong behavior
- **Tool Failures**: Issues with development tools themselves
- **Environmental Problems**: Missing files, wrong versions, permission issues
- **Resource Exhaustion**: Timeouts, memory limits, API rate limits
- **Specification Mismatches**: Implementation doesn't meet requirements

### Failure Data Structure
- **Error Type**: Categorization from failure taxonomy
- **Location**: File, function, line number where failure manifested
- **Message**: Human-readable error description
- **Technical Details**: Stack traces, exit codes, tool-specific data
- **Context**: State at time of failure, relevant variables
- **Reproduction Steps**: How to recreate the failure condition
- **Suggested Fixes**: Potential remedies based on error analysis
- **Severity**: Impact level on task completion (blocking, degrading, advisory)

### Failure Communication
- **Structured Format**: JSON or similar for machine processing
- **Human Readable**: Clear explanations for user consumption
- **Actionable Information**: Specific guidance on next steps
- **Historical Context**: Patterns across multiple failures
- **Visual Indicators**: Clear marking in UI or logs

## Human Approval Requirements

Determining when human intervention is necessary involves balancing autonomy with safety:

### Automatic Approval Criteria
- **Low-risk operations**: Formatting, renaming, comments
- **Reversible changes**: Modifications easily undone by version control
- **Well-tested domains**: Areas with comprehensive test coverage
- **Pre-approved patterns**: Previously reviewed and accepted code patterns
- **Isolated changes**: Modifications with minimal coupling to other code

### Mandatory Human Review Triggers
- **Security-sensitive areas**: Authentication, authorization, data handling
- **Architectural modifications**: Changes to core structure or interfaces
- **Public API modifications**: Changes affecting external consumers
- **Data model alterations**: Schema changes affecting persistence
- **Performance-critical code**: Sections with strict timing requirements
- **Legal/compliance boundaries**: Areas subject to regulatory requirements
- **High-impact changes**: Modifications affecting many users or systems

### Approval Mechanisms
- **Pre-execution review**: Human examines plan before implementation
- **Post-execution review**: Human verifies results after implementation
- **Continuous oversight**: Real-time monitoring with veto capability
- **Selective checkpointing**: Approval required at key milestones
- **Rollback authority**: Human can revert changes after the fact

### Approval Workflow Design
- **Clear presentation**: Understandable diffs, rationales, impacts
- **Context provision**: Relevant surrounding code and documentation
- **Alternative presentation**: Multiple ways to review (side-by-side, unified)
- **Feedback collection**: Structured mechanism for human input
- **Decision recording**: Audit trail of approvals and rejections
- **Escalation paths**: Procedures for unresolved disagreements

## Architectural Recommendations

Based on the research questions, a robust coding agent architecture should:

1. **Adopt a Plan-Execute-Verify-Recover loop** as the core execution pattern
2. **Strictly separate planning from execution** phases with clear interfaces
3. **Maintain rich, structured state** encompassing task context, progress, and diagnostics
4. **Define explicit termination conditions** for success, failure, and user control
5. **Implement intelligent retry policies** with failure analysis and budget allocation
6. **Structure failures as rich, actionable data** enabling effective recovery
7. **Establish clear criteria for human approval** balancing autonomy with safety
8. **Provide multiple approval mechanisms** matched to risk and impact levels
9. **Ensure state persistence** for long-running tasks and crash recovery
10. **Design for observability** with comprehensive logging and metrics collection

This approach provides a foundation for building reliable, transparent, and controllable AI coding agents that can safely operate in real-world software development environments.