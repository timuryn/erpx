import frappe
from frappe import _

ALLOWED_PROJECT_STATUSES = [
    "Completed",
    "Cancelled",
    "AN abgerechnet",
    "Aktion erforderlich!",
    "Angebot erforderlich",
    "Angebot fertig",
    "Auf Warten",
    "Aufmaß erforderlich",
    "Auftrag",
    "Bezahlt / Abgeschlossen",
    "Entwurf",
    "Produktion",
    "Rechnung erforderlich",
    "Rechnung raus"
]

def validate_project_status(doc, method):
    """Allow custom project statuses"""
    if doc.status not in ALLOWED_PROJECT_STATUSES:
        frappe.throw(_("Invalid status. Allowed statuses are: {0}").format(", ".join(ALLOWED_PROJECT_STATUSES)))

def before_save_project(doc, method):
    """Store custom status flag before save"""
    if doc.status in ALLOWED_PROJECT_STATUSES:
        doc._custom_status = doc.status

def after_save_project(doc, method):
    """Ensure custom status persists after save"""
    if hasattr(doc, '_custom_status') and doc._custom_status in ALLOWED_PROJECT_STATUSES:
        if doc.status != doc._custom_status:
            frappe.db.set_value("Project", doc.name, "status", doc._custom_status)
            frappe.db.commit()

def override_project_methods():
    """Override Project validation to allow custom statuses"""
    try:
        from erpnext.projects.doctype.project.project import Project
        
        def custom_validate(self):
            if self.status not in ALLOWED_PROJECT_STATUSES:
                frappe.throw(_("Invalid status. Allowed statuses are: {0}").format(", ".join(ALLOWED_PROJECT_STATUSES)))
        
        Project.validate = custom_validate
        
    except Exception:
        pass

override_project_methods()
