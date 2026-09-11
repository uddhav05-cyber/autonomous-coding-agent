 # Agent Evaluation

## Objective

Measure whether the coding agent can reliably perform software
engineering tasks.

Evaluation must measure behavior rather than relying on subjective
inspection of a few successful demos.

---

# 1. Primary Metrics

## Task Success

Percentage of benchmark tasks completed successfully.

---

## Test Success

Percentage of tasks where required tests pass.

---

## Tool Accuracy

Percentage of tool calls that:

- Use the correct tool.
- Provide valid arguments.
- Serve the task.
- Avoid unnecessary operations.

---

## Recovery Rate

Percentage of intentionally failed executions from which the agent
successfully recovers.

---

## Unnecessary Modification Rate

Percentage of tasks where unrelated files are modified.

---

## Safety Violation Rate

Percentage of evaluation tasks resulting in prohibited behavior.

Target:

0 known safety violations in the controlled benchmark.

---

## Token Efficiency

Track:

- Input tokens
- Output tokens
- Total tokens
- Model calls
- Tool calls

---

## Cost

Track estimated model cost per task.

---

## Latency

Track:

- Total task duration
- Model latency
- Tool latency
- Verification latency

---

# 2. Evaluation Categories

## Category A — Simple Changes

Examples:

- Add function
- Fix small bug
- Update validation

---

## Category B — Multi-file Changes

Examples:

- Add feature across multiple modules
- Modify API + service + tests

---

## Category C — Debugging

Provide an existing failing implementation.

The agent must identify and repair it.

---

## Category D — Test-driven Tasks

Provide requirements and existing tests.

The agent must implement behavior satisfying the tests.

---

## Category E — Ambiguous Tasks

Provide insufficient requirements.

Expected behavior:

The agent should ask for clarification rather than making
unjustified assumptions.

---

## Category F — Recovery

Introduce an implementation path that causes verification failure.

Measure whether the agent diagnoses and repairs the problem.

---

## Category G — Security

Test:

- Prompt injection
- Path traversal
- Secret access
- Dangerous commands
- Workspace escape

---

# 3. Benchmark Structure

Each benchmark case should contain:

- Task ID
- Repository fixture
- User requirement
- Expected behavior
- Relevant tests
- Safety constraints
- Evaluation criteria

---

# 4. Example Benchmark

ID:

BUG-001

Task:

Fix the pagination bug in the API.

Expected:

- Correct pagination behavior.
- Existing tests pass.
- New regression test added if appropriate.
- No unrelated files modified.

---

# 5. Evaluation Rules

Never evaluate only the final natural-language answer.

Use actual evidence:

- Test results
- Git diff
- Tool traces
- Execution state
- Benchmark assertions

---

# 6. Regression Testing

Every important agent improvement should be tested against the
existing evaluation suite.

An optimization is not considered successful if it improves token
usage while significantly reducing task success or safety.

---

# 7. Evaluation Philosophy

The objective is not to maximize benchmark numbers at any cost.

The objective is to build an agent that is:

- Correct
- Reliable
- Safe
- Efficient
- Observable
- Reproducible

