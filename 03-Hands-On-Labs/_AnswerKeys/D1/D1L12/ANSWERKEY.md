# D1L12 Answer Key — Agent Design Judgment

**Solution file:** `design_judgment.py`.
Run `python design_judgment.py` from this folder with `ANTHROPIC_API_KEY` set.

## Part 1 — Tiering table (the target answers)

| Task | Complexity | Fully specifiable? | Cost of error | Tier |
|------|-----------|--------------------|---------------|------|
| Extract one field from a PDF | low | yes | low | **single call** |
| Fetch → transform → write to DB (fixed steps) | medium | yes | medium | **workflow** (code orchestrates) |
| "Refactor this repo off the deprecated API" | high | no | high (needs tests/review) | **agent** |

Expected measurement: the agent-wrapped call costs several hundred extra input tokens (system prompt + 5 tool schemas) on turn one, for the identical answer — before a single loop iteration. The four criteria: **complexity, value, viability, cost-of-error**; any "no" drops you a tier.

## Part 2 — Error contracts

- **Generic `"Error"`:** the model waffles, guesses, or proposes retrying the identical call — it has nothing to reason with.
- **Structured `{category: not_found, retryable: false, attempted, partial_results}`:** the model concludes precisely: the account doesn't exist, retrying won't help, please supply a valid account_id. Correct recovery decision driven by structure.
- Exam wrong answers: generic messages, and tools that swallow failure into an empty "success".

## Part 3 — Escalation (expected verdicts)

| Case | naive (sentiment) rule | signal-based rule | Correct |
|------|------------------------|-------------------|---------|
| calm_explicit ("speak to a human please") | no ✗ | escalate (explicit request) | signal-based |
| angry_trivial (furious password reset) | ESCALATE ✗ | handle in-band | signal-based |
| polite_complex (3-account reconciliation) | no | route to specialist | signal-based |

Three tells to memorize: escalate **immediately on explicit request**; **sentiment ≠ complexity**; **self-reported confidence is not a trigger**.
