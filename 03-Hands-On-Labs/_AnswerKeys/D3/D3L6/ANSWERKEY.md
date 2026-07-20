# D3L6 Answer Key — Headless CI with Generator/Reviewer Isolation

This folder holds the **worked artifacts** from a completed run of the lab. Recreate them in the lab folder (`D3/D3L6/`) yourself; use these to compare.

## Artifacts

| File | Role |
|------|------|
| `src/module.py` | The seeded module with two planted bugs (an off-by-one and a swallowed exception) |
| `src/generated.py` | Code produced by the pipeline's generation stage |
| `review-pipeline.ps1` | The two-stage script: Stage 1 `claude -p` generates; Stage 2 reviews in a **fresh** session (only the code text passed, no generation context); exits 1 on blocking findings |
| `compare-review.ps1` | Side-by-side comparison of self-review vs isolated review finding counts |
| `review-self.jsonl` | Same-session self-review output ("no significant issues" territory) |
| `review-isolated.jsonl` | Fresh-session independent review output (more/realer findings) |
| `pipeline-gen-*.jsonl`, `pipeline-review-*.jsonl`, `review-output.jsonl` | Raw `--output-format json` envelopes from pipeline runs |

## Expected observations

- **JSON envelope:** `claude -p "…" --output-format json` returns a `result`-type object with `result`, `session_id`, `total_cost_usd`, `duration_ms`, `is_error` — parse this, never scrape transcripts.
- **Self-review vs isolated:** the same code reviewed in the generating session yields fewer findings (the model retains its own generation reasoning and re-derives the same conclusions); the fresh headless session finds more, including the planted bugs. Record the count difference from the two jsonl files.
- **Pipeline contract:** stage 2 receives only the diff/code text; blocking findings fail the pipeline via exit code.

## Success-criteria answers

- **The supported automation contract:** `-p` (non-interactive) + `--output-format json` (machine-readable). Anything that parses conversational text is the trap.
- **Why isolation matters:** independence beats intensity — an adversarial prompt in the same session still shares the generator's biased context; a fresh instance with only the code is the documented review pattern.
- **CI extras worth knowing:** add `--bare` for fast, reproducible scripted runs (skips CLAUDE.md/hooks/skills/MCP auto-discovery) and pre-approve just what the job needs, e.g. `--allowedTools "Read,Grep,Glob"`.
