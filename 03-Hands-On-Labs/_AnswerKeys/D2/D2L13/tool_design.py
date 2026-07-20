"""D2L13 answer key — Tool Definitions That Trigger Correctly.

Assembled solution for all three steps of D2/D2L13/README.md.
Run:  python tool_design.py   (requires ANTHROPIC_API_KEY, anthropic)
"""
import os, sys
import anthropic

MODEL = "claude-sonnet-4-6"

VAGUE = {
    "name": "search_kb",
    "description": "Gets information.",
    "input_schema": {"type": "object", "properties": {"query": {"type": "string"}},
                     "required": ["query"]},
}
PRECISE = {
    "name": "search_kb",
    "description": ("Search the company's INTERNAL knowledge base — HR policies, benefits, "
                    "and internal procedures. Call this whenever the user asks about "
                    "company-specific policies or internal processes. Do NOT call it for "
                    "general knowledge, math, or coding — answer those directly."),
    "input_schema": {"type": "object", "properties": {"query": {"type": "string"}},
                     "required": ["query"]},
}

PROMPTS = [
    ("should call",     "What is our company's parental leave policy?"),
    ("should call",     "How do I submit an expense report here?"),
    ("should NOT call", "What is the capital of France?"),
    ("should NOT call", "Write a haiku about autumn."),
    ("should NOT call", "What is 17 * 23?"),
]


def called(tool):
    hits = 0
    for expect, prompt in PROMPTS:
        r = client.messages.create(model=MODEL, max_tokens=200, tools=[tool],
                                   tool_choice={"type": "auto"},
                                   messages=[{"role": "user", "content": prompt}])
        used = any(b.type == "tool_use" for b in r.content)
        hits += used
        print(f"  [{expect:<14}] tool_used={str(used):<5} | {prompt}")
    print(f"  -> tool called on {hits}/5 prompts\n")


if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Set ANTHROPIC_API_KEY first.")
    client = anthropic.Anthropic()

    # ---- Step 1: description drives triggering ----
    print("=== Step 1a: VAGUE description ===")
    called(VAGUE)
    print("=== Step 1b: PRECISE description ===")
    called(PRECISE)

    # ---- Step 2: tool_choice modes on one prompt ----
    print("=== Step 2: tool_choice modes on one prompt ===")
    prompt = "What is the capital of France?"          # a 'should NOT call' prompt
    for choice in ({"type": "auto"}, {"type": "any"},
                   {"type": "tool", "name": "search_kb"}, {"type": "none"}):
        r = client.messages.create(model=MODEL, max_tokens=150, tools=[PRECISE],
                                   tool_choice=choice,
                                   messages=[{"role": "user", "content": prompt}])
        used = any(b.type == "tool_use" for b in r.content)
        text = next((b.text for b in r.content if b.type == "text"), "")
        print(f"  {str(choice):<45} stop={r.stop_reason:<10} tool_used={used}  {text[:40]!r}")

    # ---- Step 3: enum drift without strict, locked with strict ----
    print("\n=== Step 3: enum drift without strict, locked with strict ===")
    ROUTE = {
        "name": "route_ticket",
        "description": "Route a support ticket to a team.",
        "input_schema": {
            "type": "object",
            "properties": {"category": {"type": "string",
                            "enum": ["billing", "technical", "account", "other"]}},
            "required": ["category"], "additionalProperties": False,
        },
    }
    TICKETS = ["I was charged twice", "the app crashes on startup", "reset my 2FA", "do you support SSO?"]

    def route(strict):
        tool = {**ROUTE, "strict": strict}
        for t in TICKETS:
            r = client.messages.create(model=MODEL, max_tokens=120, tools=[tool],
                                       tool_choice={"type": "tool", "name": "route_ticket"},
                                       messages=[{"role": "user", "content": f"Route: {t}"}])
            cat = next((b.input.get("category") for b in r.content if b.type == "tool_use"), None)
            in_enum = cat in ROUTE["input_schema"]["properties"]["category"]["enum"]
            print(f"    strict={strict!s:<5} category={cat!r:<14} in_enum={in_enum} | {t}")

    route(strict=False)
    print()
    route(strict=True)
