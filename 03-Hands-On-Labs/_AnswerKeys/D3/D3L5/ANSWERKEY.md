# D3L5 Answer Key — Enforcement, Not Exhortation

This folder holds the **worked artifacts** from a completed run of the lab. Recreate them in the lab folder (`D3/D3L5/`) yourself; use these to compare.

## Artifacts

| File | Role |
|------|------|
| `CLAUDE.md` | The text-only rule (Step 1) — intentionally weak; observe it bending under persuasion |
| `infra/prod/config.yaml` | The file the policy protects |
| `.claude/settings-sample-deny.json` | Step 2 — the permissions **deny rule** variant for edits under `infra/prod/**` |
| `.claude/settings.json` | Steps 3–4 — **PreToolUse** hook (blocks `infra/prod/` edits) + **PostToolUse** hook (formatter), both matched to `Edit\|Write\|MultiEdit` |
| `.claude/hooks/pre-tool-block.ps1` | Reads the hook JSON from stdin, matches the path against `infra/prod/`, blocks with a deny decision and logs to `hook-activity.log` |
| `.claude/hooks/post-tool-format.ps1` | Runs Black on every edited Python file |
| `.claude/hooks/hook-activity.log` | Evidence: every invocation and every BLOCKED event, timestamped |
| `src/app.py` | Scratch file for the PostToolUse formatting runs |

## Expected observations

- **Step 1 (CLAUDE.md only):** the rule holds for casual asks but **bends** under persuasive framing ("approved emergency change") — prose is probabilistic guidance, not enforcement.
- **Step 2 (deny rule):** the edit is rejected deterministically before execution, every time, regardless of prompt framing.
- **Step 3 (PreToolUse):** the hook blocks the call and its stderr/deny message is fed back to Claude, which explains it cannot edit the file. Check `hook-activity.log` for the BLOCKED lines.
- **Step 4 (PostToolUse):** five edits to `src/app.py` → five formatter runs, zero prompt instructions involved.

## Success-criteria answers

- **Where each intervenes:** a settings deny rule is evaluated by the permission system before the tool runs; a PreToolUse hook is your own code at the same boundary (exit 2 / deny decision blocks, stderr goes back to the model) — use hooks when you need logic or logging, deny rules for simple path/tool patterns.
- **One-sentence articulation:** CLAUDE.md is the right tool for conventions and guidance Claude should *usually* follow; it is categorically the wrong tool the moment the requirement contains MUST/NEVER — that's what permissions and hooks are for.
