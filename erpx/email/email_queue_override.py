import frappe
from frappe.email.doctype.email_queue.email_queue import EmailQueue


class CustomEmailQueue(EmailQueue):
    def update_status(self, status, commit=False, **kwargs):
        super().update_status(status, commit=commit, **kwargs)

        # update_db() only writes to the DB — sync the in-memory doc
        # so the handler sees the final values
        self.status = status
        if "error" in kwargs:
            self.error = kwargs["error"]

        if status == "Error":
            try:
                from erpx.email.email_queue_error import on_email_queue_update
                on_email_queue_update(self, "update_status")
            except Exception:
                frappe.log_error(frappe.get_traceback(), "Email Queue error notification failed")
