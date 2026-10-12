# Autonomous Coding Agent

## Project Status

The repository now includes implementations beyond the original Phase 2
workspace milestone, including repository understanding, context engineering,
model adapter, tool, and orchestrator modules.

## What works now

- Workspace abstraction with path confinement and atomic writes
- Repository understanding components (discovery, metadata, search, relevance)
- Context engineering components (selection, budgeting, assembly)
- Model adapter abstractions and provider layer
- Tool interfaces/registry/policy/execution scaffolding
- Agent orchestrator loop structure and tests

## Quick Start

### Prerequisites

- Python 3.11+
- Git
- Docker (optional)

### Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Use `.env.example` as a reference and export required
`AUTONOMOUS_AGENT_*` variables in your shell environment.

### Development commands

```bash
# run all tests
pytest tests/

# run unit/integration suites
pytest tests/unit/
pytest tests/integration/

# run coverage
pytest tests/ --cov=src --cov-report=term-missing

# lint
python -m ruff check src tests
```

### Docker commands

```bash
docker build -t autonomous-agent .
docker run --rm autonomous-agent
```

## How to run the agent

`pyproject.toml` declares the `autonomous-agent` CLI entrypoint, but the
`autonomous_agent.__main__` module is not present yet, so the executable entry
command is not runnable in this revision.

## Configuration

Configuration is managed through Pydantic settings via:

- Environment variables (`AUTONOMOUS_AGENT_*`)
- Programmatic overrides

See `src/autonomous_agent/config/settings.py` for available options.
The settings loader reads process environment variables directly and does not
auto-load `.env` files.

## Security boundary (current)

Workspace operations accept relative paths and absolute paths that resolve
inside the configured root. Traversal paths, symlink or junction escapes, and
workspace-root deletion are rejected. Writes use temporary-file + `os.replace()`
for atomic replacement.

This is an application-level boundary, not an OS sandbox. Protection against
concurrent symlink replacement, shell commands, unrestricted network access,
and secret exfiltration is deferred to later security/tool-policy phases.

## Project structure

```
autonomous-coding-agent/
├── src/autonomous_agent/
│   ├── workspace/
│   ├── repository_understanding/
│   ├── context_engineering/
│   ├── model_adapter/
│   ├── tool/
│   ├── agentorchestrator/
│   ├── config/
│   ├── agent_logging/
│   └── errors/
├── tests/
│   ├── unit/
│   └── integration/
├── research/
├── docs/
├── PROJECT.md
├── ARCHITECTURE.md
├── DECISIONS.md
└── pyproject.toml
```

## Implemented today

- ✅ Project foundation and base configuration
- ✅ Workspace abstraction and file operations
- ✅ Repository understanding modules
- ✅ Context engineering modules
- ✅ Model adapter modules
- ✅ Tool system scaffolding
- ✅ Agent orchestrator scaffolding

## Roadmap

- Phase 8: Verification systems (test, lint, type checking)
- Phase 9: Recovery mechanisms and retry handling
- Phase 10: Evaluation framework and benchmarking
- Phase 11: Security controls and protections
- Phase 12: Observability and metrics collection
- Phase 13: Optimization based on measurements
- Phase 14: Developer interface (CLI/API)
- Phase 15: Final benchmark and validation

## Contributing

- Keep changes minimal and scoped to the task.
- Add/update tests when behavior changes.
- Run `pytest tests/` and `python -m ruff check src tests` before submitting.
- Avoid unrelated refactors in feature/fix PRs.

## License

This project is proprietary and confidential.