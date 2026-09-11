You are working on the Autonomous Coding Agent project.

IMPORTANT:
Do NOT implement application code.
Do NOT modify src/.
Do NOT modify tests/.
Do NOT modify evals/.
Do NOT change the architecture yet.

First read:

PROJECT.md
AGENTS.md
research\RESEARCH_PLAN.md
research\SOURCES.md
ARCHITECTURE.md
DECISIONS.md
CONTEXT_POLICY.md
SECURITY.md
EVALUATION.md
IMPLEMENTATION_PLAN.md

We are currently in PHASE 0: RESEARCH.

Your job is to perform rigorous technical research for the
Autonomous Coding Agent.

Research these topics in order:

1. Coding-agent architecture
2. Repository understanding
3. Context engineering
4. Tool use
5. Code editing
6. Verification
7. Agent evaluation
8. Security
9. Observability
10. Token and cost optimization

RESEARCH RULES:

1. Prefer official documentation and primary sources.
2. Use official engineering blogs where appropriate.
3. Use academic papers when relevant.
4. Use open-source repositories to understand implementation
   patterns, but do not assume their architecture is correct.
5. Do not rely on random tutorials when primary documentation
   exists.
6. Never invent APIs, benchmarks, or technical claims.
7. Record the source for every important technical claim.
8. Clearly distinguish facts from your own recommendations.
9. Do not choose a technology merely because it is popular.

For each research topic create a Markdown file under:

research/

Use this naming scheme:

research\01-coding-agent-architecture.md
research\02-repository-understanding.md
research\03-context-engineering.md
research\04-tool-use.md
research\05-code-editing.md
research\06-verification.md
research\07-agent-evaluation.md
research\08-agent-security.md
research\09-observability.md
research\10-cost-optimization.md

Each research document should contain:

# Topic

## Research Questions

## Key Findings

## Important Concepts

## Design Implications

## Alternatives Considered

## Risks / Limitations

## Recommendations for This Project

## Sources

For every source include:

- Title
- Organization / Author
- URL
- Date accessed
- What the source tells us
- Which project decision it influences

IMPORTANT:

Do not blindly recommend frameworks.

For example, do not say:

"Use framework X because it is popular."

Instead answer:

"What problem does framework X solve?
Do we actually have that problem?
What is the cost of introducing it?
Could we implement the required behavior ourselves?"

Also compare important architectural alternatives.

Examples:

- Single-agent loop vs multi-agent system
- ReAct-style loop vs structured tool loop
- Whole-file editing vs patch-based editing
- Full-repository context vs selective retrieval
- Static context vs dynamic context
- Retry-based recovery vs explicit failure diagnosis
- Local execution vs sandboxed execution

After completing the research files:

1. Update research\SOURCES.md with the most important sources.
2. Do NOT rewrite ARCHITECTURE.md yet.
3. Do NOT rewrite DECISIONS.md yet.
4. Do NOT implement code.

At the end, provide a concise research summary containing:

- 10 most important findings
- 5 architectural decisions that may need reconsideration
- 5 major risks
- 5 areas where further research is needed

STOP after the research phase.
