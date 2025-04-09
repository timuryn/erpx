import frappe

def check_and_send_email(doc, method):
    """
    When an Email Queue doc is inserted with status 'Not Sent',
    enqueue the flush job to process all pending emails.
    """
    if doc.status == "Not Sent":
        try:
            frappe.logger().info(f"[erpx] Queuing email flush triggered by: {doc.name}")
            frappe.enqueue("frappe.email.queue.flush", queue="short")
        except Exception as e:
            frappe.logger().error(f"[erpx] Failed to enqueue email flush for {doc.name}: {str(e)}")

