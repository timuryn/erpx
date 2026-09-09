"""
Override for erpnext.controllers.queries
Allows completed projects to be linked in Sales Invoices and other doctypes,
and does not restrict the Project link search by customer.
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
    Modified to:
      - Allow COMPLETED projects (only Cancelled is excluded)
      - Not restrict results by customer at all
    """
    # Handle filters - it might come as a JSON string
    if isinstance(filters, str):
        filters = json.loads(filters) if filters else {}
    if not filters:
        filters = {}

    proj = qb.DocType("Project")
    qb_filter_and_conditions = []
    qb_filter_or_conditions = []
    ifelse = CustomFunction("IF", ["condition", "then", "else"])

    # NOTE: customer restriction intentionally removed — projects show up
    # regardless of which customer they belong to.

    if filters.get("company"):
        qb_filter_and_conditions.append(proj.company == filters.get("company"))

    # Allow Completed projects, only exclude Cancelled
    qb_filter_and_conditions.append(proj.status != "Cancelled")

    q = qb.from_(proj)
    q = q.select(proj.name, proj.project_name)

    if txt:
        qb_filter_or_conditions.append(proj.project_name.like(f"%{txt}%"))
        qb_filter_or_conditions.append(proj.name.like(f"%{txt}%"))

    q = q.where(Criterion.all(qb_filter_and_conditions)).where(Criterion.any(qb_filter_or_conditions))

    if txt:
        q = q.orderby(ifelse(Locate(txt, proj.project_name) > 0, Locate(txt, proj.project_name), 99999))

    q = q.orderby(proj.idx, order=Order.desc).orderby(proj.name)

    if page_len:
        q = q.limit(page_len)
    if start:
        q = q.offset(start)

    return q.run()
