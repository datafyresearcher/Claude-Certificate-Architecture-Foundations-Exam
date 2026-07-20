import os
import sys
import anthropic

MODEL = "claude-sonnet-4-5"
BETA = "context-management-2025-06-27"

FETCH_LOG = {
    "name": "fetch_log",
    "description": "Fetch one page of incident log text.",
    "input_schema": {
        "type": "object",
        "properties": {"page": {"type": "integer", "description": "1-based page number"}},
        "required": ["page"],
    },
}

# 220 lines of noisy filler per page. This LOG_LINE tokenizes to ~48 tokens,
# so a page is ~10.6K tokens (not 3K) - big enough to cross a 20K trigger in ~2 pages.
# Want a slower, more gradual climb? Drop range(220) in log_page() to range(60) (~2.9K/page).
LOG_LINE = ("2026-07-14 02:{m:02d}:00Z host=db-7 svc=ingest level=INFO "
            "msg=heartbeat latency_ms=12 status=200 queue_depth=4\n")
# The needle we hide in tool result #2:
FACT = ("2026-07-14 03:14:00Z host=db-7 svc=ingest level=CRITICAL "
        "msg=ANOMALY_START the anomaly began at 03:14 UTC on host db-7\n")


def log_page(call_index: int) -> str:
    body = "".join(LOG_LINE.format(m=i % 60) for i in range(220))
    if call_index == 2:
        return FACT + body      # plant the critical fact in the 2nd result
    return body


def run(context_management=None, n_calls=20):
    client = anthropic.Anthropic()
    messages = [{
        "role": "user",
        "content": ("You are triaging an incident. Use fetch_log to read one log page "
                    "at a time until told to stop. Always call fetch_log."),
    }]

    print(f"{'turn':>4} {'input_tokens':>13} {'cache_read':>11} {'cleared_tokens':>15}")
    for i in range(1, n_calls + 1):
        kwargs = dict(
            model=MODEL, max_tokens=512, tools=[FETCH_LOG],
            tool_choice={"type": "tool", "name": "fetch_log"},   # force a tool call every turn
            messages=messages, betas=[BETA],
        )
        if context_management:
            kwargs["context_management"] = context_management
        resp = client.beta.messages.create(**kwargs)

        cm = getattr(resp, "context_management", None)
        cleared = 0
        if cm and getattr(cm, "applied_edits", None):
            cleared = sum(e.cleared_input_tokens for e in cm.applied_edits)
        cache_read = getattr(resp.usage, "cache_read_input_tokens", 0) or 0
        print(f"{i:>4} {resp.usage.input_tokens:>13} {cache_read:>11} {cleared:>15}")

        messages.append({"role": "assistant", "content": resp.content})
        tool_use = next(b for b in resp.content if b.type == "tool_use")
        messages.append({"role": "user", "content": [{
            "type": "tool_result", "tool_use_id": tool_use.id, "content": log_page(i),
        }]})

    # Final recall turn: forbid tools so the model MUST answer from remaining context.
    messages.append({"role": "user", "content": (
        "Stop fetching. From the logs you've read, exactly what time did the anomaly "
        "begin and on which host? If you no longer have that detail, say so explicitly.")})
    final_kwargs = dict(model=MODEL, max_tokens=256, tools=[FETCH_LOG],
                        tool_choice={"type": "none"}, messages=messages, betas=[BETA])
    if context_management:
        final_kwargs["context_management"] = context_management
    resp = client.beta.messages.create(**final_kwargs)
    answer = "".join(b.text for b in resp.content if b.type == "text").strip()
    print("\nRECALL:", answer)
    return answer


if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Set ANTHROPIC_API_KEY first.")

    #print("=== Step 1: NO context editing ===")
    #run(context_management=None)
    '''
    print("=== Step 2: WITH context editing (keep=3) ===")
    run(context_management={
        "edits": [{
            "type": "clear_tool_uses_20250919",
            "trigger": {"type": "input_tokens", "value": 20000},
            "keep": {"type": "tool_uses", "value": 3},
        }]
    })
    '''
    for k in (3, 10, 19):
        print(f"\n=== Step 3: keep={k} ===")
        run(context_management={
            "edits": [{
                "type": "clear_tool_uses_20250919",
                "trigger": {"type": "input_tokens", "value": 20000},
                "keep": {"type": "tool_uses", "value": k},
            }]
        })