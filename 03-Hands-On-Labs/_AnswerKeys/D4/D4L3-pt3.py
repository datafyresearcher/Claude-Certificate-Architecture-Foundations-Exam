from pydantic import BaseModel
from anthropic import Anthropic
from datetime import datetime
import json

client = Anthropic()

# ─────────────────────────────────────────────
# PART 3: Validation-retry loop for invoice extraction
# ─────────────────────────────────────────────
class Invoice(BaseModel):
    vendor: str
    amount: str
    due_date: str

invoice_schema = Invoice.model_json_schema()
invoice_schema["additionalProperties"] = False

def validate_invoice(data: dict) -> list[str]:
    """Returns list of validation errors. Empty = valid."""
    errors = []
    if not data.get("vendor", "").strip():
        errors.append("vendor is empty or missing")
    amount_str = data.get("amount", "")
    try:
        amount_val = float(amount_str.replace("$", "").replace(",", ""))
        if amount_val <= 0:
            errors.append(f"amount must be > 0, got {amount_val}")
    except ValueError:
        errors.append(f"amount '{amount_str}' is not a valid number")
    due_date_str = data.get("due_date", "")
    try:
        datetime.strptime(due_date_str, "%Y-%m-%d")
    except ValueError:
        errors.append(f"due_date '{due_date_str}' is not ISO 8601 (YYYY-MM-DD)")
    return errors

def extract_invoice(invoice_text: str) -> dict:
    """Extract invoice with validation-retry loop. Returns result + attempt count."""
    messages = [
        {
            "role": "user",
            "content": f"Extract vendor, amount, and due_date from this invoice: {invoice_text}"
        }
    ]
    for attempt in range(1, 3):  # max 2 attempts
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=256,
            output_config={
                "format": {"type": "json_schema", "schema": invoice_schema}
            },
            messages=messages
        )
        raw = json.loads(response.content[0].text)
        errors = validate_invoice(raw)
        if not errors:
            return {"data": raw, "attempt": attempt, "success": True}
        # Build follow-up turn with the errors
        messages.append({"role": "assistant", "content": response.content[0].text})
        messages.append({
            "role": "user",
            "content": (
                f"The extracted data failed validation:\n"
                + "\n".join(f"- {e}" for e in errors)
                + "\n\nPlease correct and return valid JSON."
            )
        })
    return {"data": raw, "attempt": 2, "success": False}

# Test cases — some intentionally malformed to trigger retry
TEST_INVOICES = [
    "Invoice from Acme Corp, Due: 2024-01-15, Total: $500.00",
    "Invoice from , Due: Jan 15 2024, Total: -$100",   # 3 failures: empty vendor, bad date, negative amount
    "Received $250 payment from TechCorp on 15/01/2024",  # ambiguous date format
    "Invoice #999 from GlobalSupplies LLC dated 2024-03-01 for $1,200.00",
]

print("\n=== VALIDATION-RETRY LOOP ===")
attempt1_pass = 0
attempt2_recovered = 0

for inv_text in TEST_INVOICES:
    result = extract_invoice(inv_text)
    status = "✅ PASS" if result["success"] else "❌ FAIL"
    attempt_label = f"Attempt {result['attempt']}"
    if result["attempt"] == 1 and result["success"]:
        attempt1_pass += 1
    elif result["attempt"] == 2 and result["success"]:
        attempt2_recovered += 1
    print(f"\n{status} ({attempt_label})")
    print(f"  Input:  {inv_text[:60]}")
    print(f"  Output: {result['data']}")

print(f"\n📊 Attempt-1 successes: {attempt1_pass}/{len(TEST_INVOICES)}")
print(f"📊 Attempt-2 recoveries: {attempt2_recovered}")
