# erpx/custom_scripts/sales_invoice.py

import frappe
from frappe.utils import getdate

@frappe.whitelist()
def allow_edit_submitted_invoice(invoice_id):
    # Get the Sales Invoice document
    invoice = frappe.get_doc("Sales Invoice", invoice_id)

    if invoice.docstatus == 1:
        # Temporarily set to Draft
        invoice.db_set("docstatus", 0)

        # Unlock child table fields
        for item in invoice.items:
            item.db_set("item_name", item.item_name)
            item.db_set("item_code", item.item_code)
            item.db_set("qty", item.qty)
            item.db_set("rate", item.rate)
            item.db_set("amount", item.amount)

        # Save changes
        invoice.save(ignore_permissions=True)

    return invoice

@frappe.whitelist()
def finalize_invoice(invoice_id):
    # Get the Sales Invoice document
    invoice = frappe.get_doc("Sales Invoice", invoice_id)

    if invoice.docstatus == 0:
        # Auto-submit linked Sales Orders if needed
        for item in invoice.items:
            if item.sales_order:
                so = frappe.get_doc("Sales Order", item.sales_order)
                if so.docstatus == 0:
                    # Ensure cost center is set for all Sales Order items
                    default_cost_center = frappe.db.get_value("Company", so.company, "cost_center")

                    for so_item in so.items:
                        if not so_item.cost_center:
                            so_item.cost_center = default_cost_center or "Haupt - WDG"  # Replace with your default

                    so.save()
                    so.submit()

        # Submit the Sales Invoice
        invoice.submit()

        # Convert due_date and posting_date to date objects
        if invoice.due_date and invoice.posting_date:
            due_date_obj = getdate(invoice.due_date)
            posting_date_obj = getdate(invoice.posting_date)

            # Compare due date to posting date
            if due_date_obj >= posting_date_obj:
                new_status = "Unpaid"
            else:
                new_status = "Overdue"

            # Set the correct status
            invoice.db_set("status", new_status)

    return invoice.status

