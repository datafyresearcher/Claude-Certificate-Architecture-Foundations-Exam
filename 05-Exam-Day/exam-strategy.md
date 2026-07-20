# CCA-F Exam Day One-Pager

Read this the night before and the morning of. Nothing new after this.

## Time math
60 questions, 120 minutes = 2 min/question. Scenario stems are long, so bank time on questions you know cold. Flag and skip anything over 3 minutes; first-pass everything, then return. Never leave blanks.

## The honeypot test (run it on every question)
1. Eliminate the two weak options fast. Almost every question comes down to two finalists.
2. Ask of each finalist: "Does this patch the symptom or fix the root cause?" The trap makes the visible failure go away; the answer removes the mechanism that produced it.
3. Check the requirement words. MUST / NEVER / GUARANTEE / ALWAYS demand a deterministic mechanism (hooks, permission deny rules, strict tool use, structured outputs, stop_reason checks). Any finalist that strengthens wording, adds emphasis, or adds diligence is the honeypot.
4. Read the scenario twice before answering. Rushed reads lose points; details like "immediately", "in the same session", or "even if instructed" are the discriminator.

## Enforcement ladder (low to high)
prompt wording < CLAUDE.md guidance < few-shot examples < validation-retry loop < hooks / permission rules / strict tool use / structured outputs. When the stakes are financial, safety, or compliance, the answer sits at the top of the ladder.

## Terminology hit list
- **stop_reason values:** end_turn (normal), max_tokens (truncated: never parse, raise limit or continue), tool_use (execute tool, append result, continue loop), refusal, pause_turn (server tools: resume). Loop termination = check stop_reason, never parse text, never rely on iteration caps as the primary stop. For *large* structured tasks that keep truncating: split into smaller scoped calls and merge the results — raising max_tokens beyond practical limits is the trap answer.
- **Hard incompatibilities:** citations + output_config.format = 400 error. Prefill + JSON outputs = incompatible. Changing output_config.format mid-thread invalidates the prompt cache. JSON outputs + strict:true tools = combinable in one request.
- **CLAUDE.md hierarchy:** enterprise policy, then project (CLAUDE.md at repo root, shared via git), then user (~/.claude/CLAUDE.md, personal). Subdirectory CLAUDE.md loads on demand when working there. @imports pull in shared files.
- **Config mechanism selection (know the whole menu):** CLAUDE.md = always-loaded guidance; `.claude/rules/*.md` with `paths:` glob frontmatter = instructions scoped to matching files, loaded when Claude touches them; skills = on-demand procedures triggered by their description; hooks = deterministic actions at lifecycle events; settings permissions = hard allow/deny enforcement. Pick by guidance type AND when it should apply.
- **Slash command vs skill vs subagent:** you invoke a slash command (explicit timing); a skill loads itself when its frontmatter description matches the task (fix triggering by fixing the description); a subagent is a separate session via the Task tool for context isolation or parallelism. Frontmatter extras: `context: fork` runs the skill in an isolated subagent context (no conversation history — prevents cross-contamination of session state); `disable-model-invocation: true` makes it user-invoke-only.
- **Hooks:** PreToolUse runs before the call and can block it (exit code 2, stderr fed back); PostToolUse runs after (normalization, formatters). Deterministic, unlike anything written in prose.
- **Headless / CI:** claude -p for non-interactive, --output-format json for machine parsing, --bare for fast reproducible scripted runs, isolated sessions for generator vs reviewer. Batch API for latency-tolerant volume (overnight), synchronous for blocking gates (pre-merge).
- **Built-in tool selection:** Grep = search file *contents* by pattern; Glob = find files by *name/path* pattern; Read = known file, need its contents; Bash = everything else (run commands, chained operations). Exploration questions want incremental understanding — Glob/Grep to locate, Read only what's needed — not "Read the whole repo".
- **Review architecture:** an independent instance without the generator's reasoning context beats same-session self-review. Large reviews: per-file passes plus a cross-file integration pass, and separate concern-focused passes (security, business logic, API design) each with dedicated few-shot examples — one prompt juggling competing concerns trades recall between them. Choosing plan mode vs direct execution vs multi-phase workflow keys on task scope, risk level, and whether human approval is required: high-risk/needs-approval → plan mode first; small and reversible → direct; large multi-concern → phased.
- **Prompt caching:** prefix-based. Stable content first, volatile content last. Cache reads dropping to zero immediately after a change = prefix mutation; gradual misses = TTL expiry.
- **Compaction summary must preserve:** task overview, current state, important discoveries (including failed/rejected approaches), next steps, context to preserve (user constraints). If compaction loses decisions, fix the summary contract, not the schedule.
- **Multi-agent:** explicit context passing in subagent prompts (never assume inheritance); structured findings with source attribution and confidence; quarantine failed subagent output; provenance survives synthesis. Pattern selection: independent subtasks → parallel orchestrator-workers; dependent stages → sequential pipeline; one contested answer → voting. Delegation style: goal-oriented instructions (objective, output format, boundaries) beat rigid procedural scripts — they enable adaptive behavior while the coordinator keeps visibility and control.
- **State persistence:** long/multi-agent pipelines checkpoint findings and decisions to durable storage outside the context; on restart, resume from the last completed step. Retry logic complements checkpointing, never replaces it.
- **Errors:** structured error context (category, retryable flag, partial results plus what was attempted). Generic messages and silent empty-result "success" are always wrong answers.
- **Escalation:** immediate on explicit customer request; sentiment is not complexity; self-reported confidence scores are unreliable triggers.
- **Human review routing (extractions):** route to reviewers by extraction confidence scores, document characteristics, and field-level ambiguity — random sampling is the wrong answer.

## Wrong-answer tells (auto-suspicion list)
Parsing natural language for loop termination. Arbitrary iteration caps as the stop mechanism. Louder prompts for critical rules. Sentiment-based escalation. Generic error messages. Swallowed errors returned as success. Many tools on one agent instead of scoped distribution. Same-session self-review. Aggregate accuracy masking per-type failures. Blanket claims that a feature "disables" another (usually the real rule is narrower: a change invalidates, a combination errors). Full-pipeline reruns instead of checkpoint-resume.

## High-yield exam-day patterns
Scenario patterns worth drilling until they're reflexive — verify each against the linked docs, never from memory:

- **Slow non-interactive startup.** Pattern: a scripted/CI `claude -p` call spends tens of seconds loading CLAUDE.md, hooks, skills, and MCP servers the job doesn't need (everything required is passed in the prompt). The fix: run with `--bare` (skips auto-discovery of hooks, skills, plugins, MCP servers, auto memory, and CLAUDE.md) and pre-approve just the tools the job needs, e.g. `--allowedTools "Read,Grep,Glob"`. Docs confirm `--bare` is the recommended mode for scripted calls. Related distinction worth knowing: `--allowedTools` auto-approves permissions; `--tools` restricts which built-in tools exist at all. (CLI reference + Headless docs.)
- **Objective clusters that reward a deliberate pass** (see the Objective Map tab in the checklist): agentic review architecture (plan mode vs direct vs multi-phase), state persistence/resumption for multi-agent pipelines, orchestration pattern selection, Claude Code review configurations (load correct standards, restrict tools, structured output), config mechanism selection (CLAUDE.md vs .claude/rules vs skills vs hooks vs settings), built-in tool selection (Grep/Glob/Read/Bash), codebase exploration strategy, subagent prompt completeness, and extraction schemas with optional/nullable/enum fields. All are covered by the docs linked in the checklist — give them a deliberate pass, not a skim.

*Note: the exam is covered by a candidate agreement — study patterns and doc references belong here, never recalled exam questions.*

## Last 24 hours
Full honeypot drill, cold and shuffled (target 21+/25). Official practice exam rationales, including for questions you got right. This page. Sleep.
