import frappe
from frappe import _

def get_custom_fields():
    """Override einvoice_profile default to EN 16931 for both Customer and Sales Invoice"""
    return {
        "Customer": [
            {
                "fieldname": "einvoice_profile",
                "label": _("E Invoice Profile"),
                "fieldtype": "Select",
                "options": "\nBASIC\nEN 16931\nEXTENDED\nXRECHNUNG",
                "default": "EN 16931",  # Set default for customers
                "insert_after": "buyer_reference",
                "print_hide": 1,
            }
        ],
        "Sales Invoice": [
            {
                "fieldname": "einvoice_profile",
                "label": _("E Invoice Profile"),
                "fieldtype": "Select",
                "options": "\nBASIC\nEN 16931\nEXTENDED\nXRECHNUNG",
                "default": "EN 16931",  # Override default
                "fetch_from": "customer.einvoice_profile",  # Still fetch from customer
                "fetch_if_empty": 1,  # But customer now defaults to EN 16931
                "insert_after": "e_invoice_validation_section",
                "print_hide": 1,
            }
        ]
    }

def execute():
    """Execute custom field creation/update"""
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    create_custom_fields(get_custom_fields(), update=True)
