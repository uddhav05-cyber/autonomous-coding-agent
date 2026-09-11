# Tool Use

## How Should Tools Be Represented?

Tools should be represented in a way that enables the LLM to understand their capabilities, requirements, and effects:

### Representation Components
- **Tool Identity**: Unique name or identifier for the tool
- **Purpose Description**: Clear, concise explanation of what the tool does
- **Interface Specification**: Formal definition of inputs, outputs, and behaviors
- **Preconditions**: Conditions that must be true before tool execution
- **Postconditions**: Expected state after successful tool execution
- **Side Effects**: Changes to system state beyond primary function
- **Error Conditions**: Situations where tool may fail and what failures look like
- **Resource Usage**: Typical time, memory, or external resource consumption
- **Safety Classification**: Risk level and potential for destructive operations

### Representation Formats
- **Structured Schemas**: JSON Schema or similar for machine-validation
- **Natural Language Descriptions**: Human-readable explanations for LLM reasoning
- **Example Usage**: Sample invocations demonstrating typical patterns
- **Type Signatures**: Formal input/output types for statically typed understanding
- **State Transition Diagrams**: Visual representations of tool effects on system state
- **Pre/post Conditions**: Formal specifications using predicates or assertions
- **Usage Patterns**: Common sequences or combinations with other tools

### LLM Interface Considerations
- **Token Efficiency**: Compact representations that convey maximum information
- **Clarity Over Brevity**: Prioritize unambiguous descriptions over minimal length
- **Consistency**: Uniform representation across all tools for easier learning
- **Grounding**: Connect tool descriptions to actual implementations and behaviors
- **Extensibility**: Easy to add new tools or modify existing representations
- **Validation**: Machine-checkable representations to prevent specification errors

## How Should Tool Schemas Be Validated?

Schema validation ensures tools are invoked correctly and safely:

### Validation Layers
- **Syntactic Validation**: Check that invocation matches expected format
- **Type Validation**: Verify parameter types match specifications
- **Constraint Validation**: Ensure values meet business rules and boundaries
- **Dependency Validation**: Confirm required preconditions are satisfied
- **Semantic Validation**: Check that combinations of parameters make sense
- **Contextual Validation**: Verify appropriateness given current state and task
- **Sequential Validation**: Ensure proper ordering in tool chains or workflows

### Validation Mechanisms
- **Schema Validators**: Use JSON Schema, Pydantic, or similar libraries
- **Type Checkers**: Leverage static or runtime type systems
- **Constraint Solvers**: Validate complex inter-parameter relationships
- **State Checkers**: Consult system state to validate preconditions
- **Rule Engines**: Apply business logic validation rules
- **Whitelisting/Blacklisting**: Approve or reject specific values or patterns
- **Range Checking**: Ensure numeric values fall within acceptable bounds
- **Format Validation**: Verify strings match expected patterns (email, paths, etc.)

### Validation Timing
- **Pre-execution**: Validate before tool runs to prevent errors
- **Post-execution**: Verify results match expected outcomes
- **Continuous**: Ongoing validation during long-running tool operations
- **Retrospective**: Audit validation effectiveness after tool use
- **Proactive**: Predict potential validation failures before invocation

### Error Reporting
- **Specificity**: Clearly indicate which validation rule failed
- **Location**: Point to exact parameter or field causing issue
- **Explanation**: Describe why the validation failed and how to fix it
- **Examples**: Provide correct usage examples when helpful
- **Hierarchy**: Group related validation failures for clarity
- **Actionability**: Suggest specific steps to resolve validation issues

## How Should Tool Errors Be Returned?

Tool error reporting should enable effective diagnosis and recovery:

### Error Classification
- **Usage Errors**: Invalid parameters, missing requirements, wrong format
- **Resource Errors**: Insufficient memory, disk space, permissions, timeouts
- **Environmental Errors**: Missing dependencies, configuration issues, version mismatches
- **Operational Errors**: Tool internal failures, unexpected states, corrupted data
- **Conflict Errors**: Race conditions, lock contention, incompatible operations
- **Boundary Errors**: Attempts to exceed limits, workspace violations, safety blocks

### Error Reporting Structure
- **Error Type**: Machine-readable categorization for automated handling
- **Human Message**: Clear, actionable description for LLM and developers
- **Technical Details**: Exit codes, stack traces, diagnostic data when appropriate
- **Context Information**: State at time of error, relevant variables, recent actions
- **Recovery Suggestions**: Potential next steps or alternative approaches
- **Severity Level**: Impact assessment (recoverable, fatal, requires intervention)
- **Retry Guidance**: Whether and how to safely retry the operation
- **Prevention Tips**: How to avoid similar errors in future invocations

### Error Communication Mechanisms
- **Structured Returns**: JSON or similar with standardized error fields
- **Exception Objects**: Language-native exception mechanisms with rich data
- **Status Codes**: Numeric or enum codes for quick classification
- **Tuple Returns**: (success, result/error) patterns for explicit handling
- **Event Emitters**: Asynchronous error notification via events or callbacks
- **Logging Integration**: Automatic logging alongside direct return
- **Metadata Attachment**: Error information attached to results or state

### Error Enrichment
- **Root Cause Analysis**: Determine underlying reasons beyond surface symptoms
- **Context Addition**: Provide relevant system state and recent history
- **Frequency Tracking**: Note if this is a recurring or isolated issue
- **Trend Analysis**: Compare against historical error patterns
- **Impact Assessment**: Estimate effects on current task and future operations
- **Similar Error Linking**: Connect to known issues or documented problems
- **Escalation Paths**: Indicate when human intervention may be needed

## How Should Tool Timeouts Work?

Timeouts prevent tools from hanging indefinitely and consuming excessive resources:

### Timeout Types
- **Fixed Duration**: Set time limit regardless of operation (simple but inflexible)
- **Adaptive Timeout**: Base timeout on operation type, size, or historical data
- **Progress-based**: Extend timeout if tool shows productive progress
- **Checkpoint Timeout**: Require periodic check-ins to confirm liveness
- **User-configurable**: Allow users to specify timeout preferences
- **Task-aware**: Adjust based on overall task time remaining or priority
- **Resource-sensitive**: Consider system load and competing operations

### Timeout Implementation
- **Wall-clock Timers**: Measure real elapsed time (simple but can be misleading)
- **CPU Time**: Measure actual processor consumption (fairer but complex)
- **Heartbeat Mechanisms**: Require periodic signals to confirm continued operation
- **Milestone Checking**: Verify progress toward expected completion points
- **Resource Monitoring**: Track memory, disk, or network usage as proxies
- **External Watchdogs**: Separate processes monitoring tool execution
- **Hierarchical Timeouts**: Different levels (operation, phase, task, session)

### Timeout Responses
- **Graceful Cancellation**: Attempt clean shutdown preserving partial results
- **Forcible Termination**: Immediate stop regardless of state (risky but necessary)
- **State Preservation**: Save checkpoint or intermediate results when possible
- **Resource Cleanup**: Ensure locks, handles, and temporary resources released
- **Partial Result Return**: Return whatever progress was made before timeout
- **Escalation Signaling**: Mark operation as timed out for higher-level handling
- **User Notification**: Inform stakeholders of timeout and implications
- **Retry Decision Logic**: Determine whether timeout warrants retry attempt

### Timeout Policy Design
- **Conservative Defaults**: Prefer shorter timeouts with extension mechanisms
- **Operation-specific Baselines**: Different timeouts for reads vs writes vs computes
- **Size-proportional Scaling**: Adjust timeouts based on data volume or complexity
- **Historical Calibration**: Base timeouts on observed performance metrics
- **Load-adaptive Adjustment**: Modify timeouts based on system conditions
- **User Override Paths**: Allow adjustment when defaults are inappropriate
- **Timeout Chaining**: Ensure nested timeouts behave predictably
- **Metrics Collection**: Track timeout frequency and causes for improvement

## How Should Tool Permissions Work?

Tool permissions ensure agents operate within authorized boundaries:

### Permission Dimensions
- **Operation Type**: Read, write, execute, delete, network, etc.
- **Resource Access**: Specific files, directories, databases, devices, APIs
- **Capability Level**: Degree of access (browse, modify, administer, etc.)
- **Contextual Constraints**: Time-based, location-based, or state-based limits
- **User/Role Mapping**: Permissions tied to specific identities or groups
- **Temporal Windows**: When permissions are active or inactive
- **Geographic Limits**: Where operations may or may not occur
- **Frequency Limits**: How often certain operations may be performed

### Permission Models
- **Allowlist/Permissive**: Explicitly permit specific operations, deny others by default
- **Denylist/Restrictive**: Explicitly forbid specific operations, allow others by default
- **Role-Based Access Control (RBAC)**: Permissions granted via roles assigned to agent
- **Attribute-Based Access Control (ABAC)**: Permissions based on agent/resource/action attributes
- **Capability-based**: Unforgeable tokens granting specific authorities
- **Hierarchical**: Permissions inherited along organizational or resource hierarchies
- **Time-bound**: Permissions that automatically expire or activate on schedule
- **Context-sensitive**: Permissions that change based on operational context

### Permission Enforcement
- **Pre-execution Checking**: Validate permissions before allowing tool invocation
- **Runtime Monitoring**: Detect and prevent permission violations during execution
- **Post-execution Auditing**: Log permission usage for review and anomaly detection
- **Gradient Enforcement**: Warning levels before hard blocks (warn, then block)
- **Delegation Controls**: Regulate whether and how permissions can be delegated
- **Amplification Prevention**: Prevent gaining more permissions than initially granted
- **Least Privilege Application**: Start with minimal permissions, add as needed
- **Permission Expiration**: Automatically revoke unused or time-limited permissions

### Permission User Experience
- **Explicit Consent**: Clear prompts for new or elevated permission requests
- **Granular Control**: Fine-grained approval rather than all-or-nothing
- **Contextual Explanations**: Explain why permission is needed for current task
- **Persistence Choices**: Remember decisions for similar future requests
- **Revoke Capability**: Easy withdrawal of previously granted permissions
- **Usage Transparency**: Visible history of permission exercises
- **Emergency Overrides**: Clearly marked paths for critical situations
- **Learning Systems**: Suggest permission adjustments based on usage patterns

## How Should Retries Work?

Retry mechanisms balance persistence with resource awareness and error discrimination:

### Retry Classification by Error Type
- **Transient Errors**: Temporary issues likely to succeed on retry (network blips, resource contention)
- **Probabilistic Errors**: Intermittent failures with success chance > 0% (flaky tests, race conditions)
- **Deterministic Errors**: Consistent failures unlikely to change without intervention (bugs, missing dependencies)
- **User-correctable Errors**: Failures resolvable by user intervention (credentials, permissions)
- **Environmental Errors**: Failures due to external system states (service downtime, quota exhaustion)
- **Self-induced Errors**: Failures resulting from previous agent actions (state corruption, resource exhaustion)

### Retry Strategies
- **Immediate Retry**: Instant retry for suspected transient glitches
- **Fixed Delay**: Constant pause between attempts (simple but can cause thundering herd)
- **Linear Backoff**: Increasing fixed increments between attempts
- **Exponential Backoff**: Delay multiplies with each attempt (good for network/contention issues)
- **Jittered Backoff**: Add randomness to prevent synchronized retries
- **Fibonacci Backoff**: Use Fibonacci sequence for delay progression
- **Adaptive Backoff**: Adjust based on error patterns and historical success rates
- **Circuit Breaker**: Temporarily stop attempts after repeated failures
- **Progressive Approaches**: Try different methods or parameters with each attempt

### Retry Budget Management
- **Per-attempt Limits**: Maximum retries for individual tool invocations
- **Per-operation Type Limits**: Different budgets for reads, writes, computes, etc.
- **Per-session Limits**: Overall retry allowance for agent session
- **Per-task Limits**: Retry budget allocated to specific tasks or objectives
- **Adaptive Allocation**: Shift budget based on error patterns and task progress
- **Priority-based Allocation**: More retries for critical path operations
- **Expiration Policies**: Retry budgets that expire or refresh over time
- **Debt Tracking**: Account for retries consumed against allocated budgets

### Retry Enhancement Techniques
- **Failure Analysis**: Modify approach based on error characteristics
- **Context Enrichment**: Provide additional information for retry attempts
- **Parameter Variation**: Try different inputs or configurations
- **Alternative Methods**: Use different tools or approaches to achieve same goal
- **Escalation Paths**: Involve different systems or techniques after thresholds
- **Learning Systems**: Adjust retry policies based on historical effectiveness
- **Fallback Mechanisms**: Predefined alternative approaches when retries exhausted
- **Circuit Breaker Integration**: Prevent wasting resources on obviously failing operations

### Retry Decision Framework
- **Error Retryability**: Determine if error type warrants retry attempts
- **Cost-benefit Analysis**: Weigh retry cost against expected value of success
- **Alternatives Evaluation**: Consider other approaches before retrying same operation
- **Impact Assessment**: Evaluate effects of continued failures on broader operations
- **User Preference Respect**: Honor explicit user guidance on retry behavior
- **System State Consideration**: Factor in current load, resources, and stability
- **Historical Pattern Recognition**: Use past success rates to inform retry decisions
- **Threshold-based Triggers**: Retry only when specific conditions are met

## How Should Destructive Operations Be Handled?

Destructive operations require special care due to their potential for irreversible harm:

### Destructive Operation Classification
- **Data Deletion**: Removing files, records, or other persistent information
- **State Mutation**: Changing system configuration, database contents, or application state
- **Resource Consumption**: Operations that irreversibly use quotas, credits, or limited resources
- **External Effects**: Actions affecting systems outside immediate control (network calls, API modifications)
- **Security Relevant**: Operations impacting authentication, authorization, or encryption
- **Infrastructure Changes**: Modifying deployment configurations, scaling, or service definitions
- **Irreversible Transformations**: Operations that cannot be undone through normal means

### Handling Strategies
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

### Specific Destructive Operation Handling
- **File Deletion**: Move to trash/recycle bin rather than immediate permanent deletion
- **Database Operations**: Use transactions, require WHERE clauses, limit affected rows
- **Network Operations**: Validate endpoints, use timeouts, limit payload sizes
- **Configuration Changes**: Validate syntax, test in staging, maintain rollback configs
- **Memory Operations**: Check bounds, use safe allocation/deallocation patterns
- **Process Operations**: Confirm targets, use graceful termination when possible
- **Security Operations**: Require multi-factor approval, use least privilege principles
- **Infrastructure Changes**: Use deployment pipelines, blue-green deployments, feature flags

### User Experience for Destructive Operations
- **Clear Warning**: Unambiguous language indicating destructive nature
- **Consequence Description**: Specific explanation of what will be destroyed or changed
- **Irreversibility Notice**: Clear statement when operation cannot be undone
- **Alternative Presentation**: Show non-destructive alternatives when available
- **Confirmation Specificity**: Require typing specific phrases or selecting explicit options
- **Timeout on Confirmation**: Require prompt response to prevent stale approvals
- **Post-operation Feedback**: Clear report of what actually happened
- **Recovery Instructions**: Easy-to-follow steps if user wants to undo or recover
- **Learning Opportunities**: Explain why destructive action was necessary or beneficial

## Architectural Recommendations

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

This approach ensures tools are used safely, effectively, and efficiently while providing the LLMs with clear understanding of capabilities and the system with robust protection against misuse and errors.