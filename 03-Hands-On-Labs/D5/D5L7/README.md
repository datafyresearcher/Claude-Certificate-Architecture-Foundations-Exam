# D5L7 — Prompt Caching Forensics

**Exam mapping:** prefix-based caching, `cache_control` breakpoints, invalidation signatures (drill Q12, Q3)
**Estimated time:** ~35 min
**Domain:** 5 — Context Management & Reliability
**Key concept:** Caching is a **prefix match**. Any byte change in the prefix invalidates every breakpoint at or after it. Stable content goes first; volatile content (timestamps, IDs, the varying question) goes last.

> **How to use this lab:** build it yourself, one step at a time. Each step below is a small edit-and-run cycle where you *observe* a usage number change. The scar tissue comes from watching `cache_read_input_tokens` collapse to zero and then recover — not from reading about it.

---

## What you're proving

| Term | Meaning |
|------|---------|
| `cache_creation_input_tokens` | Tokens **written** to cache this request (you paid the ~1.25× write premium for the 5-min TTL) |
| `cache_read_input_tokens` | Tokens **served** from cache this request (you paid ~0.1×) |
| `input_tokens` | Uncached tokens processed at full price |

The whole lab is reading these three numbers off `response.usage` and reasoning about *why* they moved.

---

## Facts to keep in front of you (Opus 4.8)

These are the load-bearing details — verify each against what you observe:

- **Render order is `tools` → `system` → `messages`.** A `cache_control` breakpoint on the last system block caches everything before it (tools + system).
- **Prefix match.** The cache key is the exact bytes up to each breakpoint. One changed byte at position N kills every breakpoint at position ≥ N.
- **Minimum cacheable prefix on Opus 4.8 is 4096 tokens.** Below that, nothing caches — *silently*. No error, just `cache_creation_input_tokens: 0`. That's why Step 1 builds a deliberately large (~5K+ token) system prompt.
  - **Cheaper models work fine** — this whole lab runs on Sonnet 4.5 / Sonnet 4.6 / Haiku 4.5 too. Just note the floor differs (Sonnet 4.5 = 1024, Sonnet 4.6 = 2048, Haiku 4.5 = 4096); the ~5K prompt clears all of them. Keep the model **constant** across a run — caches are model-scoped, so switching mid-run invalidates them.
- **`cache_control: {"type": "ephemeral"}`** = 5-minute TTL (default). **`{"type": "ephemeral", "ttl": "1h"}`** = 1 hour (~2× write premium instead of 1.25×).
- **Max 4 breakpoints** per request.
- **Prompt caching is GA** — no beta header, plain `client.messages.create(...)`.
- **Model:** `claude-opus-4-8`.

---

## Step 0 — Prereqs

```powershell
# From the D5L7 folder. Confirm the key and SDK are available.
$env:ANTHROPIC_API_KEY   # should print your key (set it if blank)
python -c "import anthropic; print(anthropic.__version__)"
```

Create an empty file to work in:

```powershell
New-Item -ItemType File cache_forensics.py
```

You'll grow this file across the steps below.

---

## Step 1 — Build a stable prefix and prove the warm hit

The first job is a system prompt **large enough to cache** (above the 4096-token floor) whose bytes are **identical** on every call. Repetition is fine — caching keys on exact bytes, not on novel content.

Put this at the top of `cache_forensics.py`:

```python
import os
import sys
from datetime import datetime, timezone

import anthropic

MODEL = "claude-opus-4-8"

# One deterministic paragraph, repeated ~60x -> comfortably above Opus 4.8's 4096-token floor.
_PARAGRAPH = (
    "Section {n}: Claims-processing policy. Every submitted invoice is validated against "
    "the vendor master list before payment is scheduled. The extracted vendor name, total "
    "amount, and due date must each pass a business rule: amount strictly positive, due "
    "date parses as ISO-8601, and vendor resolves to a known, non-terminated supplier. "
    "Rejected records route to a human reviewer with the failing rule attached, never "
    "silently dropped. This is stable reference context, reused verbatim across requests."
)
STABLE_SYSTEM = "\n\n".join(_PARAGRAPH.format(n=i) for i in range(1, 61))


def system_blocks(volatile_prefix: str = ""):
    """System prompt as a single cached text block.

    volatile_prefix (if given) is prepended to the TOP -> it lands BEFORE the breakpoint
    in the prefix, so it changes the cache key on every call. This is the Step 2 trap.
    """
    text = STABLE_SYSTEM
    if volatile_prefix:
        text = f"{volatile_prefix}\n\n{STABLE_SYSTEM}"
    return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]


def call(label, system, user):
    resp = client.messages.create(
        model=MODEL,
        max_tokens=64,  # output doesn't matter; we only read input-side usage
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    u = resp.usage
    print(f"  {label:<24} created={u.cache_creation_input_tokens:>6}  "
          f"read={u.cache_read_input_tokens:>6}  input={u.input_tokens:>5}")
    return u


if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Set ANTHROPIC_API_KEY first.")
    client = anthropic.Anthropic()

    print("Step 1 - warm hit (identical prefix twice):")
    call("call 1 (cold write)", system_blocks(), "Summarize the policy in one line.")
    call("call 2 (warm read)",  system_blocks(), "Summarize the policy in one line.")
```

Run it:

```powershell
python cache_forensics.py
```

**What to look for — and record:**
- **Call 1:** `created` is a big number (the whole system prompt got written), `read` is 0.
- **Call 2:** `created` is 0, `read` is that same big number. **This is the warm hit.**

> **If call 2 shows `read=0` and `created=0`:** your prefix is under 4096 tokens — the block never cached. Bump the `range(1, 61)` upper bound and rerun. This *is* the "silent floor" the exam tests.

> **Why the 5-minute TTL matters here:** the two calls run back-to-back, well inside the default window, so the entry is still alive for call 2. If you paused ~6 minutes between them, call 2 would miss.

---

## Step 2 — Kill the cache with a volatile prefix

Now prepend a changing timestamp to the **top** of the system prompt. Because it sits *before* the breakpoint, the prefix bytes differ on every call — every request becomes a fresh write and reads collapse to zero.

Add a helper and a second block to `__main__`:

```python
def now_stamp():
    return f"Current time: {datetime.now(timezone.utc).isoformat()}"
```

```python
    print("\nStep 2 - prefix-mutation kill (timestamp prepended to system prompt):")
    for i in range(1, 4):
        call(f"call {i} (volatile top)", system_blocks(now_stamp()),
             "Summarize the policy in one line.")
```

Run again:

```powershell
python cache_forensics.py
```

**What to look for — and record:**
- All three Step 2 calls show `read=0` and a nonzero `created` every time.
- Compare to Step 1 call 2: same prompt body, but a single mutating line at the front destroyed reuse.

**Say it in one sentence (exam framing):** *"Cache reads went to zero immediately after a deploy"* → something volatile (a build timestamp, a version string, a per-request UUID) landed **in the prefix**, so the cache key changes on every request.

---

## Step 3 — Recover by moving volatile content after the breakpoint

Same timestamp, different placement: put it in the **user turn**, after the cached system block. The system prefix is now byte-identical to Step 1, so these calls should **read from Step 1's cache entry**.

Add the final block:

```python
    print("\nStep 3 - recovery (timestamp moved into the user turn):")
    call("call 1 (warm read)", system_blocks(),
         f"{now_stamp()}\n\nSummarize the policy in one line.")
    call("call 2 (warm read)", system_blocks(),
         f"{now_stamp()}\n\nSummarize the policy in one line.")
```

Run one more time:

```powershell
python cache_forensics.py
```

**What to look for — and record:**
- Both Step 3 calls show a nonzero `read` again, even though each request still contains a unique timestamp.
- The volatile content didn't go away — it moved **downstream of the breakpoint**, so it no longer changes the cached prefix.

> **Timing caveat:** Step 3 reads from the entry Step 1 wrote. If more than ~5 minutes elapsed since Step 1 in this run, the entry may have expired and Step 3 call 1 will show a fresh `created` instead — then call 2 reads it. Either way the recovery pattern holds; just run Steps 1 and 3 within the same 5-minute window.

---

## Step 4 (bonus) — TTL expiry vs prefix mutation

Two different ways a cache "goes cold" — learn their **different signatures**:

1. **Prefix mutation (Step 2):** reads drop to zero **immediately and permanently** for that shape. It's not about time — the key changed.
2. **TTL expiry:** the *same* key simply ages out after no traffic for the TTL window.

To observe expiry:
- Run Step 1 once (warm write).
- Wait past the default TTL with no traffic (~6 minutes).
- Run Step 1's two calls again. Call 1 now shows a fresh `created` (the old entry expired), not a `read`.

Then try the 1-hour TTL — change the breakpoint in `system_blocks`:

```python
    return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral", "ttl": "1h"}}]
```

The entry now survives a 6-minute gap (at ~2× the write premium instead of 1.25×). This is the knob for bursty traffic with idle gaps.

---

## Key Observations to Record

| Step | What you proved |
|------|-----------------|
| Step 1 | An identical, large-enough prefix produces a cold **write** then a warm **read** — `cache_read_input_tokens` jumps on call 2 |
| Step 2 | One mutating line **at the top** of the prefix forces a fresh write every call — `read` stays 0 |
| Step 3 | Moving the volatile content **after** the breakpoint restores reads, even with unique per-call content |
| Step 4 | Prefix mutation kills the cache **instantly**; TTL expiry ages the same key out over **time** — distinct signatures |

**Key exam points:**

- Caching is a **prefix match**; render order is `tools` → `system` → `messages`.
- Stable content first, volatile content (timestamps, UUIDs, the varying question) **after the last breakpoint**.
- Silent invalidators to grep for: `datetime.now()` in the system prompt, unsorted `json.dumps()`, a per-user/per-request ID early in content, a tool set that varies per request.
- Below the model's minimum prefix (4096 tokens on Opus 4.8) nothing caches — **silently**.
- `{"type": "ephemeral"}` = 5-min TTL (~1.25× write); `{"ttl": "1h"}` = 1-hour (~2× write); reads cost ~0.1×.
- Changing tools or the model invalidates the **entire** cache (tools render at position 0; caches are model-scoped).

---

## Success Criteria

- [ ] A four-row table of usage numbers proving: **warm hit**, **prefix-mutation kill**, and **recovery** after moving volatile content.
- [ ] You watched `cache_read_input_tokens` go from a large number (Step 1 call 2) → 0 (Step 2) → back to a large number (Step 3).
- [ ] You can diagnose *"cache reads went to zero immediately after a deploy"* in one sentence (volatile content entered the cached prefix).
- [ ] You can state the difference between a prefix-mutation miss (instant, key changed) and a TTL-expiry miss (time-based, same key aged out).
