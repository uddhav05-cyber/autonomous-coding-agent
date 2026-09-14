# Autonomous Coding Agent

**Current Phase: Phase 2 - WORKSPACE ABSTRACTION AND FILE OPERATIONS**

## Project Vision

Build an AI software-engineering agent capable of taking a software-development task and autonomously working on an existing code repository inside a controlled workspace.

## Phase 2 Objective

Create a secure, testable workspace abstraction layer that provides controlled file system operations within a bounded directory, preventing workspace escapes and ensuring safe file operations for the autonomous coding agent.

## Development Setup

### Prerequisites
- Python 3.11+
- Git
- Docker (optional, for containerized development)

### Local Development

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -e ".[dev]"
   ```
3. Use `.env.example` as a reference and export the needed
   `AUTONOMOUS_AGENT_*` variables in the process environment
4. Run tests:
   ```bash
   pytest tests/
   ```

### Docker Development

1. Build the Docker image:
   ```bash
   docker build -t autonomous-agent .
   ```
2. Run tests in container:
   ```bash
   docker run --rm autonomous-agent
   ```

## Configuration

Configuration is managed through Pydantic settings and can be customized via:
- Environment variables (prefixed with `AUTONOMOUS_AGENT_`)
- Programmatic overrides

See `src/autonomous_agent/config/settings.py` for available configuration options.
The current settings loader reads the process environment directly; it does not
load `.env` files automatically.

## Phase 2 Security Boundary

Workspace operations accept relative paths and absolute paths that resolve
inside the configured root. Traversal paths, symlink or junction escapes, and
workspace-root deletion are rejected. Writes use a temporary file in the
destination directory followed by `os.replace()` to avoid partially written
files.

This is an application-level boundary, not an OS sandbox. Protection against
concurrent symlink replacement, shell commands, network access, secrets, and
file permissions is deferred to later security and tool-policy phases.

## Project Structure

```
autonomous-coding-agent/
├── src/                          # Source code
│   └── autonomous_agent/         # Main package
│   ├── __init__.py
│   │   │   ├── config/           # Configuration
│   │   │   │   ├── __init__.py
│   │   │   │   └── settings.py   # Pydantic settings
│   │   │   ├── errors/           # Error handling
│   │   │   │   ├── __init__.py
│   │   │   │   └── base.py       # Base error classes
│   │   │   ├── logging/          # Logging setup
│   │   │   │   ├── __init__.py
│   │   │   │   └── setup.py      # Logging configuration
│   │   │   ├── models/           # Data models
│   │   │   │   └── __init__.py
│   │   │   └── workspace/        # Workspace abstraction and file operations
│   │   │       ├── __init__.py   # Workspace package exports
│   │   │       ├── backend.py    # Filesystem backend abstraction
│   │   │       ├── errors.py     # Workspace-specific error hierarchy
│   │   │       └── manager.py    # Workspace manager interface
│   │   └── ...
├── tests/                        # Test suites
│   ├── unit/                     # Unit tests
│   │   └── workspace/            # Workspace unit tests
│   │       ├── test_backend.py   # Backend tests
│   │       └── test_manager.py   # Manager tests
│   └── integration/              # Integration tests
│       └── workspace/            # Workspace integration tests
│           └── test_workspace.py # Workspace integration tests
├── .env.example                  # Environment variables template
├── .gitignore                    # Git ignore rules
├── Dockerfile                    # Docker development environment
├── pyproject.toml                # Project configuration and dependencies
└── README.md                     # This file
```

## Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing

# Run linting
python -m ruff check src tests

# Type checking is not configured in Phase 2.

# Run specific test suite
pytest tests/unit/
pytest tests/integration/

# Run workspace tests specifically
pytest tests/unit/workspace/
pytest tests/integration/workspace/
```

## Docker Usage

```bash
# Build image
docker build -t autonomous-agent .

# Run tests
docker run --rm autonomous-agent

# Interactive development
docker run -it --rm -v $(pwd):/app autonomous-agent bash
```

## Completed Phases

- ✅ Phase 1: Project Foundation
- ✅ Phase 2: Workspace abstraction and file operations

## Next Phases

After Phase 2 completion, subsequent phases will implement:

- Phase 3: Repository understanding and code search
- Phase 4: Context management and selection
- Phase 5: Model adapter and provider abstraction
- Phase 6: Tool system with validation and permissions
- Phase 7: Agent orchestrator and execution loop
- Phase 8: Verification systems (test, lint, type checking)
- Phase 9: Recovery mechanisms and retry handling
- Phase 10: Evaluation framework and benchmarking
- Phase 11: Security controls and protections
- Phase 12: Observability and metrics collection
- Phase 13: Optimization based on measurements
- Phase 14: Developer interface (CLI/API)
- Phase 15: Final benchmark and validation

## License

This project is proprietary and confidential.