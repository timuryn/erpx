import quopri
import email.utils
import frappe.email.email_body as email_body
from frappe.email.doctype.email_queue.email_queue import SendMailContext
from frappe.utils import get_url
from frappe.utils.verified_command import get_signed_params


# --- X-Frappe-Site header removal ---
def remove_frappe_fingerprint(email_obj):
    """Hook: make_email_body_message
    Removes the X-Frappe-Site header that identifies the sending system as Frappe/ERPNext.
    """
    if "X-Frappe-Site" in email_obj.msg_root:
        del email_obj.msg_root["X-Frappe-Site"]


# --- Message-ID: kept at the site's own domain (rechnung.dippelwerbung.de),
# used as the Sieve routing marker for ERPNext_Gesendet / ERPNext_Posteingang ---
def _custom_get_message_id():
    return email.utils.make_msgid(domain="rechnung.dippelwerbung.de")


email_body.get_message_id = _custom_get_message_id


# --- Tracking pixel: add alt="" so it doesn't get flagged ---
def _custom_get_tracker_str(self, recipient_email) -> str:
    """Same logic as Frappe core's SendMailContext.get_tracker_str, with alt=""
    added so the tracking pixel doesn't get flagged by spam/accessibility checks.
    """
    tracker_url = ""
    if self.queue_doc.get("email_read_tracker_url"):
        email_read_tracker_url = self.queue_doc.email_read_tracker_url
        params = {
            "recipient_email": recipient_email,
            "reference_name": self.queue_doc.reference_name,
            "reference_doctype": self.queue_doc.reference_doctype,
        }
        tracker_url = get_url(f"{email_read_tracker_url}?{get_signed_params(params)}")
    elif (
        self.email_account_doc
        and self.email_account_doc.track_email_status
        and self.queue_doc.communication
    ):
        tracker_url = f"{get_url()}/api/method/frappe.core.doctype.communication.email.mark_email_as_seen?name={self.queue_doc.communication}"
    if tracker_url:
        tracker_url_html = f'<img src="{tracker_url}" alt=""/>'
        return quopri.encodestring(tracker_url_html.encode()).decode()
    return ""


SendMailContext.get_tracker_str = _custom_get_tracker_str
