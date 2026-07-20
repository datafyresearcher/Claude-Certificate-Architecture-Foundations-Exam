# D5L9 Answer Key — stop_reason Handling + Compaction Contract

**Solution files:** `stop_reason_recovery.py` (truncation demo + recovery handler) and `compaction-test/CLAUDE.md` (the custom compaction instructions used in Step 4). Build your own in `D5/D5L9/` per its README; compare against these.

## Expected results — stop_reason (`stop_reason_recovery.py`)

- **Forced truncation:** `max_tokens: 200` on a large extraction → `stop_reason == "max_tokens"` and JSON that ends mid-object. Parsing it raises — proving "the response looked done" is not a contract.
- **Recovery handler:** on `max_tokens`, never parse; re-request with a raised limit (or continue the generation) and parse the complete object. Before/after demonstration recovers the full extraction.
- **The value table your code must implement:** end_turn → done; max_tokens → truncated (recover, never parse); tool_use → execute + append result + continue; refusal → surface, don't blind-retry; pause_turn → re-send to resume (server tools).

## Expected results — compaction contract (Claude Code, Step 4)

- **Default `/compact`:** the explicitly rejected approach ("do not use X, it fails on Y") tends to **resurrect** after compaction — the default summary may not preserve rejected approaches or user constraints. (If it held for you, keep the summary text as evidence; the point is it's not guaranteed.)
- **Instructed compaction** (see `compaction-test/CLAUDE.md`): telling the summarizer to preserve verbatim all hard constraints, every rejected approach with its reason, and key decisions keeps X dead post-compaction.
- **The contract to memorize** — a good compaction summary preserves: task overview, current state, important discoveries (including failed/rejected approaches), next steps, and context to preserve (user constraints). When compaction loses information, fix the summary contract, not the schedule.
