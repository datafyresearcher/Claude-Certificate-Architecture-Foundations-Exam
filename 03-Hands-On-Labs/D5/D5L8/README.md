# D5L8 — Context Editing Under Tool-Call Load

**Exam mapping:** tool-result clearing, long-session degradation (drill Q11)
**Estimated time:** ~45 min
**Domain:** 5 — Context Management & Reliability
**Key concept:** In a long agentic loop, old tool results pile up and input tokens climb every turn. **Context editing prunes** stale tool results server-side so the prompt stops growing — but anything it clears is *gone*, so a fact buried in an early result can vanish before you need it.

> **How to use this lab:** build it yourself, one step at a time. You'll drive a 20-call tool loop, watch the per-turn input-token curve climb linearly, then turn on clearing and watch it flatten — and then watch a planted fact get cleared away. The insight is the retention tradeoff, felt firsthand.

---

## What you're proving

Context editing (tool-result clearing) removes the **oldest** tool interactions from the prompt once a trigger threshold is crossed, keeping only the N most-recent. It **prunes** (deletes) — unlike compaction, which **summarizes**. You'll measure:

1. Input tokens per turn **without** clearing → linear climb.
2. Input tokens per turn **with** clearing → flattens after the trigger fires.
3. Whether a critical fact planted in tool result #2 survives to turn 20 under different `keep` settings.

---

## Facts to keep in front of you (Opus 4.8)

Verified against the current context-editing docs — these identifiers are **dated and change**, so this is the version this lab targets:

> **Model choice:** the `context-management-2025-06-27` beta works on cheaper models too — **Sonnet 4.5 / Sonnet 4.6 / Haiku 4.5** are all fine here (the clearing behavior is model-independent). Use whatever's cheap.

- **Strategy identifier:** `clear_tool_uses_20250919`
- **Beta header:** `context-management-2025-06-27` → call via `client.beta.messages.create(..., betas=["context-management-2025-06-27"])`
- **Config lives in `context_management={"edits": [ ... ]}`.**

| Parameter | Default | Meaning |
|-----------|---------|---------|
| `trigger` | 100,000 input tokens | When clearing activates. `{"type": "input_tokens", "value": N}` or `{"type": "tool_uses", "value": N}` |
| `keep` | 3 tool uses | How many **most-recent** tool use/result pairs to retain. Oldest cleared first. `{"type": "tool_uses", "value": N}` |
| `clear_at_least` | none | Minimum tokens that must be cleared for the strategy to apply at all |
| `exclude_tools` | none | Tool names whose results are **never** cleared — the real-world lever for protecting critical context |
| `clear_tool_inputs` | `false` | If false, only tool **results** are cleared; Claude's original tool **calls** stay visible |

- **Response reports what was dropped:** `response.context_management.applied_edits` → each entry has `cleared_tool_uses` and `cleared_input_tokens`. It's `None`/empty on turns where nothing was cleared.
- **Prune, not summarize.** Cleared content is deleted, not condensed. There is no summary left behind — the tokens (and their facts) are simply gone from the prompt.

---

## Step 0 — Prereqs

```powershell
# From the D5L8 folder.
$env:ANTHROPIC_API_KEY   # should print your key
python -c "import anthropic; print(anthropic.__version__)"
New-Item -ItemType File context_editing.py
```

---

## Step 1 — Build the loop and watch the linear climb (no clearing)

You'll build a manual agentic loop with a fake `fetch_log(page)` tool that returns ~10.6K tokens of log filler per call. You **force** the tool each turn (`tool_choice`) so the loop is deterministic — you're studying token growth, not the model's judgment. The critical fact is planted in the **2nd** tool result now, so both runs are comparable.

Put this in `context_editing.py`:

```python
import os
import sys
import anthropic

MODEL = "claude-opus-4-8"
BETA = "context-management-2025-06-27"

FETCH_LOG = {
    "name": "fetch_log",
    "description": "Fetch one page of incident log text.",
    "input_schema": {
        "type": "object",
        "properties": {"page": {"type": "integer", "description": "1-based page number"}},
        "required": ["page"],
    },
}

# 220 lines of noisy filler per page. This LOG_LINE tokenizes to ~48 tokens,
# so a page is ~10.6K tokens (not 3K) - big enough to cross a 20K trigger in ~2 pages.
# Want a slower, more gradual climb? Drop range(220) to range(60) (~2.9K/page).
LOG_LINE = ("2026-07-14 02:{m:02d}:00Z host=db-7 svc=ingest level=INFO "
            "msg=heartbeat latency_ms=12 status=200 queue_depth=4\n")
# The needle we hide in tool result #2:
FACT = ("2026-07-14 03:14:00Z host=db-7 svc=ingest level=CRITICAL "
        "msg=ANOMALY_START the anomaly began at 03:14 UTC on host db-7\n")


def log_page(call_index: int) -> str:
    body = "".join(LOG_LINE.format(m=i % 60) for i in range(220))
    if call_index == 2:
        return FACT + body      # plant the critical fact in the 2nd result
    return body


def run(context_management=None, n_calls=20):
    client = anthropic.Anthropic()
    messages = [{
        "role": "user",
        "content": ("You are triaging an incident. Use fetch_log to read one log page "
                    "at a time until told to stop. Always call fetch_log."),
    }]

    print(f"{'turn':>4} {'input_tokens':>13} {'cache_read':>11} {'cleared_tokens':>15}")
    for i in range(1, n_calls + 1):
        kwargs = dict(
            model=MODEL, max_tokens=512, tools=[FETCH_LOG],
            tool_choice={"type": "tool", "name": "fetch_log"},   # force a tool call every turn
            messages=messages, betas=[BETA],
        )
        if context_management:
            kwargs["context_management"] = context_management
        resp = client.beta.messages.create(**kwargs)

        cm = getattr(resp, "context_management", None)
        cleared = 0
        if cm and getattr(cm, "applied_edits", None):
            cleared = sum(e.cleared_input_tokens for e in cm.applied_edits)
        cache_read = getattr(resp.usage, "cache_read_input_tokens", 0) or 0
        print(f"{i:>4} {resp.usage.input_tokens:>13} {cache_read:>11} {cleared:>15}")

        messages.append({"role": "assistant", "content": resp.content})
        tool_use = next(b for b in resp.content if b.type == "tool_use")
        messages.append({"role": "user", "content": [{
            "type": "tool_result", "tool_use_id": tool_use.id, "content": log_page(i),
        }]})

    # Final recall turn: forbid tools so the model MUST answer from remaining context.
    messages.append({"role": "user", "content": (
        "Stop fetching. From the logs you've read, exactly what time did the anomaly "
        "begin and on which host? If you no longer have that detail, say so explicitly.")})
    final_kwargs = dict(model=MODEL, max_tokens=256, tools=[FETCH_LOG],
                        tool_choice={"type": "none"}, messages=messages, betas=[BETA])
    if context_management:
        final_kwargs["context_management"] = context_management
    resp = client.beta.messages.create(**final_kwargs)
    answer = "".join(b.text for b in resp.content if b.type == "text").strip()
    print("\nRECALL:", answer)
    return answer


if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Set ANTHROPIC_API_KEY first.")

    print("=== Step 1: NO context editing ===")
    run(context_management=None)
```

Run it:

```powershell
python context_editing.py
```

**What to look for — and record (this is curve #1):**
- `input_tokens` climbs **~10.6K per turn** — a near-straight line from turn 1 to 20. By turn 20 you're processing ~200K+ tokens of prompt on every single call.
- `cleared_tokens` is 0 the whole time (nothing is being cleared).
- **RECALL** at the end is correct: the model reports *03:14 UTC on host db-7*, because result #2 is still in the prompt.

Copy the `turn` and `input_tokens` columns somewhere — that's your baseline curve.

---

## Step 2 — Turn on clearing and watch the curve flatten

Now enable tool-result clearing. Set the trigger **low** (20K) so it actually fires inside 20 calls — the 100K default never would at this transcript size.

Change the bottom of the file:

```python
    print("=== Step 2: WITH context editing (keep=3) ===")
    run(context_management={
        "edits": [{
            "type": "clear_tool_uses_20250919",
            "trigger": {"type": "input_tokens", "value": 20000},
            "keep": {"type": "tool_uses", "value": 3},
        }]
    })
```

Run again:

```powershell
python context_editing.py
```

**What to look for — and record (this is curve #2):**
- The first several turns climb identically to Step 1. Then `cleared_tokens` becomes nonzero and `input_tokens` **stops climbing** — it flattens and hovers (only the 3 most-recent tool results plus the accumulating tool *calls* remain).
- Plot curve #1 vs curve #2 on the same axes (turn on X, input_tokens on Y). The linear climb vs the flattening plateau is the whole point of the feature.

> **Why clearing fires *later* than the trigger (a real exam point).** You'll notice the prompt crosses 20K around turn 3, but `cleared_tokens` stays 0 until ~turn 5. Crossing `trigger` is **necessary but not sufficient** — clearing also needs at least one tool result **older than the `keep` window** to remove. Trace it by how many results exist at each request:
>
> | turn | tool results in prompt | > trigger? | older than keep=3? | cleared |
> |------|------------------------|-----------|---------------------|---------|
> | 3 | 2 | yes | **no** — all 2 are within keep | 0 |
> | 4 | 3 | yes | **no** — exactly 3, all kept | 0 |
> | 5 | 4 | yes | **yes** — result #1 ages out | first clear |
>
> So `keep=3` protects everything until a 4th result exists. Takeaway: **`trigger` decides *if* clearing is allowed to run; `keep` decides *whether there's anything eligible* to clear.**

> **Why `cleared_tokens` keeps *growing* every turn** (10K → 20K → 31K …) instead of holding at ~10K: clearing is applied to the prompt you *send*, and this loop never prunes its own local `messages` — you resend the full, uncleared transcript each request. So the server re-strips everything older than the last 3 results *again* every turn (turn 6 strips 2 old pages, turn 7 strips 3, …). It's per-request "how much I removed from this prompt," and it climbs because the payload you hand it climbs. What matters — `input_tokens`, i.e. what the model actually processes — correctly stays flat (~32K). The tiny +~73 tokens/turn creep on that flat line is the retained tool **calls** (`clear_tool_inputs` defaults to `false`, so the `fetch_log(page=N)` invocations stay even after their results are stripped).

> **Why the plateau sits at ~32K, not lower:** the floor is `keep × page size` = 3 × ~10.6K. Lower `keep` (or smaller pages) → lower plateau. You'll exploit exactly this in Step 3.
- **RECALL** now **fails** — the model says it no longer has the anomaly detail. Result #2 was among the oldest and got cleared; `keep=3` only preserved results 18, 19, 20.

> Note `clear_tool_inputs` defaulted to `false`, so the model can still *see that it called* `fetch_log(page=2)` — it just can't see what came back. That's why it can say "I fetched it but no longer have the contents" rather than being oblivious.

---

## Step 3 — Find the retention boundary

The fact lives in result **#2** of **20**. Clearing keeps the **most-recent** `keep` results. So the fact survives to turn 20 only if `keep` reaches back to position 2 — i.e. `keep ≥ 19`. Prove the boundary by sweeping `keep`.

Temporarily wrap the run so you can try several values:

```python
    for k in (3, 10, 19):
        print(f"\n=== Step 3: keep={k} ===")
        run(context_management={
            "edits": [{
                "type": "clear_tool_uses_20250919",
                "trigger": {"type": "input_tokens", "value": 20000},
                "keep": {"type": "tool_uses", "value": k},
            }]
        })
```

Run it and read the RECALL line for each:

```powershell
python context_editing.py
```

**What to look for — and record:**
- `keep=3` → fact **lost**, curve flattens hard (aggressive clearing).
- `keep=10` → fact still **lost** (result #2 is older than the 10 kept), curve flattens later/less.
- `keep=19` → fact **survives**, but you've kept almost the entire transcript — you've barely saved any tokens.

**The tradeoff, stated plainly:** with the fact in the 2nd of 20 results, there is *no* clearing setting that both saves meaningful tokens **and** retains the fact. Recency-based clearing protects recent context at the cost of old context. If old context is load-bearing, `keep` is the wrong tool for protecting it.

---

## Step 4 — The real fix, and the production tie-in

`keep` protects by *recency*; the right lever for protecting *specific* context is **`exclude_tools`**. Design the agent so critical data arrives through a tool you never clear.

Sketch the design (you don't have to fully build it — reason it through):
- Split the tools: `fetch_log` (noisy, clearable) **and** `record_incident_fact` / `get_incident_summary` (the durable channel).
- Add `"exclude_tools": ["record_incident_fact"]` to the strategy. Now the anomaly fact, once recorded through that tool, is immune to clearing no matter how old it gets — while the log noise still gets pruned.

Then relate it to any **long-running agent** you operate:
- At 60+ tool calls, which results genuinely need to stay live for the *finalization* steps (the summary, the write-back, the decision)? Those should not be ordinary clearable `fetch`-style results.
- Everything else — intermediate page reads, exploratory queries — is safe to clear. Route durable facts through an excluded tool (or re-surface them right before finalization), and let clearing prune the rest.

---

## Key Observations to Record

| Step | What you proved |
|------|-----------------|
| Step 1 | No clearing → `input_tokens` climbs ~linearly with tool calls; long sessions get expensive and slow, and eventually hit the context window |
| Step 2 | `clear_tool_uses_20250919` prunes oldest tool results once `trigger` is crossed → per-turn `input_tokens` **flattens**; `applied_edits` reports `cleared_tool_uses` / `cleared_input_tokens` |
| Step 3 | Recency-based `keep` retains only the newest N results; a fact in an early result is lost unless `keep` spans back to it — the token-savings vs retention tradeoff |
| Step 4 | `exclude_tools` protects specific context by tool, independent of recency — the correct pattern for load-bearing finalization data |

**Key exam points:**

- Context editing **prunes** (deletes oldest tool results); compaction **summarizes**. Different mechanisms, different failure modes.
- `trigger` decides *when* clearing starts; `keep` decides *how much recent* survives; `clear_at_least` sets a floor on how much is removed; `exclude_tools` carves out protected tools; `clear_tool_inputs` (default false) keeps the tool *calls* even when results are cleared.
- **Crossing `trigger` doesn't guarantee a clear.** There must also be a tool result *older than the `keep` window* to remove — so clearing can start several turns after the threshold is first exceeded (`keep=3` protects everything until a 4th result exists). `trigger` = *is clearing allowed*; `keep` = *is anything eligible*.
- The per-request `cleared_input_tokens` can **grow every turn** when you resend the full transcript (the server re-strips all now-too-old results each request). Judge the benefit by the flat `input_tokens`, not by `cleared_tokens`. The plateau ≈ `keep × result size`.
- The dated identifier (`clear_tool_uses_20250919`) and beta header (`context-management-2025-06-27`) are copied from the docs, not memory — they change.
- Clearing is **not free of risk**: aggressive settings silently drop facts. Protect what finalization needs via `exclude_tools` or by re-surfacing it late, not by hoping it survives in the recent window.
- You can confirm what was dropped on any turn via `response.context_management.applied_edits`.

---

## Success Criteria

- [ ] Two token-per-turn curves — **without** clearing (linear climb) and **with** clearing (flattens after the trigger fires) — captured from the `input_tokens` column.
- [ ] You watched `cleared_tokens` go nonzero the turn the trigger fired, and saw `input_tokens` stop climbing.
- [ ] You found the `keep` boundary where the planted fact survives vs gets cleared (survives only at `keep ≥ 19` for a fact in result #2 of 20), and can explain the retention tradeoff in one sentence.
- [ ] You can name the correct mechanism for protecting load-bearing context (`exclude_tools` / a durable tool channel) rather than relying on recency.
- [ ] You can state the production implication: at 60+ calls, route finalization-critical facts through an excluded/durable channel and let clearing prune the exploratory noise.
