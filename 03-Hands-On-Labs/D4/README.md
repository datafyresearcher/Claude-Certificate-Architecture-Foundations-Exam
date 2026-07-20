# D4 — Prompt Engineering & Structured Output (Labs 1–3)

**Exam mapping:** structured outputs vs prompt-level JSON, feature incompatibilities, `strict` tools & enum drift, few-shot diversity, validation-retry, format-change cache invalidation (drill Q1–Q4)
**Estimated time:** ~2 hours across the three labs
**Domain:** 4 — Prompt Engineering & Structured Output (20%)
**Key concept:** A *guarantee* of valid JSON comes from `output_config.format` (structured outputs) and `strict: true` tools — **not** from asking nicely in the prompt. Prompt-level discipline (few-shot examples, "respond only with JSON") improves the odds; it never removes the failure mode. This domain is about knowing which lever is a guarantee and which is a nudge.

> **How to use this folder:** build the scripts yourself following the steps below (worked reference copies — `D4L1.py`, `D4L2.py`, `D4L3.py`, `D4L3-pt3.py` — live in `../_AnswerKeys/D4/`). This README maps each script to the master-guide lab, tells you what to run and observe, and gives the **toggles** that trigger the incompatibilities the exam tests. Full lab framing is in `../domain-labs.md` (Labs 1–3).

---

## Facts to keep in front of you

- **`output_config.format`** (JSON schema) constrains the *response*; **`strict: true`** constrains a *tool's arguments*. Both are guarantees; both are combinable in one request.
- **Supported models:** Fable 5, Opus 4.8, Sonnet 4.6, Haiku 4.5 (+ legacy Opus 4.5/4.1). These scripts use `claude-sonnet-4-6` and `claude-haiku-4-5-20251001` — both fine. **Not Sonnet 4.5** (not on the list).
- **Hard incompatibilities (exam gold):**
  - **Citations + `output_config.format` → 400** error.
  - **Assistant prefill + structured outputs → incompatible** (prefill removed entirely on Sonnet 4.6 / Opus 4.8 anyway).
  - **`strict` tool + `output_config.format` → combinable** in one request (this one *works*).
- **Schema constraints:** every object needs `additionalProperties: false`; numeric/string constraints (`minimum`, `maxLength`, …) aren't enforced server-side (SDK strips + validates client-side). Pydantic `.model_json_schema()` needs the `additionalProperties:false` patch (the scripts do this).
- **Two different caches:** structured outputs have a **24-hour schema-compilation cache** (first request with a new schema pays a one-time compile latency); separately, **prompt caching** is prefix-based — changing the request's output format/schema between calls means the affected portion is no longer a cache hit. Confirm with the `usage` numbers, don't assume.
- **`max_tokens` truncation still applies:** `stop_reason: "max_tokens"` yields incomplete JSON even with structured outputs (see D5L9).

---

## Step 0 — Prereqs

```powershell
# From D4.
$env:ANTHROPIC_API_KEY
python -c "import anthropic, pydantic; print('ok')"
```

---

## Lab 1 — Structured outputs & incompatibilities (`D4L1.py`)

**Proves:** structured outputs guarantee shape; the citations/prefill incompatibilities; and that changing the schema affects caching.

Run it as-is:

```powershell
python D4L1.py
```

It extracts `{vendor, amount, due_date}` via `output_config.format`, `json.loads` the result (no parsing failures), and prints `cache_creation_input_tokens` / `cache_read_input_tokens`.

**Observe, then work these toggles** (each maps to a master-guide Lab 1 step):

1. **Prompt-only baseline (master step 1).** The script jumps straight to structured outputs. To *feel* the failure it removes, temporarily comment out the `output_config=...` argument and add "Respond only with valid JSON." to the user turn; run ~20 varied inputs and count `json.loads` failures (preamble text, markdown fences, trailing commas). Then restore `output_config` → zero failures. That before/after is the point.
2. **Prefill incompatibility (master step 3).** Uncomment the assistant-prefill turn (`{"role":"assistant","content":"{"}`) alongside `output_config`. Record what happens — prefill + structured outputs don't coexist (and prefill is 400 on Sonnet 4.6 outright).
3. **Citations incompatibility.** Add a `document` block with `"citations": {"enabled": True}` to the user content in the same request as `output_config.format`. Record the **400** error body.
4. **Format-change vs cache (master step 4).** The script mutates the schema (adds a property description) before the call. Run twice: once with the mutation, once without — or with two genuinely different schemas — and compare `cache_read_input_tokens`. Note whether the read collapses when the format changes.

**Success criteria:**
- [ ] Measured a nonzero prompt-only failure rate and a zero structured-outputs rate.
- [ ] Can recite both incompatibilities (citations → 400, prefill) and describe the actual error/behavior you saw.
- [ ] Observed the cache-read behavior across a format change in the usage numbers.

---

## Lab 2 — Strict tool use & enum drift (`D4L2.py`)

**Proves:** enum drift without `strict`, clean values with `strict`, and that a strict tool + `output_config.format` run together.

Note the deliberately **mixed-case enum** in the script: `["Billing", "technical", "Account", "other"]`. That casing inconsistency is bait for drift.

Run it as-is (strict is commented out):

```powershell
python D4L2.py
```

It routes 15 tickets, logging each `category` the tool produced.

**Toggles:**
1. **Baseline drift.** With `"strict": True` commented out, scan the logged categories for drift — a value that doesn't exactly match an enum entry, casing mismatches, or an invented category. Record any.
2. **Turn on strict.** Uncomment `"strict": True` and rerun. Diff the logs — values are now constrained to the exact enum set.
3. **Combined features.** The script already sends `output_config.format` (a `RoutingResult` schema) *and* the tool in one request — confirm both operate: the tool call is logged **and** the final response conforms. This is the "strict tool + JSON outputs = combinable" exam point.

**Success criteria:**
- [ ] Captured at least one drifted value without strict (or can explain why your inputs didn't drift), and clean values with strict.
- [ ] Ran a strict tool and `output_config.format` together in one request successfully.

---

## Lab 3 — Few-shot diversity & validation-retry (`D4L3.py`, `D4L3-pt3.py`)

### Part A — Example-diversity effect (`D4L3.py`)

**Proves:** a few-shot set that's all one category biases the classifier; a diverse set (one per category + an edge case) fixes it.

```powershell
python D4L3.py
```

It scores 20 mixed-category tickets under a **biased** prompt (5 all-`billing` examples) then a **diverse** prompt, and prints both accuracies plus the delta.

**Observe:** the biased prompt over-predicts `billing`; the diverse prompt recovers accuracy. Record the before/after numbers — this is drill Q4's failure-and-fix.

### Part B — Validation-retry loop (`D4L3-pt3.py`)

**Proves:** a self-correction chain — validate the parsed object against business rules, and on failure send the errors back for a corrected object.

```powershell
python D4L3-pt3.py
```

It extracts `{vendor, amount, due_date}`, validates (amount > 0, due_date parses as ISO-8601, vendor non-empty), and on failure feeds the specific errors back for a second attempt. It prints attempt-1 passes vs attempt-2 recoveries. One test invoice is intentionally malformed (empty vendor, bad date, negative amount) to force the retry.

**Observe:** attempt 2 recovers at least one attempt-1 failure. Note that validation is *your* deterministic business logic — structured outputs guarantee the *shape*, not that `amount > 0` or the date is real.

### Part C — Console tooling (manual, master step 4)

Paste your final classifier/extraction prompt into the **Console prompt improver**, diff its output against yours, then run both through the **Console evaluation tool** on ~10 test cases. Record one concrete change the improver made and whether the eval justified it.

**Success criteria:**
- [ ] Reproduced example-induced bias and fixed it with diversity (before/after numbers).
- [ ] A working validation-retry loop where attempt 2 recovers an attempt-1 failure.
- [ ] Articulated one change the Console prompt improver made and whether the eval justified it.

---

## Key exam points

- **Guarantee vs nudge:** `output_config.format` / `strict:true` *guarantee* shape and argument validity; prompts, few-shot examples, and "respond only with JSON" only improve odds. When the question says "guarantee", "never invalid", "must", the answer is the structured mechanism.
- **Incompatibilities:** citations + `output_config.format` → 400; prefill + structured outputs → incompatible; strict tool + JSON output → combinable. Memorize which combine and which error.
- **Structured outputs don't validate semantics** — shape only. Business rules (positive amount, real date, non-empty vendor) need a validation-retry loop.
- **Few-shot diversity:** the model mimics your examples; a lopsided example set induces exactly that bias. Cover categories, lengths, and an edge case.
- **Truncation:** `stop_reason: "max_tokens"` breaks JSON even under structured outputs — check `stop_reason` before parsing (D5L9).
- Enum casing/spelling must be exact and consistent; `strict` is what enforces it.

---

## Success Criteria (domain-level)

- [ ] You can state, for any "must produce valid JSON / valid category" scenario, whether the fix is structured outputs, a strict tool, both, or a validation loop — and why prompt wording alone is the wrong answer.
- [ ] You have observed: zero-failure structured extraction, a real incompatibility error, enum drift fixed by strict, few-shot bias fixed by diversity, and an attempt-2 recovery.
- [ ] You can recite the three incompatibility rules (citations/prefill/strict-with-JSON) from memory.
