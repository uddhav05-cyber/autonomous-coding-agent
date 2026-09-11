# Dockerfile for Autonomous Coding Agent - Phase 1 Development
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"

# Copy source code
COPY src/ ./src/
COPY tests/ ./tests/

# Copy configuration files
COPY .env.example .

# Create workspace directory
RUN mkdir -p ./workspace

# Set environment variables
ENV AUTONOMOUS_AGENT_ENVIRONMENT=development
ENV AUTONOMOUS_AGENT_LOG_LEVEL=INFO
ENV AUTONOMOUS_AGENT_WORKSPACE_PATH=/app/workspace

# Run tests to verify installation
CMD ["pytest", "tests/", "-v"]