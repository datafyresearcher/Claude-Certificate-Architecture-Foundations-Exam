# D4 Answer Key — Labs 1–3 (Prompt Engineering & Structured Output)

Worked reference scripts for the three D4 labs. Build your own in `D4/` following `D4/README.md`; use these to compare or unblock.

## Solution files

| File | Lab | Proves |
|------|-----|--------|
| `D4L1.py` | Lab 1 | Structured outputs (`output_config.format`) guarantee parseable shape; the citations/prefill incompatibilities; format-change cache behavior |
| `D4L2.py` | Lab 2 | Enum drift without `strict` (note the deliberately mixed-case enum bait), clean values with `strict: true`; strict tool + JSON output combinable in one request |
| `D4L3.py` | Lab 3A | Example-diversity effect: 5 same-category few-shots bias the classifier; a diverse set recovers accuracy |
| `D4L3-pt3.py` | Lab 3B | Validation-retry loop: deterministic business-rule validation, errors fed back for a corrected second attempt |

Run each with `python <file>` from this folder (`ANTHROPIC_API_KEY`, `anthropic`, `pydantic` required). Lab 3C (Console prompt improver + eval) is manual — no script.

## Expected results per toggle (see `D4/README.md` for the toggle instructions)

- **L1 prompt-only baseline:** a nonzero `json.loads` failure rate (preambles, fences, trailing commas); restoring `output_config` → zero failures.
- **L1 prefill toggle:** assistant-prefill + structured outputs don't coexist (400 on current models).
- **L1 citations toggle:** citations + `output_config.format` in one request → **400** error body.
- **L1 format change:** `cache_read_input_tokens` collapses when the schema changes between calls.
- **L2:** at least one drifted category without strict (or note your inputs didn't drift — unlikely ≠ impossible is the point); exact-enum values with strict; tool + `output_config.format` both operate in one request.
- **L3A:** biased prompt over-predicts `billing`; diverse prompt recovers accuracy — record the delta.
- **L3B:** the intentionally malformed invoice fails attempt 1 validation and is recovered on attempt 2.

## The recall set (memorize)

citations + `output_config.format` = 400 · prefill + JSON outputs = incompatible · strict tool + JSON outputs = combinable · format change mid-thread = cache invalidation · structured outputs guarantee shape, not semantics (business rules need a validation loop) · `stop_reason: "max_tokens"` breaks JSON even under structured outputs.
