# D1L12 — Agent Design Judgment: Tiering, Error Contracts, Escalation

**Exam mapping:** when-to-build-an-agent, structured error context, escalation triggers (strategy sheet "Escalation", "Errors", "Wrong-answer tells")
**Estimated time:** ~40 min
**Domain:** 1 — Agentic Architecture & Orchestration (27%, highest weight)
**Key concept:** Three design decisions the exam traps you on. (1) **Tier**: not everything should be an agent — single call < workflow < agent, chosen by four criteria. (2) **Error contracts**: a tool failure must return *structured* context (category, retryable, partial results, what was attempted), never a generic string or a swallowed success. (3) **Escalation**: fire on **explicit signals**, never on sentiment-as-complexity or self-reported confidence.

> **How to use this lab:** three short parts, each an edit-run-observe cycle. You'll measure why over-agentifying wastes tokens, watch an agent recover from a structured error but flail on a generic one, and see a sentiment-based escalation rule fail the trap cases a signal-based rule passes.

---

## Facts to keep in front of you

- **The four criteria for "should this be an agent?"** — *complexity* (multi-step, hard to fully specify up front?), *value* (does the outcome justify higher cost/latency?), *viability* (is Claude actually good at this task?), *cost-of-error* (can mistakes be caught & recovered — tests, review, rollback?). If any answer is "no", drop to a simpler tier.
- **Tiers:** *single call* (classify/extract/summarize) → *workflow* (multi-step but you know the steps; code orchestrates) → *agent* (open-ended, model decides its own trajectory).
- **Structured error context** beats a generic message: `{category, retryable, partial_results, attempted}`. Generic `"Error"` and silent empty-result "success" are always wrong answers.
- **Escalation:** immediate on an **explicit** customer request; **sentiment is not complexity** (angry ≠ hard); **self-reported confidence** (the model's or the customer's) is an unreliable trigger.
- **Model:** `claude-sonnet-4-6` (Part 3 uses structured outputs; Sonnet 4.6 / Haiku 4.5 supported, cheap).

---

## Step 0 — Prereqs

```powershell
# From D1/D1L12.
$env:ANTHROPIC_API_KEY
python -c "import anthropic, pydantic; print('ok')"
New-Item -ItemType File design_judgment.py
```

---

## Part 1 — Tiering: don't agent-ify what a single call solves

First, the decision. Fill this in yourself before coding (answers below are the target):

| Task | Complexity | Fully specifiable? | Cost of error | Tier |
|------|-----------|--------------------|---------------|------|
| Extract one field from a PDF | low | yes | low | **single call** |
| Fetch → transform → write to DB (fixed steps) | medium | yes (you know the steps) | medium | **workflow** (code orchestrates) |
| "Refactor this repo to remove the deprecated API" | high | no (trajectory unknown) | high → needs tests/review | **agent** |

Now measure the cost of getting the tier wrong. Put this in `design_judgment.py`:

```python
import os, sys, json
from pydantic import BaseModel
import anthropic

MODEL = "claude-sonnet-4-6"

TRIVIAL = "Extract the invoice number from: 'Invoice INV-2024-00123 dated 2026-03-01, $500'. Reply with only the number."

# Agent scaffolding that a trivial task does NOT need — 5 tool schemas + an agent system prompt.
NEEDLESS_TOOLS = [
    {"name": f"tool_{i}", "description": f"Does operation {i} on some data.",
     "input_schema": {"type": "object", "properties": {"x": {"type": "string"}}, "required": ["x"]}}
    for i in range(5)
]
AGENT_SYSTEM = ("You are an autonomous agent. Plan, call tools as needed, reflect after each "
                "step, and iterate until the task is complete. " * 6)

if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Set ANTHROPIC_API_KEY first.")
    client = anthropic.Anthropic()

    print("=== Part 1: tier mismatch cost ===")
    # (a) right tier: single call
    a = client.messages.create(model=MODEL, max_tokens=32,
                               messages=[{"role": "user", "content": TRIVIAL}])
    print(f"  single call    input_tokens={a.usage.input_tokens:>4}  output={a.usage.output_tokens}")

    # (b) wrong tier: same task wrapped in agent scaffolding
    b = client.messages.create(model=MODEL, max_tokens=32, system=AGENT_SYSTEM,
                               tools=NEEDLESS_TOOLS,
                               messages=[{"role": "user", "content": TRIVIAL}])
    print(f"  agent-wrapped  input_tokens={b.usage.input_tokens:>4}  output={b.usage.output_tokens}")
    print(f"  overhead: {b.usage.input_tokens - a.usage.input_tokens} extra input tokens for the SAME answer")
```

Run it:

```powershell
python design_judgment.py
```

**What to look for — and record:**
- The agent-wrapped version costs materially more input tokens (system prompt + 5 tool schemas) **on turn one**, before any loop — and a real agent would add round trips on top. Same answer, pure overhead.
- The lesson isn't "agents are bad" — it's that the tier must match the task. A single call is the right tool for a specifiable one-shot; reserve the agent tier for open-ended, high-value work where the model must decide its own path.

---

## Part 2 — Error contracts: structured context enables recovery

Build one tool that fails, in two flavors, and feed each failure back to the model. Append:

```python
    print("\n=== Part 2: generic vs structured tool error ===")

    ACCOUNT_TOOL = [{
        "name": "lookup_account",
        "description": "Look up an account balance by account_id.",
        "input_schema": {"type": "object", "properties": {"account_id": {"type": "string"}},
                         "required": ["account_id"]},
    }]

    def tool_result_for(account_id, structured):
        # ACME-001 succeeds; anything else fails.
        if account_id == "ACME-001":
            return json.dumps({"balance": "$1,240.00"}), False
        if structured:
            return json.dumps({"error": {
                "category": "not_found", "retryable": False,
                "attempted": f"lookup_account(account_id={account_id!r})",
                "partial_results": None,
            }}), True
        return "Error", True     # generic

    def one_round(structured):
        user = "What's the balance on account ACME-999?"     # a nonexistent account
        r1 = client.messages.create(model=MODEL, max_tokens=400, tools=ACCOUNT_TOOL,
                                    messages=[{"role": "user", "content": user}])
        tu = next(b for b in r1.content if b.type == "tool_use")
        content, is_err = tool_result_for(tu.input["account_id"], structured)
        r2 = client.messages.create(model=MODEL, max_tokens=400, tools=ACCOUNT_TOOL, messages=[
            {"role": "user", "content": user},
            {"role": "assistant", "content": r1.content},
            {"role": "user", "content": [{"type": "tool_result", "tool_use_id": tu.id,
                                          "content": content, "is_error": is_err}]},
        ])
        return next((b.text for b in r2.content if b.type == "text"), "").strip()

    print("  GENERIC error -> model says:\n   ", one_round(structured=False))
    print("\n  STRUCTURED error -> model says:\n   ", one_round(structured=True))
```

Run again.

**What to look for — and record:**
- **Generic `"Error"`:** the model is vague — it may guess, propose blindly retrying the same call, or waffle. It has nothing to reason with.
- **Structured error:** the model reads `category: not_found` + `retryable: false` and responds precisely — *the account doesn't exist, retrying won't help, please provide a valid account_id*. The structure drove a correct decision (don't retry, ask for a fix).
- The exam's wrong answers live here: a generic message, or a tool that swallows the failure and returns an empty "success". Both hide the mechanism; structured error context exposes it.

---

## Part 3 — Escalation: signals, not sentiment

Classify each case's signals with structured output, then compare a sentiment-based rule against a signal-based one. Append:

```python
    print("\n=== Part 3: escalation triggers ===")

    class Signals(BaseModel):
        explicit_human_request: bool     # did they ask for a human / to escalate?
        sentiment: str                   # calm | frustrated | angry
        issue_complexity: str            # trivial | moderate | complex

    CASES = {
        "calm_explicit":  "Everything's working fine, but I'd like to speak to a human agent please.",
        "angry_trivial":  "This is ABSOLUTELY INFURIATING!!! Just tell me how to reset my password.",
        "polite_complex": "Hi! My invoices across three linked accounts don't reconcile with the "
                          "payments dashboard for the last two billing cycles — can you help?",
    }

    def classify(text):
        return client.messages.parse(model=MODEL, max_tokens=200,
            messages=[{"role": "user", "content": f"Extract escalation signals from: {text!r}"}],
            output_format=Signals).parsed_output

    def naive_rule(s):      # ANTI-PATTERN: escalate on sentiment
        return s.sentiment in ("frustrated", "angry")

    def signal_rule(s):     # escalate on explicit request; route (not escalate) on complexity; ignore sentiment
        if s.explicit_human_request:
            return "escalate (explicit request)"
        if s.issue_complexity == "complex":
            return "route to specialist"
        return "handle in-band"

    for name, text in CASES.items():
        s = classify(text)
        print(f"  {name:<14} signals={s.model_dump()}")
        print(f"       naive(sentiment): {'ESCALATE' if naive_rule(s) else 'no'}"
              f"   |   signal-based: {signal_rule(s)}")
```

Run the finished file.

**What to look for — and record:**
- **`calm_explicit`:** signal-based **escalates** (explicit request); the naive sentiment rule **misses it** (customer is calm). Explicit requests must escalate immediately regardless of tone.
- **`angry_trivial`:** naive rule **escalates** (angry) — wrong; it's a password reset. Signal-based **handles in-band**: sentiment ≠ complexity.
- **`polite_complex`:** signal-based **routes to a specialist** on complexity, not "escalate to human"; naive rule does nothing (not angry). And note: nowhere did either rule trust a *self-reported confidence* number — if you'd added "I'm 95% sure…", that's not a trigger.

---

## Key Observations to Record

| Part | What you proved |
|------|-----------------|
| Part 1 | Wrapping a trivial task in agent scaffolding adds real token overhead for no benefit; tier must match the task |
| Part 2 | Structured error context (`category`/`retryable`/`partial_results`/`attempted`) drives correct recovery; a generic string doesn't |
| Part 3 | Sentiment-based escalation both over- and under-fires; explicit-signal routing is correct; confidence scores aren't triggers |

**Key exam points:**

- **Not everything is an agent.** Single call < workflow < agent, chosen by complexity / value / viability / cost-of-error. Over-agentifying is a cost and reliability liability.
- **Errors return structured context**, never a generic message and never a swallowed empty-success. Include category, a `retryable` flag, partial results, and what was attempted.
- **Escalate on explicit signals.** Immediate on an explicit human request; sentiment is not a complexity proxy; self-reported confidence (model or customer) is unreliable. These are three distinct wrong-answer tells.

---

## Success Criteria

- [ ] A one-line tier justification per task (the three in Part 1's table) using the four criteria, with the token overhead of the mismatch measured.
- [ ] Demonstrated structured error context enabling a correct "don't retry, ask for a valid id" decision where the generic message produced vague/blind behavior.
- [ ] Escalation logic that escalates the calm-explicit case, does **not** escalate the angry-trivial case, routes the complex case, and never gates on a confidence score.
- [ ] You can name the four "should this be an agent?" criteria and the three escalation tells from memory.
