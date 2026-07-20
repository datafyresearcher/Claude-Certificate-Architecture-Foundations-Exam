# D5L8 Answer Key — Context Editing Under Tool-Call Load

**Solution file:** `context_editing.py` (build your own in `D5/D5L8/` per its README; compare against this one).
Run `python context_editing.py` with `ANTHROPIC_API_KEY` set. Note: the dated strategy identifier (`clear_tool_uses_20250919`) and beta header are copied from the context-editing docs page — they change; re-copy, don't trust memory.

## Expected results

- **No clearing:** `input_tokens` climbs roughly linearly across 20+ `fetch_log` calls.
- **With tool-result clearing:** once `trigger` is crossed *and* a result is older than the `keep` window, oldest results are pruned; the per-turn `input_tokens` curve **flattens** (plateau ≈ `keep` × result size). `response.context_management.applied_edits` reports what was cleared.
- **Planted-fact recall (fact in result #2 of 20):** `keep=3` → lost; `keep=10` → lost; `keep=19` → survives but nearly nothing was saved. With an early load-bearing fact, no recency setting both saves tokens and retains it.
- **The real fix:** `exclude_tools` — route durable facts through a tool that clearing never touches (or re-surface them right before finalization), and let clearing prune the exploratory noise.

## Success-criteria answers

- **Parameter roles:** `trigger` = when clearing is allowed; `keep` = how many recent results survive; `clear_at_least` = removal floor; `exclude_tools` = protected tools; `clear_tool_inputs` (default false) = whether the calls themselves are stripped too.
- **The retention tradeoff in one sentence:** recency-based clearing protects recent context at the cost of old context, so anything old *and* load-bearing must be protected by mechanism (`exclude_tools` / durable channel), not by hoping it stays inside the window.
- **Editing vs compaction:** context editing *prunes* (deletes old tool results); compaction *summarizes* (D5L9). Different mechanisms, different failure modes.
