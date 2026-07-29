import frappe

@frappe.whitelist()
def get_invoices_with_linked_docs_by_user(created_by):
    """Get Sales Invoices that have linked docs created by specific user"""
    
    invoices = frappe.db.sql("""
        SELECT DISTINCT si.name
        FROM `tabSales Invoice` si
        INNER JOIN `tabcustom_doc_links` cdl ON si.name = cdl.parent
        WHERE si.docstatus != 2
        AND cdl.created_by = %s
        ORDER BY si.posting_date DESC
    """, (created_by,), as_dict=False)
    
    return [inv[0] for inv in invoices]
