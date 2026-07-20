import os
import sys
import json
import anthropic

MODEL = "claude-haiku-4-5"   # structured outputs supported; cheaper than Opus. Haiku 4.5 also works.

# A schema whose fully-populated instance is well over 200 tokens.
SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
        "affected_hosts": {"type": "array", "items": {"type": "string"}},
        "timeline": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "time": {"type": "string"},
                    "event": {"type": "string"},
                },
                "required": ["time", "event"],
                "additionalProperties": False,
            },
        },
        "root_cause": {"type": "string"},
        "remediation_steps": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["summary", "severity", "affected_hosts", "timeline",
                 "root_cause", "remediation_steps"],
    "additionalProperties": False,
}

POSTMORTEM = (
    "At 03:14 UTC host db-7 began rejecting writes after a disk filled to 100%. "
    "Ingest latency climbed from 12ms to 4200ms over eight minutes. The on-call "
    "rotated the write leader to db-9 at 03:31, truncated the oversized WAL, and "
    "restored writes by 03:47. Root cause: log rotation had been silently disabled "
    "by a config drift three weeks earlier. Remediation: re-enable rotation, add a "
    "disk-usage alert at 80%, and add a pre-deploy check that rejects configs "
    "missing a rotation policy. Two other hosts, db-3 and db-11, share the drifted "
    "config and must be patched before the next release."
)

PROMPT = ("Extract a detailed structured incident report from this postmortem. "
          "Populate the timeline and remediation_steps thoroughly.\n\n" + POSTMORTEM)


def extract(max_tokens):
    return client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
        messages=[{"role": "user", "content": PROMPT}],
    )

def extract_safely(start=200, ceiling=4000):
    max_tokens = start
    while True:
        resp = extract(max_tokens)
        reason = resp.stop_reason

        if reason == "max_tokens":
            if max_tokens >= ceiling:
                raise RuntimeError(f"Still truncated at ceiling={ceiling}; "
                                   "output genuinely too large - stream instead.")
            max_tokens *= 4          # raise limit and retry; do NOT parse the partial
            print(f"  truncated -> retrying with max_tokens={max_tokens}")
            continue

        if reason == "refusal":
            d = resp.stop_details
            raise RuntimeError(f"Model refused: {getattr(d, 'category', None)} / "
                               f"{getattr(d, 'explanation', None)}")

        # end_turn (or other terminal reason): safe to parse now.
        body = next(b.text for b in resp.content if b.type == "text")
        return json.loads(body)


if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Set ANTHROPIC_API_KEY first.")
    client = anthropic.Anthropic()

    print("=== Step 1: force truncation with max_tokens=200 ===")
    resp = extract(200)
    body = next(b.text for b in resp.content if b.type == "text")
    print("stop_reason:", resp.stop_reason)
    print("raw body (note it's cut mid-object):")
    print(body)
    print("\nTrying to parse it anyway:")
    try:
        json.loads(body)
        print("  parsed OK (unexpected)")
    except json.JSONDecodeError as e:
        print(f"  json.loads FAILED: {e}")

    print("\n=== Step 2: recovery handler ===")
    report = extract_safely(start=200)
    print("  recovered a valid object with keys:", sorted(report.keys()))
    print("  timeline entries:", len(report["timeline"]))
    print("  affected_hosts:", report["affected_hosts"])