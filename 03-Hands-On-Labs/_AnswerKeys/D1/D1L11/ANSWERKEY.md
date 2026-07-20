# D1L11 Answer Key — The Agent Loop Done Right

**Solution file:** `agent_loop.py`. It parametrizes Step 4 (`run(..., serialize=True)`) so no manual edit is needed.
Run `python agent_loop.py` from this folder with `ANTHROPIC_API_KEY` set.

## Expected output (abridged)

```
=== Step 1 ===
  turn 1: stop_reason=tool_use          tool_use: get_weather({'city': 'Paris'}) -> 18°C, cloudy
  turn 2: stop_reason=end_turn
ANSWER: The weather in Paris is 18°C and cloudy.

=== Step 2a (anti-pattern) ===
  turn 1: stop_reason=tool_use | text_has_'done'=True     <- fires EARLY on narration
RESULT: [stopped because text looked final]               <- or runs to cap when phrasing differs

=== Step 2b ===
  turn 1: stop_reason=tool_use ...
RESULT: [hit iteration backstop — investigate, don't treat as normal]   <- incomplete work

=== Step 3 ===  finishes on end_turn with the full comparison.

=== Step 4 ===
-- parallel:  turn 1 shows ~4 tool_use lines (weather+population × Paris+Tokyo) in ONE response
-- serialized: one tool_use per turn; more turns for the same data
```

## Success-criteria answers

- **stop_reason contract:** `tool_use` → execute every block, return one `tool_result` per `tool_use_id` in a single user turn, continue; `end_turn` → done; `pause_turn` → re-send the assistant turn (server tools); `max_tokens` → truncated, never parse (D5L9); `refusal` → surface, don't blind-retry.
- **Why NL-parsing is a tell:** the sentinel is a guess about prose — absent when the loop should end, present when it shouldn't (the model narrates "let me get the weather... done"). `stop_reason` is unambiguous every turn.
- **Why cap-as-stop is a tell:** too low → silently returns incomplete work; a stuck loop → the cap masks the bug as a normal exit. The cap is a loud backstop (an error path to investigate), never the mechanism.
- **Parallel tool use:** multiple `tool_use` blocks can arrive in one assistant message; all results go back in one user turn. `disable_parallel_tool_use` forces one per response. Read-only lookups are parallel-safe; side-effecting tools are where serialization is a deliberate design choice (D2L14).
