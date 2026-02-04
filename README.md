# invoice-generator

PDF invoice generator with auto-numbering and client profiles.

## Requirements

```bash
pip install reportlab
```

## Usage

```bash
# Interactive mode (prompts for everything)
python generate-invoice.py

# From JSON file
python generate-invoice.py --from-json example-invoice.json

# Quick CLI mode
python generate-invoice.py \
    --title "Invoice for Consulting" \
    --to "Acme Corp" \
    --item "Workshop facilitation,Jan 1-15,2,500" \
    --item "Follow-up session,Jan 20,1,200"

# Use a saved client
python generate-invoice.py --client nsm \
    --title "Invoice for Facilitation" \
    --item "Pod facilitation,Feb 2025,3,375"
```

## Client Management

```bash
# Save a client
python generate-invoice.py --save-client nsm \
    --to "Nervous System Mastery" \
    --to-company "Curious Humans LLC"

# List clients
python generate-invoice.py --list-clients

# Delete a client
python generate-invoice.py --delete-client nsm
```

## Invoice Numbering

Invoices are auto-numbered (INV-001, INV-002, etc.). The counter persists in `data/invoice-counter.json`.

```bash
# Manual invoice number
python generate-invoice.py --invoice-number "CUSTOM-123" ...

# Skip numbering
python generate-invoice.py --no-number ...
```

## Logo

To add a logo, place a file named `logo.png` in this directory. Recommended size: 200x60 pixels.

## Files

- `generate-invoice.py` — Main script
- `example-invoice.json` — Template matching the NSM invoice format
- `data/` — Stores client profiles and invoice counter (created automatically)

## Customization

Edit the `DEFAULTS` dict at the top of `generate-invoice.py` to change your default name, email, payment method, and invoice prefix.
