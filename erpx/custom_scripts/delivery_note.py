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

def preserve_posting_date(doc, method=None):
    """
    before_validate hook for Delivery Note.
    ERPNext resets posting_date/posting_time to "now" on every save and on
    submit unless set_posting_time is checked. For existing documents the
    stored date is kept; new documents still default to today.
    """
    if doc.is_new() or doc.set_posting_time or not doc.posting_date:
        return

    stored = frappe.db.get_value(
        "Delivery Note", doc.name, ["posting_date", "posting_time"], as_dict=True
    )
    if not stored or not stored.posting_date:
        return

    doc.set_posting_time = 1
    if str(doc.posting_date) == str(frappe.utils.getdate()) and str(stored.posting_date) != str(doc.posting_date):
        doc.posting_date = stored.posting_date
        doc.posting_time = stored.posting_time
