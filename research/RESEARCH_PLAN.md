# Research Plan

## Purpose

This document defines what must be researched before architectural
and implementation decisions are finalized.

Research must prioritize primary sources.

---

# 1. Research Source Hierarchy

Use sources in this order:

1. Official documentation
2. Official engineering blogs
3. Official specifications
4. Academic papers
5. High-quality technical publications
6. Open-source implementations
7. Community discussions

Community sources may be useful for discovering problems but should
not automatically be treated as architectural authority.

---

# 2. Coding Agent Architecture

## Questions

Research:

- What constitutes an AI coding agent?
- What are common agent execution loops?
- How are planning and execution separated?
- How is state represented?
- How do coding agents terminate?
- How are retries handled?
- How are failures represented?
- When is human approval required?

## Deliverable

Create:

research/01-coding-agent-architecture.md

---

# 3. Repository Understanding

## Questions

Research:

- How should an agent discover a repository?
- How should relevant files be identified?
- How can code search reduce context usage?
- How should symbols and dependencies be identified?
- How should large files be handled?
- How should generated files be detected?
- How should binary files be handled?

## Deliverable

research/02-repository-understanding.md

---

# 4. Context Engineering

## Questions

Research:

- How should context be selected?
- How can unnecessary context be avoided?
- How should context budgets work?
- How should long files be summarized?
- When should the agent expand context?
- How should previous tool results be reused?
- How should duplicate context be avoided?

## Deliverable

research/03-context-engineering.md

---

# 5. Tool Use

## Questions

Research:

- How should tools be represented?
- How should tool schemas be validated?
- How should tool errors be returned?
- How should tool timeouts work?
- How should tool permissions work?
- How should retries work?
- How should destructive operations be handled?

## Deliverable

research/04-tool-use.md

---

# 6. Code Editing

## Questions

Research:

- Whole-file replacement vs patch editing?
- How should edits be validated?
- How should syntax errors be detected?
- How should conflicting edits be handled?
- How should the agent inspect its own diff?

## Deliverable

research/05-code-editing.md

---

# 7. Verification

## Questions

Research:

- Test execution strategies
- Linting
- Type checking
- Static analysis
- Git diff analysis
- Regression testing
- Verification after repair

## Deliverable

research/06-verification.md

---

# 8. Agent Evaluation

## Questions

Research:

- Task completion
- Test success
- Tool selection
- Tool argument correctness
- Recovery
- Safety
- Unnecessary changes
- Latency
- Token usage
- Cost
- Regression evaluation

## Deliverable

research/07-agent-evaluation.md

---

# 9. Security

## Questions

Research:

- Prompt injection
- Repository-based prompt injection
- Command injection
- Path traversal
- Secret exposure
- Malicious dependencies
- Dangerous shell commands
- Sandbox boundaries
- Permission systems

## Deliverable

research/08-agent-security.md

---

# 10. Observability

## Questions

Research:

- Distributed tracing
- Agent execution traces
- Tool spans
- Model calls
- Token metrics
- Latency
- Errors
- Cost tracking

## Deliverable

research/09-observability.md

---

# 11. Cost and Token Optimization

## Questions

Research:

- Context reduction
- Model selection
- Caching
- Tool-result compression
- Retry budgets
- Context reuse
- Model escalation
- Token measurement

## Deliverable

research/10-cost-optimization.md

---

# 12. Research Rules

Do not:

- Choose technology because it is popular.
- Add libraries without a reason.
- Copy another agent's architecture blindly.
- Treat benchmarks as proof of production reliability.
- Treat a successful demo as evaluation.

Every major architectural decision must have evidence.
