import frappe
from frappe.utils import getdate, nowdate, flt

@frappe.whitelist()
def allow_edit_submitted_invoice(invoice_id):
    """Allow editing of submitted invoice and recalculate outstanding amount"""
    try:
        invoice = frappe.get_doc("Sales Invoice", invoice_id)
        if invoice.docstatus == 1:
            original_posting_date = invoice.posting_date
            original_posting_time = invoice.posting_time
            invoice.db_set("docstatus", 0)
            invoice.set_posting_time = 1
            invoice.posting_date = original_posting_date
            invoice.posting_time = original_posting_time
            _recalculate_outstanding_amount(invoice)
            invoice.save(ignore_permissions=True)
        return invoice
    except Exception as e:
        frappe.throw(f"Error editing invoice: {str(e)}")

@frappe.whitelist()
def fix_payment_outstanding_amount(invoice_id):
    """Fix outstanding amount issues - uses GL entries for accuracy"""
    try:
        invoice = frappe.get_doc("Sales Invoice", invoice_id)

        # Calculate from GL entries (handles both payments and returns)
        gl_result = frappe.db.sql("""
            SELECT SUM(debit) - SUM(credit) as net
            FROM `tabGL Entry`
            WHERE account = %s
            AND party = %s
            AND party_type = 'Customer'
            AND is_cancelled = 0
            AND (voucher_no = %s OR against_voucher = %s)
        """, (invoice.debit_to, invoice.customer, invoice_id, invoice_id), as_dict=1)

        gl_net = flt(gl_result[0].net) if gl_result and gl_result[0].net is not None else flt(invoice.grand_total)
        correct_outstanding = max(gl_net, 0)  # Can't be negative

        # Update directly in database
        frappe.db.set_value('Sales Invoice', invoice_id, 'outstanding_amount', correct_outstanding)
        frappe.db.commit()

        # Reload
        invoice.reload()

        return {
            "status": "success",
            "message": f"Fixed outstanding amount for {invoice_id}",
            "grand_total": invoice.grand_total,
            "outstanding_amount": invoice.outstanding_amount
        }

    except Exception as e:
        frappe.log_error(f"Error fixing outstanding: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

@frappe.whitelist()
def finalize_invoice(invoice_id):
    """Submit the invoice and set correct status"""
    try:
        invoice = frappe.get_doc("Sales Invoice", invoice_id)
        if invoice.docstatus == 0:
            _recalculate_outstanding_amount(invoice)
            frappe.db.set_value("Sales Invoice", invoice_id, "docstatus", 1)
            frappe.db.commit()
            invoice.reload()
            try:
                frappe.db.sql("DELETE FROM `tabGL Entry` WHERE voucher_no = %s", (invoice_id,))
                frappe.db.commit()
                invoice.make_gl_entries()
                frappe.db.commit()
            except Exception:
                pass
            _recalculate_outstanding_amount(invoice)
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
        # Use db_set to bypass validation
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

def _recalculate_outstanding_amount(invoice):
    """Recalculate outstanding amount using GL entries"""
    try:
        original_status = invoice.status

        # Use GL entries to calculate outstanding (handles both payments and returns)
        gl_result = frappe.db.sql("""
            SELECT SUM(debit) - SUM(credit) as net
            FROM `tabGL Entry`
            WHERE account = %s
            AND party = %s
            AND party_type = 'Customer'
            AND is_cancelled = 0
            AND (voucher_no = %s OR against_voucher = %s)
        """, (invoice.debit_to, invoice.customer, invoice.name, invoice.name), as_dict=1)

        gl_net = flt(gl_result[0].net) if gl_result and gl_result[0].net is not None else flt(invoice.grand_total)
        correct_outstanding = max(gl_net, 0)

        # Update outstanding amount
        frappe.db.sql("""
            UPDATE `tabSales Invoice`
            SET outstanding_amount = %s
            WHERE name = %s
        """, (correct_outstanding, invoice.name))

        # Set status
        if original_status in ["Credit Note Issued", "Return", "Debit Note Issued"]:
            new_status = original_status
        else:
            if correct_outstanding == 0:
                new_status = "Paid"
            elif invoice.due_date and getdate(invoice.due_date) < getdate(nowdate()):
                new_status = "Overdue"
            else:
                new_status = "Unpaid"

        frappe.db.sql("""
            UPDATE `tabSales Invoice`
            SET status = %s
            WHERE name = %s
        """, (new_status, invoice.name))

        frappe.db.commit()

    except Exception as e:
        frappe.log_error(f"Error recalculating outstanding: {str(e)}")
