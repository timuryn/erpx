app_name = "erpx"
app_title = "erpx"
app_publisher = "Timur Matsiev"
app_description = "mods for erpnext"
app_email = "timur@dippelwerbung.de"
app_license = "mit"

# Quick entries override
app_include_js = [
    "assets/erpx/js/customer_quick_entry.js",
    "assets/erpx/js/item_quick_entry.js",
    "assets/erpx/js/sidebar_inject.js",
    "assets/erpx/js/supplier_quick_entry.js",
    "/assets/erpx/js/navbar_search_clean_url.js"
]

# Bigger notification bell and Page width
app_include_css = [
    "/assets/erpx/css/notification_style.css",
    "/assets/erpx/css/desk_layout.css"
]

# Send email immediately and override custom status Aufwarten for project
doc_events = {
    "Email Queue": {
    "after_insert": "erpx.email.email_queue.check_and_send_email"
    },
    "Project": {
        "before_save": "erpx.custom_scripts.project_status_aufwarten.before_save_project",
        "validate": "erpx.custom_scripts.project_status_aufwarten.validate_project_status",
        "on_update": "erpx.custom_scripts.project_status_aufwarten.after_save_project"
    },
    "Sales Invoice": {
        "before_print": "erpx.epcqrcode.sales_invoice.before_print"
    }
}

override_doctype_class = {
    "Email Queue": "erpx.email.email_queue_override.CustomEmailQueue"
}

# Project link button and heatmap
doctype_js = {
    "Supplier": "public/js/supplier_quick_entry.js"
}

override_doctype_dashboards = {
    "Project": "erpx.custom_scripts.project_dashboard.get_data"
}

# Project connections with Quotation
doctype_dashboard_hooks = {
    "Project": {
        "custom_links": {
            "Quotation": "custom_projektlink"
        }
    }
}

# Override pdf print for public domain
import frappe.utils.pdf
from .pdf_override import get_pdf as custom_get_pdf
frappe.utils.pdf.get_pdf = custom_get_pdf

# Set default einvoice profile to EN 16931
# Run after installation
after_install = "erpx.custom_scripts.custom_fields_einvoice.execute"
# Run after every migration/update
after_migrate = "erpx.custom_scripts.custom_fields_einvoice.execute"

# Override ERPNext query methods to allow completed projects
override_whitelisted_methods = {
    "erpnext.controllers.queries.get_project_name": "erpx.custom_scripts.queries.get_project_name"
}

# Override eu_einvoice §13b UStG tax category
def _setup_einvoice_13b_override():
        try:
                from eu_einvoice.european_e_invoice.custom.sales_invoice import EInvoiceGenerator
                original_add_line_item = EInvoiceGenerator._add_line_item
                original_create_einvoice = EInvoiceGenerator.create_einvoice

                def _is_reverse_charge(self):
                        return any(
                                tax.charge_type == "On Net Total" and not tax.rate
                                for tax in self.invoice.taxes
                        )

                def patched_add_line_item(self, item):
                        original_add_line_item(self, item)
                        if _is_reverse_charge(self):
                                if self.doc.trade.items.children:
                                        last_li = self.doc.trade.items.children[-1]
                                        last_li.settlement.trade_tax.category_code = "AE"

                def patched_create_einvoice(self):
                        original_create_einvoice(self)
                        if _is_reverse_charge(self):
                                if self.doc.trade.settlement.trade_tax.children:
                                        header_tax = self.doc.trade.settlement.trade_tax.children[0]
                                        header_tax.category_code = "AE"
                                        header_tax.exemption_reason_code = "VATEX-EU-AE"

                EInvoiceGenerator._add_line_item = patched_add_line_item
                EInvoiceGenerator.create_einvoice = patched_create_einvoice
        except Exception:
                pass
_setup_einvoice_13b_override()

# Override outgoing email Message-ID domain and strip Frappe fingerprint header
from .email import email_body_override  # noqa: F401  (import triggers the monkey-patch)

make_email_body_message = ["erpx.email.email_body_override.remove_frappe_fingerprint"]
