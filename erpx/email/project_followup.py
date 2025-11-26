# File: erpx/erpx/project_followup.py

import frappe
from frappe import _
from frappe.utils import getdate, add_days, nowdate

def check_project_timeline_activity(project):
    """
    Check if there was any recent activity in the project timeline that should reset the countdown
    Returns True if recent activity found, False otherwise
    """
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
        # Look for Communications, Comments, Tasks, etc. that are not follow-up emails
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

        # Check if project itself was modified (excluding our follow-up modifications)
        project_modified_date = getdate(project.modified)
        if project_modified_date > reference_date:
            # Check if the modification was not just due to our follow-up system
            # We can do this by checking if there are any recent Version docs for this project
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

        # If any timeline activity found, reset countdown
        return len(timeline_activities) > 0

    except Exception as e:
        # If error in checking, don't reset countdown (fail safe)
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

def send_first_followup_notifications():
    """
    Send first follow-up notification for projects created 10 days ago
    Excludes projects with recent timeline activity that resets the countdown
    """
    cutoff_date = "2025-07-01"
    today = nowdate()
    ten_days_ago = add_days(today, -10)

    # Get all projects created exactly 10 days ago
    # FIX: Use list-based filters with 'not in' operator for proper multiple status exclusion
    projects = frappe.get_all(
        'Project',
        filters=[
            ['creation', '>=', ten_days_ago + ' 00:00:00'],
            ['creation', '<=', ten_days_ago + ' 23:59:59'],
            ['status', 'not in', ['Completed', 'Cancelled']],
            ['owner', '!=', '']
        ],
        fields=['name', 'project_name', 'owner', 'status', 'creation', 'modified']
    )

    # Filter out projects created before July 1, 2025
    cutoff_date_obj = getdate(cutoff_date)
    filtered_projects = []

    for project in projects:
        project_creation_date = getdate(project.creation)
        if project_creation_date >= cutoff_date_obj:
            filtered_projects.append(project)

    for project in filtered_projects:
        # CRITICAL: Re-check project status from database to handle status changes after initial query
        current_project = frappe.get_doc('Project', project.name)
        if current_project.status in ['Completed', 'Cancelled']:
            continue
            
        # Check for recent activity in project timeline to reset countdown
        has_recent_activity = check_project_timeline_activity(current_project)

        if has_recent_activity:
            # Skip this project if there was recent activity that should reset the countdown
            continue

        # Check if any follow-up email was already sent (check both old and new format)
        existing_communication_old = frappe.get_all(
            'Communication',
            filters={
                'reference_doctype': 'Project',
                'reference_name': current_project.name,
                'subject': ['like', '%Nachakquise%'],
                'communication_type': 'Communication'
            }
        )

        existing_communication_new = frappe.get_all(
            'Communication',
            filters={
                'subject': ['like', f'%Nachakquise%{current_project.name}%'],
                'communication_type': 'Communication'
            }
        )

        # If no follow-up email exists in either format, send first one
        if not existing_communication_old and not existing_communication_new:
            send_followup_email(current_project, notification_type="first", notification_number=1)

def send_recurring_followup_notifications():
    """
    Send recurring follow-up notifications every 5 days after the first notification
    Special case: If project status is "Aufwarten", wait 15 days before next notification
    Excludes projects with recent timeline activity that resets the countdown
    """
    cutoff_date = "2025-07-01"

    # FIX: Use list-based filters with 'not in' operator
    projects = frappe.get_all(
        'Project',
        filters=[
            ['creation', '>=', cutoff_date + ' 00:00:00'],
            ['status', 'not in', ['Completed', 'Cancelled']],
            ['owner', '!=', '']
        ],
        fields=['name', 'project_name', 'owner', 'status', 'creation', 'modified']
    )

    for project in projects:
        # CRITICAL: Re-check project status from database to handle status changes after initial query
        current_project = frappe.get_doc('Project', project.name)
        if current_project.status in ['Completed', 'Cancelled']:
            continue
            
        # Check for recent activity in project timeline to reset countdown
        has_recent_activity = check_project_timeline_activity(current_project)

        if has_recent_activity:
            # Skip this project if there was recent activity that should reset the countdown
            continue

        # Get existing follow-up communications for this project (check both old and new format)
        existing_communications_old = frappe.get_all(
            'Communication',
            filters={
                'reference_doctype': 'Project',
                'reference_name': current_project.name,
                'subject': ['like', '%Nachakquise%'],
                'communication_type': 'Communication'
            },
            fields=['creation', 'subject'],
            order_by='creation desc'
        )

        existing_communications_new = frappe.get_all(
            'Communication',
            filters={
                'subject': ['like', f'%Nachakquise%{current_project.name}%'],
                'communication_type': 'Communication'
            },
            fields=['creation', 'subject'],
            order_by='creation desc'
        )

        # Combine and sort all communications by creation date
        all_communications = existing_communications_old + existing_communications_new
        if all_communications:
            all_communications = sorted(all_communications, key=lambda x: x.creation, reverse=True)

            # Get the most recent notification
            last_notification = all_communications[0]
            last_notification_date = getdate(last_notification.creation)

            # Determine the interval based on project status
            if current_project.status == "Aufwarten":
                # For "Aufwarten" status, wait 15 days before next notification
                interval_days = 15
                interval_days_ago = getdate(add_days(nowdate(), -15))
            else:
                # For all other statuses, use normal 5-day interval
                interval_days = 5
                interval_days_ago = getdate(add_days(nowdate(), -5))

            # Check if EXACTLY the specified interval has passed since the last notification
            if last_notification_date == interval_days_ago:
                # Calculate which notification number this will be
                notification_count = len(all_communications) + 1
                send_followup_email(current_project, notification_type="recurring", notification_number=notification_count)

def send_followup_email(project, notification_type="first", notification_number=1):
    """
    Send follow-up email to project owner
    """
    try:
        # CRITICAL: Final status check before sending email
        # Reload project from database to ensure we have the latest status
        project = frappe.get_doc('Project', project.name)
        if project.status in ['Completed', 'Cancelled']:
            return False
            
        # Get project owner details
        owner = frappe.get_doc('User', project.owner)

        # Create project link
        project_link = f"https://rechnung.dippelwerbung.de/app/project/{project.name}"

        # Customize content based on notification type and number
        if notification_type == "first":
            subject = f"Nachakquise! - Erste Erinnerung - {project.project_name} ({project.name})"
            days_info = "vor 10 Tagen"
            urgency_message = "Bitte überprüfen Sie den Fortschritt und aktualisieren Sie den Status entsprechend."
        else:  # recurring notification
            # Calculate days since creation based on project status
            if project.status == "Aufwarten":
                # For "Aufwarten" status: 10 + (notification_number-1) * 15
                days_since_creation = 10 + (notification_number - 1) * 15
                status_note = '<p><em>Hinweis: Da das Projekt den Status "Aufwarten" hat, erfolgen Erinnerungen im 15-Tage-Intervall.</em></p>'
            else:
                # For other statuses: 10 + (notification_number-1) * 5
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

        # Email content
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

        # Create communication record (without reference fields to avoid showing in project)
        communication = frappe.get_doc({
            'doctype': 'Communication',
            'communication_type': 'Communication',
            'communication_medium': 'Email',
            'sent_or_received': 'Sent',
            'subject': subject,
            'content': message,
            'sender': owner.email,
            'recipients': owner.email,
            'send_email': True
        })

        communication.insert(ignore_permissions=True)

        # Send the email using owner's email account (without reference fields)
        frappe.sendmail(
            recipients=[owner.email],
            sender=owner.email,
            subject=subject,
            message=message
        )

        # Force immediate email sending
        try:
            frappe.enqueue("frappe.email.queue.flush", queue="short")
        except Exception as e:
            pass
        
        return True

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Project Followup Email Error")
        return False

# Usage:
# bench execute erpx.erpx.project_followup.send_project_followup_notifications
