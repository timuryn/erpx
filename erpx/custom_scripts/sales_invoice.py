# erpx/custom_scripts/sales_invoice.py
import frappe

@frappe.whitelist()
def allow_edit_submitted_invoice(invoice_id):
    # Get the Sales Invoice document
    invoice = frappe.get_doc("Sales Invoice", invoice_id)
    
    # Check if the document is submitted (docstatus 1)
    if invoice.docstatus == 1:
        # Temporarily set docstatus to 0 (Draft) to allow editing
        invoice.db_set("docstatus", 0)
        # Optionally, add any other fields you want to reset or change
        # For example, if you want to reset the submission date:
        # invoice.db_set("posting_date", None)
    
    # Return the invoice with the changes
    return invoice

