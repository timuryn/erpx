import frappe

@frappe.whitelist()
def get_customer_artikel_count(customer):
    """Get count of unique items from all customer quotations"""
    lead_name = frappe.db.get_value("Customer", customer, "lead_name")
    
    # Get quotations for customer and lead (if exists)
    party_names = [customer]
    if lead_name:
        party_names.append(lead_name)
    
    quotations = frappe.get_list(
        'Quotation',
        filters={
            'party_name': ['in', party_names],
            'docstatus': ['!=', 2]  # Exclude cancelled
        },
        fields=['name'],
        limit_page_length=0
    )
    
    if not quotations:
        return {
            'count': 0,
            'items': []
        }
    
    quotation_names = [q['name'] for q in quotations]
    
    # Get all items from those quotations using raw SQL
    placeholders = ','.join(['%s'] * len(quotation_names))
    query = f"""
        SELECT parent, item_name, qty, uom, rate, amount
        FROM `tabQuotation Item`
        WHERE parent IN ({placeholders})
        ORDER BY parent ASC, idx ASC
    """
    
    items = frappe.db.sql(query, quotation_names, as_dict=True)
    
    # Count unique item names
    unique_count = len(set(item['item_name'] for item in items if item['item_name']))
    
    return {
        'count': unique_count,
        'items': items
    }
