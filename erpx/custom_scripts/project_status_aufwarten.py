import frappe
from frappe import _

def validate_project_status(doc, method):
    """Allow custom status 'Aufwarten' for Project doctype"""
    allowed_statuses = ["Open", "Aufwarten", "Completed", "Cancelled"]
    
    if doc.status not in allowed_statuses:
        frappe.throw(_("Invalid status. Allowed statuses are: {0}").format(", ".join(allowed_statuses)))

def before_save_project(doc, method):
    """Store custom status flag before save"""
    if doc.status == "Aufwarten":
        doc._aufwarten_status = True

def after_save_project(doc, method):
    """Ensure custom status persists after save"""
    if hasattr(doc, '_aufwarten_status') and doc.status != "Aufwarten":
        frappe.db.set_value("Project", doc.name, "status", "Aufwarten")
        frappe.db.commit()

def override_project_methods():
    """Override Project validation to allow custom statuses"""
    try:
        from erpnext.projects.doctype.project.project import Project
        
        original_validate = Project.validate
        
        def custom_validate(self):
            # Skip original validation to prevent status reversion
            # original_validate(self)
            
            # Custom validation allowing our status
            allowed_statuses = ["Open", "Aufwarten", "Completed", "Cancelled"]
            if self.status not in allowed_statuses:
                frappe.throw(_("Invalid status. Allowed statuses are: {0}").format(", ".join(allowed_statuses)))
        
        Project.validate = custom_validate
        
    except Exception:
        pass

# Override methods when module loads
override_project_methods()
