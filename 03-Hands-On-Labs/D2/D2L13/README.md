# D2L13 — Tool Definitions That Trigger Correctly

**Exam mapping:** tool description quality / when-to-call, `tool_choice` modes, enums + `strict` (ties to Lab 2)
**Estimated time:** ~35 min
**Domain:** 2 — Tool Design & MCP Integration (18%)
**Key concept:** Claude decides *whether* to call a tool almost entirely from its **description**. A vague description ("gets information") makes the model under- or over-trigger; a description that is **prescriptive about *when* to call** fixes the routing. `tool_choice` is the deterministic override, and `strict: true` guarantees the *arguments* match your schema.

> **How to use this lab:** build it yourself. You'll watch the same tool trigger differently based on one field — its description — then see what each `tool_choice` value forces, then confirm `strict` locks the argument shape.

---

## What you're proving

1. Tool triggering is driven by the **description**; improving it (state *when* to call, and when **not** to) changes the trigger rate on identical prompts.
2. `tool_choice` (`auto` / `any` / `{type:"tool"}` / `none`) is the deterministic control over tool use.
3. `strict: true` + an `enum` guarantees valid argument values (the arg-shape half of tool design; depth in D4L2).

---

## Facts to keep in front of you

- **Description = the routing logic.** Claude reads it to decide when a tool applies. Be **prescriptive about the trigger condition** ("Call this when the user asks about X"), not just what the tool does. On recent Opus/Sonnet models — which reach for tools more conservatively — an explicit trigger condition gives measurable lift.
- **`tool_choice` values:** `{"type":"auto"}` (model decides — default), `{"type":"any"}` (must use *some* tool), `{"type":"tool","name":"..."}` (must use that one), `{"type":"none"}` (cannot use tools). Add `"disable_parallel_tool_use": true` to cap at one tool per response.
- **`strict: true`** validates arguments against the schema (enums, types, `required`, `additionalProperties:false`) — no drifted or invented values. Description controls *whether* to call; strict controls *how the args come out*.
- **Model:** `claude-sonnet-4-6` (tool use; cheap). Sonnet 4.5 / Opus 4.8 also fine.

---

## Step 0 — Prereqs

```powershell
# From D2/D2L13.
$env:ANTHROPIC_API_KEY
New-Item -ItemType File tool_design.py
```

---

## Step 1 — Description drives triggering

Define the *same* tool twice — vague vs prescriptive — and run a mix of prompts where some should call it and some shouldn't. Put this in `tool_design.py`:

```python
import os, sys
import anthropic

MODEL = "claude-sonnet-4-6"

VAGUE = {
    "name": "search_kb",
    "description": "Gets information.",
    "input_schema": {"type": "object", "properties": {"query": {"type": "string"}},
                     "required": ["query"]},
}
PRECISE = {
    "name": "search_kb",
    "description": ("Search the company's INTERNAL knowledge base — HR policies, benefits, "
                    "and internal procedures. Call this whenever the user asks about "
                    "company-specific policies or internal processes. Do NOT call it for "
                    "general knowledge, math, or coding — answer those directly."),
    "input_schema": {"type": "object", "properties": {"query": {"type": "string"}},
                     "required": ["query"]},
}

PROMPTS = [
    ("should call",     "What is our company's parental leave policy?"),
    ("should call",     "How do I submit an expense report here?"),
    ("should NOT call", "What is the capital of France?"),
    ("should NOT call", "Write a haiku about autumn."),
    ("should NOT call", "What is 17 * 23?"),
]


def called(tool):
    hits = 0
    for expect, prompt in PROMPTS:
        r = client.messages.create(model=MODEL, max_tokens=200, tools=[tool],
                                   tool_choice={"type": "auto"},
                                   messages=[{"role": "user", "content": prompt}])
        used = any(b.type == "tool_use" for b in r.content)
        hits += used
        print(f"  [{expect:<14}] tool_used={str(used):<5} | {prompt}")
    print(f"  -> tool called on {hits}/5 prompts\n")


if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Set ANTHROPIC_API_KEY first.")
    client = anthropic.Anthropic()

    print("=== Step 1a: VAGUE description ===")
    called(VAGUE)
    print("=== Step 1b: PRECISE description ===")
    called(PRECISE)
```

Run it:

```powershell
python tool_design.py
```

**What to look for — and record:**
- **Vague:** triggering is inconsistent — it may fire on general-knowledge prompts ("capital of France") or miss the policy questions. "Gets information" doesn't tell the model *when* the tool is relevant.
- **Precise:** it calls on the two internal-policy prompts and stays off the three general ones. The only thing you changed was the description — the routing followed it.
- Record the two trigger counts (e.g. vague 3/5 with wrong ones, precise 2/5 on the right ones). Run twice — the vague version is also less *stable* run to run.

---

## Step 2 — `tool_choice` is the deterministic override

Take one prompt and cycle all four modes. Append:

```python
    print("=== Step 2: tool_choice modes on one prompt ===")
    prompt = "What is the capital of France?"          # a 'should NOT call' prompt
    for choice in ({"type": "auto"}, {"type": "any"},
                   {"type": "tool", "name": "search_kb"}, {"type": "none"}):
        r = client.messages.create(model=MODEL, max_tokens=150, tools=[PRECISE],
                                   tool_choice=choice,
                                   messages=[{"role": "user", "content": prompt}])
        used = any(b.type == "tool_use" for b in r.content)
        text = next((b.text for b in r.content if b.type == "text"), "")
        print(f"  {str(choice):<45} stop={r.stop_reason:<10} tool_used={used}  {text[:40]!r}")
```

Run again.

**What to look for — and record:**
- `auto` → **no** tool (answers "Paris" directly — correct routing).
- `any` → **forces** a tool call even though it's pointless here (`stop_reason=tool_use`).
- `{type:tool,name}` → forces that specific tool.
- `none` → **cannot** call the tool; answers in text.
- Takeaway: description shapes the *default* (`auto`) behavior; `tool_choice` is how you deterministically force or forbid, independent of the description.

---

## Step 3 — `strict` locks the argument shape

Description decides *whether* to call; `strict` decides *how clean the arguments are*. Reuse the routing enum and compare. Append:

```python
    print("\n=== Step 3: enum drift without strict, locked with strict ===")
    ROUTE = {
        "name": "route_ticket",
        "description": "Route a support ticket to a team.",
        "input_schema": {
            "type": "object",
            "properties": {"category": {"type": "string",
                            "enum": ["billing", "technical", "account", "other"]}},
            "required": ["category"], "additionalProperties": False,
        },
    }
    TICKETS = ["I was charged twice", "the app crashes on startup", "reset my 2FA", "do you support SSO?"]

    def route(strict):
        tool = {**ROUTE, "strict": strict}
        for t in TICKETS:
            r = client.messages.create(model=MODEL, max_tokens=120, tools=[tool],
                                       tool_choice={"type": "tool", "name": "route_ticket"},
                                       messages=[{"role": "user", "content": f"Route: {t}"}])
            cat = next((b.input.get("category") for b in r.content if b.type == "tool_use"), None)
            in_enum = cat in ROUTE["input_schema"]["properties"]["category"]["enum"]
            print(f"    strict={strict!s:<5} category={cat!r:<14} in_enum={in_enum} | {t}")

    route(strict=False)
    print()
    route(strict=True)
```

Run the finished file.

**What to look for — and record:**
- Values should stay inside the enum in both runs for a well-behaved model, but `strict=True` is the **guarantee** — with `strict` the API constrains generation to the schema, so a drifted case (`"Billing"`, `"tech"`, an invented category) is impossible, not just unlikely.
- This is the tool-design counterpart to D4 Lab 2 (which drills strict/enum for structured output). Here the point is: a good tool needs **both** a prescriptive description (right trigger) **and** strict args (right values).

---

## Key Observations to Record

| Step | What you proved |
|------|-----------------|
| Step 1 | The description is the routing logic — prescriptive "call this when…" phrasing fixes under/over-triggering on identical prompts |
| Step 2 | `tool_choice` deterministically overrides: `auto` (decide), `any` (some tool), `{type:tool}` (that tool), `none` (no tool) |
| Step 3 | `strict: true` guarantees arguments match the schema/enum — description ≠ argument validity, you need both |

**Key exam points:**

- Claude decides tool use from the **description** — vague descriptions are the root cause of "the skill/tool didn't trigger" (and of over-triggering). Fix the description, not the prompt around it.
- Be **prescriptive about the trigger condition** and about when *not* to call.
- `tool_choice`: `auto` / `any` / `{type:"tool","name"}` / `none`; `disable_parallel_tool_use` caps at one call/response.
- `strict: true` + `enum` + `additionalProperties:false` guarantees valid argument values; it does not affect *whether* the tool is chosen.

---

## Success Criteria

- [ ] The same tool, vague vs precise description, showing different (and more stable) triggering on identical prompts.
- [ ] You can state what each `tool_choice` value forces, confirmed by observation.
- [ ] You confirmed `strict: true` constrains arguments to the enum, and can explain how description (whether-to-call) and strict (how-args-come-out) are separate design levers.
