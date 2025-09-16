__version__ = "0.0.1"

"""
ERPx App - Custom ERPNext Extensions

This module patches ERPNext's customer-project validation to allow
any customer to be associated with any project in Sales documents.
Applied at app startup to override default restrictive validation.
"""

# Force import the patching module
def patch_erpnext():
    try:
        from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice
        from erpnext.selling.doctype.sales_order.sales_order import SalesOrder
        from erpnext.stock.doctype.delivery_note.delivery_note import DeliveryNote
        
        # Create dummy validation that does nothing
        def dummy_validate_proj_cust(self):
            pass
        
        # Patch immediately
        SalesInvoice.validate_proj_cust = dummy_validate_proj_cust
        SalesOrder.validate_proj_cust = dummy_validate_proj_cust
        DeliveryNote.validate_proj_cust = dummy_validate_proj_cust
        
        print("Successfully patched customer-project validation")
    except Exception as e:
        print(f"Error patching: {e}")

# Run the patch immediately when app loads
patch_erpnext()
