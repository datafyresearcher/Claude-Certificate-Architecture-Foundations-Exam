# D2L14 Answer Key — Scoped Tool Distribution & Parallel Execution

**Solution file:** `scoped_tools.py`.
Run `python scoped_tools.py` from this folder with `ANTHROPIC_API_KEY` set.

## Expected results

- **Step 1 (kitchen sink, 9 tools):** `input_tokens` is the same inflated number on every prompt — all 9 schemas ride at position 0 of every request. Clear prompts usually route right; the cross-domain "payments failing… money back" prompt is where picks wobble (e.g. `issue_refund` when the root cause is a devops outage), and may differ across runs.
- **Step 2 (router + scoped handlers):** handler calls carry only 3 schemas → visibly fewer input tokens; selection is confined to the routed domain, so cross-domain misfires become structurally impossible. Tradeoff: one extra cheap routing call; genuinely cross-domain work fans out to two handlers (the D1L10 pattern).
- **Step 3 (parallel):** default → **two** `get_invoice` `tool_use` blocks in one response; `disable_parallel_tool_use: true` → one block, extra turn for the second invoice.

## Success-criteria answers

- **Why scoped distribution is exam-preferred:** many loosely-related tools on one agent is a wrong-answer tell — it degrades selection (decision complexity) and taxes every request (schemas are input tokens on every call). Scoping gives each handler only its role's tools, which also structurally prevents out-of-role invocations.
- **Parallel-safety:** read-only lookups (`get_invoice`, `get_status`) are safe to parallelize; side-effecting tools (`issue_refund`, `restart_service`) are where you deliberately serialize or gate — a tool-design decision, not a model one.
