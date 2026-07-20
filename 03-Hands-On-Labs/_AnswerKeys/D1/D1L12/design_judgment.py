"""D1L12 answer key — Agent Design Judgment: Tiering, Error Contracts, Escalation.

Assembled solution for all three parts of D1/D1L12/README.md.
Run:  python design_judgment.py   (requires ANTHROPIC_API_KEY, anthropic, pydantic)
"""
import os, sys, json
from pydantic import BaseModel
import anthropic

MODEL = "claude-sonnet-4-6"

TRIVIAL = "Extract the invoice number from: 'Invoice INV-2024-00123 dated 2026-03-01, $500'. Reply with only the number."

# Agent scaffolding that a trivial task does NOT need — 5 tool schemas + an agent system prompt.
NEEDLESS_TOOLS = [
    {"name": f"tool_{i}", "description": f"Does operation {i} on some data.",
     "input_schema": {"type": "object", "properties": {"x": {"type": "string"}}, "required": ["x"]}}
    for i in range(5)
]
AGENT_SYSTEM = ("You are an autonomous agent. Plan, call tools as needed, reflect after each "
                "step, and iterate until the task is complete. " * 6)

if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Set ANTHROPIC_API_KEY first.")
    client = anthropic.Anthropic()

    # ---- Part 1: tier mismatch cost ----
    print("=== Part 1: tier mismatch cost ===")
    # (a) right tier: single call
    a = client.messages.create(model=MODEL, max_tokens=32,
                               messages=[{"role": "user", "content": TRIVIAL}])
    print(f"  single call    input_tokens={a.usage.input_tokens:>4}  output={a.usage.output_tokens}")

    # (b) wrong tier: same task wrapped in agent scaffolding
    b = client.messages.create(model=MODEL, max_tokens=32, system=AGENT_SYSTEM,
                               tools=NEEDLESS_TOOLS,
                               messages=[{"role": "user", "content": TRIVIAL}])
    print(f"  agent-wrapped  input_tokens={b.usage.input_tokens:>4}  output={b.usage.output_tokens}")
    print(f"  overhead: {b.usage.input_tokens - a.usage.input_tokens} extra input tokens for the SAME answer")

    # ---- Part 2: generic vs structured tool error ----
    print("\n=== Part 2: generic vs structured tool error ===")

    ACCOUNT_TOOL = [{
        "name": "lookup_account",
        "description": "Look up an account balance by account_id.",
        "input_schema": {"type": "object", "properties": {"account_id": {"type": "string"}},
                         "required": ["account_id"]},
    }]

    def tool_result_for(account_id, structured):
        # ACME-001 succeeds; anything else fails.
        if account_id == "ACME-001":
            return json.dumps({"balance": "$1,240.00"}), False
        if structured:
            return json.dumps({"error": {
                "category": "not_found", "retryable": False,
                "attempted": f"lookup_account(account_id={account_id!r})",
                "partial_results": None,
            }}), True
        return "Error", True     # generic

    def one_round(structured):
        user = "What's the balance on account ACME-999?"     # a nonexistent account
        r1 = client.messages.create(model=MODEL, max_tokens=400, tools=ACCOUNT_TOOL,
                                    messages=[{"role": "user", "content": user}])
        tu = next(b for b in r1.content if b.type == "tool_use")
        content, is_err = tool_result_for(tu.input["account_id"], structured)
        r2 = client.messages.create(model=MODEL, max_tokens=400, tools=ACCOUNT_TOOL, messages=[
            {"role": "user", "content": user},
            {"role": "assistant", "content": r1.content},
            {"role": "user", "content": [{"type": "tool_result", "tool_use_id": tu.id,
                                          "content": content, "is_error": is_err}]},
        ])
        return next((b.text for b in r2.content if b.type == "text"), "").strip()

    print("  GENERIC error -> model says:\n   ", one_round(structured=False))
    print("\n  STRUCTURED error -> model says:\n   ", one_round(structured=True))

    # ---- Part 3: escalation triggers ----
    print("\n=== Part 3: escalation triggers ===")

    class Signals(BaseModel):
        explicit_human_request: bool     # did they ask for a human / to escalate?
        sentiment: str                   # calm | frustrated | angry
        issue_complexity: str            # trivial | moderate | complex

    CASES = {
        "calm_explicit":  "Everything's working fine, but I'd like to speak to a human agent please.",
        "angry_trivial":  "This is ABSOLUTELY INFURIATING!!! Just tell me how to reset my password.",
        "polite_complex": "Hi! My invoices across three linked accounts don't reconcile with the "
                          "payments dashboard for the last two billing cycles — can you help?",
    }

    def classify(text):
        return client.messages.parse(model=MODEL, max_tokens=200,
            messages=[{"role": "user", "content": f"Extract escalation signals from: {text!r}"}],
            output_format=Signals).parsed_output

    def naive_rule(s):      # ANTI-PATTERN: escalate on sentiment
        return s.sentiment in ("frustrated", "angry")

    def signal_rule(s):     # escalate on explicit request; route (not escalate) on complexity; ignore sentiment
        if s.explicit_human_request:
            return "escalate (explicit request)"
        if s.issue_complexity == "complex":
            return "route to specialist"
        return "handle in-band"

    for name, text in CASES.items():
        s = classify(text)
        print(f"  {name:<14} signals={s.model_dump()}")
        print(f"       naive(sentiment): {'ESCALATE' if naive_rule(s) else 'no'}"
              f"   |   signal-based: {signal_rule(s)}")
