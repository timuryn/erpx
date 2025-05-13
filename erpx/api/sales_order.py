import frappe
import re

@frappe.whitelist()
def get_related_counts(sales_order):
    # Get Delivery Notes
    delivery_note_items = frappe.db.get_all(
        "Delivery Note Item",
        filters={"against_sales_order": sales_order},
        fields=["parent"]
    )
    delivery_note_names = {item["parent"] for item in delivery_note_items}

    # Get Sales Invoices via Sales Invoice Items
    invoice_items = frappe.db.get_all(
        "Sales Invoice Item",
        filters={"sales_order": sales_order},
        fields=["parent"]
    )
    sales_invoice_names = {item["parent"] for item in invoice_items}

    # Get all related Sales Invoices and their custom_kommission field
    invoices = frappe.db.get_all(
        "Sales Invoice",
        filters={"name": ["in", list(sales_invoice_names)]},
        fields=["name", "custom_kommission"]
    )

    teilrechnungen = []
    schlussrechnungen = []
    normale_rechnungen = []

    for inv in invoices:
        kom = inv.get("custom_kommission", "") or ""
        if "Teilrechnung" in kom:
            teilrechnungen.append(inv)
        elif "Schlussrechnung" in kom:
            schlussrechnungen.append(inv)
        else:
            normale_rechnungen.append(inv)

    return {
        "delivery_notes": len(delivery_note_names),
        "delivery_note_names": list(delivery_note_names),
        "sales_invoices": len(normale_rechnungen),
        "sales_invoice_names": [inv["name"] for inv in normale_rechnungen],
        "partial_invoices": len(teilrechnungen),
        "partial_invoice_names": [inv["name"] for inv in teilrechnungen],
        "final_invoices": len(schlussrechnungen),
        "final_invoice_names": [inv["name"] for inv in schlussrechnungen],
        "has_final_invoice": len(schlussrechnungen) > 0
}

@frappe.whitelist()
def get_total_partial_invoice_percentage(sales_order):
    # Get all Sales Invoices for this SO that are only Teilrechnungen
    invoices = frappe.db.get_all(
        "Sales Invoice",
        filters={"sales_order": sales_order},
        fields=["custom_teilrechnung", "custom_kommission"]
    )

    total_percentage = 0
    teilrechnungen = [
        inv for inv in invoices if "Teilrechnung" in (inv.get("custom_kommission") or "")
    ]

    for inv in teilrechnungen:
        teilrechnung_value = inv.get("custom_teilrechnung", "")
        match = re.search(r"(\d+(\.\d+)?)%", teilrechnung_value)
        if match:
            total_percentage += float(match.group(1))

    return total_percentage
