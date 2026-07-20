# D2L14 — Scoped Tool Distribution & Parallel Execution

**Exam mapping:** scoped tool distribution vs many-tools-on-one-agent, parallel tool calls (strategy sheet "wrong-answer tells")
**Estimated time:** ~35 min
**Domain:** 2 — Tool Design & MCP Integration (18%)
**Key concept:** Piling many loosely-related tools onto one agent degrades selection and inflates every request (all schemas ride in context). The exam-preferred pattern is **scoped distribution** — route to a specialized handler that holds only the 2–3 tools its job needs. Separately: Claude can call tools **in parallel** (multiple `tool_use` in one response), which you can force off with `disable_parallel_tool_use`.

> **How to use this lab:** build a "kitchen-sink" agent, watch its selection wobble and its token cost, then refactor to a router + scoped handlers and compare. Finish by observing parallel tool calls.

---

## What you're proving

1. Many tools on one agent → less reliable selection on ambiguous prompts, and **every call pays for all schemas**.
2. A router that dispatches to a scoped handler (2–3 tools) constrains selection to the right domain and shrinks per-call tokens.
3. Multiple `tool_use` blocks can arrive in one response (parallel); `disable_parallel_tool_use` serializes them.

---

## Facts to keep in front of you

- **"Many tools on one agent" is a wrong-answer tell.** The exam prefers **scoped distribution**: give each agent/handler only the tools relevant to its role.
- Tool schemas render at **position 0** of every request and count as input tokens on *every* call — a 9-tool agent pays that overhead each turn even when one tool would do.
- **Parallel tool use:** one assistant message may contain several `tool_use` blocks; return one `tool_result` per `tool_use_id` in a single user turn. `tool_choice={"type":"auto","disable_parallel_tool_use":True}` caps at one per response. Read-only tools are the safe ones to parallelize.
- **Model:** `claude-sonnet-4-6` (tool use + structured output for the router; cheap).

---

## Step 0 — Prereqs

```powershell
# From D2/D2L14.
$env:ANTHROPIC_API_KEY
python -c "import anthropic, pydantic; print('ok')"
New-Item -ItemType File scoped_tools.py
```

---

## Step 1 — The kitchen-sink agent

Nine tools across three unrelated domains, one agent, ambiguous prompts. Put this in `scoped_tools.py`:

```python
import os, sys
from pydantic import BaseModel
import anthropic

MODEL = "claude-sonnet-4-6"


def tool(name, desc, *props):
    return {"name": name, "description": desc,
            "input_schema": {"type": "object",
                             "properties": {p: {"type": "string"} for p in props},
                             "required": list(props)}}

BILLING = [tool("get_invoice", "Fetch an invoice by id.", "invoice_id"),
           tool("issue_refund", "Refund a charge.", "charge_id"),
           tool("get_balance", "Get an account balance.", "account_id")]
DEVOPS  = [tool("restart_service", "Restart a service.", "service"),
           tool("tail_logs", "Fetch recent logs for a service.", "service"),
           tool("get_status", "Get service health status.", "service")]
HR      = [tool("lookup_pto", "Look up remaining PTO for an employee.", "employee_id"),
           tool("submit_expense", "Submit an expense.", "amount"),
           tool("get_policy", "Fetch an HR policy document.", "topic")]
ALL = BILLING + DEVOPS + HR

PROMPTS = [
    "A customer is furious about being double-charged last month.",   # billing
    "The checkout page is throwing errors for everyone.",             # devops
    "How much vacation do I have left this year?",                    # hr
    "Payments keep failing and customers are demanding their money back.",  # cross-domain
]


def picks(tools, prompt):
    r = client.messages.create(model=MODEL, max_tokens=200, tools=tools,
                               tool_choice={"type": "any"},   # force a choice so we can see routing
                               messages=[{"role": "user", "content": prompt}])
    chosen = [b.name for b in r.content if b.type == "tool_use"]
    return chosen, r.usage.input_tokens


if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Set ANTHROPIC_API_KEY first.")
    client = anthropic.Anthropic()

    print("=== Step 1: kitchen-sink agent (9 tools) ===")
    for p in PROMPTS:
        chosen, toks = picks(ALL, p)
        print(f"  picked={chosen!s:<28} input_tokens={toks:<4} | {p}")
```

Run it:

```powershell
python scoped_tools.py
```

**What to look for — and record:**
- `input_tokens` is the **same, inflated** number on every prompt — all 9 schemas ride along even when one tool is relevant.
- Selection on the clear prompts is usually right, but watch the **cross-domain** prompt ("payments failing… money back") — the model may pick a billing tool (`issue_refund`) when the root cause is a devops outage, or oscillate run to run. With nine overlapping options and a vague stem, the pick is less stable. Record what it chose across two runs.

---

## Step 2 — Scoped distribution: route, then hand over 3 tools

Add a cheap router (structured output) that classifies the domain, then dispatch to only that domain's tools. Append:

```python
    print("\n=== Step 2: router + scoped handlers (3 tools each) ===")

    class Route(BaseModel):
        domain: str      # billing | devops | hr

    HANDLERS = {"billing": BILLING, "devops": DEVOPS, "hr": HR}

    def router(prompt):
        return client.messages.parse(model=MODEL, max_tokens=60,
            messages=[{"role": "user", "content":
                f"Classify this request's primary domain (billing, devops, or hr): {prompt!r}"}],
            output_format=Route).parsed_output.domain

    for p in PROMPTS:
        domain = router(p)
        tools = HANDLERS.get(domain, ALL)
        chosen, toks = picks(tools, p)
        print(f"  route={domain:<8} picked={chosen!s:<20} input_tokens={toks:<4} | {p}")
```

Run again.

**What to look for — and record:**
- The handler's `input_tokens` is **noticeably smaller** than the kitchen-sink's — it only carries 3 schemas.
- Selection is now confined to the right domain, so cross-domain misfires are structurally impossible: the router sends the "payments failing" case to its primary domain, and the handler picks from a coherent set. (Note the tradeoff: routing is one extra cheap call, and a genuinely cross-domain task may need the orchestrator to fan out to two handlers — which is the D1L10 pattern.)
- Record both token numbers and the routing decisions.

---

## Step 3 — Parallel tool calls

Give the model a prompt that needs two independent reads and watch how many `tool_use` blocks come back. Append:

```python
    print("\n=== Step 3: parallel tool_use vs serialized ===")
    prompt = "Fetch invoice INV-100 and invoice INV-200."
    for label, choice in [("parallel (default)", {"type": "auto"}),
                          ("serialized", {"type": "auto", "disable_parallel_tool_use": True})]:
        r = client.messages.create(model=MODEL, max_tokens=300, tools=BILLING,
                                   tool_choice=choice,
                                   messages=[{"role": "user", "content": prompt}])
        calls = [(b.name, b.input) for b in r.content if b.type == "tool_use"]
        print(f"  {label:<20} tool_use blocks in ONE response: {len(calls)} -> {calls}")
```

Run the finished file.

**What to look for — and record:**
- **Parallel (default):** two `get_invoice` `tool_use` blocks in a **single** response (one for INV-100, one for INV-200). You'd return both `tool_result`s in one user turn.
- **`disable_parallel_tool_use: True`:** just **one** `tool_use` block — the model must take another turn for the second invoice (serialized).
- `get_invoice` is read-only, so parallelizing is safe. A write tool like `issue_refund` is where you'd *want* serialization/gating — a tool-design decision, not a model one.

---

## Key Observations to Record

| Step | What you proved |
|------|-----------------|
| Step 1 | One agent, 9 tools: every call pays for all schemas; selection wobbles on ambiguous/cross-domain prompts |
| Step 2 | Router + scoped handler: fewer tokens per call, selection confined to the right domain, no cross-domain misfire |
| Step 3 | Parallel `tool_use` (multiple blocks per response) vs `disable_parallel_tool_use` (one per response); read-only tools are safe to parallelize |

**Key exam points:**

- **Scoped tool distribution beats many-tools-on-one-agent** — the latter is a wrong-answer tell. Give each agent/handler only the tools its role needs.
- Tool schemas are input tokens on **every** request (they render at position 0); a bloated tool set is a per-call tax and a selection hazard.
- A cheap router/classifier that dispatches to specialized handlers is the standard scoping pattern; genuinely cross-domain work fans out to multiple handlers (D1L10).
- **Parallel tool_use** reduces round trips for independent reads; `disable_parallel_tool_use` forces one tool per response. Parallelize read-only tools; serialize/gate side-effecting ones.

---

## Success Criteria

- [ ] Documented the kitchen-sink agent's constant inflated `input_tokens` and at least one unstable/suboptimal pick on the cross-domain prompt.
- [ ] Showed the scoped handler using fewer tokens and selecting only within the routed domain.
- [ ] Observed parallel `tool_use` (two blocks in one response) and forced serialization with `disable_parallel_tool_use`.
- [ ] You can explain why scoped distribution is the exam-preferred pattern and which tools are safe to parallelize.
