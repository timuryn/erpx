import frappe
from erpx.epcqrcode.generator import get_qr_html

def before_print(doc, method=None, print_format=None):
    """Generate QR code HTML before printing"""
    if not hasattr(doc, '_qr_generated'):
        bank_iban = frappe.db.get_value(
            "Bank Account",
            filters={"company": doc.company},
            fieldname="iban"
        )

        if bank_iban:
            doc.qr_code_html = get_qr_html(
                name=doc.company,
                reference=doc.name,
                iban=bank_iban,
                amount=doc.grand_total
            )
        else:
            doc.qr_code_html = ""

        doc._qr_generated = True
