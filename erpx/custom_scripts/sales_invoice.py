import frappe
from frappe import _
from frappe.utils import getdate, nowdate, flt

@frappe.whitelist()
def allow_edit_submitted_invoice(invoice_id):
    """Allow editing of submitted invoice by properly canceling GL entries"""
    try:
        invoice = frappe.get_doc("Sales Invoice", invoice_id)
        if invoice.docstatus == 1:
            # Store original values
            original_posting_date = invoice.posting_date
            original_posting_time = invoice.posting_time

            # CRITICAL: Cancel existing GL entries to avoid double-counting
            from erpnext.accounts.general_ledger import make_reverse_gl_entries
            make_reverse_gl_entries(voucher_type="Sales Invoice", voucher_no=invoice_id)

            # Set to draft
            invoice.db_set("docstatus", 0)
            invoice.set_posting_time = 1
            invoice.posting_date = original_posting_date
            invoice.posting_time = original_posting_time

            # Clear outstanding to recalculate from scratch
            invoice.db_set("outstanding_amount", invoice.grand_total)

            invoice.save(ignore_permissions=True)
            frappe.db.commit()

        return invoice
    except Exception as e:
        frappe.throw(f"Error editing invoice: {str(e)}")

@frappe.whitelist()
def finalize_invoice(invoice_id):
    """Submit the invoice using standard ERPNext methods"""
    try:
        invoice = frappe.get_doc("Sales Invoice", invoice_id)
        if invoice.docstatus == 0:
            # Make sure there are no stale GL entries before submitting
            frappe.db.sql("""
                DELETE FROM `tabGL Entry`
                WHERE voucher_no = %s AND voucher_type = 'Sales Invoice'
            """, (invoice_id,))
            frappe.db.commit()

            # Use standard submit method - this handles GL entries and status automatically
            invoice.submit()
            invoice.reload()

        return invoice.status
    except Exception as e:
        frappe.throw(f"Failed to submit invoice: {str(e)}")

@frappe.whitelist()
def update_invoice_status_to_credit_note_issued(invoice_name):
    """
    Update the status of a Sales Invoice to 'Credit Note Issued'
    This bypasses the validation by using db_set which doesn't trigger validations
    """
    try:
        frappe.db.set_value('Sales Invoice', invoice_name, 'status', 'Credit Note Issued', update_modified=False)
        frappe.db.commit()

        return {
            'status': 'success',
            'message': f'Status updated to Credit Note Issued for {invoice_name}'
        }
    except Exception as e:
        frappe.log_error(f"Error updating status for {invoice_name}: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }

@frappe.whitelist()
def fix_invoice_outstanding_amount(invoice_id):
    """
    Fix outstanding amount for invoices that have duplicate/incorrect GL entries
    This cleans up GL entries and recalculates everything from scratch
    """
    try:
        invoice = frappe.get_doc("Sales Invoice", invoice_id)

        # Step 1: Delete ALL GL entries for this invoice
        frappe.db.sql("""
            DELETE FROM `tabGL Entry`
            WHERE voucher_no = %s AND voucher_type = 'Sales Invoice'
        """, (invoice_id,))
        frappe.db.commit()

        # Step 2: If invoice is submitted, recreate GL entries
        if invoice.docstatus == 1:
            invoice.make_gl_entries()
            frappe.db.commit()

        # Step 3: Calculate outstanding from GL entries
        gl_outstanding = frappe.db.sql("""
            SELECT SUM(debit) - SUM(credit) as outstanding
            FROM `tabGL Entry`
            WHERE (voucher_no = %s OR against_voucher = %s)
            AND party_type = 'Customer'
            AND party = %s
            AND is_cancelled = 0
        """, (invoice_id, invoice_id, invoice.customer), as_dict=1)

        calculated_outstanding = gl_outstanding[0].outstanding if gl_outstanding and gl_outstanding[0].outstanding else invoice.grand_total

        # Step 4: Update outstanding amount
        frappe.db.sql("""
            UPDATE `tabSales Invoice`
            SET outstanding_amount = %s
            WHERE name = %s
        """, (calculated_outstanding, invoice_id))
        frappe.db.commit()

        # Step 5: Update status
        invoice.reload()
        invoice.set_status(update=True)
        frappe.db.commit()

        return {
            'status': 'success',
            'message': f'Fixed outstanding amount for {invoice_id}',
            'grand_total': invoice.grand_total,
            'outstanding_amount': invoice.outstanding_amount,
            'current_status': invoice.status
        }

    except Exception as e:
        frappe.log_error(f"Error fixing outstanding for {invoice_id}: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }

@frappe.whitelist()
def fix_payment_outstanding_amount(invoice_id):
    """
    Legacy function name - calls fix_invoice_outstanding_amount
    Kept for backward compatibility with Gutschrift script
    """
    return fix_invoice_outstanding_amount(invoice_id)

@frappe.whitelist()
def update_project_on_submitted_invoice(invoice_id, project_id=None):
    """
    Update project on a submitted Sales Invoice
    Uses direct database update to bypass all validations
    """
    try:
        # Get the invoice document
        invoice = frappe.get_doc('Sales Invoice', invoice_id)
        
        # Check if invoice is submitted
        if invoice.docstatus != 1:
            frappe.throw(_('Invoice must be submitted to update project'))
        
        # Use direct database update to bypass ALL validations
        frappe.db.set_value('Sales Invoice', invoice_id, 'project', project_id if project_id else None, update_modified=True)
        frappe.db.commit()
        
        return {
            'status': 'success',
            'message': _('Project updated successfully')
        }
    except Exception as e:
        frappe.log_error(f"Error updating project for {invoice_id}: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }
