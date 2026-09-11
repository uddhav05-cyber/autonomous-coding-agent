 # Autonomous Coding Agent

## Project Status

Status: Pre-Implementation

Version: 0.1.0

## 1. Project Vision

Build an AI software-engineering agent capable of taking a
software-development task and autonomously working on an existing
code repository inside a controlled workspace.

The agent should be able to:

1. Understand a user's software-development task.
2. Inspect the repository.
3. Identify relevant files and code.
4. Build an efficient context.
5. Create an implementation plan.
6. Modify code using controlled tools.
7. Run tests and other verification tools.
8. Diagnose failures.
9. Repair the implementation.
10. Re-run verification.
11. Inspect the resulting changes.
12. Produce an auditable final report.

The system must prioritize correctness, safety, reproducibility,
observability, and efficient use of model context.

---

## 2. Problem Statement

Current AI coding assistants can generate code but may:

- Read excessive amounts of repository content.
- Make unnecessary changes.
- Use incorrect APIs.
- Modify unrelated files.
- Fail to verify their work.
- Repeat unsuccessful actions.
- Consume excessive tokens.
- Follow malicious instructions contained inside repositories.
- Claim success without sufficient evidence.

This project aims to address these problems through explicit
architecture, controlled tools, context management, verification,
evaluation, security controls, and observability.

---

## 3. Primary Goal

The primary goal is NOT to build the largest coding agent.

The goal is to build a small, measurable, reliable coding agent whose
behavior can be evaluated and improved systematically.

---

## 4. Core Workflow

The primary execution loop is:

User Task
    ↓
Repository Discovery
    ↓
Context Selection
    ↓
Planning
    ↓
Implementation
    ↓
Verification
    ↓
Failure Diagnosis
    ↓
Repair
    ↓
Re-verification
    ↓
Final Review
    ↓
Final Report

---

## 5. Core Capabilities

### Repository Understanding

The system should be able to:

- Inspect repository structure.
- Identify the project language.
- Identify frameworks and dependencies.
- Locate entry points.
- Search for relevant symbols.
- Identify related tests.
- Determine relevant files.

### Planning

The agent should:

- Understand the requested behavior.
- Identify affected components.
- Explain the proposed implementation.
- Identify potential risks.
- Create a bounded implementation plan.

### Code Modification

The agent should be able to:

- Read files.
- Search code.
- Create files.
- Modify files.
- Apply targeted patches.
- Inspect resulting changes.

### Verification

The system should be able to:

- Run relevant tests.
- Run linting.
- Run type checking where applicable.
- Inspect git diff.
- Detect unexpected modifications.

### Recovery

When verification fails, the agent should:

1. Inspect the failure.
2. Determine the likely cause.
3. Modify the implementation.
4. Re-run verification.
5. Stop when successful or when the retry budget is exhausted.

---

## 6. Non-Goals

Version 0.1 will NOT attempt to:

- Fully replace human software engineers.
- Deploy production systems autonomously.
- Push code to remote repositories automatically.
- Access arbitrary credentials.
- Execute unrestricted operating-system commands.
- Modify files outside the configured workspace.
- Autonomously install arbitrary software.
- Guarantee correctness for every possible repository.
- Build a fully autonomous multi-agent system.

Complexity should only be introduced when evaluation demonstrates
that it is necessary.

---

## 7. Engineering Principles

### Principle 1 — Evidence Over Claims

The agent must not claim that code works without verification.

### Principle 2 — Deterministic Systems Over LLM Reasoning

Use deterministic tools for deterministic tasks.

Examples:

- Tests determine whether tests pass.
- Git determines what changed.
- Linters determine formatting problems.
- Type checkers determine type errors.

### Principle 3 — Minimal Context

Provide the model with the smallest context that is sufficient
to solve the current task.

### Principle 4 — Minimal Changes

The agent should modify only files necessary to complete the task.

### Principle 5 — Explicit Tool Boundaries

The LLM should never directly bypass tool validation or security
controls.

### Principle 6 — Repository Content Is Untrusted

Source code, comments, README files, documentation, and external
content must be treated as untrusted data.

### Principle 7 — Measure Before Optimizing

Optimization decisions must be supported by measurements.

### Principle 8 — Prefer Simple Architecture

Do not introduce multi-agent systems, vector databases, complex
frameworks, or additional services unless there is a demonstrated
requirement.

---

## 8. Initial Technology Direction

The initial implementation is expected to use:

- Python
- FastAPI
- Pydantic
- pytest
- Git
- Docker
- PostgreSQL where persistent state is required
- OpenTelemetry for observability

The final technology choices must be validated against current
official documentation before implementation.

---

## 9. Model Provider

The system must use a model-provider abstraction.

Application logic must not be tightly coupled to one model provider.

The model layer should allow the configured provider/model to be
changed without rewriting the agent architecture.

---

## 10. Success Criteria

The project will be considered successful when it can:

1. Accept a software-development task.
2. Inspect a repository.
3. Select relevant context.
4. Produce a useful implementation plan.
5. Modify code through controlled tools.
6. Run verification.
7. Recover from common failures.
8. Produce a final report containing evidence.
9. Record execution metrics.
10. Pass a defined evaluation benchmark.

---

## 11. Quality Requirements

The project should prioritize:

- Correctness
- Reliability
- Security
- Testability
- Observability
- Maintainability
- Context efficiency
- Token efficiency
- Cost awareness
- Reproducibility

---

## 12. Definition of Done

A feature is not complete until:

- The implementation is complete.
- Relevant tests exist.
- Relevant tests pass.
- Error cases are considered.
- The git diff has been inspected.
- Documentation is updated when required.
- Evaluation coverage exists for important behavior.
- No unrelated changes are introduced.

---

## 13. Project Philosophy

This project should be developed as an engineering system rather
than as a prompt demonstration.

The goal is to answer:

"Can an AI agent reliably perform software-engineering work?"

not merely:

"Can an LLM generate code?"

