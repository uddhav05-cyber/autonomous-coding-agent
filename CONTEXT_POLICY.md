 # Context Policy

## Objective

Provide the model with enough information to solve the task while
minimizing unnecessary context.

---

# 1. Context Priority

Use information in this order:

1. Current task
2. Project rules
3. Relevant architecture
4. Relevant source files
5. Relevant tests
6. Relevant research
7. Broader repository context

---

# 2. Repository Discovery

Start with:

- Repository tree
- Project configuration
- Entry points
- Relevant directories

Do not automatically read every source file.

---

# 3. Search Before Reading

Prefer targeted search to broad file loading.

Example:

Task:

"Fix token refresh."

First locate:

- token refresh symbols
- authentication module
- relevant tests
- configuration

Only then read the relevant implementation.

---

# 4. Context Expansion

Expand context when:

- Relevant dependencies are unclear.
- Tests reveal unexpected behavior.
- Multiple implementations exist.
- The current context is insufficient.
- Architecture requires broader understanding.

---

# 5. Context Reduction

Remove or avoid:

- Duplicate content
- Irrelevant files
- Generated files
- Binary files
- Large logs
- Unrelated documentation

---

# 6. Context Budget

Every model invocation should ideally track:

- Input tokens
- Output tokens
- Number of files included
- Approximate context size
- Model
- Latency

---

# 7. Context Reuse

Reuse previously obtained information when it remains valid.

Do not repeatedly reload identical files without a reason.

---

# 8. Reliability Rule

Never reduce context solely to save tokens if doing so causes
meaningful reliability degradation.

Optimization must be evaluated using benchmark results.

