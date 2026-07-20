# D5L7 Answer Key — Prompt Caching Forensics

**Solution file:** `cache_forensics.py` (build your own in `D5/D5L7/` per its README; compare against this one).
Run `python cache_forensics.py` with `ANTHROPIC_API_KEY` set.

## Expected usage-number table

| Call | Setup | cache_creation | cache_read | Signature |
|------|-------|----------------|------------|-----------|
| 1 | stable system prompt behind `cache_control` | large | 0 | cache write |
| 2 | identical request, <1 min later | 0 | large | **warm hit** |
| 3–5 | timestamp prepended to TOP of system prompt | large each call | ~0 | **prefix-mutation kill** — every request has a new prefix |
| 6+ | timestamp moved into the user turn (after the stable block) | 0 | large | **recovery** |

Bonus: after the TTL passes with no traffic, the *first* call re-creates (gradual, expected) — distinct from the immediate zero of prefix mutation.

## Success-criteria answers

- **The one-sentence diagnosis:** "cache reads went to zero immediately after a deploy" = something newly volatile entered the cached prefix (prefix mutation); gradual misses over time = TTL expiry.
- **Design rule:** prompt caching is prefix-based — stable content first, volatile content (timestamps, request IDs, user data) after the breakpoint, ideally in the user turn.
- Related exam fact from D4L1: changing `output_config.format` mid-thread is also a cache-invalidating change.
