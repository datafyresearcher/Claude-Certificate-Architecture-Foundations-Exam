# D1L11 — The Agent Loop Done Right

**Exam mapping:** `stop_reason`-driven control flow, no NL parsing / no iteration-cap-as-stop, `tool_use` / `pause_turn`, parallel `tool_use` (strategy sheet "wrong-answer tells")
**Estimated time:** ~40 min
**Domain:** 1 — Agentic Architecture & Orchestration (27%, highest weight)
**Key concept:** An agent loop's control flow is driven by **`stop_reason`**, not by reading the model's prose. Terminating a loop by scanning text for "done", or by hitting a fixed iteration cap, are two of the exam's most reliable wrong-answer tells. The cap is a *safety backstop*, never the mechanism.

> **How to use this lab:** build the canonical loop, then deliberately break it the two ways the exam punishes, watch each fail, and fix it back to `stop_reason`-driven control. Then observe parallel tool calls.

---

## What you're proving

1. The correct loop advances on `stop_reason`: `tool_use` → execute & continue; `end_turn` → stop.
2. Terminating on natural-language cues ("done"/"finished") is unreliable — the signal is absent when you need it and present when you don't.
3. An iteration cap as the *primary* stop either cuts work short or masks a stuck loop.
4. Claude can emit **multiple `tool_use` blocks in one response** (parallel); you return all `tool_result`s in a single user turn. `disable_parallel_tool_use` forces serialization.

---

## Facts to keep in front of you

`stop_reason` is the loop's only reliable control signal. Each value has a fixed action:

| `stop_reason` | Loop action |
|---|---|
| `tool_use` | Execute every `tool_use` block, append the assistant turn, append one `tool_result` per block in a single user turn, continue |
| `end_turn` | Done — break |
| `pause_turn` | Server-tool loop paused — re-send the assistant turn to resume (no "continue" text). Only occurs with server-side tools (web search, code execution) |
| `max_tokens` | Truncated — raise the cap / stream, don't treat as done (see D5L9) |
| `refusal` | Terminal — surface it, don't retry blindly |

- **Prose is for humans, `stop_reason` is for control.** Never parse the model's text to decide the loop is finished.
- **Parallel tool calls:** one assistant message can contain several `tool_use` blocks. Return a `tool_result` for **each** `tool_use_id`, all in **one** following user turn. `tool_choice={"type":"auto","disable_parallel_tool_use":True}` caps it at one tool per response.
- **Iteration cap = backstop.** Keep a generous cap to prevent a runaway from burning your budget, but the loop should almost always exit via `end_turn`, not the cap.
- **Model:** plain tool use, no structured outputs — `claude-sonnet-4-6` is fine and cheap (Sonnet 4.5 or Opus 4.8 work too).

---

## Step 0 — Prereqs

```powershell
# From D1/D1L11.
$env:ANTHROPIC_API_KEY
New-Item -ItemType File agent_loop.py
```

---

## Step 1 — Build the canonical loop

Two independent client tools (so Step 4 can trigger a parallel call) and a `stop_reason`-driven loop. Put this in `agent_loop.py`:

```python
import os
import sys
import anthropic

MODEL = "claude-sonnet-4-6"

TOOLS = [
    {
        "name": "get_weather",
        "description": "Get the current weather for a city. Call this when the user asks about weather.",
        "input_schema": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    },
    {
        "name": "get_population",
        "description": "Get the population of a city. Call this when the user asks about population or size.",
        "input_schema": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    },
]

WEATHER = {"paris": "18°C, cloudy", "tokyo": "24°C, clear", "cairo": "33°C, sunny"}
POP = {"paris": "2.1M", "tokyo": "13.9M", "cairo": "10.0M"}


def execute(name, args):
    city = args.get("city", "").strip().lower()
    if name == "get_weather":
        return WEATHER.get(city, "unknown")
    if name == "get_population":
        return POP.get(city, "unknown")
    return f"unknown tool {name}"


def run(user_msg, max_iters=10):
    messages = [{"role": "user", "content": user_msg}]
    for i in range(1, max_iters + 1):
        resp = client.messages.create(
            model=MODEL, max_tokens=1024, tools=TOOLS, messages=messages,
        )
        print(f"  turn {i}: stop_reason={resp.stop_reason}")

        if resp.stop_reason == "end_turn":
            return next((b.text for b in resp.content if b.type == "text"), "")

        if resp.stop_reason == "pause_turn":          # server-tool pause; resume by re-sending
            messages.append({"role": "assistant", "content": resp.content})
            continue

        if resp.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": resp.content})
            tool_results = []
            for block in resp.content:
                if block.type == "tool_use":
                    result = execute(block.name, block.input)
                    print(f"           tool_use: {block.name}({block.input}) -> {result}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,     # MUST match the tool_use block's id
                        "content": result,
                    })
            messages.append({"role": "user", "content": tool_results})
            continue

        # max_tokens / refusal / anything else: terminal for this simple loop
        return f"[stopped on {resp.stop_reason}]"

    return "[hit iteration backstop — investigate, don't treat as normal]"


if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Set ANTHROPIC_API_KEY first.")
    client = anthropic.Anthropic()

    print("=== Step 1: canonical stop_reason-driven loop ===")
    answer = run("What's the weather in Paris?")
    print("ANSWER:", answer)
```

Run it:

```powershell
python agent_loop.py
```

**What to look for — and record:**
- Turn 1 prints `stop_reason=tool_use` and a `get_weather(Paris)` call; turn 2 prints `stop_reason=end_turn` and you get the answer.
- The loop never inspected the model's words to decide what to do — it branched purely on `stop_reason`.

---

## Step 2 — Break it two ways and watch it fail

### 2a — Terminate by parsing natural language

Add an anti-pattern loop that stops when the assistant text contains a sentinel:

```python
def run_nl_parse(user_msg, max_iters=6):
    messages = [{"role": "user", "content": user_msg}]
    for i in range(1, max_iters + 1):
        resp = client.messages.create(model=MODEL, max_tokens=1024, tools=TOOLS, messages=messages)
        text = " ".join(b.text for b in resp.content if b.type == "text").lower()
        print(f"  turn {i}: stop_reason={resp.stop_reason} | text_has_'done'={'done' in text or 'here' in text}")

        # ANTI-PATTERN: decide termination from prose, ignoring stop_reason
        if "done" in text or "here" in text or "the weather" in text:
            return "[stopped because text looked final]"

        # still have to advance tools or we deadlock
        if resp.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": resp.content})
            messages.append({"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": b.id, "content": execute(b.name, b.input)}
                for b in resp.content if b.type == "tool_use"]})
    return "[ran to cap without a text match]"
```

```python
    print("\n=== Step 2a: NL-parse termination (anti-pattern) ===")
    print("RESULT:", run_nl_parse("What's the weather in Paris?"))
```

Run and compare to Step 1. **What to look for — and record:**
- The `text_has_'done'` column is either **False when the loop should end** (the real final answer may not contain your sentinel) or **True on an intermediate turn** (the model narrates "let me get the weather…" and the scan fires early). Either way the sentinel is a guess. Different phrasings, different runs → different behavior. `stop_reason` was unambiguous every time.

### 2b — Iteration cap as the primary stop

Call the good loop but starve it:

```python
    print("\n=== Step 2b: iteration cap as the stop mechanism ===")
    print("RESULT:", run("Compare the weather AND population of Paris and Tokyo.", max_iters=1))
```

**What to look for — and record:**
- With `max_iters=1` the loop returns the backstop string **before** `end_turn` — the task needed at least two turns (tool calls, then synthesis), so a cap-as-stop design silently returns **incomplete** work. Bump `max_iters` back to 10 and the same task finishes on `end_turn`.
- The mirror failure (not shown, but state it): if the model got stuck calling tools forever, a cap would "stop" it and mask the bug as a normal exit. The cap should be a loud backstop you investigate, not a silent terminator.

---

## Step 3 — Fix: stop_reason primary, cap as backstop

Step 1's `run()` is already the fix. Confirm the contract in your notes:
- **Primary terminator:** `stop_reason == "end_turn"`.
- **Advance:** `stop_reason == "tool_use"` (execute all blocks) / `pause_turn` (re-send).
- **Backstop only:** the `for i in range(max_iters)` cap exists to bound a runaway; reaching it is an *error path* ("investigate"), not the normal exit.

Re-run the comparison prompt on the good loop to see it finish properly:

```python
    print("\n=== Step 3: same task, correct loop ===")
    print("ANSWER:", run("Compare the weather AND population of Paris and Tokyo."))
```

---

## Step 4 — Parallel tool calls

The comparison prompt needs four independent lookups. Watch how many `tool_use` blocks land per turn, then force serialization.

You already saw the parallel version in Step 3 — count the `tool_use:` lines under turn 1. Now add a serialized variant by editing the `create` call in a copy of `run` (or temporarily add `tool_choice` to `run`'s call):

```python
        resp = client.messages.create(
            model=MODEL, max_tokens=1024, tools=TOOLS, messages=messages,
            tool_choice={"type": "auto", "disable_parallel_tool_use": True},   # <- add this
        )
```

Run the comparison prompt both ways.

**What to look for — and record:**
- **Parallel (default):** turn 1 shows **multiple `tool_use` blocks in one response** (e.g. `get_weather(Paris)`, `get_weather(Tokyo)`, `get_population(Paris)`, `get_population(Tokyo)`), and you return all their `tool_result`s in one user turn. Fewer round trips.
- **`disable_parallel_tool_use: True`:** at most **one** `tool_use` per response — the loop takes more turns to gather the same data (serialized).
- Note which tools are safe to parallelize: read-only lookups (`get_weather`, `get_population`) are; a write/side-effecting tool usually is not — that's a tool-design decision (see D2L14).

---

## Key Observations to Record

| Step | What you proved |
|------|-----------------|
| Step 1 | The loop branches on `stop_reason` alone: `tool_use` → act, `end_turn` → stop |
| Step 2a | NL-parse termination misfires — the sentinel is absent when needed, present when not |
| Step 2b | A cap-as-stop returns incomplete work (too low) or masks a stuck loop (as a fake normal exit) |
| Step 3 | Correct contract: `stop_reason` primary, iteration cap is a loud backstop only |
| Step 4 | Multiple `tool_use` blocks can arrive in one response; return one `tool_result` per id in one turn; `disable_parallel_tool_use` serializes |

**Key exam points:**

- **Loop termination = check `stop_reason`.** Never parse natural language for "done"; never rely on an iteration cap as the primary stop. Both are classic wrong-answer tells.
- Each `stop_reason` maps to one action: `tool_use` (execute + continue), `end_turn` (stop), `pause_turn` (re-send to resume — server tools), `max_tokens` (don't parse; raise/stream), `refusal` (surface).
- **Parallel tool_use:** one assistant turn may hold several `tool_use` blocks; every `tool_use_id` needs a matching `tool_result`, all returned in a single user message.
- The iteration cap is a **safety backstop**; hitting it is an error condition to investigate, not a clean exit.

---

## Success Criteria

- [ ] A loop that terminates on `stop_reason`, handles multiple `tool_use` blocks per turn, and never inspects prose to decide it's done.
- [ ] You reproduced the NL-parse misfire and the cap-cuts-work-short failure, with the turn-by-turn `stop_reason` log as evidence.
- [ ] You observed parallel `tool_use` (multiple blocks in one response) and forced serialization with `disable_parallel_tool_use`.
- [ ] You can recite the action for each `stop_reason` value and explain why iteration caps / NL parsing are wrong-answer tells.
