# Phase 6: Tool System Research

## Overview
This document outlines the research and implementation plan for the Tool System component (Phase 6) of the autonomous coding agent system. The Tool System provides controlled access to operating-system capabilities through a secure interface that enables validation, permissions, logging, timeouts, testing, and security controls.

## Components Implemented
- **Tool Interface** - Standardized representation of tool capabilities, requirements, and effects
- **Tool Registry** - Central repository for tool registration, schema exposure, and metadata management
- **Tool Schemas** - Formal definition of tool inputs, outputs, and behaviors using JSON Schema or similar
- **Tool Validation** - Multi-layer validation (syntactic, type, constraint, dependency, semantic, contextual, sequential)
- **Tool Permissions** - Fine-grained permission system validating requested operations and enforcing boundaries
- **Tool Executor** - Secure execution of approved operations with timeout and error handling
- **Initial Tools** - list_files, read_file, search_code, write_file, apply_patch

## Current Status
- [x] Tool interface design and representation standards
- [x] Tool schema validation mechanisms
- [x] Tool error reporting and enrichment strategies
- [x] Tool timeout policies and implementation approaches
- [x] Tool permission models and enforcement mechanisms
- [x] Destructive operation handling strategies
- [ ] Tool registry implementation
- [ ] Tool executor implementation
- [ ] Initial tool implementations (list_files, read_file, search_code, write_file, apply_patch)
- [ ] Integration with Model Adapter (Phase 5) and Workspace (Phase 2)

## Implementation Details

### Tool Representation
Tools should be represented in a way that enables the LLM to understand their capabilities, requirements, and effects:

#### Representation Components
- **Tool Identity**: Unique name or identifier for the tool
- **Purpose Description**: Clear, concise explanation of what the tool does
- **Interface Specification**: Formal definition of inputs, outputs, and behaviors
- **Preconditions**: Conditions that must be true before tool execution
- **Postconditions**: Expected state after successful tool execution
- **Side Effects**: Changes to system state beyond primary function
- **Error Conditions**: Situations where tool may fail and what failures look like
- **Resource Usage**: Typical time, memory, or external resource consumption
- **Safety Classification**: Risk level and potential for destructive operations

#### Representation Formats
- **Structured Schemas**: JSON Schema or similar for machine-validation
- **Natural Language Descriptions**: Human-readable explanations for LLM reasoning
- **Example Usage**: Sample invocations demonstrating typical patterns
- **Type Signatures**: Formal input/output types for statically typed understanding
- **State Transition Diagrams**: Visual representations of tool effects on system state
- **Pre/post Conditions**: Formal specifications using predicates or assertions
- **Usage Patterns**: Common sequences or combinations with other tools

### Tool Schema Validation
Schema validation ensures tools are invoked correctly and safely:

#### Validation Layers
- **Syntactic Validation**: Check that invocation matches expected format
- **Type Validation**: Verify parameter types match specifications
- **Constraint Validation**: Ensure values meet business rules and boundaries
- **Dependency Validation**: Confirm required preconditions are satisfied
- **Semantic Validation**: Check that combinations of parameters make sense
- **Contextual Validation**: Verify appropriateness given current state and task
- **Sequential Validation**: Ensure proper ordering in tool chains or workflows

#### Validation Mechanisms
- **Schema Validators**: Use JSON Schema, Pydantic, or similar libraries
- **Type Checkers**: Leverage static or runtime type systems
- **Constraint Solvers**: Validate complex inter-parameter relationships
- **State Checkers**: Consult system state to validate preconditions
- **Rule Engines**: Apply business logic validation rules
- **Whitelisting/Blacklisting**: Approve or reject specific values or patterns
- **Range Checking**: Ensure numeric values fall within acceptable bounds
- **Format Validation**: Verify strings match expected patterns (email, paths, etc.)

#### Validation Timing
- **Pre-execution**: Validate before tool runs to prevent errors
- **Post-execution**: Verify results match expected outcomes
- **Continuous**: Ongoing validation during long-running tool operations
- **Retrospective**: Audit validation effectiveness after tool use
- **Proactive**: Predict potential validation failures before invocation

### Tool Error Reporting
Tool error reporting should enable effective diagnosis and recovery:

#### Error Classification
- **Usage Errors**: Invalid parameters, missing requirements, wrong format
- **Resource Errors**: Insufficient memory, disk space, permissions, timeouts
- **Environmental Errors**: Missing dependencies, configuration issues, version mismatches
- **Operational Errors**: Tool internal failures, unexpected states, corrupted data
- **Conflict Errors**: Race conditions, lock contention, incompatible operations
- **Boundary Errors**: Attempts to exceed limits, workspace violations, safety blocks

#### Error Reporting Structure
- **Error Type**: Machine-readable categorization for automated handling
- **Human Message**: Clear, actionable description for LLM and developers
- **Technical Details**: Exit codes, stack traces, diagnostic data when appropriate
- **Context Information**: State at time of error, relevant variables, recent actions
- **Recovery Suggestions**: Potential next steps or alternative approaches
- **Severity Level**: Impact assessment (recoverable, fatal, requires intervention)
- **Retry Guidance**: Whether and how to safely retry the operation
- **Prevention Tips**: How to avoid similar errors in future invocations

#### Error Communication Mechanisms
- **Structured Returns**: JSON or similar with standardized error fields
- **Exception Objects**: Language-native exception mechanisms with rich data
- **Status Codes**: Numeric or enum codes for quick classification
- **Tuple Returns**: (success, result/error) patterns for explicit handling
- **Event Emitters**: Asynchronous error notification via events or callbacks
- **Logging Integration**: Automatic logging alongside direct return
- **Metadata Attachment**: Error information attached to results or state

#### Error Enrichment
- **Root Cause Analysis**: Determine underlying reasons beyond surface symptoms
- **Context Addition**: Provide relevant system state and recent history
- **Frequency Tracking**: Note if this is a recurring or isolated issue
- **Trend Analysis**: Compare against historical error patterns
- **Impact Assessment**: Estimate effects on current task and future operations
- **Similar Error Linking**: Connect to known issues or documented problems
- **Escalation Paths**: Indicate when human intervention may be needed

### Tool Timeouts
Timeouts prevent tools from hanging indefinitely and consuming excessive resources:

#### Timeout Types
- **Fixed Duration**: Set time limit regardless of operation (simple but inflexible)
- **Adaptive Timeout**: Base timeout on operation type, size, or historical data
- **Progress-based**: Extend timeout if tool shows productive progress
- **Checkpoint Timeout**: Require periodic check-ins to confirm liveness
- **User-configurable**: Allow users to specify timeout preferences
- **Task-aware**: Adjust based on overall task time remaining or priority
- **Resource-sensitive**: Consider system load and competing operations

#### Timeout Implementation
- **Wall-clock Timers**: Measure real elapsed time (simple but can be misleading)
- **CPU Time**: Measure actual processor consumption (fairer but complex)
- **Heartbeat Mechanisms**: Require periodic signals to confirm continued operation
- **Milestone Checking**: Verify progress toward expected completion points
- **Resource Monitoring**: Track memory, disk, or network usage as proxies
- **External Watchdogs**: Separate processes monitoring tool execution
- **Hierarchical Timeouts**: Different levels (operation, phase, task, session)

#### Timeout Responses
- **Graceful Cancellation**: Attempt clean shutdown preserving partial results
- **Forcible Termination**: Immediate stop regardless of state (risky but necessary)
- **State Preservation**: Save checkpoint or intermediate results when possible
- **Resource Cleanup**: Ensure locks, handles, and temporary resources released
- **Partial Result Return**: Return whatever progress was made before timeout
- **Escalation Signaling**: Mark operation as timed out for higher-level handling
- **User Notification**: Inform stakeholders of timeout and implications
- **Retry Decision Logic**: Determine whether timeout warrants retry attempt

#### Timeout Policy Design
- **Conservative Defaults**: Prefer shorter timeouts with extension mechanisms
- **Operation-specific Baselines**: Different timeouts for reads vs writes vs computes
- **Size-proportional Scaling**: Adjust timeouts based on data volume or complexity
- **Historical Calibration**: Base timeouts on observed performance metrics
- **Load-adaptive Adjustment**: Modify timeouts based on system conditions
- **User Override Paths**: Allow adjustment when defaults are inappropriate
- **Timeout Chaining**: Ensure nested timeouts behave predictably
- **Metrics Collection**: Track timeout frequency and causes for improvement

### Tool Permissions
Tool permissions ensure agents operate within authorized boundaries:

#### Permission Dimensions
- **Operation Type**: Read, write, execute, delete, network, etc.
- **Resource Access**: Specific files, directories, databases, devices, APIs
- **Capability Level**: Degree of access (browse, modify, administer, etc.)
- **Contextual Constraints**: Time-based, location-based, or state-based limits
- **User/Role Mapping**: Permissions tied to specific identities or groups
- **Temporal Windows**: When permissions are active or inactive
- **Geographic Limits**: Where operations may or may not occur
- **Frequency Limits**: How often certain operations may be performed

#### Permission Models
- **Allowlist/Permissive**: Explicitly permit specific operations, deny others by default
- **Denylist/Restrictive**: Explicitly forbid specific operations, allow others by default
- **Role-Based Access Control (RBAC)**: Permissions granted via roles assigned to agent
- **Attribute-Based Access Control (ABAC)**: Permissions based on agent/resource/action attributes
- **Capability-based**: Unforgeable tokens granting specific authorities
- **Hierarchical**: Permissions inherited along organizational or resource hierarchies
- **Time-bound**: Permissions that automatically expire or activate on schedule
- **Context-sensitive**: Permissions that change based on operational context

#### Permission Enforcement
- **Pre-execution Checking**: Validate permissions before allowing tool invocation
- **Runtime Monitoring**: Detect and prevent permission violations during execution
- **Post-execution Auditing**: Log permission usage for review and anomaly detection
- **Gradient Enforcement**: Warning levels before hard blocks (warn, then block)
- **Delegation Controls**: Regulate whether and how permissions can be delegated
- **Amplification Prevention**: Prevent gaining more permissions than initially granted
- **Least Privilege Application**: Start with minimal permissions, add as needed
- **Permission Expiration**: Automatically revoke unused or time-limited permissions

#### Permission User Experience
- **Explicit Consent**: Clear prompts for new or elevated permission requests
- **Granular Control**: Fine-grained approval rather than all-or-nothing
- **Contextual Explanations**: Explain why permission is needed for current task
- **Persistence Choices**: Remember decisions for similar future requests
- **Revoke Capability**: Easy withdrawal of previously granted permissions
- **Usage Transparency**: Visible history of permission exercises
- **Emergency Overrides**: Clearly marked paths for critical situations
- **Learning Systems**: Suggest permission adjustments based on usage patterns

### Retry Mechanisms
Retry mechanisms balance persistence with resource awareness and error discrimination:

#### Retry Classification by Error Type
- **Transient Errors**: Temporary issues likely to succeed on retry (network blips, resource contention)
- **Probabilistic Errors**: Intermittent failures with success chance > 0% (flaky tests, race conditions)
- **Deterministic Errors**: Consistent failures unlikely to change without intervention (bugs, missing dependencies)
- **User-correctable Errors**: Failures resolvable by user intervention (credentials, permissions)
- **Environmental Errors**: Failures due to external system states (service downtime, quota exhaustion)
- **Self-induced Errors**: Failures resulting from previous agent actions (state corruption, resource exhaustion)

#### Retry Strategies
- **Immediate Retry**: Instant retry for suspected transient glitches
- **Fixed Delay**: Constant pause between attempts (simple but can cause thundering herd)
- **Linear Backoff**: Increasing fixed increments between attempts
- **Exponential Backoff**: Delay multiplies with each attempt (good for network/contention issues)
- **Jittered Backoff**: Add randomness to prevent synchronized retries
- **Fibonacci Backoff**: Use Fibonacci sequence for delay progression
- **Adaptive Backoff**: Adjust based on error patterns and historical success rates
- **Circuit Breaker**: Temporarily stop attempts after repeated failures
- **Progressive Approaches**: Try different methods or parameters with each attempt

#### Rety Budget Management
- **Per-attempt Limits**: Maximum retries for individual tool invocations
- **Per-operation Type Limits**: Different budgets for reads, writes, computes, etc.
- **Per-session Limits**: Overall retry allowance for agent session
- **Per-task Limits**: Retry budget allocated to specific tasks or objectives
- **Adaptive Allocation**: Shift budget based on error patterns and task progress
- **Priority-based Allocation**: More retries for critical path operations
- **Expiration Policies**: Retry budgets that expire or refresh over time
- **Debt Tracking**: Account for retries consumed against allocated budgets

#### Retry Enhancement Techniques
- **Failure Analysis**: Modify approach based on error characteristics
- **Context Enrichment**: Provide additional information for retry attempts
- **Parameter Variation**: Try different inputs or configurations
- **Alternative Methods**: Use different tools or approaches to achieve same goal
- **Escalation Paths**: Involve different systems or techniques after thresholds
- **Learning Systems**: Adjust retry policies based on historical effectiveness
- **Fallback Mechanisms**: Predefined alternative approaches when retries exhausted
- **Circuit Breaker Integration**: Prevent wasting resources on obviously failing operations

#### Retry Decision Framework
- **Error Retryability**: Determine if error type warrants retry attempts
- **Cost-benefit Analysis**: Weigh retry cost against expected value of success
- **Alternatives Evaluation**: Consider other approaches before retrying same operation
- **Impact Assessment**: Evaluate effects of continued failures on broader operations
- **User Preference Respect**: Honor explicit user guidance on retry behavior
- **System State Consideration**: Factor in current load, resources, and stability
- **Historical Pattern Recognition**: Use past success rates to inform retry decisions
- **Threshold-based Triggers**: Retry only when specific conditions are met

### Destructive Operations Handling
Destructive operations require special care due to their potential for irreversible harm:

#### Destructive Operation Classification
- **Data Deletion**: Removing files, records, or other persistent information
- **State Mutation**: Changing system configuration, database contents, or application state
- **Resource Consumption**: Operations that irreversibly use quotas, credits, or limited resources
- **External Effects**: Actions affecting systems outside immediate control (network calls, API modifications)
- **Security Relevant**: Operations impacting authentication, authorization, or encryption
- **Infrastructure Changes**: Modifying deployment configurations, scaling, or service definitions
- **Irreversible Transformations**: Operations that cannot be undone through normal means

#### Handling Strategies
- **Explicit Confirmation**: Require clear, explicit approval before execution
- **Two-factor Validation**: Multiple independent approval mechanisms
- **Preview/Modes**: Show what will happen without actually doing it (dry run, preview)
- **Backup Creation**: Automatically save state before allowing destructive operation
- **Undo Mechanisms**: Ability to reverse operation when possible
- **Version Control Integration**: Leverage VCS for easy recovery of deleted/modified content
- **Snapshot/Restore Points**: Create recoverable states before high-risk operations
- **Staged Execution**: Break destructive operations into intermediate, reviewable steps
- **Rollback Planning**: Prepare recovery procedures before starting operation
- **Impact Assessment**: Analyze potential consequences before execution
- **Permission Escalation**: Require special approvals beyond normal operation thresholds
- **Audit Trail Creation**: Detailed logging of what was changed and why
- **Delayed Execution**: Queue operations for later execution with cancellation window
- **Constrained Parameters**: Limit scope or intensity of destructive operations
- **Sandbox Testing**: Test operations in safe environments before production use
- **Gradual Rollout**: Apply changes incrementally with monitoring at each stage
- **Kill Switches**: Immediate halt mechanisms for operations showing problems

#### Specific Destructive Operation Handling
- **File Deletion**: Move to trash/recycle bin rather than immediate permanent deletion
- **Database Operations**: Use transactions, require WHERE clauses, limit affected rows
- **Network Operations**: Validate endpoints, use timeouts, limit payload sizes
- **Configuration Changes**: Validate syntax, test in staging, maintain rollback configs
- **Memory Operations**: Check bounds, use safe allocation/deallocation patterns
- **Process Operations**: Confirm targets, use graceful termination when possible
- **Security Operations**: Require multi-factor approval, use least privilege principles
- **Infrastructure Changes**: Use deployment pipelines, blue-green deployments, feature flags

#### User Experience for Destructive Operations
- **Clear Warning**: Unambiguous language indicating destructive nature
- **Consequence Description**: Specific explanation of what will be destroyed or changed
- **Irreversibility Notice**: Clear statement when operation cannot be undone
- **Alternative Presentation**: Show non-destructive alternatives when available
- **Confirmation Specificity**: Require typing specific phrases or selecting explicit options
- **Timeout on Confirmation**: Require prompt response to prevent stale approvals
- **Post-operation Feedback**: Clear report of what actually happened
- **Recovery Instructions**: Easy-to-follow steps if user wants to undo or recover
- **Learning Opportunities**: Explain why destructive action was necessary or beneficial

### Architectural Recommendations
Based on the research questions, a robust tool use system should:

1. **Implement rich tool representations** combining structured schemas, natural language descriptions, and usage examples
2. **Deploy multi-layered schema validation** with syntactic, type, constraint, dependency, semantic, contextual, and sequential checks
3. **Create comprehensive tool error reporting** with structured formats, enrichment mechanisms, and clear recovery guidance
4. **Establish intelligent timeout policies** with adaptive durations, progressive responses, and metrics collection
5. **Build fine-grained permission systems** using RBAC/ABAC models with pre-execution checking, runtime monitoring, and clear UX
6. **Implement sophisticated retry mechanisms** with error classification, adaptive strategies, budget management, and enhancement techniques
7. **Apply special handling for destructive operations** including explicit confirmations, previews, backups, undo mechanisms, and staged execution
8. **Provide tool usage analytics** to inform optimization, permission adjustments, and retry policy improvements
9. **Enable dynamic tool discovery and registration** for extensibility and adaptation to changing capabilities
10. **Design for failure atomicity** where possible, ensuring tools either fully succeed or leave system unchanged

## Integration Points

- **Model Adapter (Phase 5)**: Receives tool calls from LLM, validates them through Tool System, returns results
- **Workspace (Phase 2)**: Provides secure file system operations that tools can access (after permission validation)
- **Agent Orchestrator (Phase 7)**: Coordinates tool usage within the agent loop, handles iteration based on tool results
- **Context Manager (Phase 4)**: May provide repository context to inform tool selection and usage

## Data Flow

1. LLM generates tool call request through Model Adapter
2. Model Adapter forwards request to Tool System
3. Tool Registry validates tool exists and retrieves schema
4. Tool Policy checks permissions, validates arguments against schema, applies timeouts
5. If approved, Tool Executor performs operation using Workspace interfaces
6. Results returned through Tool System to Model Adapter to LLM

## Security Requirements

- All tool operations must be validated before execution (ADR-003 - Controlled Tools)
- Permissions must be checked for every tool invocation
- Workspace boundaries must be enforced for file system operations
- Tool executions must be subject to configurable timeouts
- All tool usage must be logged for audit trails
- Destructive operations require explicit confirmation
- Error information must not leak sensitive data in messages
- Tool schemas must prevent injection attacks through strict validation

## Error Handling Requirements

- Tools must return structured error responses with machine-readable error types
- Error messages must be actionable and user-focused
- System must distinguish between usage errors, resource errors, and operational errors
- Retry guidance must be provided for transient errors
- Timeout handling must preserve state when possible and cleanup resources
- Destructive operation failures must not leave system in inconsistent state

## Testing Strategy

- **Unit Tests**: Validate individual tool interfaces, schemas, validation logic
- **Integration Tests**: Test tool execution workflows with mocked workspace
- **Permission Tests**: Verify permission granting and denying works correctly
- **Validation Tests**: Test all validation layers (syntactic, type, constraint, etc.)
- **Timeout Tests**: Verify timeout behavior and cleanup
- **Error Handling Tests**: Verify error reporting and enrichment
- **Destructive Operation Tests**: Verify confirmation requirements and safety mechanisms
- **Integration Tests**: Test end-to-end flow from LLM tool call to workspace operation and back

## Performance Considerations

- Tool validation should be lightweight to minimize latency overhead
- Permission checking should use efficient lookup mechanisms (O(1) or O(log n))
- Tool execution should leverage workspace optimizations
- Caching of tool schemas and permissions where appropriate
- Async/non-blocking implementation for I/O-bound tools
- Metrics collection for tool usage, performance, and error rates

## Configuration Requirements

- Tool registry configuration (auto-discovery vs manual registration)
- Permission policy configuration (RBAC, ABAC, etc.)
- Timeout defaults and overrides per tool type
- Retry budget allocations and policies
- Audit logging configuration and retention policies
- Destructive operation confirmation requirements
- Sandboxing constraints for testing purposes

## Documentation Requirements

- Tool registry documentation (how to register new tools)
- Tool schema documentation format and examples
- Permission model explanation and configuration guide
- Timeout policy documentation
- Error code reference and troubleshooting guide
- Tutorial for creating new tools with proper validation and security
- Best practices for tool usage in agent workflows

## Implementation Stages

1. **Stage 1**: Tool interface and representation standards
2. **Stage 2**: Tool schema validation system
3. **Stage 3**: Tool permission system
4. **Stage 4**: Tool timeout and error handling mechanisms
5. **Stage 5**: Tool registry implementation
6. **Stage 6**: Tool executor implementation
7. **Stage 7**: Initial tool implementations (list_files, read_file, search_code, write_file, apply_patch)
8. **Stage 8**: Integration with Model Adapter and Workspace
9. **Stage 9**: Comprehensive testing and validation

## Deferred Features

- Advanced tool chaining and workflow composition
- Tool result caching and memoization
- Distributed tool execution across multiple workers
- Tool usage-based adaptive permissions
- Machine learning-based tool recommendation system
- Real-time tool performance monitoring and optimization
- Plugin architecture for third-party tool extensions
- Visual tool composition interface for non-programmers

## Risks and Edge Cases

- **Performance Overhead**: Validation and permission checking adding latency
  *Mitigation*: Optimize validation paths, use caching, benchmark regularly
- **Permission Complexity**: Managing fine-grained permissions becoming burdensome
  *Mitigation*: Start with sensible defaults, provide grouping mechanisms, regular review
- **Timeout Inappropriateness**: Fixed timeouts being too short for legitimate operations
  *Mitigation*: Implement adaptive timeouts, user override mechanisms, metrics-based tuning
- **Error Information Leakage**: Error messages revealing sensitive system information
  *Mitigation*: Sanitize error messages, separate internal diagnostics from user messages
- **Incomplete Cleanup**: Failed operations leaving resources locked or state inconsistent
  *Mitigation*: Use RAII patterns, try/finally blocks, resource tracking, health checks
- **Tool Registry Bottleneck**: Central registry becoming performance bottleneck
  *Mitigation*: Implement caching, consider hierarchical or distributed registry for large scale
- **Permission Escalation**: Agents finding ways to exceed granted permissions
  *Mitigation*: Principle of least privilege, regular permission audits, behavior monitoring
- **Context Confusion**: Agents misunderstanding tool capabilities or side effects
  *Mitigation*: Rich tool representations, validation of tool descriptions against implementations
- **Dependency Hell**: Tool schemas becoming overly complex and brittle
  *Mitigation*: Simple, focused tools; composition over complex parameters; versioning

## Open Questions

1. How should tool discovery work in dynamic environments where tools may be added/removed?
2. What is the optimal balance between permission specificity and usability?
3. How should tool versioning work when schemas change over time?
4. What metrics should be collected to measure tool system effectiveness?
5. How should we handle tools that have both safe and unsafe modes of operation?
6. What is the best approach for documenting complex tools with many optional parameters?
7. How should tool system security be audited and tested?
8. What is the appropriate level of abstraction for tool interfaces - low-level syscalls or high-level operations?
9. How should we handle tools that require elevated privileges for certain operations?
10. What fallback mechanisms should be available when the tool system itself fails?

## Recommended Implementation Order

1. Define core tool interface and representation standards
2. Implement schema validation system
3. Build permission checking framework
4. Develop timeout and error handling mechanisms
5. Create tool registry for tool discovery and metadata
6. Implement tool executor with workspace integration
7. Build initial tool set (list_files, read_file, search_code, write_file, apply_patch)
8. Integrate with Model Adapter to receive and respond to tool calls
9. Connect to Workspace for secure operation execution
10. Implement comprehensive test suite
11. Perform security review and penetration testing
12. Optimize based on performance measurements
13. Document and provide examples for external tool developers

## Verification Results

- Research validated: Comprehensive tool system architecture addresses all security and reliability concerns
- Architecture confirms: Separation of tool interface, validation, permissions, and execution is optimal
- Integration readiness: Design allows clean separation between LLM reasoning (Model Adapter) and tool execution
- Security compliance: Meets ADR-003 requirement for controlled tool access
- Testability: Clear interfaces enable unit and integration testing at each layer

## Next Steps

1. Finalize tool interface representation standards (JSON Schema + natural language)
2. Implement schema validation engine with all validation layers
3. Build permission system with RBAC/ABAC support
4. Develop timeout manager with adaptive capabilities
5. Create tool registry with discovery and caching mechanisms
6. Implement secure tool executor with workspace integration
7. Develop initial tool set:
   - list_files: Secure directory listing with filtering
   - read_file: Secure file reading with size limits and encoding detection
   - search_code: Code search with regex and context options
   - write_file: Secure file writing with atomic operations and backup options
   - apply_patch: Secure patch application with validation and conflict detection
8. Integrate with Model Adapter phase 5 component
9. Connect to Workspace phase 2 component
10. Implement comprehensive test suite
11. Perform security review and penetration testing
12. Optimize based on performance measurements
13. Document and provide examples for external tool developers
