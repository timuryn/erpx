import frappe
from email.parser import Parser
from email.policy import SMTP

NOTIFY_SUBJECT = "E-Mail-Versand fehlgeschlagen"


def on_email_queue_update(doc, method):
    """Send notification when Email Queue status changes to Error"""
    frappe.logger().warning(f"[EMAIL_QUEUE] Hook fired: {doc.name}, status={doc.status}, method={method}")

    if doc.status != "Error":
        return

    # Loop guard: never alert about a failed alert email
    original_subject = _get_subject(doc)
    if NOTIFY_SUBJECT in original_subject:
        frappe.logger().warning(f"[EMAIL_QUEUE] Skipping notification-about-notification for {doc.name}")
        return

    frappe.logger().warning(f"[EMAIL_QUEUE] Processing error for {doc.name}")

    # Details straight from the doc — reliable for every error type
    sender = doc.sender or "Unknown"
    recipient = ", ".join(r.recipient for r in doc.recipients) or "Unknown"
    error_msg = _get_error_summary(doc.error)

    try:
        notification_account = frappe.get_value(
            'Email Account',
            filters={'email_id': 'notification@dippelwerbung.de'},
            fieldname='name'
        ) or frappe.get_value('Email Account', filters={'name': 'Notification'}, fieldname='name')

        if not notification_account:
            return

        notification_email = frappe.get_doc('Email Account', notification_account).email_id

        message = f"""
        <p><strong>E-Mail konnte nicht versendet werden</strong></p>
        <p><b>Betreff:</b> {original_subject or '–'}</p>
        <p><b>Empfänger:</b> {recipient}</p>
        <p><b>Absender:</b> {sender}</p>
        <p><b>Fehler:</b> {error_msg}</p>
        <p><a href="/app/email-queue/{doc.name}">Email Queue anzeigen →</a></p>
        """

        subject_parts = [NOTIFY_SUBJECT]
        if recipient != "Unknown":
            subject_parts.append(recipient)
        if original_subject:
            subject_parts.append(original_subject)

        frappe.sendmail(
            recipients=['info@dippelwerbung.de'],
            sender=notification_email,
            subject=" – ".join(subject_parts),
            message=message
        )
        frappe.logger().warning(f"[EMAIL_QUEUE] Notification sent for {doc.name}")

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Email Queue Error")


def _get_subject(doc):
    """Read the Subject header from the raw MIME message"""
    try:
        return Parser(policy=SMTP).parsestr(doc.message or "")["Subject"] or ""
    except Exception:
        return ""


def _get_error_summary(error):
    """Last line of the traceback = the actual exception"""
    if not error:
        return "Email send failed"
    lines = [l.strip() for l in error.strip().splitlines() if l.strip()]
    return lines[-1] if lines else "Email send failed"
