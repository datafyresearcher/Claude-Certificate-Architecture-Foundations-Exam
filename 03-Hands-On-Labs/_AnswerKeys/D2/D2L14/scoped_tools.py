"""D2L14 answer key — Scoped Tool Distribution & Parallel Execution.

Assembled solution for all three steps of D2/D2L14/README.md.
Run:  python scoped_tools.py   (requires ANTHROPIC_API_KEY, anthropic, pydantic)
"""
import os, sys
from pydantic import BaseModel
import anthropic

MODEL = "claude-sonnet-4-6"


def tool(name, desc, *props):
    return {"name": name, "description": desc,
            "input_schema": {"type": "object",
                             "properties": {p: {"type": "string"} for p in props},
                             "required": list(props)}}

BILLING = [tool("get_invoice", "Fetch an invoice by id.", "invoice_id"),
           tool("issue_refund", "Refund a charge.", "charge_id"),
           tool("get_balance", "Get an account balance.", "account_id")]
DEVOPS  = [tool("restart_service", "Restart a service.", "service"),
           tool("tail_logs", "Fetch recent logs for a service.", "service"),
           tool("get_status", "Get service health status.", "service")]
HR      = [tool("lookup_pto", "Look up remaining PTO for an employee.", "employee_id"),
           tool("submit_expense", "Submit an expense.", "amount"),
           tool("get_policy", "Fetch an HR policy document.", "topic")]
ALL = BILLING + DEVOPS + HR

PROMPTS = [
    "A customer is furious about being double-charged last month.",   # billing
    "The checkout page is throwing errors for everyone.",             # devops
    "How much vacation do I have left this year?",                    # hr
    "Payments keep failing and customers are demanding their money back.",  # cross-domain
]


def picks(tools, prompt):
    r = client.messages.create(model=MODEL, max_tokens=200, tools=tools,
                               tool_choice={"type": "any"},   # force a choice so we can see routing
                               messages=[{"role": "user", "content": prompt}])
    chosen = [b.name for b in r.content if b.type == "tool_use"]
    return chosen, r.usage.input_tokens


if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Set ANTHROPIC_API_KEY first.")
    client = anthropic.Anthropic()

    # ---- Step 1: kitchen-sink agent (9 tools) ----
    print("=== Step 1: kitchen-sink agent (9 tools) ===")
    for p in PROMPTS:
        chosen, toks = picks(ALL, p)
        print(f"  picked={chosen!s:<28} input_tokens={toks:<4} | {p}")

    # ---- Step 2: router + scoped handlers (3 tools each) ----
    print("\n=== Step 2: router + scoped handlers (3 tools each) ===")

    class Route(BaseModel):
        domain: str      # billing | devops | hr

    HANDLERS = {"billing": BILLING, "devops": DEVOPS, "hr": HR}

    def router(prompt):
        return client.messages.parse(model=MODEL, max_tokens=60,
            messages=[{"role": "user", "content":
                f"Classify this request's primary domain (billing, devops, or hr): {prompt!r}"}],
            output_format=Route).parsed_output.domain

    for p in PROMPTS:
        domain = router(p)
        tools = HANDLERS.get(domain, ALL)
        chosen, toks = picks(tools, p)
        print(f"  route={domain:<8} picked={chosen!s:<20} input_tokens={toks:<4} | {p}")

    # ---- Step 3: parallel tool_use vs serialized ----
    print("\n=== Step 3: parallel tool_use vs serialized ===")
    prompt = "Fetch invoice INV-100 and invoice INV-200."
    for label, choice in [("parallel (default)", {"type": "auto"}),
                          ("serialized", {"type": "auto", "disable_parallel_tool_use": True})]:
        r = client.messages.create(model=MODEL, max_tokens=300, tools=BILLING,
                                   tool_choice=choice,
                                   messages=[{"role": "user", "content": prompt}])
        calls = [(b.name, b.input) for b in r.content if b.type == "tool_use"]
        print(f"  {label:<20} tool_use blocks in ONE response: {len(calls)} -> {calls}")
