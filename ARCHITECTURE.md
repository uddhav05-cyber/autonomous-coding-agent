 # Architecture

## Status

Proposed — subject to research validation.

---

# 1. Architectural Goal

Build a simple, testable coding-agent architecture where the LLM
is responsible for reasoning and decision-making while deterministic
software performs validation and execution.

---

# 2. High-Level Architecture

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

---

# 3. Components

## Task Manager

Responsible for:

- Receiving tasks
- Creating task state
- Tracking task status
- Enforcing task-level limits

---

## Agent Orchestrator

Responsible for:

- Controlling the agent loop
- Sending context to the model
- Processing model decisions
- Calling tools
- Handling iteration limits
- Determining when verification is required

The orchestrator should not directly implement filesystem,
shell, git, or testing operations.

---

## Context Manager

Responsible for:

- Repository discovery
- Relevant-file selection
- Context assembly
- Context budgeting
- Context compression where necessary
- Preventing unnecessary context duplication

---

## Model Adapter

Responsible for:

- Model-provider communication
- Structured model responses
- Tool-call parsing
- Model usage metrics
- Provider-specific translation

The rest of the application should not depend directly on a
specific model provider SDK.

---

## Tool Registry

Responsible for:

- Registering tools
- Exposing tool schemas
- Tool metadata
- Permission requirements

---

## Tool Policy

Responsible for:

- Validating requested operations
- Checking permissions
- Blocking prohibited actions
- Applying timeouts
- Enforcing workspace boundaries

---

## Tool Executor

Responsible for executing approved operations.

Examples:

- File reading
- File writing
- Search
- Test execution
- Git operations

---

## Workspace

Represents the repository being modified.

The agent must not modify files outside the configured workspace.

---

## Verification

Responsible for deterministic validation.

Examples:

- Tests
- Lint
- Type checking
- Syntax checking
- Git diff

---

## Recovery

Responsible for handling verification failures.

The recovery system should:

1. Receive structured failure information.
2. Provide relevant evidence to the model.
3. Allow a bounded repair attempt.
4. Re-run verification.
5. Stop after the configured retry budget.

---

# 4. Initial Agent Loop

The first implementation should use a bounded loop:

Task
 ↓
Understand
 ↓
Plan
 ↓
Tool call
 ↓
Observe result
 ↓
Next decision
 ↓
Verification
 ↓
Success / Repair / Stop

---

# 5. Architectural Constraints

The system must:

- Use typed tool interfaces.
- Validate tool arguments.
- Enforce workspace boundaries.
- Apply execution timeouts.
- Record tool calls.
- Record model calls.
- Record verification results.
- Limit retries.
- Limit execution time.
- Limit model usage.

---

# 6. Deliberately Excluded From V1

The following are not included unless evaluation demonstrates
a need:

- Complex multi-agent architecture
- Distributed execution
- Autonomous deployment
- Remote code execution
- Arbitrary internet access
- Automatic GitHub pushing
- Large vector databases
- Complex memory systems

---

# 7. Architecture Evolution Rule

Architecture changes must be justified using:

- Evaluation results
- Reliability problems
- Performance measurements
- Security requirements
- Maintainability requirements

Popularity alone is not sufficient justification.

