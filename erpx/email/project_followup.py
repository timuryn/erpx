# File: erpx/erpx/email/project_followup.py
# Production-ready project followup notification system
# FIXED: Use email_id instead of account name + flush email queue

import frappe
from frappe.utils import getdate, add_days, nowdate

def check_project_timeline_activity(project):
    """Check if there was any recent activity in the project timeline that should reset the countdown"""
    try:
        # Get the most recent follow-up communication for this project
        existing_communications_old = frappe.get_all(
            'Communication',
            filters={
                'reference_doctype': 'Project',
                'reference_name': project.name,
                'subject': ['like', '%Nachakquise%'],
                'communication_type': 'Communication'
            },
            fields=['creation'],
            order_by='creation desc',
            limit=1
        )

        existing_communications_new = frappe.get_all(
            'Communication',
            filters={
                'subject': ['like', f'%Nachakquise%{project.name}%'],
                'communication_type': 'Communication'
            },
            fields=['creation'],
            order_by='creation desc',
            limit=1
        )

        # Get the most recent follow-up notification date
        last_followup_date = None

        if existing_communications_old:
            last_followup_date = getdate(existing_communications_old[0].creation)
        if existing_communications_new:
            new_date = getdate(existing_communications_new[0].creation)
            if last_followup_date is None or new_date > last_followup_date:
                last_followup_date = new_date

        # If no previous follow-up exists, use project creation date as reference
        if last_followup_date is None:
            reference_date = getdate(project.creation)
        else:
            reference_date = last_followup_date

        # Check for timeline activities since the reference date
        timeline_activities = []

        # Check for Communications (excluding our follow-up emails)
        communications = frappe.get_all(
            'Communication',
            filters={
                'reference_doctype': 'Project',
                'reference_name': project.name,
                'creation': ['>', reference_date.strftime('%Y-%m-%d %H:%M:%S')],
                'subject': ['not like', '%Nachakquise%'],
                'communication_type': ['!=', 'Automated Message']
            },
            fields=['creation']
        )
        timeline_activities.extend(communications)

        # Check for Comments
        comments = frappe.get_all(
            'Comment',
            filters={
                'reference_doctype': 'Project',
                'reference_name': project.name,
                'creation': ['>', reference_date.strftime('%Y-%m-%d %H:%M:%S')],
                'comment_type': ['!=', 'Workflow']
            },
            fields=['creation']
        )
        timeline_activities.extend(comments)

        # Check for Tasks related to the project
        tasks = frappe.get_all(
            'Task',
            filters={
                'project': project.name,
                'creation': ['>', reference_date.strftime('%Y-%m-%d %H:%M:%S')]
            },
            fields=['creation']
        )
        timeline_activities.extend(tasks)

        # Check if project itself was modified
        project_modified_date = getdate(project.modified)
        if project_modified_date > reference_date:
            versions = frappe.get_all(
                'Version',
                filters={
                    'ref_doctype': 'Project',
                    'docname': project.name,
                    'creation': ['>', reference_date.strftime('%Y-%m-%d %H:%M:%S')]
                },
                fields=['creation']
            )
            timeline_activities.extend(versions)

        return len(timeline_activities) > 0

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Project Followup - Timeline Activity Check Error")
        return False

def send_project_followup_notifications():
    """
    Check all projects created from 01.07.2025 and send follow-up emails:
    - First notification: 10 days after creation if not completed
    - Recurring notifications: Every 5 days after first notification if still not completed
    - Special case: If project status is "Aufwarten", wait 15 days before next notification
    - Timeline activity reset: Any new activity in project timeline resets the countdown
    - Excludes projects with status "Completed" or "Cancelled"
    """
    send_first_followup_notifications()
    send_recurring_followup_notifications()
    
    # IMPORTANT: Flush the email queue to actually send the emails
    frappe.log_error("Flushing email queue...", "Project Followup - Queue Flush")
    try:
        from frappe.email.queue import flush
        flush()
        frappe.log_error("Email queue flushed successfully", "Project Followup - Queue Flush")
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Project Followup - Queue Flush Error")

def send_first_followup_notifications():
    """Send first follow-up notification for projects at least 10 days old"""
    cutoff_date = "2025-07-01"
    today = nowdate()
    ten_days_ago = add_days(today, -10)

    projects = frappe.get_all(
        'Project',
        filters=[
            ['creation', '<=', ten_days_ago + ' 23:59:59'],
            ['creation', '>=', cutoff_date + ' 00:00:00'],
            ['status', 'not in', ['Completed', 'Cancelled']],
            ['owner', '!=', '']
        ],
        fields=['name', 'project_name', 'owner', 'status', 'creation', 'modified']
    )

    sent_count = 0
    skipped_count = 0

    for project in projects:
        current_project = frappe.get_doc('Project', project.name)

        # Skip if status changed after query
        if current_project.status in ['Completed', 'Cancelled']:
            skipped_count += 1
            continue

        # Skip if recent activity detected
        if check_project_timeline_activity(current_project):
            skipped_count += 1
            continue

        # Check if follow-up already sent
        existing_communication = frappe.get_all(
            'Communication',
            filters={
                'reference_doctype': 'Project',
                'reference_name': current_project.name,
                'subject': ['like', '%Nachakquise%'],
                'communication_type': 'Communication'
            },
            limit=1
        )

        if not existing_communication:
            if send_followup_email(current_project, notification_type="first", notification_number=1):
                sent_count += 1
            else:
                skipped_count += 1

    frappe.log_error(f"First notifications: {sent_count} sent, {skipped_count} skipped", "Project Followup Summary")

def send_recurring_followup_notifications():
    """Send recurring follow-up notifications every 5 days after the first notification"""
    cutoff_date = "2025-07-01"

    projects = frappe.get_all(
        'Project',
        filters=[
            ['creation', '>=', cutoff_date + ' 00:00:00'],
            ['status', 'not in', ['Completed', 'Cancelled']],
            ['owner', '!=', '']
        ],
        fields=['name', 'project_name', 'owner', 'status', 'creation', 'modified']
    )

    sent_count = 0
    skipped_count = 0

    for project in projects:
        current_project = frappe.get_doc('Project', project.name)

        # Skip if status changed after query
        if current_project.status in ['Completed', 'Cancelled']:
            skipped_count += 1
            continue

        # Skip if recent activity detected
        if check_project_timeline_activity(current_project):
            skipped_count += 1
            continue

        # Get existing follow-up communications
        existing_communications = frappe.get_all(
            'Communication',
            filters={
                'reference_doctype': 'Project',
                'reference_name': current_project.name,
                'subject': ['like', '%Nachakquise%'],
                'communication_type': 'Communication'
            },
            fields=['creation'],
            order_by='creation desc'
        )

        if existing_communications:
            last_notification_date = getdate(existing_communications[0].creation)

            # Determine interval based on project status
            if current_project.status == "Aufwarten":
                interval_days_ago = getdate(add_days(nowdate(), -15))
            else:
                interval_days_ago = getdate(add_days(nowdate(), -5))

            # Send if interval has passed (exact date match)
            if last_notification_date == interval_days_ago:
                notification_count = len(existing_communications) + 1
                if send_followup_email(current_project, notification_type="recurring", notification_number=notification_count):
                    sent_count += 1
                else:
                    skipped_count += 1

    frappe.log_error(f"Recurring notifications: {sent_count} sent, {skipped_count} skipped", "Project Followup Summary")

def send_followup_email(project, notification_type="first", notification_number=1):
    """Send follow-up email to project owner using the Notification email account"""
    try:
        # Final status check before sending
        project = frappe.get_doc('Project', project.name)
        if project.status in ['Completed', 'Cancelled']:
            return False

        owner = frappe.get_doc('User', project.owner)

        # Verify owner has email
        if not owner.email:
            frappe.log_error(
                f"Project owner {project.owner} has no email address",
                "Project Followup - No Email Address"
            )
            return False

        # Get Notification email account and extract the email address
        notification_email_account = frappe.get_value(
            'Email Account',
            filters={'email_id': 'notification@dippelwerbung.de'},
            fieldname='name'
        )

        if not notification_email_account:
            notification_email_account = frappe.get_value(
                'Email Account',
                filters={'name': 'Notification'},
                fieldname='name'
            )

        if not notification_email_account:
            frappe.log_error(
                "Notification email account not found. Create Email Account with name='Notification'",
                "Project Followup - Email Account Missing"
            )
            return False

        # IMPORTANT: Get the actual email address from the account, not the account name
        email_doc = frappe.get_doc('Email Account', notification_email_account)
        sender_email = email_doc.email_id

        # Generate email content
        project_link = f"https://rechnung.dippelwerbung.de/app/project/{project.name}"

        if notification_type == "first":
            subject = f"Nachakquise! - Erste Erinnerung - {project.project_name} ({project.name})"
            days_info = "vor 10 Tagen"
            urgency_message = "Bitte überprüfen Sie den Fortschritt und aktualisieren Sie den Status entsprechend."
        else:  # recurring notification
            if project.status == "Aufwarten":
                days_since_creation = 10 + (notification_number - 1) * 15
                status_note = '<p><em>Hinweis: Da das Projekt den Status "Aufwarten" hat, erfolgen Erinnerungen im 15-Tage-Intervall.</em></p>'
            else:
                days_since_creation = 10 + (notification_number - 1) * 5
                status_note = ""

            if notification_number == 2:
                subject = f"Nachakquise! - Zweite Erinnerung - {project.project_name} ({project.name})"
                urgency_message = f'<p><strong style="color: #d73502;">DRINGEND:</strong> Dieses Projekt benötigt Ihre Aufmerksamkeit!</p><p>Bitte aktualisieren Sie den Projektstatus oder wenden Sie sich an Ihren Vorgesetzten, falls Hindernisse bestehen.</p>{status_note}'
            elif notification_number == 3:
                subject = f"Nachakquise! - Dritte Erinnerung - {project.project_name} ({project.name})"
                urgency_message = f'<p><strong style="color: #d73502;">SEHR DRINGEND:</strong> Dieses Projekt ist überfällig!</p><p>Dies ist die dritte Erinnerung. Bitte nehmen Sie sofort Kontakt mit Ihrem Vorgesetzten auf und klären Sie den Status dieses Projekts.</p>{status_note}'
            elif notification_number >= 4:
                subject = f"Nachakquise! - {notification_number}. Erinnerung (KRITISCH) - {project.project_name} ({project.name})"
                urgency_message = f'<p><strong style="color: #b71c1c; background-color: #ffebee; padding: 5px;">⚠️ KRITISCH:</strong> Dieses Projekt ist kritisch überfällig!</p><p>Dies ist bereits die {notification_number}. Erinnerung für dieses Projekt. Eine sofortige Statusaktualisierung oder Eskalation an das Management ist erforderlich.</p>{status_note}'

            days_info = f"vor {days_since_creation} Tagen"

        message = f"""
        <p>Hallo {owner.full_name or owner.first_name or project.owner},</p>

        <p>Erinnerung: Das Projekt "<strong>{project.project_name}</strong>" wurde {days_info} erstellt und ist noch nicht abgeschlossen.</p>

        <p>Aktueller Status: <strong>{project.status}</strong></p>

        {urgency_message}

        <p>Den Link zum entsprechenden Projekt finden Sie unten:<br>
        <a href="{project_link}">Klicken Sie hier, um das Projekt anzuzeigen</a></p>

        <p><em>Dies ist eine automatische Erinnerung aus Ihrem Projektmanagement-System.</em></p>

        <p>Mit freundlichen Grüßen,<br>
        Ihr Projektmanagement-System</p>
        """

        # Create communication record with CORRECT email address
        communication = frappe.get_doc({
            'doctype': 'Communication',
            'communication_type': 'Communication',
            'communication_medium': 'Email',
            'sent_or_received': 'Sent',
            'subject': subject,
            'content': message,
            'sender': sender_email,  # Use email address, not account name!
            'recipients': owner.email,
            'send_email': True,
            'reference_doctype': 'Project',
            'reference_name': project.name
        })

        communication.insert(ignore_permissions=True)

        # Send the email with CORRECT email address
        frappe.sendmail(
            recipients=[owner.email],
            sender=sender_email,  # Use email address, not account name!
            subject=subject,
            message=message
        )

        frappe.log_error(f"Email sent: {project.name} - {subject}", "Project Followup - Email Sent")
        return True

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Project Followup - Email Send Error")
        return False
