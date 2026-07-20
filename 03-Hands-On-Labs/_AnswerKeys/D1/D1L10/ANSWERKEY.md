# D1L10 Answer Key — Orchestrator-Worker: Isolation & Provenance

**Solution file:** `orchestrator.py` (the fully assembled script from all four README steps).
Run `python orchestrator.py` from this folder with `ANTHROPIC_API_KEY` set.

## Expected output (abridged)

```
=== Step 1: no context passed (subagents inherit nothing) ===
  finding:    No incident log evidence was provided, so no anomaly can be identified.
  source:     none / no evidence received
  confidence: 0.05                     <- or a confident hallucination; both prove the point

=== Step 2: explicit context passing ===
  [logs] (0.95) Disk on db-7 filled to 100% at 03:14:02Z, rejecting writes...  <- source: incident log
  [config_diff] (0.92) Log rotation was removed 21 days ago...                 <- source: config diff

=== Step 3: context isolation vs monolith ===
  worker[logs] input_tokens: ~60      | worker[config_diff] input_tokens: ~55
  monolith    input_tokens: ~130      <- carries every blob at once

=== Step 4: quarantine + provenance-preserving synthesis ===
  VERIFIED FINDINGS: (two findings, each with source + confidence)
  QUARANTINED (excluded from synthesis, not dropped):
    - timeline: low confidence (0.10)
  ROOT CAUSE: log rotation removal (config_diff) filled db-7's disk, causing writes_rejected at 03:14Z (logs).
```

## Success-criteria answers

- **No-inheritance proof:** the Step 1 worker cannot answer ("the evidence I gave you" is empty across the process boundary) — a subagent is a fresh `messages.create` conversation with no shared memory, history, or system prompt.
- **Fix:** pass every needed fact explicitly in the worker's prompt; return a structured `{finding, source, confidence}` so the handoff is auditable.
- **Isolation payoff:** each worker's `input_tokens` covers only its slice; the monolith carries all slices — and in a real investigation grows without bound. The orchestrator only ever sees short findings.
- **Quarantine:** the empty-evidence `timeline` worker lands in the quarantined list *with a reason*, and is excluded from synthesis. Silent omission is the honeypot ("just skip the ones that errored") because a missing finding reads as a clean result.
- **One-sentence answer:** quarantine-with-provenance keeps the failure visible and traceable; skipping errored workers hides a coverage gap inside a confident-looking synthesis.
