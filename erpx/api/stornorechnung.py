import frappe

@frappe.whitelist()
def create_stornorechnung(original_invoice):
    """Cancel the original invoice and create a balancing Stornorechnung with reference"""

    # Fetch the original invoice
    invoice = frappe.get_doc("Sales Invoice", original_invoice)

    if invoice.docstatus != 1:
        frappe.throw("Invoice must be submitted before cancellation.")

    if invoice.outstanding_amount == 0:
        frappe.throw("Invoice is already paid. Use a Gutschrift instead.")

    # Step 1: Cancel the original invoice
    invoice.cancel()

    # Step 2: Create a Stornorechnung with negative values
    storno_invoice = frappe.copy_doc(invoice)
    storno_invoice.name = None  # Generate new name
    storno_invoice.is_return = 1  # Mark as return
    storno_invoice.set("items", [])

    for item in invoice.items:
        item.qty = -item.qty  # Reverse quantity
        item.rate = item.rate  # Reverse rate ✅ FIXED
        item.amount = -item.amount
        item.base_amount = -item.base_amount
        storno_invoice.append("items", item)

    # Step 3: Add reference in custom_kommission field ✅ FIXED NAME
    storno_invoice.custom_kommission = f"Stornorechnung Nr. {invoice.name} zur Rechnung Nr. {{name}}"

    storno_invoice.insert()
    storno_invoice.submit()

    # Update the reference with the correct Stornorechnung number
    frappe.db.set_value("Sales Invoice", storno_invoice.name, "custom_kommission",
                        f"Stornorechnung Nr. {invoice.name} zur Rechnung Nr. {storno_invoice.name}")

    frappe.msgprint(f"Stornorechnung {storno_invoice.name} created successfully!", alert=True)
    return storno_invoice.name

