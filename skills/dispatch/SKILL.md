# Dispatch Skill

**Purpose:** Enforce dispatch patterns for all sub-agent tasks. This skill is read
at dispatch time — every time the agent is about to call `sessions_spawn`.

**Supporting files:**
- `skills/dispatch/roles.md` — role contracts (Thinker/Worker/Tester/Judge)
- `skills/dispatch/models.yaml` — model assignments and pipeline compositions

---

## MANDATORY RULES

1. **Read `roles.md` before dispatching.** Know what each role does.
2. **Read `models.yaml` before dispatching.** Know which models to use.
3. **Declare a role for every sub-agent.** No unnamed dispatches.
4. **Assess difficulty before choosing a pipeline.** Not every task needs full fusion.
5. **Judge subsumes verification.** When multiple workers are dispatched, the Judge checks acceptance criteria — no separate Verifier dispatch. Tester is the proactive second lens on correctness.
6. **Use access lists.** Each sub-agent gets only the context it needs.

---

## Dispatch Flow

### Step 0: Read Supporting Files

Before doing anything else, read:
- `skills/dispatch/roles.md`
- `skills/dispatch/models.yaml`

If either is missing, use hardcoded defaults from this file.

### Step 1: Assess Difficulty

Before classifying task type, assess difficulty:

| Signal | Simple | Complex |
|--------|--------|---------|
| File count | 1-2 files | 3+ files |
| Spec clarity | Clear, unambiguous | Ambiguous, open-ended |
| Task length | < 200 words | > 500 words |
| Domain | Single domain | Cross-domain |
| Stakes | Internal tool, low risk | Production, high risk, irreversible |
| Prior work | None needed | Depends on existing codebase patterns |

**Simple** = 3+ signals in "Simple" column.
**Complex** = 3+ signals in "Complex" column.
**Standard** = mixed or middle ground.

### Step 2: Classify Task Type

Match the incoming task to exactly one type:

| Task type | Matches when |
|-----------|-------------|
| **code** | implementation, debugging, refactoring, testing, file changes |
| **research** | investigation, analysis, comparison, summarization, reading, synthesis |
| **design** | UX critique, UI review, visual analysis, layout, interaction flow |
| **compare** | evaluating options, tradeoff analysis, "which is better" |

If genuinely ambiguous, default to **research**.

### Step 3: Select Pipeline

Consult the routing table in `models.yaml`:

```
routing.{task_type}.{difficulty} → pipeline name
```

Then load the pipeline config to get:
- Whether a Thinker is needed
- Which Workers to use (with model IDs)
- Whether fusion is enabled (parallel Workers → Judge)
- Timeout

### Step 4: Dispatch Thinker (if needed)

If the pipeline includes a Thinker:

```
sessions_spawn(
    agentId = <agent type for task>,
    model = <thinker model from pipeline>,
    label = "thinker-{task_type}-{short_description}",
    task = <task description + constraints + available resources>,
    runTimeoutSeconds = <pipeline timeout>,
    cleanup = "delete"
)
```

Thinker returns a plan. Extract the plan for Workers.

### Step 5: Dispatch Worker(s)

For each Worker in the pipeline, spawn with:
- The task (or task slice from Thinker's plan)
- **Access list:** only the context this Worker needs (see below)
- Role declaration: "You are the WORKER."
- Acceptance criteria

```
sessions_spawn(
    agentId = <agent type>,
    model = <worker model>,
    label = "worker-{task_type}-{model_short_name}",
    task = <structured task with role declaration + context + criteria>,
    runTimeoutSeconds = <pipeline timeout>,
    cleanup = "delete"
)
```

If fusion is enabled, all Workers get the SAME task prompt in parallel.
If fusion is disabled, single Worker gets the task.

### Step 6: Collect Worker Outputs

Panel agents auto-announce when complete. If not streaming, check via
`subagents(action='list')`. Wait for ALL Workers to finish.

### Step 7: Dispatch Judge (if fusion enabled)

If 2+ Workers ran in parallel, dispatch Judge with all outputs:

```
sessions_spawn(
    agentId = <agent type>,
    model = <judge model from pipeline>,
    label = "judge-{task_type}",
    task = <synthesis prompt from panels.yaml> + all Worker outputs,
    runTimeoutSeconds = 300,
    cleanup = "delete"
)
```

Judge output becomes the primary result.

### Step 8: Judge's Verdict (collapsed from old Step 8/9)

When multiple workers were dispatched (fusion or complementary), the Judge's output is the final gate. Judge checks:
- Acceptance criteria (PASS/PARTIAL/FAIL for each)
- Disagreements between workers
- Final verdict: ACCEPT / REVISE / ESCALATE

The Tester (in complementary pattern) is the proactive second lens — writes failing tests that surface bugs. The Judge's synthesis is the reactive gate.

**If Judge verdict is ACCEPT:** Deliver result. Done.
**If Judge verdict is REVISE:** Extract failed criteria, re-dispatch to relevant worker with:
- Original task
- Failed criteria (specific)
- What passed (so Worker doesn't break working parts)
- Max 2 revision rounds total per slice
**If Judge verdict is ESCALATE:** Surface question to Pilgrim before continuing.
**Budget exhausted:** Escalate to Pilgrim with Judge's findings.

### Step 9: Deliver

Present the final result. Include:
- What was done
- Judge's verdict and acceptance criteria check
- Any caveats or remaining risks
- Follow-up slices (if Judge surfaced any)

---

## Access Lists

Every sub-agent task string should be structured with explicit context sections:

```markdown
## Task
{what to do}

## Prior Work
### From: Thinker (approach plan)
{thinker output — only if Worker depends on it}

### From: Worker-1 (initial implementation)
{worker output — only for revision worker}

## Constraints
{what NOT to do}

## Acceptance Criteria
{how to know when done}
```

**Rules:**
- Parallel Workers get NO prior context (they're independent)
- Worker after Thinker gets: Thinker's plan + original task
- Tester (complementary pattern) gets: implementer's file scope declaration + acceptance criteria + spec
- Judge gets: ALL Worker outputs (implementer + tester), plus original task + acceptance criteria
- Revision Worker gets: original task + failed criteria + what passed
- NEVER dump full conversation history into a sub-agent task

---

## Quick Reference — Panels (from panels.yaml)

| Task type | Panel models | Judge |
|-----------|-------------|-------|
| research | MiniMax M3 + DeepSeek V4 Pro | MiMo v2.5 Pro |
| code | Kimi K2.7 Code + MiMo v2.5 Pro | GLM 5.2 |
| design | GLM 5.2 + Kimi K2.6 | Gemini 3 Flash |

---

## MANDATORY: Citation Requirements for Research Tasks

Every research task prompt MUST include this block at the end:

```
### CRITICAL: Citation Requirements
- Every factual claim MUST include a URL or specific document reference inline
- If you cannot verify a claim with a source, mark it [UNVERIFIED — no source found]
- Prefer primary sources: government filings, court documents, board minutes, SEC/SOS records
- Secondary sources: news articles, investigative reports, academic papers
- Tertiary: industry publications, organizational websites
- Never present an unsourced claim as "confirmed" — use "alleged", "reported", or "unverified"
- Include the date accessed for all URLs
```

This is NOT optional. Omitting citation requirements from a research task is a bug.

---

## Exceptions (ONLY these)

1. **Pilgrim explicitly says "no fusion" or "single agent"** — direct override
2. **Trivially mechanical tasks** (e.g., "list files in this directory") — no
   reasoning needed, no value in multiple models. Use judgment, but when in
   doubt, fuse.
3. **The task IS the fusion** (e.g., running the fusion orchestrator itself) —
   don't recurse.

---

## Anti-Patterns

- ❌ "This is just a quick code review, single agent is fine" → ALWAYS use complementary dispatch for code
- ❌ "I'll use the same model for all panel slots" → defeats the purpose
- ❌ Dispatching before reading this skill → read it every time
- ❌ Dispatching a separate Verifier after Judge → Judge subsumes verification, this is redundant cost
- ❌ Parallel writers on the same files ("fusion" applied to code) → data loss via last-write-wins race. Use `complementary` pattern instead (implementer + tester, disjoint file scopes).
- ❌ Dumping full context into a sub-agent → use access lists
- ❌ Skipping difficulty assessment → simple tasks shouldn't burn 6 calls

---

## Dispatch Patterns

### Fusion (parallel same-prompt, judge synthesizes)
- **Use for:** research, design, brainstorming tasks where workers produce text/synthesis
- **File scope:** all workers write to similar artifacts (markdown, findings) — judge merges
- **Collision risk:** low for text/markdown; high for code files
- **Pipeline key:** `fusion: true`
- **Example:** research panels — both workers research a topic, judge synthesizes findings

### Complementary (specialized roles, disjoint file scopes)
- **Use for:** code tasks where the goal is shipping a coherent change set
- **File scope:** each role writes to DIFFERENT files by design — no collision possible
- **Collision risk:** zero (disjoint scopes enforced by dispatch task spec)
- **Pipeline key:** `pattern: complementary`
- **Roles:**
  - `implementer` — writes the implementation (src/**, styles, types)
  - `tester` — writes tests + reviews impl (src/**/__tests__/**, SLICE_<n>_REVIEW.md)
  - `judge` — synthesizes impl + tests + review + checks acceptance criteria (subsumes verifier role)
- **Example:** complex-code pipeline — Qwen writes impl, MiMo writes tests in disjoint files, GLM 5.2 judge synthesizes + gates

### When to use which
- **Research tasks:** fusion (workers research different angles, judge merges)
- **Design tasks:** fusion (workers critique from different perspectives, judge merges)
- **Code tasks:** complementary (implementer writes impl, tester writes tests in different files)
- **Single-worker tasks:** no fusion or complementary — one worker, no extra dispatch needed

---

## Integration

This skill is referenced by AGENTS.md in the Subagent Routing section.
When AGENTS.md says "Always use fusion panels," this skill defines HOW.

Supporting files:
- `roles.md` — role contracts (read before every dispatch)
- `models.yaml` — model assignments and pipeline compositions (read before every dispatch)
- `fusion-orchestrator/panels.yaml` — synthesis prompts (read when dispatching Judge)
- `reviewer-loop/SKILL.md` — historical; Verifier role removed 2026-06-24, see roles.md