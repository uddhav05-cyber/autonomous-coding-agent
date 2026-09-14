 # Implementation Plan

## Status

Phase 2 implemented and release-reviewed.

---

# Phase 0 — Research

- Complete research plan.
- Collect authoritative sources.
- Document architectural findings.
- Validate technology choices.

Deliverables:

- research/*.md
- research/SOURCES.md

---

# Phase 1 — Project Foundation

Implement:

- Python project
- Configuration
- Logging
- Error model
- Basic test infrastructure
- Docker development environment

Verification:

- Project starts.
- Tests execute.
- Configuration loads correctly.

---

# Phase 2 — Workspace

Implement:

- Workspace abstraction
- File listing
- File reading
- File writing
- Patch application
- Path validation

Verification:

- Workspace boundaries tested.
- Invalid paths rejected.
- File operations tested.
- Symlink and workspace-root deletion protections tested.
- Atomic write behavior tested.
- Full test, lint, and coverage review required before commit.

Phase 2 release limitations:

- No OS-level sandbox or descriptor-based protection against concurrent
	symlink replacement (TOCTOU).
- No shell command, network, secret, permission, audit, or tool-policy layer.
- No configured static type checker.
- `.env` files are not loaded by the current settings model.

---

# Phase 3 — Repository Understanding

Implement:

- Repository scanner
- File filtering
- Code search
- Relevant-file discovery
- Repository metadata

Verification:

- Repository fixtures.
- Search tests.
- Large repository tests.

---

# Phase 4 — Context Manager

Implement:

- Context selection
- Context budget
- Context assembly
- Duplicate prevention
- Context metrics

Verification:

- Token measurements.
- Relevant-file selection tests.
- Context regression tests.

---

# Phase 5 — Model Adapter

Implement:

- Provider abstraction
- Model request/response types
- Tool-call representation
- Usage tracking
- Error handling

Verification:

- Mock model tests.
- Provider integration tests.

---

# Phase 6 — Tool System

Implement:

- Tool interface
- Tool registry
- Tool schemas
- Tool validation
- Tool permissions
- Tool execution

Initial tools:

- list_files
- read_file
- search_code
- write_file
- apply_patch

---

# Phase 7 — Agent Orchestrator

Implement:

- Agent state
- Agent loop
- Tool selection
- Iteration limits
- Stop conditions
- Failure handling

Verification:

- Mock-model agent tests.
- Tool-loop tests.
- Stop-condition tests.

---

# Phase 8 — Verification

Implement:

- Test runner
- Lint runner
- Type-check runner
- Git diff inspection
- Verification result model

---

# Phase 9 — Recovery

Implement:

- Failure classification
- Failure context
- Repair loop
- Retry budget
- Stop conditions

---

# Phase 10 — Evaluation

Implement:

- Benchmark format
- Repository fixtures
- Evaluation runner
- Metrics
- Regression suite

Initial target:

30 carefully designed benchmark tasks.

---

# Phase 11 — Security

Implement:

- Workspace boundary
- Secret protection
- Command policy
- Tool permissions
- Prompt-injection evaluations
- Security regression tests

---

# Phase 12 — Observability

Implement:

- Agent traces
- Model-call metrics
- Tool-call metrics
- Token metrics
- Latency metrics
- Cost metrics
- Verification traces

---

# Phase 13 — Optimization

Only after baseline measurements exist.

Investigate:

- Context reduction
- Model routing
- Tool-result compression
- Caching
- Retry optimization
- Context reuse

Every optimization must be benchmarked.

---

# Phase 14 — Developer Interface

Only after the core agent is reliable.

Possible interfaces:

- CLI
- HTTP API
- Optional web dashboard

The interface must not drive unnecessary complexity into the
core architecture.

---

# Phase 15 — Final Benchmark

Run the complete evaluation suite.

Record:

- Task success
- Test success
- Recovery rate
- Safety violations
- Unnecessary modifications
- Token usage
- Cost
- Latency

Document failures and limitations.

---

# Implementation Rule

Implement one phase at a time.

Do not implement later phases prematurely.

Do not create abstractions for hypothetical future requirements.

Do not introduce additional frameworks unless they solve a
demonstrated problem.

