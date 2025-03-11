import frappe
import zipfile
import io
import requests
from urllib.parse import quote

@frappe.whitelist()
def download_selected_sales_invoices(selected_invoices):
    ERP_URL = "http://192.168.178.180:8080"  # Your ERPNext instance URL
    API_KEY = "08c7d11f154511f"  # Your API Key
    API_SECRET = "3cfbd25115db034"  # Your API Secret
    ZIP_FILENAME = "rechnungen.zip"

    headers = {"Authorization": f"token {API_KEY}:{API_SECRET}"}

    selected_invoices = selected_invoices.split(',')
    if not selected_invoices:
        frappe.throw("Keine Rechnungen ausgewählt")

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for invoice_id in selected_invoices:
            pdf_url = f"{ERP_URL}/api/method/frappe.utils.print_format.download_pdf?doctype=Sales Invoice&name={quote(invoice_id)}&format=Rechnung&no_letterhead=0"
            pdf_response = requests.get(pdf_url, headers=headers)

            if pdf_response.status_code == 200:
                zipf.writestr(f"{invoice_id}.pdf", pdf_response.content)

    zip_buffer.seek(0)
    frappe.response["filecontent"] = zip_buffer.read()
    frappe.response["type"] = "download"
    frappe.response["filename"] = ZIP_FILENAME

