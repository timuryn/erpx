import frappe
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice
from erpnext.selling.doctype.sales_order.sales_order import SalesOrder
from erpnext.stock.doctype.delivery_note.delivery_note import DeliveryNote

# Patch the classes directly
def dummy_validate_proj_cust(self):
    """Dummy validation that does nothing"""
    pass

# Apply patches
SalesInvoice.validate_proj_cust = dummy_validate_proj_cust
SalesOrder.validate_proj_cust = dummy_validate_proj_cust
DeliveryNote.validate_proj_cust = dummy_validate_proj_cust

def skip_customer_project_validation(doc, method):
    """This ensures the patch is applied"""
    pass
