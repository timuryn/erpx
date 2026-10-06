frappe.ui.form.Sidebar.prototype.refresh = function () {
    this.page.sidebar.removeClass("hide-sidebar");
    this.sidebar.toggle(true);

    const docinfo = this.frm.get_docinfo ? this.frm.get_docinfo() : null;

    this.frm.assign_to && this.frm.assign_to.refresh();
    this.frm.attachments && this.frm.attachments.refresh();
    if (this.frm.shared && docinfo && docinfo.shared) {
        this.frm.shared.refresh();
    }
    this.frm.tags && this.frm.tags.refresh(docinfo && docinfo.tags);
};

// Default to full width unless the user has explicitly toggled it off
$(document).ready(function () {
    if (localStorage.container_fullwidth === undefined) {
        localStorage.container_fullwidth = "true";
    }
    frappe.ui.toolbar.set_fullwidth_if_enabled();
});
