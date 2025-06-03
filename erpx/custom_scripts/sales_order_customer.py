import frappe
from erpnext.selling.doctype.sales_order.sales_order import SalesOrder

def skip_customer_project_validation(doc, method):
    """Skip various customer validations"""
    doc.flags.ignore_validate = True
    doc.flags.ignore_mandatory = True
    doc.flags.ignore_customer_validation = True

# Override the specific validation method
def validate_proj_cust(self):
    """Override to disable customer-project validation"""
    pass

# Override general validate method to catch other validations
original_validate = SalesOrder.validate

def custom_validate(self):
    """Custom validate that skips customer restrictions"""
    try:
        original_validate(self)
    except Exception as e:
        error_msg = str(e)
        if "Customer must be equal to" in error_msg or "does not belong to project" in error_msg:
            frappe.log_error(f"Skipped validation: {error_msg}", "Customer Validation Override - Sales Order")
            pass
        else:
            raise

# Apply monkey patches
SalesOrder.validate_proj_cust = validate_proj_cust
SalesOrder.validate = custom_validate
