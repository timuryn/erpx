import frappe

@frappe.whitelist()
def allow_edit_submitted_delivery_note(delivery_note_id):
    # Get the Delivery Note document
    delivery_note = frappe.get_doc("Delivery Note", delivery_note_id)
    
    if delivery_note.docstatus == 1:
        # Temporarily set to Draft
        delivery_note.db_set("docstatus", 0)

        # Unlock child table fields
        for item in delivery_note.items:
            item.db_set("item_name", item.item_name)
            item.db_set("item_code", item.item_code)
            item.db_set("qty", item.qty)
            item.db_set("rate", item.rate)
            item.db_set("amount", item.amount)

        # Save changes
        delivery_note.save(ignore_permissions=True)

    return delivery_note
