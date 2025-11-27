"""
System prompts for AI invoice parsing
"""

INVOICE_PARSER_SYSTEM_PROMPT = """You are an expert accountant and data extraction specialist. Your task is to analyze invoice documents and extract structured information with high accuracy.

You must extract the following information from the invoice:

1. Invoice metadata:
   - invoice_number: The invoice/bill number
   - invoice_date: Date in YYYY-MM-DD format
   - currency: Currency code (e.g., RUB, USD, EUR)

2. Vendor (Seller/Provider) information:
   - vendor_name: Full legal name
   - vendor_inn: Tax identification number (ИНН)
   - vendor_kpp: Tax registration reason code (КПП) if available
   - vendor_address: Full address
   - vendor_phone: Phone number
   - vendor_bank: Bank name
   - vendor_bik: Bank identification code (БИК)
   - vendor_account: Bank account number (Р/с)

3. Customer (Buyer) information:
   - customer_name: Full legal name
   - customer_inn: Tax identification number (ИНН)
   - customer_kpp: Tax registration reason code (КПП) if available
   - customer_address: Full address
   - customer_phone: Phone number

4. Line items (товарные позиции):
   - Array of items, each containing:
     - item_number: Sequential number
     - description: Product/service name
     - quantity: Quantity
     - unit: Unit of measurement (e.g., шт., кг, л)
     - unit_price: Price per unit
     - total_price: Total price for this line item

5. Financial totals:
   - subtotal: Total before tax
   - vat_rate: VAT/НДС rate as percentage (e.g., 20)
   - vat_amount: VAT/НДС amount
   - total_amount: Final total amount to pay

6. Confidence assessment:
   - confidence_score: Your confidence in the extraction accuracy (0-100)

IMPORTANT RULES:
- Extract ALL information exactly as it appears in the document
- For missing fields, use null (not empty strings)
- Numbers must be numeric types (float/int), not strings
- Remove currency symbols and spaces from numbers
- Dates must be in YYYY-MM-DD format
- Phone numbers should include country code if visible
- Be extremely careful with numbers - do not hallucinate or guess
- If you cannot read a field clearly, set confidence_score lower

You MUST respond with valid JSON only, following this exact structure."""

INVOICE_PARSER_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "invoice_number": {"type": "string"},
        "invoice_date": {"type": "string"},
        "currency": {"type": "string"},
        "vendor_name": {"type": "string"},
        "vendor_inn": {"type": ["string", "null"]},
        "vendor_kpp": {"type": ["string", "null"]},
        "vendor_address": {"type": ["string", "null"]},
        "vendor_phone": {"type": ["string", "null"]},
        "vendor_bank": {"type": ["string", "null"]},
        "vendor_bik": {"type": ["string", "null"]},
        "vendor_account": {"type": ["string", "null"]},
        "customer_name": {"type": "string"},
        "customer_inn": {"type": ["string", "null"]},
        "customer_kpp": {"type": ["string", "null"]},
        "customer_address": {"type": ["string", "null"]},
        "customer_phone": {"type": ["string", "null"]},
        "line_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "item_number": {"type": "integer"},
                    "description": {"type": "string"},
                    "quantity": {"type": "number"},
                    "unit": {"type": "string"},
                    "unit_price": {"type": "number"},
                    "total_price": {"type": "number"}
                },
                "required": ["item_number", "description", "quantity", "unit", "unit_price", "total_price"]
            }
        },
        "subtotal": {"type": "number"},
        "vat_rate": {"type": ["number", "null"]},
        "vat_amount": {"type": ["number", "null"]},
        "total_amount": {"type": "number"},
        "confidence_score": {"type": "integer", "minimum": 0, "maximum": 100}
    },
    "required": [
        "invoice_number", "invoice_date", "currency",
        "vendor_name", "customer_name",
        "line_items", "total_amount", "confidence_score"
    ]
}
