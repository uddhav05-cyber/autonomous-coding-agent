# Autonomous Coding Agent

**Current Phase: Phase 1 - PROJECT FOUNDATION**

## Project Vision

Build an AI software-engineering agent capable of taking a software-development task and autonomously working on an existing code repository inside a controlled workspace.

## Phase 1 Objective

Create a clean, testable Python project foundation that can support the architecture defined in ARCHITECTURE.md.

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
3. Copy environment example:
   ```bash
   cp .env.example .env
   ```
4. Edit `.env` with your configuration
5. Run tests:
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
- `.env` file
- Programmatic overrides

See `src/autonomous_agent/config/settings.py` for available configuration options.

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
│   │   │   └── models/           # Data models
│   │   │       └── __init__.py
│   │   └── ...
├── tests/                        # Test suites
│   ├── unit/                     # Unit tests
│   └── integration/              # Integration tests
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
pytest tests/ --cov=src

# Run specific test suite
pytest tests/unit/
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

## Next Phases

After Phase 1 completion, subsequent phases will implement:

- Phase 2: Workspace abstraction and file operations
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