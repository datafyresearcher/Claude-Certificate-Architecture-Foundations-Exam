# The tool doesn't need to do anything real.
# Its job is to enforce schema compliance on the output.

tools = [
    {
        "name": "extract_invoice_data",
        "description": "Extract structured invoice information from the document",
        "input_schema": {
            "type": "object",
            "properties": {
                "vendor_name": {
                    "type": "string",
                    "description": "The name of the vendor or supplier"
                },
                "total_amount": {
                    "type": "number",
                    "description": "Total invoice amount in USD"
                },
                "invoice_date": {
                    "type": "string",
                    "description": "Invoice date in YYYY-MM-DD format"
                }
            },
            "required": ["vendor_name", "total_amount", "invoice_date"]
        }
    }
]

response = client.messages.create(
    model="claude-opus-4-5-20251001",
    max_tokens=1024,
    tools=tools,
    # We haven't set tool_choice yet — more on that in a moment
    messages=[{"role": "user", "content": f"Extract invoice data from: {document}"}]