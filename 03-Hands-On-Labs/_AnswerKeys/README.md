# Lab Answer Keys

Worked solutions and reference outputs for all 15 labs, mirrored by domain/lab. **Attempt each lab first** from its README in the lab folder; come here to unblock yourself or to compare results. The discrimination the exam tests is built by observing the behavior yourself, not by reading a key.

## Map

| Key | Contents |
|-----|----------|
| `D1/D1L10/` | `ANSWERKEY.md` + `orchestrator.py` (orchestrator-worker isolation & provenance) |
| `D1/D1L11/` | `ANSWERKEY.md` + `agent_loop.py` (stop_reason-driven loop, parallel tool use) |
| `D1/D1L12/` | `ANSWERKEY.md` + `design_judgment.py` (tiering, error contracts, escalation) |
| `D2/D2L13/` | `ANSWERKEY.md` + `tool_design.py` (descriptions, tool_choice, strict) |
| `D2/D2L14/` | `ANSWERKEY.md` + `scoped_tools.py` (scoped distribution, parallel execution) |
| `D2/D2L15/` | `ANSWERKEY.md` (expected CLI transcript, sample `.mcp.json`, scopes & auth) |
| `D3/D3L4/` | `ANSWERKEY.md` + worked artifacts (marker CLAUDE.md files, @import, fixed skill) |
| `D3/D3L5/` | `ANSWERKEY.md` + worked artifacts (deny-rule settings, PreToolUse/PostToolUse hooks, activity log) |
| `D3/D3L6/` | `ANSWERKEY.md` + worked artifacts (two-stage pipeline scripts, self vs isolated review outputs) |
| `D4/` | `ANSWERKEY.md` + the four solution scripts for Labs 1–3 |
| `D5/D5L7/` | `ANSWERKEY.md` + `cache_forensics.py` (caching signatures) |
| `D5/D5L8/` | `ANSWERKEY.md` + `context_editing.py` (tool-result clearing) |
| `D5/D5L9/` | `ANSWERKEY.md` + `stop_reason_recovery.py` + `compaction-test/` (truncation recovery, compaction contract) |

All Python keys expect `ANTHROPIC_API_KEY` set and `pip install anthropic pydantic`. Scripts make real (cheap) API calls; exact outputs vary run to run — the ANSWERKEY.md files state what should hold invariantly.
