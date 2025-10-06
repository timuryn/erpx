import frappe
import json

@frappe.whitelist()
def get_customer_open_counts(doctype, name, items):
    """Get open counts for Customer including lead quotations"""
    from frappe.desk.notifications import get_open_count
    
    # Get original counts
    result = get_open_count(doctype, name, items)
    
    # If this is a Customer and Quotation is in items, recalculate
    if doctype == "Customer" and "Quotation" in items:
        lead_name = frappe.db.get_value("Customer", name, "lead_name")
        
        if lead_name:
            # Recalculate Quotation count to include lead quotations
            filters = [["party_name", "in", [name, lead_name]]]
            quotation_count = frappe.db.count("Quotation", filters)
            
            # Update the result
            if result and "count" in result:
                result["count"]["Quotation"] = quotation_count
    
    return result

@frappe.whitelist()
def get_combined_quotations_link(customer_name):
    """Get the proper link to view quotations for customer and lead"""
    lead_name = frappe.db.get_value("Customer", customer_name, "lead_name")
    
    if lead_name:
        # Build filter for both customer and lead
        filters = json.dumps([
            ["Quotation", "party_name", "in", [customer_name, lead_name]]
        ])
        return f"/app/quotation?#{filters}"
    else:
        # Just customer quotations
        return f"/app/quotation?quotation_to=Customer&party_name={customer_name}"
