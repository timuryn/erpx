# File: erpx/erpx/project_followup.py

import frappe
from frappe import _
from frappe.utils import getdate, add_days, nowdate

def send_project_followup_notifications():
    """
    Check all projects created from 01.07.2025 and send follow-up emails:
    - First notification: 10 days after creation if not completed
    - Recurring notifications: Every 5 days after first notification if still not completed
    """
    
    # Send first follow-up notifications (10 days after creation)
    send_first_followup_notifications()
    
    # Send recurring follow-up notifications (every 5 days after first notification)
    send_recurring_followup_notifications()

def send_first_followup_notifications():
    """
    Send first follow-up notification for projects created 10 days ago
    """
    # Calculate the date 10 days ago
    ten_days_ago = add_days(nowdate(), -10)
    
    # Only check projects created from July 1, 2025 onwards
    cutoff_date = "2025-07-01"
    
    # Get projects created exactly 10 days ago that are not completed
    projects = frappe.get_all(
        'Project',
        filters={
            'creation': ['>=', ten_days_ago + ' 00:00:00'],
            'creation': ['<=', ten_days_ago + ' 23:59:59'],
            'creation': ['>=', cutoff_date + ' 00:00:00'],  # Only from July 1, 2025
            'status': ['!=', 'Completed'],
            'owner': ['!=', '']
        },
        fields=['name', 'project_name', 'owner', 'status', 'creation']
    )
    
    for project in projects:
        # Check if any follow-up email was already sent
        existing_communication = frappe.get_all(
            'Communication',
            filters={
                'reference_doctype': 'Project',
                'reference_name': project.name,
                'subject': ['like', '%Nachakquise%'],
                'communication_type': 'Communication'
            }
        )
        
        # If no follow-up email exists, send first one
        if not existing_communication:
            send_followup_email(project, notification_type="first", notification_number=1)

def send_recurring_followup_notifications():
    """
    Send recurring follow-up notifications every 5 days after the first notification
    """
    # Get all projects created from July 1, 2025 that are still not completed and have received at least one notification
    cutoff_date = "2025-07-01"
    
    projects = frappe.get_all(
        'Project',
        filters={
            'creation': ['>=', cutoff_date + ' 00:00:00'],  # Only from July 1, 2025
            'status': ['!=', 'Completed'],
            'owner': ['!=', '']
        },
        fields=['name', 'project_name', 'owner', 'status', 'creation']
    )
    
    for project in projects:
        # Get all existing follow-up communications for this project, ordered by creation date
        existing_communications = frappe.get_all(
            'Communication',
            filters={
                'reference_doctype': 'Project',
                'reference_name': project.name,
                'subject': ['like', '%Nachakquise%'],
                'communication_type': 'Communication'
            },
            fields=['creation', 'subject'],
            order_by='creation desc'
        )
        
        # If there are existing notifications
        if existing_communications:
            # Get the most recent notification
            last_notification = existing_communications[0]
            last_notification_date = getdate(last_notification.creation)
            
            # Check if EXACTLY 5 days have passed since the last notification
            five_days_ago = getdate(add_days(nowdate(), -5))
            
            if last_notification_date == five_days_ago:
                # Calculate which notification number this will be
                notification_count = len(existing_communications) + 1
                send_followup_email(project, notification_type="recurring", notification_number=notification_count)

def send_followup_email(project, notification_type="first", notification_number=1):
    """
    Send follow-up email to project owner
    notification_type: "first" or "recurring"
    notification_number: number of the notification (1, 2, 3, etc.)
    """
    try:
        # Get project owner details
        owner = frappe.get_doc('User', project.owner)
        
        # Create project link
        project_link = f"http://192.168.178.180:8080/app/project/{project.name}"
        
        # Customize content based on notification type and number
        if notification_type == "first":
            subject = "Nachakquise! - Erste Erinnerung"
            days_info = "vor 10 Tagen"
            urgency_message = "Bitte überprüfen Sie den Fortschritt und aktualisieren Sie den Status entsprechend."
        else:  # recurring notification
            # Calculate days since creation (10 + (notification_number-1) * 5)
            days_since_creation = 10 + (notification_number - 1) * 5
            
            if notification_number == 2:
                subject = "Nachakquise! - Zweite Erinnerung"
                urgency_message = '<p><strong style="color: #d73502;">DRINGEND:</strong> Dieses Projekt benötigt Ihre Aufmerksamkeit!</p><p>Bitte aktualisieren Sie den Projektstatus oder wenden Sie sich an Ihren Vorgesetzten, falls Hindernisse bestehen.</p>'
            elif notification_number == 3:
                subject = "Nachakquise! - Dritte Erinnerung"
                urgency_message = '<p><strong style="color: #d73502;">SEHR DRINGEND:</strong> Dieses Projekt ist überfällig!</p><p>Dies ist die dritte Erinnerung. Bitte nehmen Sie sofort Kontakt mit Ihrem Vorgesetzten auf und klären Sie den Status dieses Projekts.</p>'
            elif notification_number >= 4:
                subject = f"Nachakquise! - {notification_number}. Erinnerung (KRITISCH)"
                urgency_message = f'<p><strong style="color: #b71c1c; background-color: #ffebee; padding: 5px;">⚠️ KRITISCH:</strong> Dieses Projekt ist kritisch überfällig!</p><p>Dies ist bereits die {notification_number}. Erinnerung für dieses Projekt. Eine sofortige Statusaktualisierung oder Eskalation an das Management ist erforderlich.</p>'
            
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
        
        # Create communication record
        communication = frappe.get_doc({
            'doctype': 'Communication',
            'communication_type': 'Communication',
            'communication_medium': 'Email',
            'sent_or_received': 'Sent',
            'reference_doctype': 'Project',
            'reference_name': project.name,
            'subject': subject,
            'content': message,
            'sender': owner.email,
            'recipients': owner.email,
            'send_email': True
        })
        
        communication.insert(ignore_permissions=True)
        
        # Send the email using owner's email account
        frappe.sendmail(
            recipients=[owner.email],
            sender=owner.email,
            subject=subject,
            message=message,
            reference_doctype='Project',
            reference_name=project.name
        )
        
        # Force immediate email sending
        try:
            frappe.enqueue("frappe.email.queue.flush", queue="short")
        except Exception as e:
            pass
        
        frappe.logger().info(f"Follow-up email sent for project {project.name} to {owner.email}")
        
    except Exception as e:
        frappe.logger().error(f"Error sending follow-up email for project {project.name}: {str(e)}")
        frappe.log_error(f"Project Follow-up Email Error: {str(e)}")

# Usage:
# bench execute erpx.erpx.project_followup.send_project_followup_notifications
