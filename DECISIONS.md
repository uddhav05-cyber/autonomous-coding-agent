 # Architecture Decisions

This document records important technical decisions and their
rationale.

---

# ADR-001 — Start With a Single Agent Orchestrator

## Status

Accepted

## Decision

Use a single primary agent orchestrator for V1.

## Reason

A multi-agent architecture introduces additional:

- Model calls
- Context transfers
- Coordination failures
- State management
- Debugging complexity
- Cost

There is no reason to introduce that complexity before evaluation
demonstrates a measurable benefit.

## Revisit When

Evaluation demonstrates that specialized agents provide meaningful
improvements in task success, reliability, or cost.

---

# ADR-002 — Deterministic Verification

## Status

Accepted

## Decision

Tests, linters, type checkers, and git state are treated as
authoritative verification mechanisms.

## Reason

LLM reasoning is not sufficient evidence that generated code works.

---

# ADR-003 — Controlled Tools

## Status

Accepted

## Decision

The model cannot directly access operating-system capabilities.

All capabilities must be exposed through controlled tools.

## Reason

This enables:

- Validation
- Permissions
- Logging
- Timeouts
- Testing
- Security controls

---

# ADR-004 — Context Must Be Selective

## Status

Accepted

## Decision

The agent should retrieve the smallest useful context rather than
sending the entire repository to the model.

## Reason

This improves:

- Cost
- Latency
- Model focus
- Scalability

It also makes context behavior measurable.

---

# ADR-005 — Measure Before Optimizing

## Status

Accepted

## Decision

Token and latency optimization must be based on measurements.

## Reason

Premature optimization can reduce reliability while providing
little actual benefit.

