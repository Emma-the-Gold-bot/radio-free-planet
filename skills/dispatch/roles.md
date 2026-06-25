# Dispatch Role Contracts

**Purpose:** Define what each role does, what it receives, and what it returns.
Referenced by dispatch/SKILL.md. Every dispatch declares exactly one role per sub-agent.

---

## Thinker

**Job:** Decompose the task. Assess risk. Recommend an approach. Do NOT implement.

**Receives:**
- Task description
- Available resources (file paths, data sources, constraints)
- Domain context (project docs if relevant)

**Returns:**
- Decomposed task plan with ordered steps
- Risk assessment (what could go wrong)
- Recommended approach with justification
- Explicit "ready for execution" signal

**Model preference:** Strong reasoning (GLM 5.2 primary, Gemini Flash fallback)

**When to use:**
- Task is ambiguous or open-ended
- Multi-file changes (3+ files)
- Cross-domain work
- High-stakes (production, security, irreversible)
- Task description is > 500 words or underspecified

**When NOT to use:**
- Single file, clear spec, bounded task → go straight to Worker
- Research or design tasks where the panel IS the thinking

---

## Worker

**Job:** Execute a specific task slice. Implement, extract, build. Follow the plan (if one exists).

**Receives:**
- Specific task slice (from Thinker's plan, or direct from dispatch)
- Context from prior steps (per access list, NOT everything)
- Constraints and acceptance criteria

**Returns:**
- Implementation / artifacts / findings
- Validation results (tests run, commands executed, etc.)
- Files changed (for code tasks)
- Clear statement of what was done and what remains

**Model preference:** Varies by task type:
- Code: Kimi K2.6 (implementation), DeepSeek V4 Pro (complex), Qwen 3.7 Plus (alt)
- Research: DeepSeek V4 Pro, MiniMax M3 (large context)
- Design: GLM 5.2 (visual), Kimi K2.6 (UX)

**When to use:**
- Always (every task needs at least one Worker)
- Task is well-defined and bounded
- Following a Thinker's plan

**Access list rule:** Worker receives ONLY what it needs:
- If following a Thinker: Thinker's plan + original task spec
- If revising: original task + failed criteria + what passed
- NEVER: full conversation history, internal reasoning, unrelated context

---

## Judge (Synthesis + Verification)

**Job:** Synthesize outputs from multiple parallel Workers into one definitive result AND verify acceptance criteria. Judge both merges *and* gates.

**Receives:**
- All panel Worker outputs (implementer + tester in complementary pattern, multiple workers in fusion)
- Synthesis prompt (from panels.yaml)
- Original task spec with acceptance criteria

**Returns:**
- Single synthesized output (which files to keep, which to revise)
- Disagreements resolved
- Acceptance criteria check with code evidence (PASS/PARTIAL/FAIL for each)
- Unique insights preserved
- Blind spots flagged
- Final verdict: ACCEPT / REVISE / ESCALATE

**Model preference:** Per models.yaml pipeline config.

**When to use:**
- Always, when more than one worker is dispatched
- Complementary pattern: always (judge merges impl + tests + review)
- Fusion pattern: always (judge merges parallel research findings)

**When NOT to use:**
- Single-worker tasks (no synthesis needed)

---

## Verifier (REMOVED 2026-06-24)

**Status:** Role collapsed into Judge as of 2026-06-24. Judge already checks acceptance criteria against code evidence — separate verifier was redundant cost without demonstrated value. Tester remains as proactive second lens on correctness.

**Historical:** The verifier role was designed for binary code correctness checks (run the build, run the tests, check the spec). In practice, the judge role was already doing this end-of-task, so dispatching a separate verifier was just an extra round-trip.

**If you need independent model diversity on the gate** (e.g. you want a different model reviewing the same work), use complementary pattern with two testers instead of judge + verifier. The diversity comes from two proactive lenses, not a reactive verification.

---

## Role Assignment Quick Reference

| Pipeline | Thinker | Worker(s) | Judge | Notes |
|----------|---------|-----------|-------|-------|
| simple-code | — | 1× MiMo | — | Single worker |
| standard-code | — | 2× Kimi K2.7+MiMo | GLM 5.2 | Fusion (text synthesis) |
| complex-code | GLM 5.2 | 1× Qwen implementer + 1× MiMo tester | GLM 5.2 | Complementary (disjoint files) |
| simple-research | — | 2× MiniMax+DeepSeek | MiMo | Fusion |
| deep-research | GLM 5.2 | 2× MiniMax+DeepSeek | MiMo | Fusion |
| design | — | 2× GLM 5.2+Kimi | Gemini Flash | Fusion |

All assignments configurable in `skills/dispatch/models.yaml`.