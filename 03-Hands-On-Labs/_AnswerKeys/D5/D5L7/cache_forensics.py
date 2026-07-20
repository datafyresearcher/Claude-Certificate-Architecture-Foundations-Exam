import os
import sys
from datetime import datetime, timezone

import anthropic

MODEL = "claude-opus-4-8"

# One deterministic paragraph, repeated ~60x -> comfortably above Opus 4.8's 4096-token floor.
_PARAGRAPH = (
    "Section {n}: Claims-processing policy. Every submitted invoice is validated against "
    "the vendor master list before payment is scheduled. The extracted vendor name, total "
    "amount, and due date must each pass a business rule: amount strictly positive, due "
    "date parses as ISO-8601, and vendor resolves to a known, non-terminated supplier. "
    "Rejected records route to a human reviewer with the failing rule attached, never "
    "silently dropped. This is stable reference context, reused verbatim across requests."
)
STABLE_SYSTEM = "\n\n".join(_PARAGRAPH.format(n=i) for i in range(1, 61))


def system_blocks(volatile_prefix: str = ""):
    """System prompt as a single cached text block.

    volatile_prefix (if given) is prepended to the TOP -> it lands BEFORE the breakpoint
    in the prefix, so it changes the cache key on every call. This is the Step 2 trap.
    """
    text = STABLE_SYSTEM
    if volatile_prefix:
        text = f"{volatile_prefix}\n\n{STABLE_SYSTEM}"
    return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral", "ttl": "1h"}}]


def call(label, system, user):
    resp = client.messages.create(
        model=MODEL,
        max_tokens=64,  # output doesn't matter; we only read input-side usage
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    u = resp.usage
    print(f"  {label:<24} created={u.cache_creation_input_tokens:>6}  "
          f"read={u.cache_read_input_tokens:>6}  input={u.input_tokens:>5}")
    return u

def now_stamp():
    return f"Current time: {datetime.now(timezone.utc).isoformat()}"

if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Set ANTHROPIC_API_KEY first.")
    client = anthropic.Anthropic()

    print("Step 1 - warm hit (identical prefix twice):")
    call("call 1 (cold write)", system_blocks(), "Summarize the policy in one line.")
    call("call 2 (warm read)",  system_blocks(), "Summarize the policy in one line.")

    print("\nStep 2 - prefix-mutation kill (timestamp prepended to system prompt):")
    for i in range(1, 4):
        call(f"call {i} (volatile top)", system_blocks(now_stamp()),
             "Summarize the policy in one line.")

    print("\nStep 3 - recovery (timestamp moved into the user turn):")
    call("call 1 (warm read)", system_blocks(),
         f"{now_stamp()}\n\nSummarize the policy in one line.")
    call("call 2 (warm read)", system_blocks(),
         f"{now_stamp()}\n\nSummarize the policy in one line.")