import frappe
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice

def skip_customer_project_validation(doc, method):
    """Skip various customer validations"""
    # Skip customer field validations
    doc.flags.ignore_validate = True
    doc.flags.ignore_mandatory = True
    doc.flags.ignore_customer_validation = True

# Override the specific validation method
def validate_proj_cust(self):
    """Override to disable customer-project validation"""
    pass

# Override general validate method to catch other validations
original_validate = SalesInvoice.validate

def custom_validate(self):
    """Custom validate that skips customer restrictions"""
    try:
        # Temporarily store customer value
        original_customer = self.customer
        
        # Call original validate
        original_validate(self)
        
    except Exception as e:
        error_msg = str(e)
        # Skip customer-related validation errors
        if "Customer must be equal to" in error_msg or "does not belong to project" in error_msg:
            frappe.log_error(f"Skipped validation: {error_msg}", "Customer Validation Override")
            pass  # Skip this validation
        else:
            raise  # Re-raise other errors

# Apply monkey patches
SalesInvoice.validate_proj_cust = validate_proj_cust
SalesInvoice.validate = custom_validate
