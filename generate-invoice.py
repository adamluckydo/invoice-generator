#!/usr/bin/env python3
"""
Invoice Generator

Generates PDF invoices from command-line input or a JSON file.

Usage:
    # Interactive mode (prompts for all fields)
    python generate-invoice.py

    # From JSON file
    python generate-invoice.py --from-json invoice-data.json

    # Quick mode with args
    python generate-invoice.py --title "Invoice for Consulting" \
        --to "Acme Corp" \
        --item "Consulting,Jan 1-15,10,150"

    # Use a saved client profile
    python generate-invoice.py --client nsm --item "Facilitation,Jan 2025,2,375"

    # List saved clients
    python generate-invoice.py --list-clients

    # Save a new client
    python generate-invoice.py --save-client nsm --to "Nervous System Mastery" \
        --to-company "Curious Humans LLC"

Requirements:
    pip install reportlab
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
except ImportError:
    print("Error: reportlab not installed. Run: pip install reportlab")
    sys.exit(1)


# ============================================================================
# PATHS
# ============================================================================

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR / "data"
CLIENTS_FILE = DATA_DIR / "clients.json"
COUNTER_FILE = DATA_DIR / "invoice-counter.json"
LOGO_FILE = SCRIPT_DIR / "logo.png"  # TODO: Add your logo here


# ============================================================================
# DEFAULT VALUES (edit these to match your info)
# ============================================================================

DEFAULTS = {
    "from_name": "Adam Luck",
    "from_email": "adamluckydo@gmail.com",
    "payment_method": "PayPal – adamluckydo@gmail.com",
    "invoice_prefix": "INV",  # Invoice numbers will be INV-001, INV-002, etc.
}


# ============================================================================
# DATA PERSISTENCE
# ============================================================================

def ensure_data_dir():
    """Create data directory if it doesn't exist."""
    DATA_DIR.mkdir(exist_ok=True)


def load_clients():
    """Load saved client profiles."""
    if CLIENTS_FILE.exists():
        with open(CLIENTS_FILE) as f:
            return json.load(f)
    return {}


def save_clients(clients):
    """Save client profiles."""
    ensure_data_dir()
    with open(CLIENTS_FILE, "w") as f:
        json.dump(clients, f, indent=2)


def get_next_invoice_number():
    """Get and increment the invoice counter."""
    ensure_data_dir()

    if COUNTER_FILE.exists():
        with open(COUNTER_FILE) as f:
            data = json.load(f)
    else:
        data = {"last_number": 0}

    data["last_number"] += 1

    with open(COUNTER_FILE, "w") as f:
        json.dump(data, f, indent=2)

    return f"{DEFAULTS['invoice_prefix']}-{data['last_number']:03d}"


def peek_next_invoice_number():
    """See what the next invoice number would be without incrementing."""
    if COUNTER_FILE.exists():
        with open(COUNTER_FILE) as f:
            data = json.load(f)
        return f"{DEFAULTS['invoice_prefix']}-{data['last_number'] + 1:03d}"
    return f"{DEFAULTS['invoice_prefix']}-001"


# ============================================================================
# INVOICE DATA STRUCTURE
# ============================================================================

def create_empty_invoice():
    """Returns an empty invoice structure with defaults filled in."""
    return {
        "invoice_number": None,  # Will be auto-assigned if not provided
        "title": "",
        "date": datetime.now().strftime("%B %d, %Y"),
        "from": {
            "name": DEFAULTS["from_name"],
            "email": DEFAULTS["from_email"],
        },
        "to": {
            "name": "",
            "company": "",  # optional
        },
        "items": [
            # Each item: {"service": "", "date": "", "quantity": 1, "rate": 0}
        ],
        "payment_method": DEFAULTS["payment_method"],
        "notes": "",  # optional, appears at bottom
    }


# ============================================================================
# INTERACTIVE INPUT
# ============================================================================

def prompt(msg, default=None):
    """Prompt for input with optional default."""
    if default:
        result = input(f"{msg} [{default}]: ").strip()
        return result if result else default
    return input(f"{msg}: ").strip()


def prompt_client_selection(clients):
    """Let user select from saved clients or enter new."""
    if not clients:
        return None

    print("\n--- Saved Clients ---")
    client_list = list(clients.keys())
    for i, key in enumerate(client_list, 1):
        client = clients[key]
        name = client.get("name", key)
        company = client.get("company", "")
        display = f"{name} ({company})" if company else name
        print(f"  {i}. {key}: {display}")
    print(f"  {len(client_list) + 1}. Enter new client")

    choice = prompt(f"\nSelect client (1-{len(client_list) + 1})", "")

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(client_list):
            return clients[client_list[idx]]
    except ValueError:
        # Maybe they typed the client key directly
        if choice in clients:
            return clients[choice]

    return None


def prompt_items():
    """Interactively collect line items."""
    items = []
    print("\n--- Line Items ---")
    print("Enter items one at a time. Leave service blank to finish.\n")

    while True:
        service = input("Service description (or Enter to finish): ").strip()
        if not service:
            if not items:
                print("Need at least one item.")
                continue
            break

        date = prompt("  Date/date range", "")
        quantity = prompt("  Quantity", "1")
        rate = prompt("  Rate ($)", "0")

        try:
            quantity = int(quantity)
            rate = float(rate.replace("$", "").replace(",", ""))
        except ValueError:
            print("  Invalid number, using defaults.")
            quantity = 1
            rate = 0

        items.append({
            "service": service,
            "date": date,
            "quantity": quantity,
            "rate": rate,
        })
        print(f"  Added: {service} | qty {quantity} @ ${rate} = ${quantity * rate}\n")

    return items


def interactive_input():
    """Collect all invoice data interactively."""
    invoice = create_empty_invoice()
    clients = load_clients()

    print("\n=== Invoice Generator ===")
    print(f"Next invoice number: {peek_next_invoice_number()}\n")

    # Title and date
    invoice["title"] = prompt("Invoice title (e.g., 'Invoice for Consulting')")
    invoice["date"] = prompt("Invoice date", invoice["date"])

    # From (with defaults)
    print("\n--- From (your info) ---")
    invoice["from"]["name"] = prompt("Your name", DEFAULTS["from_name"])
    invoice["from"]["email"] = prompt("Your email", DEFAULTS["from_email"])

    # To (with client selection)
    selected_client = prompt_client_selection(clients)
    if selected_client:
        invoice["to"]["name"] = selected_client.get("name", "")
        invoice["to"]["company"] = selected_client.get("company", "")
        print(f"\nUsing client: {invoice['to']['name']}")
    else:
        print("\n--- To (client) ---")
        invoice["to"]["name"] = prompt("Client name/company")
        invoice["to"]["company"] = prompt("Additional line (optional)", "")

    # Items
    invoice["items"] = prompt_items()

    # Payment
    print("\n--- Payment ---")
    invoice["payment_method"] = prompt("Payment method", DEFAULTS["payment_method"])

    # Notes
    invoice["notes"] = prompt("Notes (optional)", "")

    return invoice


# ============================================================================
# PDF GENERATION
# ============================================================================

def generate_pdf(invoice, output_path):
    """Generate a PDF invoice."""
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'InvoiceTitle',
        parent=styles['Heading1'],
        fontSize=14,
        spaceAfter=6,
    )
    normal_style = styles['Normal']

    elements = []

    # Logo placeholder
    # TODO: To add a logo, place a file named "logo.png" in the invoice-generator directory
    # Recommended size: 200x60 pixels
    if LOGO_FILE.exists():
        logo = Image(str(LOGO_FILE), width=2*inch, height=0.6*inch)
        elements.append(logo)
        elements.append(Spacer(1, 0.25*inch))

    # Invoice number (if present)
    if invoice.get("invoice_number"):
        elements.append(Paragraph(f"<b>Invoice #:</b> {invoice['invoice_number']}", normal_style))

    # Title and date
    elements.append(Paragraph(invoice["title"], title_style))
    elements.append(Paragraph(f"<b>Date:</b> {invoice['date']}", normal_style))
    elements.append(Spacer(1, 0.25*inch))

    # From
    elements.append(Paragraph("<b>From:</b>", normal_style))
    elements.append(Paragraph(invoice["from"]["name"], normal_style))
    elements.append(Paragraph(invoice["from"]["email"], normal_style))
    elements.append(Spacer(1, 0.15*inch))

    # To
    elements.append(Paragraph("<b>To:</b>", normal_style))
    elements.append(Paragraph(invoice["to"]["name"], normal_style))
    if invoice["to"].get("company"):
        elements.append(Paragraph(invoice["to"]["company"], normal_style))
    elements.append(Spacer(1, 0.25*inch))

    # Items table
    table_data = [["Services", "Date", "Quantity", "Rate", "Total"]]
    grand_total = 0

    for item in invoice["items"]:
        total = item["quantity"] * item["rate"]
        grand_total += total
        table_data.append([
            item["service"],
            item.get("date", ""),
            str(item["quantity"]),
            f"${item['rate']:.0f}" if item['rate'] == int(item['rate']) else f"${item['rate']:.2f}",
            f"${total:.0f}" if total == int(total) else f"${total:.2f}",
        ])

    # Total row
    table_data.append(["Total", "", "", "", f"${grand_total:.0f}" if grand_total == int(grand_total) else f"${grand_total:.2f}"])

    table = Table(table_data, colWidths=[2.5*inch, 1.25*inch, 0.75*inch, 0.75*inch, 0.75*inch])
    table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),

        # Body
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),

        # Total row
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),

        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),

        # Alignment
        ('ALIGN', (2, 0), (4, -1), 'LEFT'),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 0.25*inch))

    # Payment method
    elements.append(Paragraph(f"<b>Payment Method:</b> {invoice['payment_method']}", normal_style))

    # Notes
    if invoice.get("notes"):
        elements.append(Spacer(1, 0.25*inch))
        elements.append(Paragraph(f"<b>Notes:</b> {invoice['notes']}", normal_style))

    doc.build(elements)
    return output_path


# ============================================================================
# CLI
# ============================================================================

def parse_item_string(item_str):
    """Parse 'service,date,quantity,rate' into an item dict."""
    parts = [p.strip() for p in item_str.split(",")]
    if len(parts) < 4:
        parts.extend([""] * (4 - len(parts)))

    return {
        "service": parts[0],
        "date": parts[1],
        "quantity": int(parts[2]) if parts[2] else 1,
        "rate": float(parts[3].replace("$", "")) if parts[3] else 0,
    }


def main():
    parser = argparse.ArgumentParser(description="Generate PDF invoices")

    # Invoice data options
    parser.add_argument("--from-json", "-j", help="Load invoice data from JSON file")
    parser.add_argument("--title", "-t", help="Invoice title")
    parser.add_argument("--date", "-d", help="Invoice date (default: today)")
    parser.add_argument("--to", help="Client name")
    parser.add_argument("--to-company", help="Client company (optional second line)")
    parser.add_argument("--from-name", help=f"Your name (default: {DEFAULTS['from_name']})")
    parser.add_argument("--from-email", help=f"Your email (default: {DEFAULTS['from_email']})")
    parser.add_argument("--item", "-i", action="append",
                        help="Line item as 'service,date,quantity,rate' (can repeat)")
    parser.add_argument("--payment", "-p", help="Payment method")
    parser.add_argument("--notes", "-n", help="Additional notes")
    parser.add_argument("--output", "-o", help="Output filename (default: auto-generated)")
    parser.add_argument("--save-json", help="Also save invoice data to JSON file")

    # Invoice numbering
    parser.add_argument("--invoice-number", help="Manual invoice number (default: auto-generated)")
    parser.add_argument("--no-number", action="store_true", help="Don't include invoice number")

    # Client management
    parser.add_argument("--client", "-c", help="Use saved client profile by key")
    parser.add_argument("--list-clients", action="store_true", help="List saved client profiles")
    parser.add_argument("--save-client", metavar="KEY", help="Save client as profile (use with --to)")
    parser.add_argument("--delete-client", metavar="KEY", help="Delete a saved client profile")

    args = parser.parse_args()

    # Client management commands
    if args.list_clients:
        clients = load_clients()
        if not clients:
            print("No saved clients.")
        else:
            print("\nSaved clients:")
            for key, client in clients.items():
                name = client.get("name", "")
                company = client.get("company", "")
                display = f"{name} ({company})" if company else name
                print(f"  {key}: {display}")
        return

    if args.delete_client:
        clients = load_clients()
        if args.delete_client in clients:
            del clients[args.delete_client]
            save_clients(clients)
            print(f"Deleted client: {args.delete_client}")
        else:
            print(f"Client not found: {args.delete_client}")
        return

    if args.save_client:
        if not args.to:
            print("Error: --save-client requires --to")
            return
        clients = load_clients()
        clients[args.save_client] = {
            "name": args.to,
            "company": args.to_company or "",
        }
        save_clients(clients)
        print(f"Saved client: {args.save_client}")
        if not args.item:  # If only saving client, don't generate invoice
            return

    # Load from JSON or start fresh
    if args.from_json:
        with open(args.from_json) as f:
            invoice = json.load(f)
    elif args.title or args.item or args.client:
        # CLI mode
        invoice = create_empty_invoice()

        # Load client profile if specified
        if args.client:
            clients = load_clients()
            if args.client not in clients:
                print(f"Error: Unknown client '{args.client}'. Use --list-clients to see available.")
                return
            client = clients[args.client]
            invoice["to"]["name"] = client.get("name", "")
            invoice["to"]["company"] = client.get("company", "")

        if args.title:
            invoice["title"] = args.title
        if args.date:
            invoice["date"] = args.date
        if args.to:
            invoice["to"]["name"] = args.to
        if args.to_company:
            invoice["to"]["company"] = args.to_company
        if args.from_name:
            invoice["from"]["name"] = args.from_name
        if args.from_email:
            invoice["from"]["email"] = args.from_email
        if args.item:
            invoice["items"] = [parse_item_string(i) for i in args.item]
        if args.payment:
            invoice["payment_method"] = args.payment
        if args.notes:
            invoice["notes"] = args.notes
    else:
        # Interactive mode
        invoice = interactive_input()

    # Handle invoice numbering
    if args.no_number:
        invoice["invoice_number"] = None
    elif args.invoice_number:
        invoice["invoice_number"] = args.invoice_number
    elif not invoice.get("invoice_number"):
        invoice["invoice_number"] = get_next_invoice_number()

    # Generate output filename
    if args.output:
        output_path = args.output
    else:
        safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in invoice["title"])
        safe_title = safe_title.replace(" ", "-")
        if invoice.get("invoice_number"):
            output_path = f"{invoice['invoice_number']}-{safe_title}.pdf"
        else:
            output_path = f"{safe_title}.pdf"

    # Generate PDF
    generate_pdf(invoice, output_path)
    if invoice.get("invoice_number"):
        print(f"\nGenerated: {output_path} (Invoice #{invoice['invoice_number']})")
    else:
        print(f"\nGenerated: {output_path}")

    # Optionally save JSON
    if args.save_json:
        with open(args.save_json, "w") as f:
            json.dump(invoice, f, indent=2)
        print(f"Saved data: {args.save_json}")


if __name__ == "__main__":
    main()
