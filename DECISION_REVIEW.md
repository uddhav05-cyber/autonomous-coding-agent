# Decision Review: Specific Decisions Requiring Changes

This document focuses on specific architectural decisions that require modification based on the Phase 0 research findings.

## Summary of Decisions Requiring Changes

After reviewing all original architectural assumptions and decisions against the comprehensive research conducted in Phase 0, only **one decision requires modification**:

1. **Code Editing Strategy** - Modify to prefer patch editing over whole-file replacement for most operations

All other original architectural decisions (ADR-001 through ADR-005) are confirmed by research and should proceed as originally specified.

## Detailed Analysis of Decisions Requiring Changes

### Decision: Code Editing Strategy

**Original Specification (PROJECT.md, Section 5 - Core Capabilities):**
> The agent should be able to:
> 
> - Read files.
> - Search code.
> - Create files.
> - Modify files.
> - Apply targeted patches.
> - Inspect resulting changes.

**Research Findings (05-code-editing.md):**
The research provides a detailed comparison of whole-file replacement versus patch editing:

**Whole-file Replacement Advantages:**
- Simplicity: Single operation replaces entire file content
- Consistency: No risk of leaving file in partially modified state
- Conflict avoidance: Eliminates concerns about conflicting edits to same file
- Complete control: Guarantees exact final state as specified
- External tool compatibility: Works with formatters, linters, and other processing tools

**Whole-file Replacement Disadvantages:**
- Context loss: Discards unrelated but potentially valuable content (comments, formatting)
- Inefficiency: Transmits and processes entire file for small changes
- Change obscurity: Makes it difficult to see what actually changed
- Collaboration issues: Overwrites others' concurrent changes without merging
- History pollution: Creates large diffs that obscure intent in version control
- Risk amplification: Errors affect entire file rather than localized area

**Patch Editing Advantages:**
- Precision: Changes only what needs to be changed
- Efficiency: Minimal data transfer and processing
- Transparency: Clear visibility of exact modifications made
- Collaboration friendly: Compatible with concurrent editing and merging
- History preservation: Creates meaningful, interpretable diffs
- Context retention: Preserves unrelated content, comments, formatting
- Risk localization: Errors affect only modified regions
- Incremental building: Supports stepwise construction of complex changes

**Patch Editing Disadvantages:**
- Complexity: Requires precise location and formatting of changes
- Conflict potential: Concurrent edits to same regions require merging
- State dependence: Success depends on file being in expected state
- Formatting challenges: Maintaining consistent style across patches
- Boundary errors: Risk of modifying wrong lines or sections
- Validation complexity: Harder to verify overall correctness incrementally

**Research Recommendation:**
> Prefer patch editing for most agent operations due to:
> - Better preservation of human-written context (comments, formatting)
> - Improved collaboration compatibility
> - Clearer audit trails and change visibility
> - Reduced risk of unintended side effects
> - Greater efficiency for typical small-to-moderate changes
> 
> Reserve whole-file replacement for:
> - Specific cases like formatters/linters
> - When external tool compatibility is needed

**Final Recommendation:**
Modify the code editing strategy to explicitly prefer patch editing (using unified diff format or similar) for most code modification operations, reserving whole-file replacement only for specific cases like formatters, linters, or when external tool compatibility is required.

**Justification:**
The research clearly demonstrates that patch editing provides significant advantages for AI coding agent operations:
1. Better context preservation maintains valuable comments and formatting that might be relevant to the task
2. Improved collaboration compatibility prevents overwriting concurrent changes by humans or other agents
3. Clearer audit trails enable better traceability of what the agent actually changed
4. Reduced risk of unintended side effects minimizes the chance of breaking unrelated code
5. Greater efficiency for typical small-to-moderate changes reduces token usage and processing time

**Implementation Approach:**
1. Implement a patch-based code editor that generates unified diffs for modifications
2. Include validation to ensure patches apply cleanly
3. Provide fallback to whole-file replacement only when specifically needed for:
   - Integration with code formatters (prettier, black, etc.)
   - Integration with linters that require full file processing
   - External tool compatibility requirements
4. Implement conflict detection and resolution mechanisms for patch editing
5. Add audit trail capabilities that clearly show what was modified

**Sources:**
- 05-code-editing.md (lines 25-80): Comprehensive comparison of whole-file replacement vs patch editing
- 05-code-editing.md (lines 80-100): Specific recommendation to prefer patch editing for most operations

## Decisions Confirmed (No Changes Required)

All other original architectural decisions are confirmed by research and should proceed as originally specified:

### ADR-001 — Start With a Single Agent Orchestrator
- **Status**: CONFIRMED
- **Research Validation**: Multi-agent architecture introduces additional complexity (model calls, context transfers, coordination failures, state management, debugging complexity, cost) with no demonstrated benefit for V1
- **Sources**: 01-coding-agent-architecture.md (execution loop patterns), 07-agent-evaluation.md (complexity considerations)

### ADR-002 — Deterministic Verification
- **Status**: CONFIRMED
- **Research Validation**: LLM reasoning is not sufficient evidence that generated code works; deterministic verification mechanisms (tests, linters, type checkers, git state) are essential
- **Sources**: 06-verification.md (comprehensive validation strategies), SECURITY.md (verification as security control)

### ADR-003 — Controlled Tools
- **Status**: CONFIRMED
- **Research Validation**: Tool mediation enables validation, permissions, logging, timeouts, testing, and security controls
- **Sources**: 04-tool-use.md (comprehensive tool use research), SECURITY.md (tool-based security controls)

### ADR-004 — Context Must Be Selective
- **Status**: CONFIRMED
- **Research Validation**: Selective context improves cost, latency, model focus, scalability, and makes context behavior measurable
- **Sources**: 03-context-engineering.md (context selection principles), 10-cost-optimization.md (context reduction techniques)

### ADR-005 — Measure Before Optimizing
- **Status**: CONFIRMED
- **Research Validation**: Premature optimization can reduce reliability while providing little actual benefit
- **Sources**: 10-cost-optimization.md (measurement-based optimization approaches), PROJECT.md (Principle 7)

## Recommended New Decisions to Add

Based on the research, two new architectural decisions should be formally added:

### Proposed ADR-006 — Prefer Patch Editing for Code Modifications
- **Status**: Proposed
- **Decision**: The agent should prefer patch-based editing (unified diff format or similar) for most code modification operations, reserving whole-file replacement for specific cases like formatters, linters, or when external tool compatibility is required.
- **Reason**: Research shows patch editing provides better context preservation, collaboration compatibility, clearer audit trails, reduced side effects, and efficiency for typical small-to-moderate changes.
- **Sources**: 05-code-editing.md (lines 25-80)

### Proposed ADR-007 — Implement Context Importance Scoring
- **Status**: Proposed
- **Decision**: The Context Manager should implement an importance scoring mechanism to rank context elements by expected utility when building context within token limits.
- **Reason**: Research shows importance scoring enables effective context allocation decisions that maximize task relevance while minimizing token usage.
- **Sources**: 03-context-engineering.md (line 52 - importance scoring), 10-cost-optimization.md (line 54 - importance scoring)

## Impact Assessment

### Positive Impacts of the Change:
1. **Improved Context Preservation**: Better maintenance of comments and formatting that may be relevant to understanding code
2. **Enhanced Collaboration**: Reduced risk of overwriting concurrent changes by humans or other tools
3. **Clearer Audit Trails**: More visible and understandable change history
4. **Reduced Side Effects**: Lower probability of inadvertently breaking unrelated code
5. **Greater Efficiency**: Less data transfer and processing for typical small-to-moderate changes

### Mitigation Strategies for Potential Drawbacks:
1. **Increased Complexity**: Implement robust patch validation and application mechanisms
2. **Merge Conflicts**: Implement conflict detection and resolution strategies
3. **State Dependence**: Implement file state verification before patch application
4. **Validation Complexity**: Implement incremental verification approaches alongside patch editing

## Conclusion

Only one architectural decision requires modification based on the Phase 0 research: the code editing strategy should be updated to prefer patch editing over whole-file replacement for most operations. All other original architectural decisions are validated by research and should proceed as specified. Additionally, two new decisions should be added to formalize research-backed improvements: preferring patch editing for code modifications and implementing context importance scoring.

These changes align with the research findings while maintaining the core architectural vision of a simple, measurable, reliable coding agent whose behavior can be evaluated and improved systematically.

ADR-006 — Prefer Patch Editing
ADR-007 — Context Importance Scoring
ADR-008 — Start With Minimal Dependencies
