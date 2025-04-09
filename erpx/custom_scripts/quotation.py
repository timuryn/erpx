import frappe

@frappe.whitelist()
def allow_edit_submitted_quotation(quotation_id):
    # Get the Quotation document
    quotation = frappe.get_doc("Quotation", quotation_id)

    if quotation.docstatus == 1:
        # Temporarily set to Draft
        quotation.db_set("docstatus", 0)

        # Unlock child table fields
        for item in quotation.items:
            item.db_set("item_name", item.item_name)
            item.db_set("item_code", item.item_code)
            item.db_set("qty", item.qty)
            item.db_set("rate", item.rate)
            item.db_set("amount", item.amount)

        # Save changes
        quotation.save(ignore_permissions=True)

    return quotation

