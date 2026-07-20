from anthropic import Anthropic
from pydantic import BaseModel
import json

client = Anthropic()

TOOL_STRICT = {
    "name": "route_ticket",
    "description": "Routes a support ticket to the correct team based on category.",
    #"strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "enum": [
                    "Billing",
                    "technical",
                    "Account",
                    "other"
                ],
                "description": "The category of the support ticket."
            },
            "summary": {
                "type": "string",
                "description": "One-sentence summary ofthe issue"
            }
        },
        "required": ["category", "summary"],
        "additionalProperties": False
    }
}

TICKETS = [
    "I was charged twice this month",
    "My login isn't working",
    "Can't access my dashboard after password reset",
    "The API keeps returning 500 errors",
    "Billing statement shows wrong company name",
    "My subscription says active but features are locked",
    "Need to update credit card on file",
    "Account got suspended without warning",
    "The software crashes on startup",
    "I want to cancel my plan",
    "Invoice was sent to wrong email",
    "Two-factor auth is not sending codes",
    "Payment failed but money was deducted",
    "I need to transfer my account to another user",
    "The app is very slow and keeps freezing",   
]

strict_log = []


class RoutingResult(BaseModel):
    routed_to: str
    priority: str    # "high", "medium", "low"
    reason: str
routing_schema = RoutingResult.model_json_schema()
routing_schema["additionalProperties"] = False

for ticket in TICKETS:
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        tools=[TOOL_STRICT],
        tool_choice={"type":"auto"},
        output_config={
            "format":{
                "type": "json_schema",
                "schema": routing_schema
            }
        },
        messages=[{"role":"user","content":f"Route this ticket: {ticket}"}]
    )

    for block in response.content:
        if block.type == "tool_use":
            strict_log.append({
                "ticket": ticket,
                "input": block.input
            })

for entry in strict_log:
    print(f"[{entry['input'].get('category')}] {entry['ticket']}")