# D5L9 — stop_reason Handling + Compaction Contract

**Exam mapping:** `stop_reason` values, truncation recovery, compaction summary quality (drill Q13, Q15)
**Estimated time:** ~40 min
**Domain:** 5 — Context Management & Reliability
**Key concept:** Two reliability contracts. (A) **Never parse a truncated response** — `stop_reason` tells you *why* generation stopped, and `max_tokens` means the body is incomplete. (B) **Compaction is a lossy summary** — what survives it is a contract you can shape, not a guarantee; decisions, rejected approaches, and constraints must be explicitly preserved or they can resurrect.

> **How to use this lab:** two parts. Part A is an API/SDK exercise you build and run (`python`). Part B is an interactive Claude Code exercise you drive by hand in the CLI. Do both — they test different halves of the same "long/interrupted sessions fail silently unless you handle it" idea.

---

## Part A — stop_reason + truncation recovery (API)

### Facts to keep in front of you (Sonnet 4.6)

> **Model choice:** this part uses **structured outputs** (`output_config.format`). The documented support list is **Fable 5, Opus 4.8, Sonnet 4.6, Haiku 4.5** (plus legacy Opus 4.5 / 4.1) — **Sonnet 4.5 is *not* on it**, so `output_config.format` may 400 there. Use `claude-sonnet-4-6` (balance) or `claude-haiku-4-5` (cheapest). Everything else in Part A — `stop_reason` values, the truncation, the recovery handler — is identical across models.

`response.stop_reason` tells you why the model stopped. Every value demands a *different* code path:

| `stop_reason` | Meaning | What your code MUST do |
|---|---|---|
| `end_turn` | Finished naturally | Safe to parse / use the response |
| `max_tokens` | Hit the `max_tokens` cap | **Do not parse** — body is incomplete. Re-request with a higher limit (or stream), then parse |
| `tool_use` | Wants to call a tool | Execute the tool, append the result, continue the loop |
| `pause_turn` | Server-tool loop paused (agentic) | Re-send the assistant turn to resume — no extra "continue" message |
| `refusal` | Refused for safety | Don't retry the same prompt; read `response.stop_details` (`.category`, `.explanation`) |
| `stop_sequence` | Hit a custom stop sequence | Handle per your stop-sequence design |
| `model_context_window_exceeded` | Hit the **context window** (not the output cap) | Compact/split the conversation — raising `max_tokens` won't help |

Other facts this part leans on:
- **Structured outputs do NOT save you from truncation.** `output_config.format` guarantees the *shape* only when generation completes. If `stop_reason == "max_tokens"`, the JSON is cut mid-object and `json.loads` will raise.
- On Sonnet 4.6 (and the whole 4.6/4.7/4.8 family + Fable 5), assistant-turn **prefill is removed**, so "continue from the partial text" via a prefill 400s. The clean, documented recovery is **re-request with a higher `max_tokens`** (or stream for legitimately large outputs). *(On Sonnet 4.5 prefill still works, so continuation is also available there — but the re-request path we use works everywhere.)*

### Step 0 — Prereqs

```powershell
# From the D5L9 folder.
$env:ANTHROPIC_API_KEY
python -c "import anthropic; print(anthropic.__version__)"
New-Item -ItemType File stop_reason_recovery.py
```

### Step 1 — Force a truncation and watch a structured output break

Build a structured extraction whose full answer is comfortably longer than 200 tokens, then cap it at 200. Put this in `stop_reason_recovery.py`:

```python
import os
import sys
import json
import anthropic

MODEL = "claude-sonnet-4-6"   # structured outputs supported; cheaper than Opus. Haiku 4.5 also works.

# A schema whose fully-populated instance is well over 200 tokens.
SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
        "affected_hosts": {"type": "array", "items": {"type": "string"}},
        "timeline": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "time": {"type": "string"},
                    "event": {"type": "string"},
                },
                "required": ["time", "event"],
                "additionalProperties": False,
            },
        },
        "root_cause": {"type": "string"},
        "remediation_steps": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["summary", "severity", "affected_hosts", "timeline",
                 "root_cause", "remediation_steps"],
    "additionalProperties": False,
}

POSTMORTEM = (
    "At 03:14 UTC host db-7 began rejecting writes after a disk filled to 100%. "
    "Ingest latency climbed from 12ms to 4200ms over eight minutes. The on-call "
    "rotated the write leader to db-9 at 03:31, truncated the oversized WAL, and "
    "restored writes by 03:47. Root cause: log rotation had been silently disabled "
    "by a config drift three weeks earlier. Remediation: re-enable rotation, add a "
    "disk-usage alert at 80%, and add a pre-deploy check that rejects configs "
    "missing a rotation policy. Two other hosts, db-3 and db-11, share the drifted "
    "config and must be patched before the next release."
)

PROMPT = ("Extract a detailed structured incident report from this postmortem. "
          "Populate the timeline and remediation_steps thoroughly.\n\n" + POSTMORTEM)


def extract(max_tokens):
    return client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
        messages=[{"role": "user", "content": PROMPT}],
    )


if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Set ANTHROPIC_API_KEY first.")
    client = anthropic.Anthropic()

    print("=== Step 1: force truncation with max_tokens=200 ===")
    resp = extract(200)
    body = next(b.text for b in resp.content if b.type == "text")
    print("stop_reason:", resp.stop_reason)
    print("raw body (note it's cut mid-object):")
    print(body)
    print("\nTrying to parse it anyway:")
    try:
        json.loads(body)
        print("  parsed OK (unexpected)")
    except json.JSONDecodeError as e:
        print(f"  json.loads FAILED: {e}")
```

Run it:

```powershell
python stop_reason_recovery.py
```

**What to look for — and record:**
- `stop_reason` is `max_tokens` (not `end_turn`).
- The raw body ends mid-object — a dangling key, an unterminated string, no closing `}`.
- `json.loads` raises `JSONDecodeError`. **This is the failure mode: a naive pipeline that always calls `json.loads()` crashes (or worse, silently retries and double-charges) whenever output happens to run long.**

### Step 2 — Write the recovery handler and prove it works

The rule: **branch on `stop_reason` before you ever parse.** On `max_tokens`, raise the limit and retry; never parse the truncated body. Add this to the file:

```python
def extract_safely(start=200, ceiling=4000):
    max_tokens = start
    while True:
        resp = extract(max_tokens)
        reason = resp.stop_reason

        if reason == "max_tokens":
            if max_tokens >= ceiling:
                raise RuntimeError(f"Still truncated at ceiling={ceiling}; "
                                   "output genuinely too large - stream instead.")
            max_tokens *= 4          # raise limit and retry; do NOT parse the partial
            print(f"  truncated -> retrying with max_tokens={max_tokens}")
            continue

        if reason == "refusal":
            d = resp.stop_details
            raise RuntimeError(f"Model refused: {getattr(d, 'category', None)} / "
                               f"{getattr(d, 'explanation', None)}")

        # end_turn (or other terminal reason): safe to parse now.
        body = next(b.text for b in resp.content if b.type == "text")
        return json.loads(body)
```

And call it from `__main__`:

```python
    print("\n=== Step 2: recovery handler ===")
    report = extract_safely(start=200)
    print("  recovered a valid object with keys:", sorted(report.keys()))
    print("  timeline entries:", len(report["timeline"]))
    print("  affected_hosts:", report["affected_hosts"])
```

Run again:

```powershell
python stop_reason_recovery.py
```

**What to look for — and record (this is your before/after):**
- The handler starts at 200, sees `max_tokens`, prints the retry at 800 (and maybe 3200), then lands on `end_turn` and parses cleanly.
- You get a full object — all six keys, a multi-entry timeline, `db-7`/`db-3`/`db-11` in `affected_hosts`.
- **Before:** blind `json.loads` on the 200-token call crashed. **After:** the `stop_reason` branch recovered the complete object with zero parsing errors.

### Step 3 — The stop_reason cheat sheet

Copy the table from the Facts box into your own notes, one line per value, in your own words — *what my code does when I see this*. This is drill Q13 material; the exam rewards knowing that `max_tokens` ≠ `model_context_window_exceeded` (raise the output cap vs compact the conversation) and that `pause_turn` resumes by re-sending, not by adding a "continue" message.

---

## Part B — Compaction contract (Claude Code)

Compaction summarizes earlier conversation to free context. The **contract** you're testing: does a decision you made — a rejected approach, a hard constraint — survive the summary? By default the summarizer guesses what matters; you can shape it with instructions.

### Facts to keep in front of you (Claude Code)

- **`/compact [instructions]`** — summarize now; optional free-form instructions steer *what the summary keeps* (e.g. `/compact preserve all rejected approaches and constraints`). Works on demand at any size.
- **Persistent** compaction guidance: add a **`# Compact Instructions`** section to `CLAUDE.md` (project-root or user-level). It applies on *every* compaction — manual and automatic — not just one call.
- **Auto-compact** fires automatically as you near the context limit (clears old tool outputs first, then summarizes). The exact threshold isn't published and there's no documented setting to disable it.
- **`/compact` vs `/clear`:** compact *summarizes and keeps* the gist; clear *discards* history (recoverable via `/resume`). Different tools.
- **Verifying it happened:** the CLI shows a brief `Conversation compacted` line. There's no "view the summary" command — use **`/context`** to see current usage, or just ask Claude to paraphrase the summary it produced.

### Step 4 — Establish a decision, then compact (default) and test recall

Open a Claude Code session in a scratch directory:

```powershell
mkdir compaction-test; cd compaction-test; claude
```

> Compaction here is **model-agnostic** — run it on whatever's cheap. Inside the session, `/model sonnet` (or your preferred cheaper model) is fine; a weaker summarizer can even make the "does the rejected approach survive?" failure show up more readily.

Then, **in the Claude Code session**, establish a clear constraint and an explicitly rejected approach. Type something like:

```
We're designing a request rate limiter for our service. Two hard rules for this whole session:
CONSTRAINT: it must be dependency-free — standard library only, no new packages.
REJECTED: do NOT use a Redis-backed token bucket. We tried it and it fails on our
air-gapped deployment, which has no network access to Redis. Don't propose it again.
Acknowledge these, then wait — I'll ask for the implementation later.
```

Have a few more exchanges so there's real history to summarize (ask it to sketch the interface, discuss edge cases, whatever). Then compact with **no** instructions:

```
/compact
```

You'll see the `Conversation compacted` line. Now ask for the original task **without restating the rules**:

```
Implement the rate limiter we discussed.
```

**What to look for — and record:**
- Does it honor the **dependency-free** constraint, or reach for a package?
- Does the **rejected** Redis token-bucket resurrect?
- Optionally, ask: `Summarize the conversation summary you just created` — read whether the constraint and the rejected approach are actually in the summary text. Paste that summary into your notes as evidence.

> Modern default compaction is decent and may hold. That's a valid outcome — **record what actually happened** (resurrected vs held) plus the summary text. The exam point is understanding the contract and its failure mode, not forcing a failure.

### Step 5 — Compact WITH instructions and compare

Start clean so nothing leaks between runs:

```
/clear
```

Re-establish the *same* constraint and rejected approach (paste the same setup message and have a similar short exchange). This time, compact **with explicit preservation instructions**:

```
/compact Preserve verbatim: all hard constraints, every rejected approach and the reason it was rejected, and any decisions made. Do not drop them even if they seem resolved.
```

Then ask again, without restating:

```
Implement the rate limiter we discussed.
```

**What to look for — and record:**
- Compare against Step 4. With instructions, the constraint and the "no Redis token bucket" rejection should reliably survive and shape the answer.
- Ask it to paraphrase this summary too, and diff the two summary texts. The instructed one should explicitly carry the constraint + rejected approach; the default one may have compressed or dropped them.

### Step 6 (bonus) — Make it persistent via CLAUDE.md

One-off `/compact` instructions don't help against **auto**-compaction (which fires unprompted near the limit). For durable behavior, add this to a `CLAUDE.md` in the scratch dir:

```markdown
# Compact Instructions

When compacting, always preserve verbatim:
- All hard constraints stated in the session
- Every rejected approach and the specific reason it was rejected
- Key decisions and their rationale
Do not drop these even if they appear resolved.
```

Restart the session, redo the setup, run a bare `/compact`, and confirm the constraint/rejection survive **without** you passing instructions on the command — the CLAUDE.md section now drives every compaction, including automatic ones.

---

## Key Observations to Record

| Step | What you proved |
|------|-----------------|
| Step 1 | `stop_reason == "max_tokens"` yields incomplete JSON; blind `json.loads` fails — structured outputs don't protect against truncation |
| Step 2 | Branching on `stop_reason` (retry with higher `max_tokens` on truncation, never parse the partial) recovers the full object |
| Step 3 | Each `stop_reason` has a distinct required action; `max_tokens` ≠ `model_context_window_exceeded` |
| Step 4 | Default compaction may drop a rejected approach / constraint — the summary is a lossy guess |
| Step 5 | `/compact <instructions>` shapes what survives; the constraint + rejection stay when you ask for them |
| Step 6 | A `# Compact Instructions` section in CLAUDE.md makes preservation persistent across manual *and* auto compaction |

**Key exam points:**

- **Never parse before checking `stop_reason`.** `max_tokens` means truncated — raise the cap (or stream) and retry; don't `json.loads` the fragment.
- `max_tokens` (raise output cap) vs `model_context_window_exceeded` (compact/split the conversation) vs `pause_turn` (re-send to resume) vs `refusal` (read `stop_details`, don't blind-retry) — different reasons, different handlers.
- Structured outputs guarantee shape **only on a complete response**; truncation still produces invalid JSON.
- Compaction is a **lossy summary**, not lossless history. What it keeps is a contract you shape with `/compact <instructions>` (one-off) or a CLAUDE.md `# Compact Instructions` section (persistent, covers auto-compaction).
- `/compact` summarizes-and-keeps; `/clear` discards. Auto-compact fires near the limit; you can't disable it, so make your preservation rules persistent.

---

## Success Criteria

- [ ] A working truncation-recovery handler with a **before/after** demo: blind `json.loads` fails on the `max_tokens` response; the `stop_reason`-aware handler recovers the full object.
- [ ] You can recite the `stop_reason` values and the one action each demands (Step 3 cheat sheet in your own words).
- [ ] You ran the compaction contract test and **recorded the outcome**: whether the rejected approach resurrected after *default* compaction and whether it stayed dead after *instructed* compaction — with the summary text as evidence either way.
- [ ] You can explain why a persistent `# Compact Instructions` section beats a one-off `/compact <instructions>` (it also governs automatic compaction).
