# Invoice Generator

Generate professional PDF invoices — in your browser or from the command line.

## Web App

**[Use the web app →](https://adamluckydo.github.io/invoice-generator/)**

No installation needed. Works entirely in your browser. Data stays on your device.

## Command Line

For power users who want auto-numbering, client profiles, and scriptability.

### Requirements

```bash
pip install reportlab
```

### Usage

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
python generate-invoice.py --client acme \
    --title "Invoice for Facilitation" \
    --item "Training session,Feb 2025,3,375"
```

### Client Management

```bash
# Save a client
python generate-invoice.py --save-client acme \
    --to "Acme Corp" \
    --to-company "Acme Industries LLC"

# List clients
python generate-invoice.py --list-clients

# Delete a client
python generate-invoice.py --delete-client acme
```

### Invoice Numbering

Invoices are auto-numbered (INV-001, INV-002, etc.). The counter persists in `data/invoice-counter.json`.

```bash
# Manual invoice number
python generate-invoice.py --invoice-number "CUSTOM-123" ...

# Skip numbering
python generate-invoice.py --no-number ...
```

### Logo

To add a logo, place a file named `logo.png` in this directory. Recommended size: 200x60 pixels.

### Customization

Create `data/config.json` to set your default name, email, payment method, and invoice prefix. It's git-ignored, so your details stay out of the repo. Any key you leave out falls back to the placeholder in `DEFAULTS` at the top of `generate-invoice.py`.

```json
{
  "from_name": "Your Name",
  "from_email": "you@example.com",
  "payment_method": "PayPal – you@example.com"
}
```

## Files

- `index.html` — Web app (GitHub Pages)
- `generate-invoice.py` — CLI script
- `example-invoice.json` — Example invoice data
- `data/` — Your config, client profiles, and invoice counter (CLI only, git-ignored)
