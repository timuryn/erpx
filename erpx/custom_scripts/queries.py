"""
Override for erpnext.controllers.queries
Allows completed projects to be linked in Sales Invoices and other doctypes
"""
import frappe
import json
from frappe import qb
from frappe.query_builder import Criterion, Order
from frappe.query_builder.functions import Locate
from pypika import CustomFunction

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_project_name(doctype, txt, searchfield, start, page_len, filters):
    """
    Override of erpnext.controllers.queries.get_project_name
    Modified to allow COMPLETED projects (but still exclude Cancelled)
    Original: proj.status.notin(["Completed", "Cancelled"])
    Modified: proj.status != "Cancelled"
    """
    # Handle filters - it might come as a JSON string
    if isinstance(filters, str):
        filters = json.loads(filters) if filters else {}
    
    proj = qb.DocType("Project")
    qb_filter_and_conditions = []
    qb_filter_or_conditions = []
    ifelse = CustomFunction("IF", ["condition", "then", "else"])
    
    if filters:
        if filters.get("customer"):
            qb_filter_and_conditions.append(
                (proj.customer == filters.get("customer")) | proj.customer.isnull() | proj.customer == ""
            )
        if filters.get("company"):
            qb_filter_and_conditions.append(proj.company == filters.get("company"))
    
    # MODIFICATION: Allow Completed projects, only exclude Cancelled
    qb_filter_and_conditions.append(proj.status != "Cancelled")
    
    q = qb.from_(proj)
    # Select only Project fields that we need
    q = q.select(proj.name, proj.project_name)
    
    # Search in project name and name fields
    if txt:
        qb_filter_or_conditions.append(proj.project_name.like(f"%{txt}%"))
        qb_filter_or_conditions.append(proj.name.like(f"%{txt}%"))
    
    q = q.where(Criterion.all(qb_filter_and_conditions)).where(Criterion.any(qb_filter_or_conditions))
    
    # Ordering
    if txt:
        # project_name containing search string 'txt' will be given higher precedence
        q = q.orderby(ifelse(Locate(txt, proj.project_name) > 0, Locate(txt, proj.project_name), 99999))
    
    q = q.orderby(proj.idx, order=Order.desc).orderby(proj.name)
    
    if page_len:
        q = q.limit(page_len)
    if start:
        q = q.offset(start)
    
    return q.run()
