# CCA-F Labs (all five domains)

Fifteen hands-on exercises across every exam domain. Each lab is designed so you *observe* the behavior the exam tests, because a 301-level exam punishes doc-reading without hands-on scar tissue.

Domain weights (exam guide): D1 27%, D3 20%, D4 20%, D2 18%, D5 15%. This file is the index + exam-mapping; full step-by-step build instructions for each lab live in that lab's folder `README.md` (e.g. `D1/D1L10/README.md`, `D5/D5L7/README.md`). Lab numbers are stable IDs tied to the folder names (`D#L#`), so they appear out of sequence when the index is read domain-by-domain — that is expected.

Worked solutions and reference outputs live in `_AnswerKeys/` (mirrored per lab, e.g. `_AnswerKeys/D1/D1L10/`). Attempt the lab first; use the key to unblock yourself or to compare results.

**Prereqs:** `ANTHROPIC_API_KEY` set, Python 3.10+ with the `anthropic` and `pydantic` SDKs, Claude Code installed, `jq`, and a throwaway git repo (`mkdir cca-lab && cd cca-lab && git init`). Lab 15 (MCP) also needs Node.js / `npx`.

**How to use:** run the paired drill questions first (in the HTML drill), then do the lab, then re-run the drill questions the next day. The lab is what makes the discrimination stick.

---

## Domain 1: Agentic Architecture & Orchestration

*Highest-weight domain (27%). Multi-agent provenance and the design-judgment honeypots (tiering, error contracts, escalation) are where even strong scorers lose points — treat this as a deliberate pass, never a skip.*

### Lab 10: Orchestrator–worker isolation & provenance (~45 min)

**Exam mapping:** multi-agent context passing, structured findings with source + confidence, quarantining failed workers, orchestration pattern selection (drill Q14, Q17, Q18). Detail: `D1/D1L10/README.md`.

1. Build an orchestrator that splits a task into 2–3 independent subtasks and spawns one worker per subtask as a **separate `messages.create` conversation**. First spawn a worker with **no** context passed and watch it fail or hallucinate — subagents do **not** inherit the parent's context.
2. Fix it: pass each worker only the context it needs, explicitly, in its prompt. Have each worker return a structured finding via a schema `{finding, source, confidence}`.
3. Compare context growth: log `input_tokens` for the orchestrator vs a single monolithic agent doing all subtasks in one window. Isolation keeps each window small.
4. Force one worker to error. **Quarantine** it — tag it failed with provenance and keep it out of synthesis — rather than letting a null/garbage finding flow into the final answer.

**Success criteria:**
- [ ] Demonstrated no-inheritance (worker fails without explicit context), then fixed it with explicit passing.
- [ ] Final synthesis carries per-finding source + confidence, and a failed worker is quarantined, not silently dropped.

### Lab 11: The agent loop done right (~40 min)

**Exam mapping:** `stop_reason`-driven control flow, no NL parsing / no iteration-cap-as-stop, `tool_use` / `pause_turn`, parallel `tool_use` (drill Q16; strategy "wrong-answer tells"). Detail: `D1/D1L11/README.md`.

1. Build the canonical manual loop with a real client tool: call → if `stop_reason == "tool_use"`, execute, append `tool_result`, continue → break on `end_turn`.
2. Break it two ways and watch it fail: (a) terminate by scanning the text for "done"/"finished"; (b) terminate only on a fixed iteration cap. The NL-parse misfires; the cap either cuts work short or masks a stuck loop.
3. Fix with `stop_reason` as the sole primary terminator; keep an iteration cap only as a safety backstop, not the mechanism.
4. Trigger a **parallel** tool call (ask something needing two independent tools) — observe multiple `tool_use` blocks in **one** response; return all `tool_result`s in one user turn. Then set `disable_parallel_tool_use` and observe serialization.

**Success criteria:**
- [ ] A loop that terminates on `stop_reason`, handles multiple `tool_use` blocks per turn, and never parses text to decide it's done.
- [ ] You can state why iteration caps and NL-parsing are wrong-answer tells.

### Lab 12: Agent design judgment — tiering, error contracts, escalation (~40 min)

**Exam mapping:** when-to-build-an-agent, structured error context, escalation triggers (drill Q20; strategy "Escalation", "Errors"). Detail: `D1/D1L12/README.md`.

1. **Tiering:** for three tasks (extract one field from a PDF; a 3-step deterministic pipeline; an open-ended repo refactor), decide single-call vs workflow vs agent using the four criteria — complexity, value, viability, cost-of-error. Implement the trivial one as a single call and the refactor as a loop; measure the token/latency gap. Over-agentifying the trivial task wastes tokens for no gain.
2. **Error contracts:** build a tool that fails. Compare returning a generic `"error"` string vs a structured error `{category, retryable, partial_results, attempted}`. Feed each back; the agent recovers/decides with structure and flails (or silently "succeeds") with the generic one.
3. **Escalation:** triage cases designed to trap you — explicit "let me talk to a human" (escalate immediately), angry-but-simple (sentiment ≠ complexity), and a self-reported confidence score (unreliable trigger). Compare a sentiment-based rule vs an explicit-signal rule.

**Success criteria:**
- [ ] A one-line tier justification per task using the four criteria, with the token gap measured.
- [ ] Structured error context enables recovery where a generic message does not.
- [ ] Escalation fires on explicit request, ignores sentiment as a complexity proxy, and doesn't trust self-reported confidence.

---

## Domain 2: Tool Design & MCP Integration

### Lab 13: Tool definitions that trigger correctly (~35 min)

**Exam mapping:** tool description quality / when-to-call, enums + required, `tool_choice` modes, `strict` (drill Q21, Q22; ties to Lab 2). Detail: `D2/D2L13/README.md`.

1. Define a tool with a vague description ("gets data"). Ask questions that should call it; observe under/over-triggering. Rewrite the description to be prescriptive about **when** to call it ("Call this when the user asks about current prices or recent events"); retest and compare the trigger rate.
2. Cycle `tool_choice`: `auto` / `any` / `{type:"tool",name}` / `none` on the same prompt and record how each changes behavior.
3. Enum discipline: reuse the Lab 2 `route_ticket` enum; show drift without `strict`, clean with `strict: true` — the tool-design angle on Lab 2.

**Success criteria:**
- [ ] Same tool, before/after description, with different trigger behavior.
- [ ] You can state what each `tool_choice` value forces.

### Lab 14: Scoped tools & parallel execution (~35 min)

**Exam mapping:** scoped tool distribution vs many-tools-on-one-agent, parallel tool calls (drill Q23; strategy "wrong-answer tells"). Detail: `D2/D2L14/README.md`.

1. Build a "kitchen-sink" agent with ~10 loosely-related tools and ambiguous prompts; log which tool it picks. Look for wrong-tool selection / confusion.
2. Refactor to **scoped distribution**: a small router that dispatches to specialized handlers, each holding 2–3 tools. Rerun; observe cleaner selection.
3. Parallel: prompt something needing two independent reads; observe multiple `tool_use` blocks in one response. Set `disable_parallel_tool_use` and observe forced serialization. Note which read-only tools are parallel-safe.

**Success criteria:**
- [ ] Documented at least one wrong-tool pick in the kitchen-sink setup and cleaner behavior when scoped.
- [ ] Observed parallel `tool_use` and forced serialization, and can say why scoped distribution is the exam-preferred pattern.

### Lab 15: MCP integration (~40 min)

**Exam mapping:** MCP client/server model, connecting servers in Claude Code, tool naming, scopes, auth, resources vs tools (drill Q24, Q25; Academy MCP courses). Detail: `D2/D2L15/README.md`.

1. Add a local stdio MCP server to Claude Code: `claude mcp add filesystem -- npx -y @modelcontextprotocol/server-filesystem <path>`. Run `claude mcp list`, start a session, run `/mcp`, and confirm the tools appear as `mcp__filesystem__*`.
2. Use it: ask Claude to list/read files via the server; watch the `mcp__` tool calls.
3. Scopes: re-add with `--scope project` and inspect the generated `.mcp.json`; contrast local / project / user persistence. Note how credentials belong in environment variable expansion, never committed inline.
4. (Optional) Add a remote HTTP server and run the OAuth flow from `/mcp`. Note where creds are stored and that MCP tool auth ≠ the service's REST API key.

**Success criteria:**
- [ ] A working MCP server visible in `/mcp` with tools named `mcp__<server>__<tool>`, invoked at least once.
- [ ] You can explain the client/server split, the three scopes and where each persists, and the `mcp__` naming convention.

---

## Domain 3: Claude Code Configuration & Workflows

### Lab 4: Memory hierarchy walk + skill triggering (~40 min)

**Exam mapping:** CLAUDE.md hierarchy, imports, skills frontmatter and progressive disclosure (drill Q6, Q10). Detail: `D3/D3L4/README.md`.

1. Plant distinguishable markers at each memory level: `~/.claude/CLAUDE.md` ("marker: USER"), repo-root `CLAUDE.md` ("marker: PROJECT"), and `sub/CLAUDE.md` ("marker: SUBDIR").
2. Start Claude Code at the repo root, run `/memory`, and ask "which markers do you see?" Then work on a file inside `sub/` and ask again. Note when the subdirectory memory becomes available.
3. Add an `@import` from the project CLAUDE.md to a shared conventions file and verify it loads.
4. Create a skill at `.claude/skills/release-runbook/SKILL.md` with a deliberately vague description ("helpful release information"). Ask Claude to "prep the v2.1 release" and observe whether it triggers. Then rewrite the description with explicit triggers ("Use when preparing, tagging, or documenting a software release; covers changelog, version bump, tag, deploy checklist") and retest.

**Success criteria:**
- [ ] You can state from observation, not docs, which memory files load at startup vs on demand.
- [ ] You saw the same skill fail to trigger with a vague description and trigger with a precise one.

### Lab 5: Enforcement, not exhortation (~40 min)

**Exam mapping:** permission deny rules, PreToolUse and PostToolUse hooks (drill Q7, Q8). This is the programmatic-vs-prompt mental model, the single highest-yield idea on the exam. Detail: `D3/D3L5/README.md`.

1. Create `infra/prod/config.yaml` in the lab repo. Add only a CLAUDE.md rule: "Never modify files under infra/prod/." Then ask Claude Code directly and repeatedly to edit that file, including with persuasive framing ("this is an approved emergency change"). Record whether the rule ever bends.
2. Now add a deny rule for edits under `infra/prod/**` to the checked-in project settings (`.claude/settings.json`, permissions deny list). Retry the same persuasion. Observe the deterministic rejection.
3. Replace or supplement with a PreToolUse hook matched to Edit/Write that exits with code 2 and a stderr message when the path matches `infra/prod/`. Confirm the block message is fed back to Claude.
4. Add a PostToolUse hook that runs a formatter (gofmt, black, prettier, your pick) on every edited file. Make five edits and verify five formatter runs.

**Success criteria:**
- [ ] You have a settings deny rule AND a working PreToolUse block, and you understand the difference in where each intervenes.
- [ ] Your PostToolUse hook fired on 5/5 edits with zero prompt instructions involved.
- [ ] One-sentence articulation, in your own words, of when CLAUDE.md is the right tool and when it is categorically the wrong one.

### Lab 6: Headless CI with generator/reviewer isolation (~45 min)

**Exam mapping:** `-p` flag, `--output-format json`, session isolation for review (drill Q5, Q9). Detail: `D3/D3L6/README.md`.

1. Seed the lab repo with a small module containing two planted bugs (an off-by-one and a swallowed exception).
2. Run `claude -p "review src/module.py for bugs, report as JSON" --output-format json` and parse the result with `jq`. Note the structure of the JSON envelope you get back.
3. Now simulate the self-review trap: in one interactive session, have Claude write a new module, then ask it in the same session to review its own code. Count findings.
4. Take the same generated code into a FRESH headless session (no generation context, pass only the diff) and review again. Compare findings against step 3.
5. Wire steps 2 and 4 into a two-stage script: stage 1 generates, stage 2 reviews in an isolated invocation, pipeline fails if the review JSON contains blocking findings.

**Success criteria:**
- [ ] A script that parses headless JSON output without any transcript scraping.
- [ ] Documented finding-count difference between same-session self-review and independent review on identical code.

---

## Domain 4: Prompt Engineering & Structured Output

*Unlike the build-it-yourself labs, `D4/` ships runnable scripts; `D4/README.md` maps them to the three labs below. Worked copies live in `_AnswerKeys/D4/`.*

### Lab 1: Break JSON on purpose, then make it unbreakable (~40 min)

**Exam mapping:** structured outputs vs prompt-level JSON; feature incompatibilities (drill Q1, Q2). Detail: `D4/README.md`.

1. Write a script that sends 20 varied "extract vendor, amount, due_date from this invoice text" requests with only a prompt instruction: "Respond only with valid JSON." Count `json.loads` failures and near-misses (preamble text, trailing commas, markdown fences).
2. Rewrite the same calls using structured outputs (`output_config.format` with a JSON schema). Copy the exact parameter shape from the structured outputs docs page rather than from memory, then run the same 20 inputs. Failure count should be zero.
3. Now trigger the incompatibilities deliberately:
   - Enable citations in the same request as `output_config.format`. Record the 400 error body.
   - Attempt an assistant-prefill turn alongside JSON outputs. Record what happens.
4. Send two requests in the same conversation where the second changes `output_config.format` to a different schema. Compare `cache_read_input_tokens` across the two responses.

**Success criteria:**
- [ ] You measured a nonzero prompt-only failure rate and a zero structured-outputs failure rate.
- [ ] You can recite both incompatibilities (citations, prefill) and describe the actual error you saw.
- [ ] You observed cache invalidation from a format change in the usage numbers, in dollars-equivalent tokens.

### Lab 2: Strict tool use and schema drift (~30 min)

**Exam mapping:** `strict: true`, enum enforcement, combining strict tools with JSON outputs. Detail: `D4/README.md`.

1. Define a tool `route_ticket` with an enum field `category: ["billing","technical","account","other"]`. Run 15 ambiguous ticket texts WITHOUT `strict` and log every tool call input. Look for drifted values ("Billing", "tech", invented categories).
2. Add `strict: true` and rerun. Diff the two logs.
3. In one request, combine a strict tool with `output_config.format` for the final response. Confirm both operate together.
4. Audit one of your team's real extraction pipelines for reliance on prompt-level enum discipline. A real audit doubles as exam prep.

**Success criteria:**
- [ ] You captured at least one drifted enum value without strict mode, or can explain why your inputs never drifted.
- [ ] You ran strict tools and JSON outputs together successfully in a single request.

### Lab 3: Validation-retry loop and the example-diversity effect (~45 min)

**Exam mapping:** few-shot design (drill Q4), self-correction chains, Console prompt tooling. Detail: `D4/README.md`.

1. Build a classifier prompt with 5 few-shot examples that are all the SAME category, then run 20 mixed-category inputs and record the bias.
2. Replace with 3 to 5 diverse examples in `<example>` tags covering categories, lengths, and one edge case. Rerun and compare accuracy. You should reproduce the drill Q4 failure and fix.
3. Wrap the extraction from Lab 1 in a validation-retry loop: validate the parsed object against business rules (amount > 0, due_date parses, vendor non-empty); on failure, send the error back in a follow-up turn asking for a corrected object. Measure accuracy at attempt 1 vs attempt 2.
4. Paste your final prompt into the Console prompt improver. Diff its output against yours, then run both through the Console evaluation tool on 10 test cases.

**Success criteria:**
- [ ] Reproduced example-induced bias and fixed it with diversity, with before/after numbers.
- [ ] Working validation-retry loop where attempt 2 recovers at least one attempt-1 failure.
- [ ] You can articulate one concrete change the prompt improver made and whether the eval justified it.

---

## Domain 5: Context Management & Reliability

### Lab 7: Prompt caching forensics (~35 min)

**Exam mapping:** prefix-based caching, cache_control breakpoints, invalidation signatures (drill Q12, Q3). Detail: `D5/D5L7/README.md`.

1. Build a request with a large (~5K+ token) system prompt behind a `cache_control` breakpoint. Send it twice within a minute. Log `cache_creation_input_tokens` and `cache_read_input_tokens` for both calls; call 2 should show a large cache read.
2. Prepend `Current time: <timestamp>` to the TOP of the system prompt and send three more requests. Watch cache reads collapse to zero.
3. Move the timestamp into the user turn (after the stable cached block) and confirm cache reads recover.
4. Bonus: wait past the default TTL with no traffic and observe the difference in signature (gradual expiry vs the immediate zero from prefix mutation).

**Success criteria:**
- [ ] A four-row table of usage numbers proving: warm hit, prefix-mutation kill, recovery after moving volatile content.
- [ ] You can diagnose "cache reads went to zero immediately after a deploy" in one sentence.

### Lab 8: Context editing under tool-call load (~45 min)

**Exam mapping:** tool-result clearing, long-session degradation (drill Q11). Detail: `D5/D5L8/README.md`.

1. Build a small agentic loop with a fake tool `fetch_log(page)` that returns ~3K tokens of filler per call. Drive 20+ tool calls in one conversation and log total input tokens per turn. Watch the linear climb.
2. Enable context editing with the tool-result clearing strategy (copy the current strategy name and parameters from the context editing docs page; the dated strategy identifiers change). Rerun the same 20-call loop and log input tokens per turn.
3. Plant a critical fact in tool result #2 ("the anomaly began at 03:14 UTC on host db-7") and at call #20 ask the agent to recall it. Test with clearing configured to keep different numbers of recent results, and find the setting where the fact survives vs gets cleared.
4. Relate this to any long-running agent you operate: at 60+ tool calls, which results actually need to stay live for the finalization steps?

**Success criteria:**
- [ ] Two token-per-turn curves (with and without clearing) showing the flattening effect.
- [ ] You found the boundary where aggressive clearing loses a needed fact, and can explain the retention tradeoff.

### Lab 9: stop_reason handling + compaction contract (~40 min)

**Exam mapping:** stop_reason values, truncation recovery, compaction summary quality (drill Q13, Q15). Detail: `D5/D5L9/README.md`.

1. Force truncation: request a long structured extraction with `max_tokens: 200`. Confirm `stop_reason == "max_tokens"` and that the JSON is mid-object.
2. Write a handler: on `max_tokens`, never parse; either re-request with a raised limit or continue the generation, then parse. Prove it recovers the full object.
3. List the stop_reason values from the docs (end_turn, max_tokens, tool_use, refusal, pause_turn) and write one line each on what your code must do.
4. Compaction contract test in Claude Code: run a long session where you explicitly reject an approach ("do not use approach X, we tried it, it fails on Y") and state a constraint. Trigger `/compact`. Then ask the post-compaction session to solve the original problem and see whether X comes back. Repeat, but this time pass custom compaction instructions telling it to preserve decisions, failed approaches, and constraints. Compare.

**Success criteria:**
- [ ] Working truncation-recovery handler with a before/after demonstration.
- [ ] Observed a rejected approach resurrect after default compaction, and stay dead after instructed compaction (or documented that default compaction held, with the summary text as evidence).

---

## Suggested sequence

Work domains in checklist order, pairing each with its drill filter:

- **D1 (27%):** Drill (D1 filter) → Labs 10, 12 first — multi-agent provenance and the design-judgment honeypots are where strong candidates lose points — then Lab 11.
- **D2 (18%):** Drill (D2 filter) → Labs 13, 14. Lab 15 (MCP) is the lightest lift once Node/`npx` is available — do it whenever.
- **D3 (20%):** Drill (D3 filter) → Labs 4, 5, 6. Lab 5 is the highest-yield lab in the kit.
- **D4 (20%):** Drill (D4 filter) → Labs 1, 2, 3.
- **D5 (15%):** Drill (D5 filter) → Labs 7, 8, 9.

After each domain, re-run its drill filter the next day; target 5/5. **Final week:** rerun the full 25-question drill cold and shuffled (target 21+), redo Lab 5, Lab 7, and Lab 10 from scratch (the highest-yield mental models plus the highest-weight domain), and do the official Skilljar practice exam reading every rationale, including for questions you got right.
