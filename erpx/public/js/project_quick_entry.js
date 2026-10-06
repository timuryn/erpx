// apps/erpx/erpx/public/js/project_quick_entry.js
frappe.provide("frappe.ui.form");

frappe.ui.form.ProjectQuickEntryForm = class ProjectQuickEntryForm extends frappe.ui.form.QuickEntryForm {
    render_dialog() {
        this.mandatory = (this.mandatory || []).filter(df => df.fieldname !== "naming_series");
        super.render_dialog();
    }
};
