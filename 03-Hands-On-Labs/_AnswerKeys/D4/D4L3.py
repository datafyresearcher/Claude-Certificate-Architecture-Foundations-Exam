from anthropic import Anthropic
import json

client = Anthropic()

# ─────────────────────────────────────────────
# PART 1: BIASED prompt — all 5 examples are "billing"
# ─────────────────────────────────────────────
BIASED_SYSTEM = """You are a support ticket classifier. Classify tickets into one of:
billing, technical, account, other
<examples>
<example>
Ticket: I was charged twice last week
Category: billing
</example>
<example>
Ticket: My invoice shows the wrong amount
Category: billing
</example>
<example>
Ticket: I need a refund for my last payment
Category: billing
</example>
<example>
Ticket: My credit card was declined
Category: billing
</example>
<example>
Ticket: Where can I find my receipt?
Category: billing
</example>
</examples>
Respond with ONLY the category word. No explanation."""

MIXED_TICKETS = [
    "I was charged twice this month",           # billing
    "My login isn't working",                    # account
    "The API keeps returning 500 errors",        # technical
    "I need to cancel my subscription",          # account
    "The app crashes on startup",                # technical
    "Invoice sent to wrong email",               # billing
    "Password reset isn't sending emails",       # technical
    "I want to upgrade my plan",                 # account
    "Payment failed but I was still charged",    # billing
    "Two-factor auth codes not arriving",        # technical
    "How do I export my data?",                  # other
    "Account suspended without warning",         # account
    "Refund hasn't arrived after 10 days",       # billing
    "Integration with Slack not working",        # technical
    "I need to add a team member",               # account
    "My free trial ended unexpectedly",          # billing
    "Dashboard loading very slowly",             # technical
    "I forgot which email I used to sign up",    # account
    "Can I use the API for commercial use?",     # other
    "Wrong name on my invoice",                  # billing
]

EXPECTED = [
    "billing","account","technical","account","technical",
    "billing","technical","account","billing","technical",
    "other","account","billing","technical","account",
    "billing","technical","account","other","billing"
]


# Run with biased prompt
biased_results = []
for ticket in MIXED_TICKETS:
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=20,
        system=BIASED_SYSTEM,
        messages=[{"role": "user", "content": f"Ticket: {ticket}"}]
    )
    prediction = response.content[0].text.strip().lower()
    biased_results.append(prediction)

# Score it
biased_correct = sum(p == e for p, e in zip(biased_results, EXPECTED))
print(f"\n=== BIASED PROMPT: {biased_correct}/20 correct ===")
for ticket, pred, exp in zip(MIXED_TICKETS, biased_results, EXPECTED):
    flag = "✅" if pred == exp else "❌"
    print(f"  {flag} [{pred}] (expected: {exp}) — {ticket[:45]}")


# ─────────────────────────────────────────────
# PART 2: DIVERSE prompt — one example per category + edge case
# ─────────────────────────────────────────────
DIVERSE_SYSTEM = """You are a support ticket classifier. Classify tickets into one of:
billing, technical, account, other

<examples>
<example>
Ticket: I was charged twice last week
Category: billing
</example>
<example>
Ticket: The API keeps returning 500 errors and my integration is broken
Category: technical
</example>
<example>
Ticket: I can't log in — my account seems to be locked
Category: account
</example>
<example>
Ticket: Does your service comply with GDPR?
Category: other
</example>
<example>
Ticket: My free trial ended but I never got a charge warning — not sure if this is billing or account
Category: billing
</example>
</examples>

The last example shows an edge case where a ticket could be multiple categories — pick the PRIMARY one.
Respond with ONLY the category word. No explanation."""

# Run with diverse prompt — same 20 tickets
diverse_results = []
for ticket in MIXED_TICKETS:
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=20,
        system=DIVERSE_SYSTEM,
        messages=[{"role": "user", "content": f"Ticket: {ticket}"}]
    )
    prediction = response.content[0].text.strip().lower()
    diverse_results.append(prediction)

diverse_correct = sum(p == e for p, e in zip(diverse_results, EXPECTED))
print(f"\n=== DIVERSE PROMPT: {diverse_correct}/20 correct ===")
for ticket, pred, exp in zip(MIXED_TICKETS, diverse_results, EXPECTED):
    flag = "✅" if pred == exp else "❌"
    print(f"  {flag} [{pred}] (expected: {exp}) — {ticket[:45]}")

print(f"\n📊 Improvement: {biased_correct} → {diverse_correct} (+{diverse_correct - biased_correct})")