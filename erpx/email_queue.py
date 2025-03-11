import frappe
from frappe.email.queue import get_email_queue

def check_and_send_email(doc, method):
    """
    Checks if an email in Email Queue has status 'Not Sent' and forces it to send.
    """
    if doc.status == "Not Sent":
        try:
            frappe.logger().info(f"Force sending email: {doc.name}")

            # Fetch the email data from the queue
            email_data = get_email_queue(doc.name)

            if email_data:
                # Send the email
                frappe.sendmail(
                    recipients=email_data.recipients,
                    subject=email_data.subject,
                    message=email_data.message,
                    attachments=email_data.attachments,
                    cc=email_data.cc,
                    bcc=email_data.bcc,
                    reply_to=email_data.reply_to,
                    headers=email_data.headers,
                    send_priority=email_data.send_priority
                )

                # Update the status to 'Sent'
                doc.status = "Sent"
                doc.save()

                frappe.logger().info(f"Email {doc.name} sent successfully.")
            else:
                frappe.logger().error(f"Email data not found for {doc.name}")
        except Exception as e:
            frappe.logger().error(f"Error sending email {doc.name}: {str(e)}")

