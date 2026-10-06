# Phase 7: Agent Orchestration Research

## 1. Phase 7 Objective
The Agent Orchestrator is responsible for coordinating the autonomous coding-agent loop, serving as the central control layer that manages the iterative process of LLM reasoning, tool execution, and state updates to accomplish complex software engineering tasks.

## 2. Problem Statement
Current autonomous agents lack sophisticated coordination mechanisms for iterative problem-solving. The Agent Orchestrator must manage the complex interplay between LLM reasoning, tool execution, context management, and workspace operations while maintaining safety, security, and task focus.

## 3. Responsibilities of the Agent Orchestrator
- **Iteration Control**: Manage the agent-execution loop with proper termination conditions
- **Decision Making**: Interpret LLM responses and determine next actions based on tool results
- **State Management**: Maintain and update agent state across iterations
- **Error Handling**: Classify and respond to errors from LLMs, tools, and system components
- **Resource Management**: Enforce iteration limits, timeouts, and resource constraints
- **Safety Enforcement**: Apply security boundaries and prevent harmful actions
- **Coordination**: Synchronize interactions between all system components (LLM, Context Manager, Tool System, Workspace)

## 4. Non-responsibilities / Explicit Boundaries
- **NOT** responsible for LLM inference or model specifics (handled by Model Adapter)
- **NOT** responsible for tool implementation details (handled by Tool System)
- **NOT** responsible for context storage mechanisms (handled by Context Manager)
- **NOT** responsible for workspace file operations (handled by Workspace)
- **NOT** responsible for agent learning or memory persistence (separate concern)
- **NOT** responsible for user interface or interaction protocols

## 5. Architecture
```
Iteration Loop:
[Orchestrator] 
  ↓ (decides action)
[Model Adapter] → LLM 
  ↓ (gets response)
[Orchestrator] 
  ↓ (interprets response, validates safety)
[Tool System] → [Workspace] (if tool execution needed)
  ↓ (gets results)
[Context Manager] 
  ↓ (updates context with results)
[Orchestrator] 
  ↓ (evaluates completion, continues/stop)
```

## 6. Agent Execution Loop
1. **Initialization**: Load task, set initial state, establish iteration counters
2. **Prompt Construction**: Build LLM prompt from current context, task description, and available tools
3. **LLM Invocation**: Call Model Adapter to get LLM response
4. **Response Parsing**: Extract tool calls or reasoning from LLM response
5. **Safety Check**: Validate proposed actions against security policies
6. **Tool Execution**: Invoke requested tools through Tool System
7. **Result Processing**: Collect and interpret tool execution results
8. **Context Update**: Update Context Manager with execution results
9. **Completion Evaluation**: Determine if task is complete or requires another iteration
10. **Iteration**: Continue loop or terminate based on conditions

## 7. Agent State Representation
The orchestrator maintains:
- **Task Definition**: Original goal, requirements, constraints
- **Iteration Counter**: Current iteration number, max iterations allowed
- **Execution History**: Sequence of LLM responses, tool calls, results
- **Context Summary**: Compressed representation of workspace state and knowledge
- **Resource Usage**: Tokens consumed, time elapsed, tool call counts, model call counts, retry counts
- **Error State**: Classification and details of any errors encountered
- **Completion Signals**: Flags indicating task completion, blocking conditions, or failures

## 8. Task Lifecycle
```
TASK_START
  ↓
[INITIALIZE] → Set up initial state, load resources
  ↓
[ITERATION_BEGIN] → Increment counter, check limits
  ↓
[LLM_QUERY] → Get reasoning/action from model
  ↓
[TOOL_EXECUTE] → Execute requested operations
  ↓
[CONTEXT_UPDATE] → Integrate results into knowledge base
  ↓
[COMPLETION_CHECK] → Evaluate if goal achieved
  ↓
{YES → TASK_COMPLETE}
{NO → [ITERATION_BEGIN] (if not maxed)}
  ↓
[FAILURE_HANDLING] → Address errors, timeouts, or blocks
  ↓
{RETRY → [ITERATION_BEGIN]} {ABORT → TASK_FAILED}
```

## 9. Model Adapter Integration
- Receives formatted prompts from orchestrator
- Returns structured responses (tool invocations, reasoning, text)
- Handles provider-specific details (OpenAI, Anthropic, etc.)
- Manages token limits, temperature, and sampling parameters
- Provides timing and usage metrics to orchestrator

## 10. Context Manager Integration
- Receives updates from tool executions and LLM reasoning
- Provides contextual information for prompt construction
- Manages context window size and relevance scoring
- Implements forgetting/compression strategies for long sessions
- Stores conversation history, file summaries, and discovered facts

## 11. Tool System Integration
- Validates requested tools against available registry
- Enforces permission levels and security policies
- Manages tool execution with timeouts and resource limits
- Returns structured results or error information
- Provides audit trail of all tool invocations

## 12. Workspace Integration
- Defines the bounded file system for agent operations
- Enforces path boundaries and security restrictions
- Provides file reading/writing capabilities through tools
- Maintains workspace consistency during concurrent operations

## 13. Tool-call Execution Flow
1. Orchestrator receives LLM response with tool invocations
2. Validates tool names exist in registry
3. Checks permission levels for each requested tool
4. Validates input arguments against tool schemas
5. Executes tools with configured timeouts
6. Captures results, errors, timing, and resource usage
7. Returns structured output to orchestrator for context update

## 14. Iteration Management
- Tracks current iteration against maximum allowed
- Implements exponential backoff for retry scenarios
- Provides progress reporting and intermediate checkpoints
- Allows graceful degradation when approaching limits
- Supports pause/resume functionality for long-running tasks

## 15. Maximum Iteration Limits
- Configurable per-task based on complexity estimates
- Hard limits to prevent runaway execution
- Soft limits with warnings for graceful handling
- Different limits for different phases (research vs implementation)
- Dynamic adjustment based on progress velocity

## 16. Timeout Handling
- Per-iteration timeout (LLM response + tool execution)
- Per-tool timeout configurations (inherited from Tool System)
- Overall task timeout with checkpointing capability
- Timeout escalation policies (warn → interrupt → terminate)
- Progress-based timeout adjustment (more time if making progress)

## 17. Failure Recovery
- **Transient Failures**: Automatic retry with backoff (network, temp. resource issues)
- **Permanent Failures**: Alternative tool selection or approach modification
- **Partial Failures**: Continue with available information, mark missing data
- **Cascading Failures**: Safe termination with diagnostic information
- **Recovery Checkpoints**: Periodic state saving to enable restart from known good state

## 18. Retry Strategy
- Exponential backoff: 1s, 2s, 4s, 8s, max 30s between retries
- Maximum retry attempts per operation type (typically 3)
- Jitter addition to prevent thundering herd problems
- Different strategies for different failure types (timeout vs permission vs not found)
- Circuit breaker pattern to temporarily disable repeatedly failing tools

## 19. Error Classification
```
FATAL:    Cannot continue (permission denied on critical resource, workspace corruption)
RECOVERABLE: Temporary issue (network timeout, rate limit, tool temporarily unavailable)
CONTINUABLE: Non-blocking (optional tool missing, non-critical file access issue)
USER_ACTION: Requires user intervention (credentials needed, clarification required)
MODEL_ERROR: LLM-specific issues (malformed response, provider error, content filter)
```

## 20. Stopping/Termination Conditions
- **SUCCESS**: Task completion criteria met
- **MAX_ITERATIONS**: Iteration limit reached without completion
- **TIMEOUT**: Overall task timeout exceeded
- **RESOURCE_EXHAUSTION**: Token, memory, or quota limits exceeded
- **USER_INTERRUPT**: Explicit cancellation request
- **SAFETY_VIOLATION**: Security boundary or policy violation detected
- **IRRECOVERABLE_ERROR**: Cannot proceed due to permanent failure
- **NO_PROGRESS**: Detected stall despite multiple iterations

## 21. User Cancellation/Interruption
- Asynchronous signal handling for immediate response
- Graceful termination with state preservation
- Clear communication of partial results and completion status
- Option to resume from interruption point
- Cleanup of temporary resources and temporary files

## 22. Context Updates Between Iterations
- **Incremental**: Add new facts, tool results, and observations
- **Compressive**: Summarize lengthy exchanges to stay within context limits
- **Relevance-based**: Prioritize recent and task-relevant information
- **Contradiction Resolution**: Detect and resolve conflicting information
- **Knowledge Consolidation**: Extract patterns, file structures, and API understanding

## 23. Handling Malformed Model Responses
- **Detection**: JSON parsing errors, missing required fields, invalid tool names
- **Fallback**: Request clarification or reformatting from LLM
- **Repair Attempts**: Extract usable information from malformed responses
- **Escalation**: After multiple failures, request human intervention or simplify request
- **Logging**: Detailed capture of malformed responses for debugging

## 24. Handling Unavailable Tools
- **Validation**: Check tool registry before execution attempt
- **Notification**: Inform LLM of tool unavailability in next prompt
- **Alternatives**: Suggest equivalent tools or approaches when possible
- **Documentation**: Maintain list of available/tools for LLM context
- **Fallback**: Modify approach to work with available toolset

## 25. Handling Tool Failures
- **Classification**: Distinguish between user errors, system errors, and environmental issues
- **Retry Logic**: Apply appropriate retry strategy based on error type
- **Fallback Tools**: Attempt to achieve same goal with different tools
- **Partial Success**: Extract usable information from failed executions
- **Escalation**: Report persistent tool failures as system issues

## 26. Handling Model Failures
- **Provider Issues**: Switch to backup model/provider if configured
- **Rate Limits**: Implement backoff and queueing strategies
- **Content Filters**: Request reformulation or approach adjustment
- **Quality Degradation**: Adjust expectations for simpler models when needed
- **Fallback**: Reduce complexity of requests or break into smaller steps

## 27. Handling Repeated Failures
- **Pattern Detection**: Identify cyclic failure patterns indicating fundamental issues
- **Approach Modification**: Suggest fundamentally different strategies after N failures
- **Resource Consultation**: Recommend breaking task into subtasks or seeking external help
- **Escalation Path**: Progress from automated retry → simplified approach → human consultation
- **Learning**: Record failure patterns for future task planning optimization

## 28. Prevention of Infinite Loops
- **Iteration Counters**: Hard limits on total iterations
- **Progress Tracking**: Detect lack of meaningful advancement over time
- **State Repetition Detection**: Identify when agent returns to identical states
- **Action Repetition Detection**: Prevent cycling through same ineffective action sequences
- **Time-based Guards**: Absolute time limits regardless of iteration count
- **Resource Monitoring**: Token, memory, and CPU usage boundaries

## 29. Safety Boundaries
- **Workspace Constraints**: Strict path boundaries preventing system access
- **Tool Permission Levels**: Least privilege access to capabilities
- **Network Controls**: Whitelist/blacklist for external API calls
- **File Type Restrictions**: Limitations on executable or dangerous file types
- **Content Filtering**: Prevent generation of harmful code or content
- **Privilege Escalation Prevention**: Block attempts to gain elevated permissions

## 30. Security Considerations
- **Input Validation**: Sanitize all LLM outputs before tool execution
- **Output Encoding**: Prevent injection attacks in generated content
- **Audit Trails**: Complete logging of all decisions, actions, and results
- **Principle of Least Privilege**: Minimum permissions required for task completion
- **Secure Defaults**: Fail-secure configurations for all safety mechanisms
- **Information Flow Control**: Prevent unauthorized data exfiltration

## 31. Resource Limits
- **Token Limits**: Per-iteration and cumulative token usage tracking
- **Tool Call Limits**: Maximum number of tool invocations per iteration/task
- **Model Call Limits**: Maximum number of LLM invocations per task (tracked via total_model_calls)
- **Retry Limits**: Maximum number of retry attempts per task (tracked via total_retries_used)
- **Time Limits**: Iteration-level and overall task duration caps
- **Memory Limits**: Working memory usage monitoring and control
- **Network Bandwidth**: Constraints on external API call frequency and volume
- **Disk Usage**: Workspace size limits and cleanup policies

## 32. Auditability
- **Decision Logging**: Record all orchestrator decisions with reasoning
- **Action Logging**: Timestamped logs of all tool invocations and LLM calls
- **State Snapshots**: Periodic saves of agent state for forensic analysis
- **Metric Collection**: Quantitative data on performance, resource usage, success rates
- **Replay Capability**: Ability to reconstruct and debug task execution paths
- **Compliance Reporting**: Generate reports for security and usage audits

## 33. Observability/Metrics
- **Performance Metrics**: Iteration duration, tool execution time, LLM response time
- **Success Rates**: Task completion percentages by task type and complexity
- **Resource Efficiency**: Token usage per unit of progress, tool call efficiency
- **Error Analysis**: Classification and frequency of different error types
- **User Interaction**: Frequency and nature of required user interventions
- **Progress Indicators**: Real-time feedback on task advancement toward goals

## 34. Deterministic Behavior Where Possible
- **Seed Management**: Fixed seeds for reproducible LLM sampling when beneficial
- **Tool Ordering**: Consistent ordering when multiple valid tool sequences exist
- **Tie Breaking**: Deterministic selection when multiple options have equal value
- **Cache Utilization**: Deterministic caching of repeated operations
- **Fallback Determinism**: Predictable behavior when primary approaches fail

## 35. Testing Strategy
- **Unit Tests**: Individual component testing with mocked dependencies
- **Integration Tests**: End-to-end testing of orchestrator with real components
- **Failure Injection**: Testing resilience to various failure modes
- **Load Testing**: Performance under various resource constraints
- **Security Testing**: Validation of boundary enforcement and attack resistance
- **Regression Testing**: Ensuring changes don't break existing functionality
- **Property-Based Testing**: Validation of invariants across varied inputs

## 36. Unit Testing Requirements
- **Orchestrator Logic**: Test decision-making processes in isolation
- **State Transitions**: Validate iteration loop progression rules
- **Error Handling**: Verify proper classification and response to error types
- **Resource Limit Enforcement**: Confirm limits are properly enforced
- **Safety Boundary Testing**: Ensure security mechanisms block inappropriate actions
- **Integration Points**: Test interfaces with Model Adapter, Context Manager, Tool System
- **Edge Cases**: Test boundary conditions, empty inputs, malformed data

## 37. Implementation Approach
### Phase 7.1: Basic Orchestrator (IMPLEMENTED)
- Simple iteration loop with fixed limits
- Basic LLM prompt construction and response parsing
- Sequential tool execution without parallelization
- Minimal state tracking and context management
- Basic error handling and termination conditions

### Phase 7.2: Enhanced Control (IMPLEMENTED)
- Sophisticated termination conditions and progress detection
- Retry strategies with exponential backoff
- Basic error classification and recovery
- Resource limit enforcement and monitoring

### Phase 7.3: Advanced Features (RESEARCH)
- Context compression and relevance scoring
- Adaptive iteration limits based on progress
- Sophisticated failure recovery and alternative approach generation
- Comprehensive audit trail and metrics collection
- User interruption handling and state persistence

## 38. Dependencies on Previous Phases
- **Phase 5 (Model Adapter)**: Standardized interface for LLM providers - INTEGRATED
- **Phase 6 (Tool System)**: Secure, validated tool execution framework - INTEGRATED
- **Phase 4 (Context Engineering)**: Context management and compression strategies - INTEGRATED (basic context package retrieval)
- **Phase 3 (Repository Understanding)**: Code navigation and comprehension capabilities - INTEGRATED (via Context Manager)
- **Phase 2 (Workspace)**: Bounded file system abstraction - INTEGRATED (via Tool System and Context Manager)
- **Phase 1 (Foundations)**: Core architecture and communication protocols - INTEGRATED

## 39. Success Criteria
- **Task Completion Rate**: ≥80% success rate on representative task suite
- **Resource Efficiency**: <2x token usage of expert human baseline
- **Reliability**: <5% failure rate due to orchestrator-related issues
- **Safety**: Zero security boundary violations in test suite
- **User Experience**: Minimal required intervention for well-specified tasks
- **Scalability**: Effective handling of tasks from trivial to moderately complex

## 40. Open Questions and Research Areas
- Optimal context compression ratios for different task types
- Best practices for balancing exploration vs. exploitation in tool selection
- Most effective failure recovery strategies for different error domains
- Ideal iteration limit settings based on task complexity metrics
- Most informative metrics for predicting task success/failure early in execution

## Phase 7.2 — Enhanced Control Research

### Phase 7.2 Objective
Research how to evolve the existing Basic Agent Orchestrator into a more reliable and controllable autonomous execution system without rewriting the Phase 7.1 foundation.
The research must build directly on the existing AgentOrchestrator, AgentOrchestratorState, AgentState, Model Adapter, Context Manager, Tool System, and Workspace architecture.

### Research Areas
Cover the following areas in detail.

1. Advanced Error Recovery
Research:
* transient vs permanent failures
* model failures
* tool failures
* validation failures
* permission failures
* timeout failures
* repeated failures
* recovery strategies
* safe retry boundaries
* retry budgets
* maximum consecutive failures
* failure classification
* when to stop instead of retrying
Clearly distinguish which errors should be retried and which must immediately terminate execution.

2. Retry Strategy
Research a controlled retry mechanism for the orchestrator.
Consider:
* exponential backoff
* jitter
* maximum retry count
* per-operation retry budgets
* per-task retry budgets
* retryable vs non-retryable errors
* interaction with Model Adapter retry logic
* interaction with Tool System error handling
* prevention of retry storms
* preventing duplicate destructive tool operations
Do NOT duplicate retry logic that already belongs to Phase 5 or Phase 6.

3. Sophisticated Termination Conditions
Research termination beyond the basic Phase 7.1 conditions.
Consider:
* successful completion
* explicit model completion
* repeated identical actions
* no-progress detection
* excessive tool failures
* excessive token/resource consumption
- safety violations
- retry exhaustion
- context exhaustion
- iteration exhaustion
- task timeout
- unrecoverable errors
Define deterministic termination rules wherever possible.

4. Progress Detection
Research how the orchestrator can determine whether an agent is actually making progress.
Consider:
* state changes
* workspace changes
* tool results
* repeated tool calls
* repeated model responses
* task completion signals
* progress counters
* stagnation detection
Avoid implementing vague or unreliable "AI decides if it is progressing" logic.

5. Cancellation and Interruption
Research controlled cancellation support.
Consider:
* user cancellation
* programmatic cancellation
* cancellation between iterations
* cancellation during model execution
* cancellation during tool execution
* cleanup requirements
* state transitions
* preserving audit/history information
* safe handling of partially completed operations
Ensure cancellation cannot bypass Tool System safety controls.

6. State Persistence
Research whether and how AgentOrchestratorState should be persisted.
Consider:
* serializable state representation
* task identifiers
* iteration state
* execution history
* tool-call history
* error state
* timestamps
* resumability
* crash recovery
* consistency guarantees
* security of persisted state
Do not introduce a database unless research demonstrates that it is necessary.

7. Resource and Execution Budgets
Research controlled limits for:
* maximum iterations
* maximum model calls
* maximum tool calls
* maximum execution time
* maximum consecutive failures
* maximum retry attempts
* token/cost budget
* tool-specific limits
Determine which component should own each budget.
Do not duplicate Phase 4 Context Manager budgeting or Phase 6 Tool System limits.

8. Safety Controls
Research additional orchestrator-level safety controls.
Consider:
* action allowlists/denylists
* destructive-operation awareness
* confirmation requirements
* safety violation tracking
* escalation handling
* privilege boundaries
* untrusted model output
* protection against infinite loops
* protection against repeated destructive actions
The orchestrator must not bypass Phase 6 Tool Policy or Tool Executor controls.

9. Observability
Research useful orchestration metrics.
Consider:
* task duration
* iteration count
* model calls
* tool calls
* successful/failed tool calls
* retries
* termination reason
* token usage
* estimated cost
* errors
* cancellation
* progress/stagnation events
Clearly separate orchestration metrics from Phase 4, Phase 5, and Phase 6 responsibilities.

10. Architecture Changes
Determine the minimum architectural changes required for Phase 7.2.
Identify:
* new classes
* new dataclasses
* new enums

## Phase 7.3 — Advanced Features Research

### Phase 7.3 Objective
Research advanced features to enhance the Agent Orchestrator's capabilities for complex, long-running tasks while maintaining reliability, safety, and user control. The research must build directly on the existing AgentOrchestrator implementation from Phase 7.1 and the enhanced control mechanisms from Phase 7.2.

### Research Areas

#### 1. Adaptive Iteration Control
Research mechanisms for dynamically adjusting iteration limits based on:
- Progress velocity (rate of meaningful workspace changes)
- Task complexity indicators (file count, dependency depth, API surface)
- Historical performance on similar tasks
- Resource consumption patterns
Consider:
- How to measure meaningful progress vs. busywork
- Adaptive thresholds that increase/decrease limits based on observed progress
- Preventing both premature termination and excessive computation
- Integration with existing termination conditions without creating conflicts

#### 2. Advanced Failure Recovery
Research sophisticated recovery strategies beyond basic retry:
- Alternative approach generation when standard approaches fail
- Skill-based fallback (trying different methodologies for the same goal)
- Decomposition strategies (breaking complex tasks into subtasks)
- Knowledge transfer from failed attempts to inform future approaches
- Cascading failure prevention and isolation
Consider:
- When to persist with retries vs. when to change approach entirely
- How to detect fundamental flaws in current approach
- Mechanisms for generating and evaluating alternative strategies
- Learning from failure patterns to improve future task handling

#### 3. Context Optimization
Research advanced context management techniques:
- Semantic relevance scoring for context inclusion/exclusion
- Hierarchical context summarization (different levels of detail)
- Temporal decay models for information relevance
- Cross-referencing and deduplication of contextual information
- Contextual bandit algorithms for exploration vs. exploitation
Consider:
- Balancing context richness with token efficiency
- Dynamic adjustment of context window size based on task phase
- Mechanisms for identifying and preserving critical context
- Preventing context drift in long-running tasks

#### 4. Progress and Goal Tracking
Research sophisticated progress measurement mechanisms:
- Multi-dimensional progress tracking (completion, quality, efficiency)
- Milestone detection and tracking
- Goal decomposition and subgoal achievement measurement
- Progress prediction and estimation of remaining effort
- Detecting goal drift or scope creep
Consider:
- Objective metrics for progress that don't rely on LLM self-assessment
- How to define and measure "meaningful progress" for different task types
- Integration with adaptive iteration control and termination conditions
- Visualization and reporting of progress to users

#### 5. Advanced Termination Conditions
Research nuanced termination conditions beyond basic success/failure:
- Diminishing returns detection (when additional iterations yield minimal value)
- Quality threshold achievement (when output meets acceptable standards)
- Resource efficiency optimization (stopping when marginal cost exceeds benefit)
- User-satisfaction prediction (estimating likelihood user will accept current state)
- External validation triggers (when certain criteria are met via external checks)
Consider:
- How to define and measure task "completeness" for different domains
- Balancing thoroughness with timely delivery
- Mechanisms for estimating task difficulty and adjusting expectations
- Preventing premature termination while avoiding unnecessary work

#### 6. State Persistence and Recovery
Research mechanisms for persisting orchestrator state:
- Serializable state representations for crash recovery
- Checkpointing strategies for long-running tasks
- Selective persistence (what to save vs. what to recompute)
- Incremental state updates to minimize persistence overhead
- Consistency guarantees for recovered state
Consider:
- Security implications of persisting potentially sensitive state
- Performance impact of frequent state persistence
- Mechanisms for validating recovered state integrity
- Integration with user interruption handling and resumability

#### 7. User Interruption and Control
Research sophisticated user interaction mechanisms:
- Granular interruption points (safe places to pause execution)
- User guidance during execution (suggesting next steps or requesting input)
- Real-time progress feedback with actionable insights
- Ability to modify task parameters mid-execution
- Collaborative execution modes (user and agent working together)
Consider:
- How to interrupt safely without leaving system in inconsistent state
- Mechanisms for presenting useful information to users during execution
- Balancing user control with agent autonomy
- Feedback loops for improving user-agent collaboration

#### 8. Resource and Budget Management
Research advanced resource management:
- Predictive resource modeling (forecasting future resource needs)
- Dynamic budget reallocation based on task phase
- Cost-aware decision making (factoring resource costs into choices)
- Quality-per-resource-unit optimization
- Resource pooling and sharing across concurrent tasks
Consider:
- How to accurately predict resource consumption for different operations
- Mechanisms for enforcing budgets without hindering progress
- Trade-offs between different resource types (time vs. tokens vs. tool calls)
- Integration with adaptive iteration control and termination conditions

#### 9. Observability and Metrics
Research comprehensive observability features:
- Real-time dashboards showing orchestration internals
- Predictive analytics for task outcome estimation
- Anomaly detection in execution patterns
- Root cause analysis for failures and inefficiencies
- Cross-task learning and pattern extraction
Consider:
- Which metrics provide the most actionable insights
- How to present complex orchestration state in understandable ways
- Mechanisms for detecting and diagnosing problems early
- Learning from execution history to improve future performance

#### 10. Execution History and Auditability
Research detailed execution tracking:
- Complete, queryable execution history with timestamps
- Ability to replay and investigate specific decision points
- Comparative analysis across multiple task executions
- Provenance tracking for decisions and actions
- Compliance reporting capabilities
Consider:
- Storage efficiency for detailed execution histories
- Mechanisms for extracting insights from execution patterns
- Integration with debugging and troubleshooting workflows
- Legal and compliance requirements for audit trails

#### 11. Safety and Security Boundaries
Research advanced safety mechanisms:
- Real-time risk assessment during execution
- Adaptive safety boundaries based on task context
- Predictive prevention of unsafe actions
- Sandboxing and isolation techniques for risky operations
- Emergency shutdown mechanisms for critical situations
Consider:
- How to assess risk without hindering legitimate task progress
- Mechanisms for learning and improving safety assessments over time
- Balancing safety with task completion ability
- Integration with user controls for overriding safety decisions

#### 12. Concurrency and Execution Control
Research mechanisms for managing concurrent operations:
- Safe parallel execution of independent subtasks
- Resource contention resolution and deadlock prevention
- Priority-based task scheduling and preemption
- Checkpointing and rollback for concurrent operations
- Load balancing across available resources
Consider:
- How to identify safely parallelizable work
- Mechanisms for coordinating between concurrent operations
- Handling dependencies between concurrent tasks
- Preventing race conditions and inconsistent states

#### 13. Advanced Error Taxonomy
Research detailed error classification and handling:
- Fine-grained error categorization for targeted recovery
- Error propagation analysis and impact assessment
- Error prediction and prevention mechanisms
- Learning from error patterns to improve system robustness
- Adaptive error handling based on historical effectiveness
Consider:
- How to classify errors in ways that inform recovery strategies
- Mechanisms for detecting error patterns before they cause failures
- Integration with adaptive retry and failure recovery mechanisms
- Feedback loops for improving error handling based on outcomes

#### 14. Architecture and Component Boundaries
Research architectural refinements:
- Clear separation of concerns between orchestrator subcomponents
- Pluggable architecture for different orchestration strategies
- Minimal coupling between orchestrator and dependent systems
- Extensibility points for adding new capabilities
- Backward compatibility mechanisms for evolution
Consider:
- How to maintain architectural integrity while adding features
- Mechanisms for testing architectural boundaries
- Strategies for evolving the system without breaking changes
- Integration patterns for new component types

#### 15. Testing Strategy
Research comprehensive testing approaches:
- Property-based testing for orchestration invariants
- Chaos engineering for resilience validation
- Long-running task testing for stability verification
- Cross-LLM provider testing for portability
- Human-in-the-loop testing for usability validation
Consider:
- How to test complex, stateful systems effectively
- Mechanisms for validating emergent behaviors
- Strategies for testing rare edge cases and failure modes
- Integration with continuous integration and delivery pipelines

### Implementation Plan
Research the implementation approach for Phase 7.3 features:
- Prioritization of features based on impact and implementation complexity
- Incremental rollout strategy with backward compatibility
- Performance benchmarks for each feature addition
- Integration testing approach with existing Phase 7.1 and 7.2 components
- Validation methodology for measuring feature effectiveness
Consider:
- Which features provide the highest value for implementation effort
- How to validate that features work correctly without breaking existing functionality
- Mechanisms for measuring performance impact of each feature
- Approaches for gathering user feedback during implementation

### Non-Goals/Deferred Scope
Research what to explicitly exclude from Phase 7.3:
- Full autonomy without any human oversight
- General problem-solving capabilities beyond software engineering
- Real-time collaboration features requiring persistent connections
- Advanced planning capabilities requiring significant computational resources
- Learning across completely unrelated task domains
Consider:
- Boundaries that maintain focus on the core autonomous coding agent mission
- Features that would significantly increase complexity without proportional benefit
- Capabilities better suited for separate systems or future phases
- Legal, ethical, or safety considerations that preclude certain features

### Open Questions
Research unresolved questions for future investigation:
- What is the optimal balance between automation and human control?
- How can we measure and improve agent "judgment" in complex situations?
- What are the most effective ways to prevent goal misalignment in long-running tasks?
- How should the system handle contradictory information from reliable sources?
- What are the theoretical limits of autonomous coding agents?
Consider:
- Fundamental challenges in autonomous agent design
- Metrics for evaluating agent intelligence and capability
- Mechanisms for ensuring agent alignment with human intentions
- Approaches for handling uncertainty and ambiguity in task requirements

## 41. Phase 7.3.3: Advanced Failure Recovery Implementation

### Objective
Implement sophisticated recovery strategies beyond basic retry to handle fundamental flaws in the agent's approach, enabling the orchestrator to detect when standard retry mechanisms are insufficient and generate alternative approaches for task completion.

### Implementation Details

#### Failure History Tracking
- **failure_history**: List of dictionaries tracking timestamp, iteration, error type, error message, and retryability status for each failure
- **Bounded to 50 entries** to prevent memory growth
- **Persisted and recovered** with agent state for continuity across sessions

#### Failure Pattern Detection
- **failure_type_counts**: Dictionary counting occurrences of each error type in failure history
- **Used for fundamental flaw detection** to identify persistent error patterns

#### Fundamental Flaw Detection
The `_detect_fundamental_flaw()` method identifies when standard retry mechanisms are unlikely to succeed by checking:
1. **Repeated error type**: Any single error type has occurred 3 or more times in failure history
2. **High non-retryable ratio**: 70% or more of recent failures (up to last 10) are non-retryable
   - Uses existing `_is_retryable_error()` for classification
   - With fewer than 10 failures, evaluates all available failures

#### Alternative Approach Generation
The `_generate_alternative_approach()` method creates contextual guidance based on failure patterns:
- **Tool-related failures**: Suggest verifying parameters, trying different tools, checking preconditions
- **Timeout-related failures**: Recommend breaking down operations, using more efficient algorithms, checking for infinite loops
- **Resource-related failures**: Advise optimizing resource usage, finding efficient solutions, completing partial work
- **After initial alternatives**: Suggest rethinking the approach, solving simplified versions first, using completely different methodologies

#### Alternative Approach Execution
The `_attempt_alternative_approach()` method manages recovery attempts:
- **Resets consecutive error counter** to 0 to give the alternative approach a fair chance
- **Bounds recovery attempts** to maximum 3 alternative approaches
- **Returns boolean** indicating whether an alternative approach was attempted
- **Preserves failure history** while resetting only the consecutive error counter

#### Integration with Existing Systems
- **Builds on Phase 7.2 foundation**: Uses existing exponential backoff, retry logic, and error classification
- **Complementary to stall detection**: Operates alongside existing `_check_stall()` mechanism
- **State persistence compatible**: New fields are included in `_persist_state()` and `_recover_state()` methods
- **Does not bypass safety systems**: All tool execution still goes through Tool System with proper policy enforcement
- **Preserves normal failure handling**: Falls back to standard failure recovery after alternative approaches are exhausted

### Recovery Flow
1. When retries are exhausted and consecutive errors ≥ max_consecutive_failures:
2. Check if fundamental flaw detected via `_detect_fundamental_flaw()`
3. If flaw detected and alternatives remain (< 3 attempted):
   - Attempt alternative approach via `_attempt_alternative_approach()`
   - Reset consecutive error counter to 0
   - Continue to next iteration with alternative approach context
4. If no fundamental flaw or no alternatives remain:
   - Transition to FAILED state with appropriate completion reason

### Testing
- **Unit tests**: 15/15 passed in test_orchestrator.py
- **Trace tests**: 15/15 passed in test_orchestrator_trace.py
- **Timeout isolated tests**: 1/1 passed in test_timeout_isolated.py
- **Full test suite**: 257 passed, 0 failed, 4 skipped

### Known Limitations
- **Hardcoded thresholds**: Failure count threshold (3) and non-retryable ratio (70%) are fixed values
- **Guidance-based alternatives**: Alternative approaches modify LLM context rather than directly changing tool/model behavior
- **Pattern detection simplicity**: Uses basic frequency analysis rather than advanced sequence or temporal pattern detection

### Non-Goals (Explicitly Out of Scope for Phase 7.3.3)
- Full autonomy without human oversight
- General problem-solving capabilities beyond software engineering
- Real-time collaboration features requiring persistent connections
- Advanced planning capabilities requiring significant computational resources
- Learning across completely unrelated task domains
- Implementation of Adaptive Iteration Control (Phase 7.3.2)
- Implementation of Observability and Metrics (Phase 7.3.9)

## 42. Phase 7.3.4: Progress/Goal Tracking + User Interruption/Control

### Phase 7.3.4.1: Progress Tracking Foundation (IMPLEMENTED)

Implemented a focused ProgressMetrics / ProgressTracker abstraction that provides reliable progress information for later stages.

#### Implementation Details

**ProgressMetrics Data Model**
- Created a compact, serializable ProgressMetrics class that tracks:
  - Iteration-level metrics (successful/failed/total tool calls)
  - Workspace change tracking (file count deltas)
  - Error tracking (count and deltas)
  - Success rate calculation
  - Bounded historical metrics for trend analysis (last 10 iterations)
- Supports serialization/deserialization for persistence/recovery
- Provides trend calculation (improving/stable/declining)
- Defines meaningful progress detection based on successful operations, positive workspace changes, or error reduction

**Integration with AgentOrchestratorState**
- Added progress_metrics: ProgressMetrics field (with default factory)
- Added previous iteration counters (prev_total_tool_calls, prev_error_count, prev_workspace_file_count) for calculating per-iteration deltas
- Updated _persist_state() and _recover_state() methods to handle progress metrics persistence
- Updated _validate_recovered_state() to validate new fields while maintaining backward compatibility

**Integration with Orchestrator**
- Enhanced _update_progress() method to use ProgressMetrics instead of legacy fields
- Progress updates occur at appropriate lifecycle boundaries (success and failure paths)
- Maintains backward compatibility with legacy progress tracking fields
- Progress reflects actual execution outcomes from tool execution results

**Trend Calculation**
- Implements simple deterministic trend model based on:
  - Success rate trend (weighted 0.5)
  - Workspace change trend (weighted 0.3)
  - Error trend (weighted 0.2, negative = improving)
- Returns "improving", "stable", or "declining" based on weighted scoring
- Avoids machine learning or complex statistical prediction

**Meaningful Progress Definition**
- Conservative rule: meaningful progress if any of:
  - Successful relevant tool operations (successful tool calls > 0)
  - Relevant workspace changes (positive file count delta)
  - Error reduction (negative error delta)
- Explicitly does NOT consider:
  - Repeated identical operations
  - Failed operations
  - Unrelated changes
  - Changes that immediately regress

**Persistence and Recovery**
- Integrates with existing _persist_state() and _recover_state() methods
- Progress history is bounded to prevent memory growth
- Values are validated during recovery
- Malformed progress data handled gracefully
- Maintains compatibility with existing Phase 7.3.1 persisted state

**Tests Added**
- ProgressMetrics initialization and basic functionality
- Metric updates and delta calculations
- Current statistics retrieval
- Trend calculation (improving, stable, declining)
- Meaningful progress detection
- Bounded history maintenance
- Serialization and deserialization
- Recovery with valid and malformed data
- Integration with existing orchestrator behavior

#### Integration Points
- Uses existing iteration/tool execution information from _execute_tool_calls
- Leverages existing workspace interfaces for file counting (read-only, no direct filesystem access in AgentOrchestrator)
- Preserves existing AgentOrchestratorState structure and persistence mechanisms
- Does not modify termination decisions, max iteration calculations, or adaptive iteration budget (reserved for later stages)

#### Known Limitations
- Trend calculation uses simple weighted scoring rather than advanced statistical methods
- Meaningful progress definition is conservative and may not capture all nuances of progress
- Workspace tracking relies on file count changes rather than semantic relevance
- History size is fixed at 10 iterations (configurable but not exposed externally)


### Phase 7.3.4.2: Goal Tracking & Integration (IMPLEMENTED)

Implemented minimal goal tracking to represent task goal and completion state, integrated with existing ProgressMetrics system.

#### Implementation Details

**GoalTracker Data Model**
- Created a compact, serializable GoalTracker class that tracks:
  - Goal description: Text description of the task/goal
  - Completion criteria: List of specific, detectable conditions that indicate goal completion
  - Status: Current goal status (pending, in_progress, completed, failed)
  - Progress: Numerical progress value (0.0 to 1.0) representing completion ratio
  - Progress evidence: List of strings tracking evidence supporting the progress value
  - Bounded history: Limited history of goal states for serialization/persistence (last 10 iterations)

**Key Features**
- Minimal, focused design avoiding unnecessary fields
- Deterministic, serializable, and recoverable state transitions
- Progress evaluation based on evidence-based criteria
- Integration with existing termination logic through state transitions
- Backward compatibility - older states without goal information initialize appropriately

**Goal Progress Evaluation**
- Completion evaluated based on evidence matching completion criteria
- Progress calculated as ratio of matched criteria to total criteria (0.0 to 1.0)
- Status transitions:
  - pending → in_progress when progress > 0
  - in_progress → completed when progress >= 1.0 AND all completion criteria are satisfied
  - in_progress → failed when error count reaches max_consecutive_failures
  - For goals with no completion criteria, progress remains 0.0 and status stays pending

**Integration with AgentOrchestratorState**
- Added goal_tracker: GoalTracker field (with default factory)
- Updated _persist_state() and _recover_state() methods to handle goal tracker persistence
- Updated _validate_recovered_state() to validate new fields while maintaining backward compatibility
- Goal tracking initialized in execute_task() with task description as goal and basic completion criteria ["Task completed successfully"]

**Integration with Orchestrator**
- Enhanced _update_goal_tracker() method called after each iteration to update goal progress
- Goal completion checked in _update_goal_tracker() - sets state to COMPLETED when goal is completed
- Goal failure checked in _update_goal_tracker() - sets state to FAILED when goal has failed
- Goal tracking updates occur at appropriate lifecycle boundaries (after each iteration)
- Works cooperatively with existing adaptive iteration and failure recovery systems

**Persistence and Recovery**
- Integrates with existing _persist_state() and _recover_state() methods
- Goal history is bounded to prevent memory growth
- Values are validated during recovery using type checking and value validation
- Malformed goal data handled gracefully with safe defaults
- Maintains compatibility with existing persisted state from earlier phases

**Tests Added**
- GoalTracker initialization with default and custom values
- Goal description and completion criteria updates
- Progress evaluation with various completion criteria combinations
- Goal status transitions (pending → in_progress → completed/failed)
- Progress clamping to [0, 1] range
- History recording and bounded maintenance
- Serialization and deserialization of goal tracker state
- Recovery with valid and malformed goal data
- Integration with orchestrator update and persistence mechanisms
- Backward compatibility with states lacking goal tracker information
- Orchestrator-level integration testing

#### Integration Points
- Uses existing iteration and tool execution information from _update_goal_tracker
- Leverages existing workspace interfaces for file counting (read-only, no direct filesystem access)
- Integrates with existing state persistence mechanisms (_persist_state/_recover_state)
- Cooperates with existing termination logic through state transitions
- Works with existing adaptive iteration and failure recovery systems
- Does not modify core orchestrator loop or decision-making processes

#### Known Limitations
- Completion criteria matching uses simple string matching (case-insensitive substring)
- Default completion criteria is simplistic: ["Task completed successfully"]
- Goal description is currently just the task description
- Progress evidence tracking is basic string-based
- History size is fixed at 10 iterations (configurable but not exposed externally)


### Phase 7.3.4.3: User Interruption & Control (IMPLEMENTED)

Implemented user interruption and control mechanisms to allow safe user-driven control of an active task including cancel, pause, resume, and stop-after-iteration functionality.

#### Implementation Details

**Control Model**
- Added PAUSED state to AgentState enum for representing paused execution
- Added control flags to AgentOrchestrator: _cancelled, _paused, _stop_after_iteration
- Added public control methods: cancel(), pause(), resume(), stop_after_iteration()
- Control fields are persisted and recovered to maintain state across sessions

**Integration with AgentOrchestratorState**
- Added control fields to persistence mechanism:
  - cancelled: Boolean flag for cancellation state
  - paused: Boolean flag for pause state
  - stop_after_iteration: Boolean flag for stop-after-iteration request
- Updated _persist_state() and _recover_state() methods to handle control fields
- Updated _validate_recovered_state() to validate new control fields

**Integration with Orchestrator Loop**
- Added pause/resume handling at safe iteration boundaries:
  - Check for pause before starting each iteration
  - When paused, enter wait loop until resumed or cancelled
  - Persist state when entering paused state
  - Resume execution from exact point of pause
- Enhanced cancellation handling:
  - Works correctly with pause state (can cancel while paused)
  - Does not override TIMED_OUT or COMPLETED states
  - Properly sets state to CANCELLED when cancelled
- Implemented stop-after-iteration functionality:
  - Completes current iteration before stopping
  - Does not start next iteration when flag is set
  - Respects existing completion logic

**Safe Interruption Boundaries**
- Pause/resume checks occur at iteration boundaries (safe points)
- Does not interrupt ongoing model invocations or tool executions
- Allows current iteration to complete before pausing or stopping
- Maintains existing safety boundaries for tool execution and policy enforcement

**State Transition Rules**
- PAUSED state can only be entered from RUNNING state at iteration boundaries
- From PAUSED: can transition to RUNNING (via resume) or CANCELLED (via cancel)
- CANCELLED state overrides RUNNING/PAUSED but not TIMED_OUT or COMPLETED
- STOP_AFTER_ITERATION completes current iteration normally then stops
- All terminal states (COMPLETED, FAILED, CANCELLED, TIMED_OUT) are preserved

**Persistence and Recovery**
- Control state is fully persisted and recoverable
- Paused state is correctly restored upon recovery
- Control flags are reset appropriately for fresh task execution
- Backward compatibility maintained with older state formats
- Malformed control data handled gracefully with safe defaults

**Integration with Existing Systems**
- Cooperates with existing adaptive iteration control
- Works with failure recovery and alternative approach mechanisms
- Integrates with progress tracking and goal tracking systems
- Respects timeout handling (TIMED_OUT takes precedence)
- Does not modify core decision-making processes

**Tests Added**
- Cancel active task and verify CANCELLED state
- Cancel before execution and verify immediate cancellation
- Cancel while paused and verify proper transition to CANCELLED
- Cancel after completion verifies no state change
- Repeated cancel calls are idempotent
- Pause active task and verify PAUSED state
- Repeated pause calls are idempotent
- Pause at safe boundary (before iteration start)
- Verify paused task does not begin another iteration
- Resume paused task and verify continuation from exact point
- Repeated resume calls are idempotent/safe
- Verify state preservation across pause/resume (progress, goals, history)
- Verify iteration count preserved across pause/resume
- Verify progress metrics preserved across pause/resume
- Verify goal tracking preserved across pause/resume
- Verify execution history preserved across pause/resume
- Stop-after-iteration requested during iteration:
  - Current iteration completes safely
  - Next iteration does not start
  - No false FAILED state generated
- Stop-after-iteration requested before iteration starts:
  - Stops before starting the iteration
  - Reports appropriate completion state
- State transition verification:
  - CANCELLED remains CANCELLED during cleanup
  - TIMED_OUT remains TIMED_OUT during cleanup
  - COMPLETED remains COMPLETED during cleanup
  - FAILED remains FAILED during cleanup
  - PAUSED remains PAUSED when appropriate
- Race/boundary case testing:
  - Cancellation during retry backoff
  - Cancellation around timeout boundaries
  - Pause/resume near iteration boundaries
  - Stop-after-iteration near iteration boundaries
- Regression testing: All existing orchestrator behavior remains intact

#### Integration Points
- Uses existing iteration boundaries for safe interruption checks
- Leverages existing state persistence mechanisms (_persist_state/_recover_state)
- Integrates with existing state validation (_validate_recovered_state)
- Cooperates with existing termination logic through proper state transitions
- Works with existing adaptive iteration and failure recovery systems
- Integrates with progress tracking and goal tracking updates
- Does not modify core orchestrator loop or decision-making processes

#### Known Limitations
- Pause/resume granularity is at iteration boundaries only
- No mid-tool-execution or mid-model-invocation interruption
- Stop-after-iteration completes current iteration fully before stopping
- Control state increases persistence footprint slightly (3 boolean fields)

## 43. Phase 7.3.5: Context Optimization Enhancements

### Phase 7.3.5.2.1: Symbol-Level Context Selection (IMPLEMENTED)

Enhanced the Context Selector to support symbol-level context selection using Phase 3 Symbol Dependency Analyzer output, providing more granular context selection capabilities beyond file-level selection.

#### Implementation Details

**Enhanced ContextSelector Class**
- Modified `__init__` method to accept optional `symbol_analyzer` parameter for Phase 3 Symbol Dependency Analyzer integration
- Updated `SelectionCriteria` dataclass:
  - Added `use_symbol_level_selection` boolean field (defaults to True)
  - Added `symbol_similarity_weight` float field (defaults to 0.1, range 0.0-1.0)
  - Updated `__hash__` method to include new fields for proper caching
- Enhanced `select_context` method with multi-scenario handling:
  - Uses both relevance engine and symbol analyzer when both are available
  - Falls back to relevance-only selection when symbol analyzer unavailable
  - Falls back to symbol-only selection when relevance engine unavailable
  - Uses basic selection when neither analyzer is available
- Added helper methods for symbol-based selection:
  - `_select_context_with_symbols`: Combines relevance scores with symbol similarity bonuses
  - `_select_context_relevance_only`: Uses relevance engine exclusively (fallback)
  - `_select_context_symbols_only`: Uses symbol analyzer exclusively (fallback)
  - `_get_file_context_enhanced`: Extracts file context with symbol information
  - `_get_file_context_basic`: Extracts file context without symbol information (fallback)
  - `_extract_file_symbols`: Now functional, uses symbol_analyzer when available
  - `_format_symbols_for_output`: Formats Symbol objects for context output
  - `_is_within_workspace`: Checks if file is within workspace boundaries
  - `_calculate_symbol_relevance_bonus`: Computes symbol-task similarity bonus
  - `_extract_keywords`: Extracts keywords from task description for symbol matching
- Preserved all existing methods for backward compatibility:
  - `_extract_file_snippets`, `_extract_snippets_from_content`, `_detect_language`, `_get_repository_info`, `__repr__`

**Symbol-Level Selection Algorithm**
When both relevance engine and symbol analyzer are available:
1. Calculate base relevance scores for all files using Phase 3 RelevanceEngine
2. Extract symbols for each file using Phase 3 SymbolDependencyAnalyzer
3. Calculate symbol relevance bonus based on keyword matching between task description and symbol names/scopes
4. Combine relevance score and symbol bonus (capped at 1.0)
5. Select files based on combined score meeting minimum relevance threshold
6. Apply maximum files limit
7. Extract detailed context (including symbols and snippets) for selected files

**Fallback Mechanisms**
- When symbol analyzer unavailable: Uses relevance engine only (existing behavior)
- When relevance engine unavailable: Uses symbol analyzer only (new capability)
- When neither available: Falls back to basic file selection (existing behavior)
- Symbol analysis failures gracefully handled with empty symbol lists

**Backward Compatibility**
- All existing interfaces preserved
- Symbol-level selection configurable via `use_symbol_level_selection` flag
- Existing functionality unchanged when symbol analyzer not provided
- No changes to ContextManager, ContextBudgeter, ContextAssembler, or DuplicatePreventer
- No duplicate SymbolAnalyzer creation - consumes Phase 3 output directly

**Testing**
- Unit tests: 7/7 passed in test_context_selector.py
- All existing tests continue to pass, confirming no regressions
- Verified symbol-level selection enhances context relevance when symbol information available
- Verified fallback mechanisms work correctly when analyzers unavailable

#### Key Benefits
- More precise context selection at symbol/function level rather than file level
- Better alignment between task requirements and selected context
- Improved token efficiency by selecting only relevant symbols within files
- Maintains all existing file-level selection capabilities as fallback
- Leverages existing Phase 3 infrastructure without duplication

#### Configuration
Symbol-level selection can be controlled through SelectionCriteria:
```python
criteria = SelectionCriteria(
    use_symbol_level_selection=True,    # Enable/disable symbol-level selection
    symbol_similarity_weight=0.1        # Weight for symbol similarity signal (0.0-1.0)
)
```

#### Non-Goals (Explicitly Out of Scope for Phase 7.3.5.2.1)
- Implementation of Context Budgeting enhancements (Phase 7.3.5.2.2)
- Implementation of Context Assembly enhancements (Phase 7.3.5.2.3)
- Redesign of ContextManager architecture
- Creation of duplicate SymbolAnalyzer
- Changes to existing ContextSelector methods beyond those specified

### Phase 7.3.5.2.2: Relevance-Guided Extraction (Stage 1 - Basic Line Relevance IMPLEMENTED)

Enhanced the Context Selector to use relevance information from task descriptions to preferentially select relevant code regions within selected files, providing more precise context extraction while maintaining all existing functionality as fallback.

#### Implementation Details

**Enhanced ContextSelector Class**
- Modified `_extract_snippets_from_content` method to accept `task_description` parameter
- Updated `_extract_file_snippets` method to accept `task_description` parameter (for API consistency)
- Enhanced `select_context` method callers to pass `task_description` to snippet extraction:
  - `_select_context_with_symbols`
  - `_select_context_relevance_only` 
  - `_select_context_symbols_only`

**Relevance-Guided Extraction Algorithm**
When task description contains usable keywords:
1. Extract keywords from task description using existing `_extract_keywords` method
2. Score each line based on keyword matches (normalized by line length to avoid bias)
3. For small files (lines ≤ lines_per_snippet × max_snippets_per_file):
   - Evaluate all possible chunks and select top-scoring ones by average line relevance
4. For large files (lines > lines_per_snippet × max_snippets_per_file):
   - Create probability distribution based on line scores
   - Select highest scoring lines first (deterministic)
   - Fill remaining slots with uniform sampling if needed
   - Respect lines_per_snippet and max_snippets_per_file constraints

**Fallback Mechanisms** (Preserve Existing Behavior)
- When task_description is empty → Original extraction behavior
- When no keywords extracted from task_description → Original extraction behavior  
- When keywords exist but no matches found in content → Original extraction behavior
- When relevance-guided sampling insufficient → Supplement with uniform sampling
- All existing criteria parameters (lines_per_snippet, max_snippets_per_file) respected

**Backward Compatibility**
- All existing interfaces preserved
- Existing functionality unchanged when task_description not usable
- No changes to ContextManager, ContextBudgeter, ContextAssembler, or DuplicatePreventer
- No modifications to token budgeting systems
- No duplicate analyzer creation - uses existing relevance information from task description

#### Configuration
Relevance-guided extraction is automatically triggered when:
- `criteria.extract_snippets == True` (default)
- `task_description` parameter is provided and contains usable keywords

#### Testing
- Unit tests: 7/7 passed in test_context_selector.py
- All existing unit tests continue to pass (270 passed, 0 failed, 4 skipped)
- All existing integration tests continue to pass (14 passed, 0 failed, 0 skipped)
- Total test suite: 284 passed, 0 failed, 4 skipped (matches baseline)
- Verified relevance-guided extraction selects more relevant regions when keywords match
- Verified fallback mechanisms work correctly when relevance information unavailable

#### Key Benefits
- More precise context selection at line level rather than uniform sampling
- Better alignment between task requirements and extracted code regions
- Improved token efficiency by focusing on relevant code within selected files
- Maintains all existing extraction capabilities as fallback
- Leverages existing keyword extraction infrastructure

#### Configuration
Relevance-guided extraction happens automatically when task_description is provided to the ContextSelector.select_context() method.

### Phase 7.3.5.2.2: Relevance-Guided Extraction (Stage 2 - Symbol-Aware Extraction IMPLEMENTED)

Enhanced the Context Selector to use symbol information from Phase 3 SymbolDependencyAnalyzer to guide which regions of a selected file are extracted, providing even more precise context extraction when symbol information is available.

#### Implementation Details

**Enhanced ContextSelector Class**
- Modified `_extract_snippets_from_content` method to accept an optional `symbols` parameter
- Enhanced line scoring algorithm to combine task keyword relevance with symbol proximity bonuses
- Updated all snippet extraction call sites to pass symbol information when available
- Added `_calculate_symbol_line_relevance_bonus` helper method to compute symbol-based line relevance

**Symbol-Aware Extraction Algorithm**
When both task description keywords and symbol information are available:
1. Extract keywords from task description using existing `_extract_keywords` method
2. Score each line based on keyword matches (normalized by line length to avoid bias)
3. Calculate symbol relevance bonus based on proximity to relevant symbols:
   - A symbol is considered relevant if its name or scope contains task keywords
   - Relevance decreases with distance from the symbol's line range
   - Configurable weighting via existing `symbol_similarity_weight` in SelectionCriteria
4. Combine keyword relevance and symbol bonus (capped at 1.0)
5. For small files (lines ≤ lines_per_snippet × max_snippets_per_file):
   - Evaluate all possible chunks and select top-scoring ones by combined line relevance
6. For large files (lines > lines_per_snippet × max_snippets_per_file):
   - Create probability distribution based on combined line scores
   - Select highest scoring lines first (deterministic)
   - Fill remaining slots with uniform sampling if needed
   - Respect lines_per_snippet and max_snippets_per_file constraints

**Fallback Mechanisms** (Preserve Existing Behavior)
- When task_description is empty → Original extraction behavior
- When no keywords extracted from task_description → Symbol-aware extraction if symbols available
- When keywords exist but no matches found in content → Symbol-aware extraction if symbols available
- When no symbols available → Keyword-only relevance-guided extraction (Stage 1)
- When neither keywords nor symbols available → Original extraction behavior
- When relevance-guided sampling insufficient → Supplement with uniform sampling
- All existing criteria parameters (lines_per_snippet, max_snippets_per_file) respected

**Backward Compatibility**
- All existing interfaces preserved
- Existing functionality unchanged when task_description or symbols not usable
- No changes to ContextManager, ContextBudgeter, ContextAssembler, or DuplicatePreventer
- No modifications to token budgeting systems
- No duplicate analyzer creation - uses existing Phase 3 SymbolDependencyAnalyzer output

#### Configuration
Symbol-aware extraction is automatically triggered when:
- `criteria.extract_snippets == True` (default)
- `task_description` parameter is provided and/or symbol information is available from Phase 3
- `criteria.use_symbol_level_selection == True` (default)

#### Testing
- Unit tests: 7/7 passed in test_context_selector.py
- All existing unit tests continue to pass (270 passed, 0 failed, 4 skipped)
- All existing integration tests continue to pass (14 passed, 0 failed, 0 skipped)
- Total test suite: 284 passed, 0 failed, 4 skipped (matches baseline)
- Verified symbol-aware extraction selects more relevant regions when symbols match task keywords
- Verified fallback mechanisms work correctly when symbol information unavailable
- Verified deterministic output for identical inputs

#### Key Benefits
- More precise context selection at line level with symbol awareness
- Better alignment between task requirements and extracted code regions using both task keywords and symbol information
- Improved token efficiency by focusing on code near relevant symbols
- Maintains all existing extraction capabilities as fallback
- Leverages existing Phase 3 Symbol Dependency Analyzer infrastructure without duplication

#### Non-Goals (Explicitly Out of Scope for Stage 2)
- Implementation of context-window optimization/snippet merging (Phase 7.3.5.2.2 Stage 3)
- Changes to Context Budgeting or Context Assembly systems
- Creation of semantic duplicate detectors or vector search capabilities
- Machine learning ranking or embeddings-based relevance scoring

#### Non-Goals (Explicitly Out of Scope for Stage 1)
- Implementation of context-window optimization/snippet merging (Phase 7.3.5.2.2 Stage 3)
- Changes to Context Budgeting or Context Assembly systems
- Creation of semantic duplicate detectors or vector search capabilities
- Machine learning ranking or embeddings-based relevance scoring