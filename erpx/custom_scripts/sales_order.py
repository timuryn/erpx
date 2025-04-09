import frappe

@frappe.whitelist()
def allow_edit_submitted_order(order_id):
    # Get the Sales Order document
    order = frappe.get_doc("Sales Order", order_id)
    
    # Check if the document is submitted (docstatus 1)
    if order.docstatus == 1:
        # Temporarily set docstatus to 0 (Draft) to allow editing
        order.db_set("docstatus", 0)
        # Optionally, add any other fields you want to reset or change

        # Unlock child table fields
        for item in order.items:
            item.db_set("item_name", item.item_name)
            item.db_set("item_code", item.item_code)
            item.db_set("qty", item.qty)
            item.db_set("rate", item.rate)
            item.db_set("amount", item.amount)

        # Save changes
        order.save(ignore_permissions=True)

    # Return the order with the changes
    return order
