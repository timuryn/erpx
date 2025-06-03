import frappe
import zipfile
import io
import requests
from urllib.parse import quote
import concurrent.futures
import time
import json
import csv
import os

@frappe.whitelist()
def download_selected_sales_invoices(selected_invoices=None, from_date=None, to_date=None):
    """
    Download Sales Invoice PDFs as a ZIP file
    
    Args:
        selected_invoices (str, optional): Comma-separated list of invoice names
        from_date (str, optional): Start date for filtering invoices
        to_date (str, optional): End date for filtering invoices
    """
    # Get configuration from site_config.json
    ERP_URL = frappe.conf.get("erp_url")
    API_KEY = frappe.conf.get("api_key")
    API_SECRET = frappe.conf.get("api_secret")
    
    # Validate configuration
    if not ERP_URL or not API_KEY or not API_SECRET:
        frappe.throw(
            "API configuration not found. Please add erp_url, api_key, and api_secret to site_config.json"
        )
    
    ZIP_FILENAME = "rechnungen.zip"
    headers = {"Authorization": f"token {API_KEY}:{API_SECRET}"}
    
    # Get invoices either from the parameter or by date range
    invoice_list = []
    
    if selected_invoices:
        if isinstance(selected_invoices, str):
            invoice_list = selected_invoices.split(',')
    elif from_date and to_date:
        # Get invoices by date range
        invoices = frappe.get_all(
            "Sales Invoice",
            filters={
                "docstatus": 1,  # Submitted documents
                "posting_date": ["between", [from_date, to_date]]
            },
            fields=["name"]
        )
        invoice_list = [inv.name for inv in invoices]
    
    if not invoice_list:
        frappe.throw("Keine Rechnungen gefunden")
    
    # Show a message if there are many invoices
    if len(invoice_list) > 20:
        frappe.publish_realtime("msgprint", 
            {"message": f"Download von {len(invoice_list)} Rechnungen gestartet. Bitte warten..."})
    
    zip_buffer = io.BytesIO()
    
    # Function to download a single invoice PDF
    def download_invoice(invoice_id):
        try:
            pdf_url = f"{ERP_URL}/api/method/frappe.utils.print_format.download_pdf?doctype=Sales Invoice&name={quote(invoice_id)}&format=Rechnung&no_letterhead=0"
            pdf_response = requests.get(pdf_url, headers=headers, timeout=30)
            if pdf_response.status_code == 200:
                return (invoice_id, pdf_response.content)
            else:
                frappe.log_error(f"Error downloading {invoice_id}: Status {pdf_response.status_code}")
                return (invoice_id, None)
        except Exception as e:
            frappe.log_error(f"Exception downloading {invoice_id}: {str(e)}")
            return (invoice_id, None)
    
    # Use ThreadPoolExecutor for parallel downloads
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(download_invoice, invoice_id): invoice_id for invoice_id in invoice_list}
            
            completed = 0
            total = len(invoice_list)
            
            for future in concurrent.futures.as_completed(futures):
                invoice_id, content = future.result()
                completed += 1
                
                if content:
                    zipf.writestr(f"{invoice_id}.pdf", content)
                
                if completed % max(1, int(total/20)) == 0:
                    frappe.publish_realtime("progress", {
                        "progress": [completed, total], 
                        "title": f"Downloading Invoices ({completed}/{total})"
                    })
    
    # Send the zip file as a response
    zip_buffer.seek(0)
    frappe.response["filecontent"] = zip_buffer.read()
    frappe.response["type"] = "download"
    frappe.response["filename"] = ZIP_FILENAME
    
    frappe.publish_realtime("msgprint", 
        {"message": f"Download von {len(invoice_list)} Rechnungen abgeschlossen!"})

@frappe.whitelist()
def download_invoices_with_excel(from_date=None, to_date=None):
    """
    Download both Sales Invoice PDFs and an Excel file
    
    Args:
        from_date (str): Start date for filtering invoices
        to_date (str): End date for filtering invoices
    """
    if not from_date or not to_date:
        frappe.throw("Bitte geben Sie sowohl ein Anfangs- als auch ein Enddatum an")
    
    # Get invoices by date range
    invoices = frappe.get_all(
        "Sales Invoice",
        filters={
            "docstatus": 1,  # Submitted documents
            "posting_date": ["between", [from_date, to_date]]
        },
        fields=[
            "name", "customer", "taxes_and_charges", "status", 
            "posting_date", "due_date", "base_grand_total", "customer_name"
        ]
    )
    
    if not invoices:
        frappe.throw("Keine Rechnungen im angegebenen Zeitraum gefunden")
    
    # Create a ZIP file with PDFs and Excel
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Generate Excel using Frappe's built-in functions
        from frappe.utils.xlsxutils import make_xlsx
        
        # Prepare data for Excel
        xlsx_data = []
        
        # Add headers matching your SQL query
        headers = [
            "Rechnung", "Konto", "Gegenkonto", "Soll/Haben", 
            "Datum", "Fälligkeit", "Umsatz", "Debitorennummer", "Debitor"
        ]
        xlsx_data.append(headers)
        
        # Add invoice data with transformations
        for invoice in invoices:
            # Transform customer to "Konto" (CAST as UNSIGNED equivalent)
            try:
                konto = int(invoice.customer) if invoice.customer.isdigit() else invoice.customer
            except (ValueError, AttributeError):
                konto = invoice.customer
            
            # Transform taxes_and_charges (CASE statement equivalent)
            tax_code = invoice.taxes_and_charges
            if tax_code == 'Lieferung oder sonstige Leistung im Inland - WDG':
                tax_code = '8400'
            elif tax_code == 'Lieferung an Unternehmen in der EU - WDG':
                tax_code = '8336'
            elif tax_code == 'Bauleistungen nach § 13b UStG - WDG':
                tax_code = '8337'
            # else: keep original value
            
            # Transform status (CASE statement equivalent)
            transformed_status = invoice.status
            if invoice.status in ['Paid', 'Overdue', 'Unpaid', 'Credit Note Issued']:
                transformed_status = 'S'
            elif invoice.status == 'Return':
                transformed_status = 'H'
            # else: keep original value
            
            # Create Debitorennummer (CONCAT equivalent)
            # CONCAT(SUBSTRING(customer, 2), '0') - take from position 2 and add '0'
            try:
                if len(invoice.customer) > 1:
                    debitorennummer = invoice.customer[1:] + '0'  # Skip first character, add '0'
                else:
                    debitorennummer = invoice.customer + '0'
            except (TypeError, AttributeError):
                debitorennummer = str(invoice.customer) + '0'
            
            # Add row with all transformations
            xlsx_data.append([
                invoice.name,
                konto,
                tax_code,
                transformed_status,
                invoice.posting_date,  # Keep as date object for Excel
                invoice.due_date,      # Keep as date object for Excel
                invoice.base_grand_total,  # Keep as number for Excel
                debitorennummer,
                invoice.customer_name
            ])
        
        # Create Excel file
        xlsx_file = make_xlsx(xlsx_data, "Invoices")
        
        # Add Excel to ZIP
        zipf.writestr(f"Rechnungen_{from_date}_bis_{to_date}.xlsx", xlsx_file.getvalue())
        
        # Get configuration from site_config.json
        ERP_URL = frappe.conf.get("erp_url")
        API_KEY = frappe.conf.get("api_key")
        API_SECRET = frappe.conf.get("api_secret")
        
        # Validate configuration
        if not ERP_URL or not API_KEY or not API_SECRET:
            frappe.throw(
                "API configuration not found. Please add erp_url, api_key, and api_secret to site_config.json"
            )
        
        headers = {"Authorization": f"token {API_KEY}:{API_SECRET}"}
        
        # Download PDFs and add to ZIP
        frappe.publish_realtime("msgprint", {"message": f"Excel erstellt. Starte PDF-Downloads..."})
        
        invoice_names = [inv.name for inv in invoices]
        
        # Create PDFs directory in ZIP
        zipf.writestr("PDFs/", "")
        
        # Function to download a single invoice PDF
        def download_invoice(invoice_id):
            try:
                pdf_url = f"{ERP_URL}/api/method/frappe.utils.print_format.download_pdf?doctype=Sales Invoice&name={quote(invoice_id)}&format=Rechnung&no_letterhead=0"
                pdf_response = requests.get(pdf_url, headers=headers, timeout=30)
                if pdf_response.status_code == 200:
                    return (invoice_id, pdf_response.content)
                else:
                    frappe.log_error(f"Error downloading {invoice_id}: Status {pdf_response.status_code}")
                    return (invoice_id, None)
            except Exception as e:
                frappe.log_error(f"Exception downloading {invoice_id}: {str(e)}")
                return (invoice_id, None)
        
        # Use ThreadPoolExecutor for parallel downloads
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(download_invoice, invoice_id): invoice_id for invoice_id in invoice_names}
            
            completed = 0
            total = len(invoice_names)
            
            for future in concurrent.futures.as_completed(futures):
                invoice_id, content = future.result()
                completed += 1
                
                if content:
                    zipf.writestr(f"PDFs/{invoice_id}.pdf", content)
                
                if completed % max(1, int(total/20)) == 0:
                    frappe.publish_realtime("progress", {
                        "progress": [completed, total], 
                        "title": f"Downloading Invoices ({completed}/{total})"
                    })
    
    # Send the zip file as a response
    zip_buffer.seek(0)
    frappe.response["filecontent"] = zip_buffer.read()
    frappe.response["type"] = "download"
    frappe.response["filename"] = f"Rechnungen_und_Excel_{from_date}_bis_{to_date}.zip"
    
    frappe.publish_realtime("msgprint", 
        {"message": f"Download von {len(invoice_names)} Rechnungen und Excel abgeschlossen!"})

