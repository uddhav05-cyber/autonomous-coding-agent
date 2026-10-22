```markdown
# Autonomous Coding Agent

A research-driven autonomous coding agent for understanding repositories, selecting relevant context, using controlled tools, and executing software-engineering tasks through a structured agent workflow.

The project is designed to evolve into a reliable coding agent capable of:

- Understanding unfamiliar repositories
- Selecting relevant code and documentation
- Planning implementation tasks
- Editing files through controlled tools
- Running verification commands
- Diagnosing failures
- Recovering from unsuccessful attempts
- Measuring performance, cost, safety, and reliability

> **Current status:** Core architecture implemented through the Agent Orchestrator stage. Verification, recovery, benchmarking, security hardening, and developer interfaces are the next major milestones.

---

## Project Status

The project has progressed beyond the initial workspace milestone and currently includes implementations or scaffolding for the first major stages of the system.

### Implemented

- Project foundation and configuration
- Workspace abstraction and secure file operations
- Repository discovery and metadata handling
- Repository search and relevance scoring
- Context selection and token budgeting
- Context assembly
- Model adapter abstractions
- Provider-layer structure
- Tool interfaces and tool registry
- Tool policy and execution scaffolding
- Agent orchestrator loop structure
- Unit and integration tests for implemented components

### In Progress / Planned

- Verification systems
- Failure diagnosis and recovery
- Evaluation and benchmarking
- Security hardening
- Observability and metrics
- Performance and cost optimization
- CLI/API developer interface
- End-to-end autonomous coding workflows

---

## Architecture

The agent is organized as a sequence of controlled stages:

```text
User Task
   ↓
Repository Discovery
   ↓
Repository Understanding
   ↓
Context Selection
   ↓
Context Assembly
   ↓
Planning
   ↓
Tool Execution
   ↓
Code Modification
   ↓
Verification
   ↓
Failure Diagnosis
   ↓
Recovery and Retry
   ↓
Final Review
   ↓
Result Report
```

The current implementation provides the foundation for the stages through tool execution and orchestration. Verification and recovery systems are planned as the next major development stages.

---

## Core Components

### Workspace

Provides controlled filesystem access within a configured workspace.

Current capabilities include:

- Relative path handling
- Absolute path resolution inside the workspace
- Path traversal protection
- Symlink and junction escape detection
- Workspace-root deletion protection
- Atomic file replacement using temporary files and `os.replace()`

### Repository Understanding

Provides the foundation for analyzing an existing codebase.

Planned and implemented responsibilities include:

- Repository discovery
- File and directory metadata
- Search capabilities
- Relevance scoring
- Repository structure analysis

### Context Engineering

Controls the information provided to the model.

The context layer is designed to support:

- Relevant file selection
- Context prioritization
- Token budgeting
- Context assembly
- Reduced unnecessary model input
- Reproducible context decisions

### Model Adapter

Provides an abstraction between the agent and model providers.

This allows the rest of the system to remain independent from a specific model vendor or API implementation.

### Tool System

Provides the foundation for controlled agent actions.

The tool layer includes structures for:

- Tool interfaces
- Tool registration
- Tool policy
- Tool validation
- Tool execution
- Permission-aware operations

### Agent Orchestrator

Coordinates the agent workflow and provides the structure for:

- Task execution
- Planning
- Model interaction
- Tool calls
- State management
- Execution results
- Future verification and recovery loops

---

## Project Roadmap

The project is being developed in phases:

- ✅ Phase 1 — Project foundation
- ✅ Phase 2 — Workspace abstraction and file operations
- ✅ Phase 3 — Repository understanding
- ✅ Phase 4 — Context engineering
- ✅ Phase 5 — Model adapter and provider abstraction
- ✅ Phase 6 — Tool system foundation
- ✅ Phase 7 — Agent orchestrator foundation
- ⏳ Phase 8 — Verification systems
- ⏳ Phase 9 — Recovery mechanisms and retry handling
- ⏳ Phase 10 — Evaluation framework and benchmarking
- ⏳ Phase 11 — Security controls and protections
- ⏳ Phase 12 — Observability and metrics
- ⏳ Phase 13 — Performance and cost optimization
- ⏳ Phase 14 — Developer interface through CLI/API
- ⏳ Phase 15 — Final benchmark and validation

> The completed phases include working implementations and scaffolding. Some components are intentionally incomplete until the verification, recovery, and evaluation layers are added.

---

## Project Structure

```text
autonomous-coding-agent/
├── src/
│   └── autonomous_agent/
│       ├── workspace/
│       │   ├── backend.py
│       │   ├── errors.py
│       │   └── manager.py
│       ├── repository_understanding/
│       ├── context_engineering/
│       ├── model_adapter/
│       ├── tool/
│       ├── agentorchestrator/
│       ├── config/
│       ├── agent_logging/
│       └── errors/
├── tests/
│   ├── unit/
│   └── integration/
├── docs/
├── research/
├── .env.example
├── AGENTS.md
├── ARCHITECTURE.md
├── ARCHITECTURE_REVIEW.md
├── CONTEXT_POLICY.md
├── DECISIONS.md
├── DECISION_REVIEW.md
├── EVALUATION.md
├── IMPLEMENTATION_PLAN.md
├── PHASE_2_WORKSPACE_SPECIFICATION.md
├── PROJECT.md
├── SECURITY.md
├── Dockerfile
├── pyproject.toml
└── README.md
```

---

## Requirements

- Python 3.11 or newer
- Git
- Docker — optional

---

## Installation

Clone the repository:

```bash
git clone https://github.com/uddhav05-cyber/autonomous-coding-agent.git
cd autonomous-coding-agent
```

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows:

```powershell
.venv\Scripts\activate
```

Install the project and development dependencies:

```bash
pip install -e ".[dev]"
```

---

## Configuration

Use `.env.example` as a reference for available settings.

Configuration values use the following environment-variable prefix:

```text
AUTONOMOUS_AGENT_
```

Example:

```bash
export AUTONOMOUS_AGENT_<SETTING_NAME>=<VALUE>
```

Configuration is managed through the settings module:

```text
src/autonomous_agent/config/settings.py
```

The current settings loader reads values from process environment variables. `.env` files are not loaded automatically unless explicitly supported by the application configuration.

---

## Running Tests

Run the complete test suite:

```bash
pytest tests/
```

Run unit tests:

```bash
pytest tests/unit/
```

Run integration tests:

```bash
pytest tests/integration/
```

Run tests with coverage:

```bash
pytest tests/ --cov=src --cov-report=term-missing
```

---

## Code Quality

Run Ruff:

```bash
python -m ruff check src tests
```

Before submitting changes:

```bash
pytest tests/
python -m ruff check src tests
```

---

## Docker

Build the Docker image:

```bash
docker build -t autonomous-agent .
```

Run the test suite inside Docker:

```bash
docker run --rm autonomous-agent
```

Start an interactive development container:

```bash
docker run -it --rm -v "$(pwd):/app" autonomous-agent bash
```

---

## CLI Status

The project declares an `autonomous-agent` CLI entry point in `pyproject.toml`.

The command-line interface is still under development, and the executable entry module is not yet available in the current revision. The CLI/API developer interface is planned for Phase 14.

---

## Security Boundary

The workspace layer provides an application-level filesystem boundary.

It currently protects against:

- Path traversal outside the configured workspace
- Symlink and junction escapes
- Deletion of the workspace root
- Partially written files during normal atomic-write operations

This is **not an operating-system sandbox**.

The current implementation does not yet provide complete protection against:

- Concurrent symlink replacement attacks
- Arbitrary shell commands
- Unrestricted network access
- Secret exposure or exfiltration
- Malicious dependencies
- Unsafe repository instructions
- Host-level container escapes

Additional security controls will be introduced in later phases.

---

## Design Principles

The project follows these principles:

### Controlled execution

Agent actions should be performed through validated and permission-aware tools.

### Minimal sufficient context

The model should receive only the repository information required for the current task.

### Deterministic verification

Changes should be validated through tests, linters, type checkers, syntax checks, and repository state.

### Measurable behavior

The system should measure task success, verification results, tool accuracy, recovery rate, unnecessary changes, token usage, cost, latency, and safety violations.

### Modular architecture

Models, tools, repository analysis, context management, verification, and orchestration should remain independently replaceable and testable.

### Security by design

Workspace access, command execution, dependencies, secrets, network access, and repository instructions should be treated as explicit security boundaries.

---

## Research and Documentation

Important project documents include:

- [`PROJECT.md`](PROJECT.md) — project scope and objectives
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — system architecture
- [`ARCHITECTURE_REVIEW.md`](ARCHITECTURE_REVIEW.md) — architecture review
- [`CONTEXT_POLICY.md`](CONTEXT_POLICY.md) — context selection policy
- [`DECISIONS.md`](DECISIONS.md) — architecture decisions
- [`DECISION_REVIEW.md`](DECISION_REVIEW.md) — decision review
- [`EVALUATION.md`](EVALUATION.md) — evaluation and benchmarking strategy
- [`SECURITY.md`](SECURITY.md) — security model
- [`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md) — development plan
- [`PHASE_2_WORKSPACE_SPECIFICATION.md`](PHASE_2_WORKSPACE_SPECIFICATION.md) — workspace specification
- [`research/`](research/) — supporting research material

---

## Contributing

When contributing:

1. Keep changes focused and scoped to the task.
2. Add or update tests when behavior changes.
3. Run the test suite before submitting changes.
4. Run Ruff before submitting changes.
5. Avoid unrelated refactoring.
6. Update the relevant documentation when architecture or behavior changes.

---

## Current Limitations

The project is not yet a fully autonomous production coding agent.

The following capabilities are still being developed:

- Complete end-to-end model execution
- Reliable verification loops
- Automatic failure recovery
- Benchmarking against coding tasks
- Production-grade sandboxing
- Full CLI/API access
- Comprehensive observability
- Cost and latency optimization

---

## License

This project is currently proprietary and confidential.

See the repository licensing information before using, modifying, or distributing the code.
```

The main correction is this section:

```text
✅ Phase 1 — Project foundation
✅ Phase 2 — Workspace abstraction
✅ Phase 3 — Repository understanding
✅ Phase 4 — Context engineering
✅ Phase 5 — Model adapter
✅ Phase 6 — Tool system foundation
✅ Phase 7 — Agent orchestrator foundation
⏳ Phase 8 — Verification systems
```

That matches the current repository contents and the roadmap shown in your GitHub project. The README also correctly notes that the CLI entry point is declared but not yet runnable in the current revision. ([github.com](https://github.com/uddhav05-cyber/autonomous-coding-agent))

### Sources

- Current repository README, directory structure, implemented modules, roadmap, and CLI status: ([github.com](https://github.com/uddhav05-cyber/autonomous-coding-agent))
