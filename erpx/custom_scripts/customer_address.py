import frappe

@frappe.whitelist()
def get_customer_billing_addresses(customer_names):
    """
    Return the first linked address (street + city only) for each customer in the given list.
    Works for all users by ignoring permissions on Address doctype.
    """
    if isinstance(customer_names, str):
        customer_names = frappe.parse_json(customer_names)

    result = []

    if not customer_names:
        return result

    # Step 1: fetch Dynamic Links for the given customers
    dynamic_links = frappe.get_all(
        "Dynamic Link",
        filters={
            "link_doctype": "Customer",
            "link_name": ["in", customer_names]
        },
        fields=["parent", "parenttype", "link_name"],
        order_by="creation asc"
    )

    # Step 2: build map customer -> first linked address (parenttype must be "Address")
    customer_address_map = {}
    for dl in dynamic_links:
        if dl.link_name not in customer_address_map and dl.parenttype == "Address":
            customer_address_map[dl.link_name] = dl.parent

    # Step 3: fetch Address docs for the linked addresses, ignoring permissions
    if customer_address_map:
        address_docs = frappe.get_all(
            "Address",
            filters={"name": ["in", list(customer_address_map.values())]},
            fields=["name", "address_title", "address_line1", "address_line2", "city"],
            ignore_permissions=True  # <-- this allows all users to read
        )
        address_doc_map = {d["name"]: d for d in address_docs}

        # Step 4: prepare result per customer
        for customer in customer_names:
            addr_name = customer_address_map.get(customer)
            if addr_name and addr_name in address_doc_map:
                doc = address_doc_map[addr_name]
                street_parts = [doc.get("address_line1"), doc.get("address_line2")]
                street = ", ".join(filter(None, street_parts))
                city = doc.get("city") or ""
                full_address = ", ".join(filter(None, [street, city]))
                result.append({
                    "customer": customer,
                    "address": full_address,
                    "title": doc.get("address_title") or doc.get("name")
                })
            else:
                result.append({"customer": customer, "address": None, "title": None})
    else:
        for customer in customer_names:
            result.append({"customer": customer, "address": None, "title": None})

    return result
