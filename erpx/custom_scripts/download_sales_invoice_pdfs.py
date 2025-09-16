# apps/erpx/erpx/api/download_sales_invoice_pdfs.py
import frappe
import zipfile
import io
import time
import threading
import requests
import concurrent.futures
from urllib.parse import quote
from frappe.utils.xlsxutils import make_xlsx

# Thread lock to prevent concurrent processing of same session
_processing_lock = threading.Lock()
_active_sessions = set()

@frappe.whitelist()
def cancel_session(session_id):
    """
    Cancel a running download session
    """
    try:
        # Mark session as canceled in cache
        existing_progress = frappe.cache().get_value(f"progress_{session_id}")
        if existing_progress:
            frappe.cache().set_value(f"progress_{session_id}", {
                "status": "canceled",
                "completed": existing_progress.get("completed", 0),
                "total": existing_progress.get("total", 0),
                "canceled_at": time.time(),
                "start_time": existing_progress.get("start_time", time.time())
            }, expires_in_sec=60)  # Keep for 1 minute to show cancel status

            # Remove from active sessions
            with _processing_lock:
                _active_sessions.discard(session_id)

            return {"status": "success", "message": "Sitzung wurde zum Abbruch markiert"}
        else:
            return {"status": "not_found", "message": "Sitzung nicht gefunden"}

    except Exception as e:
        frappe.log_error(f"Error canceling session {session_id}: {str(e)}")
        return {"status": "error", "message": "Fehler beim Abbrechen der Sitzung"}


@frappe.whitelist()
def download_selected_sales_invoices_with_progress(selected_invoices=None, from_date=None, to_date=None, session_id=None):
    """
    Download Sales Invoice PDFs with cache-based progress tracking
    """
    start_time = time.time()
    ZIP_FILENAME = "rechnungen.zip"

    # Create session ID if not provided
    if not session_id:
        session_id = f"pdf_session_{int(time.time())}"

    # Check for existing session data
    existing_progress = frappe.cache().get_value(f"progress_{session_id}")
    if existing_progress:
        if existing_progress.get("status") == "completed":
            frappe.throw("Diese Anfrage wurde bereits abgeschlossen.")
        if existing_progress.get("status") in ["processing", "zip_creation"]:
            frappe.throw("Diese Anfrage wird bereits verarbeitet.")

    # Prevent duplicate processing
    with _processing_lock:
        if session_id in _active_sessions:
            frappe.throw("Diese Anfrage wird bereits verarbeitet.")
        _active_sessions.add(session_id)

    try:
        # Get invoices
        invoice_list = []
        if selected_invoices:
            if isinstance(selected_invoices, str):
                invoice_list = selected_invoices.split(',')
        elif from_date and to_date:
            invoices = frappe.get_all(
                "Sales Invoice",
                filters={
                    "docstatus": 1,
                    "posting_date": ["between", [from_date, to_date]]
                },
                fields=["name"]
            )
            invoice_list = [inv.name for inv in invoices]

        if not invoice_list:
            frappe.throw("Keine Rechnungen gefunden")

        # Initialize progress tracking
        total_invoices = len(invoice_list)
        completed = 0
        pdf_generation_time = 0

        # Store initial progress in cache
        frappe.cache().set_value(f"progress_{session_id}", {
            "status": "processing",
            "completed": 0,
            "total": total_invoices,
            "current_invoice": "Initialisierung...",
            "avg_time": 0,
            "start_time": start_time
        }, expires_in_sec=300)

        zip_buffer = io.BytesIO()

        # Create ZIP file with progress tracking
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for invoice_id in invoice_list:
                # Check for cancellation
                current_progress = frappe.cache().get_value(f"progress_{session_id}")
                if current_progress and current_progress.get("status") == "canceled":
                    frappe.throw("Download wurde abgebrochen")

                try:
                    # Update progress before processing
                    frappe.cache().set_value(f"progress_{session_id}", {
                        "status": "processing",
                        "completed": completed,
                        "total": total_invoices,
                        "current_invoice": invoice_id,
                        "avg_time": round(pdf_generation_time / max(1, completed), 2) if completed > 0 else 0,
                        "start_time": start_time
                    }, expires_in_sec=300)

                    # Generate PDF
                    pdf_start = time.time()
                    pdf_content = frappe.get_print(
                        "Sales Invoice",
                        invoice_id,
                        "Rechnung",
                        as_pdf=True,
                        no_letterhead=False
                    )
                    pdf_end = time.time()
                    pdf_generation_time += (pdf_end - pdf_start)

                    if pdf_content:
                        zipf.writestr(f"{invoice_id}.pdf", pdf_content)

                except Exception as e:
                    frappe.log_error(f"Error generating PDF for {invoice_id}: {str(e)}")
                    continue

                completed += 1

                # Update progress after processing
                frappe.cache().set_value(f"progress_{session_id}", {
                    "status": "processing",
                    "completed": completed,
                    "total": total_invoices,
                    "current_invoice": invoice_id,
                    "avg_time": round(pdf_generation_time / completed, 2) if completed > 0 else 0,
                    "start_time": start_time
                }, expires_in_sec=300)

        # ZIP creation phase
        frappe.cache().set_value(f"progress_{session_id}", {
            "status": "zip_creation",
            "completed": completed,
            "total": total_invoices,
            "current_invoice": "Erstelle ZIP-Datei...",
            "avg_time": round(pdf_generation_time / completed, 2) if completed > 0 else 0,
            "start_time": start_time
        }, expires_in_sec=300)

        # Finalize
        zip_buffer.seek(0)
        zip_content = zip_buffer.read()

        if len(zip_content) < 100:
            frappe.throw("Fehler beim Erstellen der PDF-Dateien. Bitte versuchen Sie es erneut.")

        # Calculate final statistics
        end_time = time.time()
        total_time = round(end_time - start_time, 2)
        zip_size_mb = round(len(zip_content) / (1024 * 1024), 2)

        # Mark as completed in cache
        frappe.cache().set_value(f"progress_{session_id}", {
            "status": "completed",
            "completed": completed,
            "total": total_invoices,
            "total_time": total_time,
            "zip_size": zip_size_mb,
            "avg_time": round(pdf_generation_time / completed, 2) if completed > 0 else 0,
            "start_time": start_time
        }, expires_in_sec=300)

        # Send response
        frappe.response["filecontent"] = zip_content
        frappe.response["type"] = "download"
        frappe.response["filename"] = ZIP_FILENAME

    finally:
        # Always remove session from active list
        with _processing_lock:
            _active_sessions.discard(session_id)


@frappe.whitelist()
def download_invoices_with_excel_progress(from_date=None, to_date=None, session_id=None):
    """
    Download both Sales Invoice PDFs and an Excel file with progress tracking
    """
    start_time = time.time()

    if not from_date or not to_date:
        frappe.throw("Bitte geben Sie sowohl ein Anfangs- als auch ein Enddatum an")

    # Create session ID if not provided
    if not session_id:
        session_id = f"excel_session_{int(time.time())}"

    # Check for existing session data
    existing_progress = frappe.cache().get_value(f"progress_{session_id}")
    if existing_progress:
        if existing_progress.get("status") == "completed":
            frappe.throw("Diese Anfrage wurde bereits abgeschlossen.")
        if existing_progress.get("status") in ["processing", "excel_creation", "pdf_download", "zip_creation"]:
            frappe.throw("Diese Anfrage wird bereits verarbeitet.")

    # Prevent duplicate processing
    with _processing_lock:
        if session_id in _active_sessions:
            frappe.throw("Diese Anfrage wird bereits verarbeitet.")
        _active_sessions.add(session_id)

    try:
        # Get invoices by date range with deductions calculation
        invoices_query = """
            SELECT 
                si.name, 
                si.customer,
                si.taxes_and_charges,
                si.status,
                si.posting_date, 
                si.due_date, 
                si.base_grand_total,
                IFNULL(SUM(d.amount), 0) AS deductions,
                si.customer_name
            FROM `tabSales Invoice` si
            LEFT JOIN `tabPayment Entry Reference` per 
                ON per.reference_name = si.name AND per.reference_doctype = 'Sales Invoice'
            LEFT JOIN `tabPayment Entry` pe 
                ON pe.name = per.parent AND pe.docstatus = 1
            LEFT JOIN `tabPayment Entry Deduction` d 
                ON d.parent = pe.name
            WHERE si.docstatus = 1 
              AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
            GROUP BY si.name
            ORDER BY si.name ASC
        """

        invoices = frappe.db.sql(invoices_query, {
            'from_date': from_date,
            'to_date': to_date
        }, as_dict=True)

        if not invoices:
            frappe.throw("Keine Rechnungen im angegebenen Zeitraum gefunden")

        total_steps = len(invoices) + 2  # PDFs + Excel creation + ZIP creation
        completed_steps = 0

        # Store initial progress
        frappe.cache().set_value(f"progress_{session_id}", {
            "status": "excel_creation",
            "completed": 0,
            "total": total_steps,
            "current_step": "Erstelle Excel-Datei...",
            "phase": "Excel-Erstellung",
            "start_time": start_time
        }, expires_in_sec=600)

        # Create ZIP buffer
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # PHASE 1: Create Excel file
            frappe.cache().set_value(f"progress_{session_id}", {
                "status": "excel_creation",
                "completed": completed_steps,
                "total": total_steps,
                "current_step": "Erstelle Excel-Datei...",
                "phase": "Excel-Erstellung",
                "start_time": start_time
            }, expires_in_sec=600)

            # Prepare data for Excel with Abzüge column
            xlsx_data = []
            headers = [
                "Rechnung", "Konto", "Gegenkonto", "Soll/Haben",
                "Datum", "Fälligkeit", "Umsatz", "Abzüge", "Debitorennummer", "Debitor"
            ]
            xlsx_data.append(headers)

            # Add invoice data with transformations and deductions
            for invoice in invoices:
                # Transform customer to "Konto"
                try:
                    konto = int(invoice.customer) if invoice.customer.isdigit() else invoice.customer
                except (ValueError, AttributeError):
                    konto = invoice.customer

                # Transform taxes_and_charges
                tax_code = invoice.taxes_and_charges
                if tax_code == 'Lieferung oder sonstige Leistung im Inland - WDG':
                    tax_code = '8400'
                elif tax_code == 'Lieferung an Unternehmen in der EU - WDG':
                    tax_code = '8336'
                elif tax_code == 'Bauleistungen nach § 13b UStG - WDG':
                    tax_code = '8337'

                # Transform status
                transformed_status = invoice.status
                if invoice.status in ['Paid', 'Overdue', 'Unpaid', 'Credit Note Issued']:
                    transformed_status = 'S'
                elif invoice.status == 'Return':
                    transformed_status = 'H'

                # Create Debitorennummer
                try:
                    if len(invoice.customer) > 1:
                        debitorennummer = invoice.customer[1:] + '0'
                    else:
                        debitorennummer = invoice.customer + '0'
                except (TypeError, AttributeError):
                    debitorennummer = str(invoice.customer) + '0'

                # Calculate Umsatz (base_grand_total - deductions)
                deductions = float(invoice.deductions or 0)
                umsatz = float(invoice.base_grand_total) - deductions

                # Add row with Abzüge column
                xlsx_data.append([
                    invoice.name, 
                    konto, 
                    tax_code, 
                    transformed_status,
                    invoice.posting_date, 
                    invoice.due_date, 
                    umsatz,
                    deductions,  # This is the new Abzüge column
                    debitorennummer, 
                    invoice.customer_name
                ])

            # Create Excel file
            xlsx_file = make_xlsx(xlsx_data, "Invoices")
            zipf.writestr(f"Rechnungen_{from_date}_bis_{to_date}.xlsx", xlsx_file.getvalue())

            completed_steps += 1

            # PHASE 2: Download PDFs
            frappe.cache().set_value(f"progress_{session_id}", {
                "status": "pdf_download",
                "completed": completed_steps,
                "total": total_steps,
                "current_step": "Lade PDFs herunter...",
                "phase": "PDF-Download",
                "pdfs_completed": 0,
                "pdfs_total": len(invoices),
                "start_time": start_time
            }, expires_in_sec=600)

            # Get configuration from site_config.json
            ERP_URL = frappe.conf.get("erp_url")
            API_KEY = frappe.conf.get("api_key")
            API_SECRET = frappe.conf.get("api_secret")

            if not ERP_URL or not API_KEY or not API_SECRET:
                # If no external API config, use internal PDF generation
                pdf_completed = 0
                for invoice in invoices:
                    # Check for cancellation
                    current_progress = frappe.cache().get_value(f"progress_{session_id}")
                    if current_progress and current_progress.get("status") == "canceled":
                        frappe.throw("Download wurde abgebrochen")

                    try:
                        pdf_content = frappe.get_print(
                            "Sales Invoice",
                            invoice.name,
                            "Rechnung",
                            as_pdf=True,
                            no_letterhead=False
                        )

                        if pdf_content:
                            zipf.writestr(f"PDFs/{invoice.name}.pdf", pdf_content)

                        pdf_completed += 1

                        # Update progress for PDF downloads
                        frappe.cache().set_value(f"progress_{session_id}", {
                            "status": "pdf_download",
                            "completed": completed_steps,
                            "total": total_steps,
                            "current_step": f"PDF {pdf_completed}/{len(invoices)}: {invoice.name}",
                            "phase": "PDF-Download",
                            "pdfs_completed": pdf_completed,
                            "pdfs_total": len(invoices),
                            "start_time": start_time
                        }, expires_in_sec=600)

                    except Exception as e:
                        frappe.log_error(f"Error generating PDF for {invoice.name}: {str(e)}")
                        continue

            else:
                # Use external API for PDF downloads
                headers = {"Authorization": f"token {API_KEY}:{API_SECRET}"}
                invoice_names = [inv.name for inv in invoices]

                # Function to download a single invoice PDF
                def download_invoice(invoice_id):
                    try:
                        pdf_url = f"{ERP_URL}/api/method/frappe.utils.print_format.download_pdf?doctype=Sales Invoice&name={quote(invoice_id)}&format=Rechnung&no_letterhead=0"
                        pdf_response = requests.get(pdf_url, headers=headers, timeout=30)
                        if pdf_response.status_code == 200:
                            return (invoice_id, pdf_response.content)
                        else:
                            frappe.log_error(f"Fehler beim Herunterladen von {invoice_id}: Status {pdf_response.status_code}")
                            return (invoice_id, None)
                    except Exception as e:
                        frappe.log_error(f"Ausnahme beim Herunterladen von {invoice_id}: {str(e)}")
                        return (invoice_id, None)

                # Use ThreadPoolExecutor for parallel downloads
                pdf_completed = 0
                with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                    futures = {executor.submit(download_invoice, invoice_id): invoice_id for invoice_id in invoice_names}

                    for future in concurrent.futures.as_completed(futures):
                        invoice_id, content = future.result()
                        pdf_completed += 1

                        if content:
                            zipf.writestr(f"PDFs/{invoice_id}.pdf", content)

                        # Update progress for PDF downloads
                        frappe.cache().set_value(f"progress_{session_id}", {
                            "status": "pdf_download",
                            "completed": completed_steps,
                            "total": total_steps,
                            "current_step": f"PDF {pdf_completed}/{len(invoices)}: {invoice_id}",
                            "phase": "PDF-Download",
                            "pdfs_completed": pdf_completed,
                            "pdfs_total": len(invoices),
                            "start_time": start_time
                        }, expires_in_sec=600)

            completed_steps += len(invoices)

            # PHASE 3: Finalize ZIP
            frappe.cache().set_value(f"progress_{session_id}", {
                "status": "zip_creation",
                "completed": completed_steps,
                "total": total_steps,
                "current_step": "Schließe ZIP-Datei ab...",
                "phase": "ZIP-Erstellung",
                "start_time": start_time
            }, expires_in_sec=600)

        # Finalize
        zip_buffer.seek(0)
        zip_content = zip_buffer.read()

        if len(zip_content) < 100:
            frappe.throw("Fehler beim Erstellen der ZIP-Datei. Bitte versuchen Sie es erneut.")

        # Calculate final statistics
        end_time = time.time()
        total_time = round(end_time - start_time, 2)
        zip_size_mb = round(len(zip_content) / (1024 * 1024), 2)

        # Mark as completed
        frappe.cache().set_value(f"progress_{session_id}", {
            "status": "completed",
            "completed": total_steps,
            "total": total_steps,
            "total_time": total_time,
            "zip_size": zip_size_mb,
            "invoices_count": len(invoices),
            "start_time": start_time
        }, expires_in_sec=600)

        # Send response
        frappe.response["filecontent"] = zip_content
        frappe.response["type"] = "download"
        frappe.response["filename"] = f"Rechnungen_und_Excel_{from_date}_bis_{to_date}.zip"

    finally:
        # Always remove session from active list
        with _processing_lock:
            _active_sessions.discard(session_id)


@frappe.whitelist()
def check_progress_status(session_id):
    """
    Check the progress status of a PDF generation session
    """
    try:
        progress_data = frappe.cache().get_value(f"progress_{session_id}")

        if progress_data:
            return {
                "status": progress_data.get("status", "unknown"),
                "completed": progress_data.get("completed", 0),
                "total": progress_data.get("total", 0),
                "current_invoice": progress_data.get("current_invoice", "Unbekannt"),
                "current_step": progress_data.get("current_step", "Unbekannt"),
                "phase": progress_data.get("phase", "Verarbeitung"),
                "pdfs_completed": progress_data.get("pdfs_completed", 0),
                "pdfs_total": progress_data.get("pdfs_total", 0),
                "avg_time": progress_data.get("avg_time", 0),
                "total_time": progress_data.get("total_time"),
                "zip_size": progress_data.get("zip_size"),
                "invoices_count": progress_data.get("invoices_count"),
                "elapsed_time": round(time.time() - progress_data.get("start_time", time.time()), 2)
            }
        else:
            return {
                "status": "not_found",
                "message": "Sitzung nicht gefunden oder abgelaufen"
            }

    except Exception as e:
        frappe.log_error(f"Error checking progress for session {session_id}: {str(e)}")
        return {
            "status": "error",
            "message": "Fehler beim Prüfen des Fortschrittsstatus"
        }


@frappe.whitelist()
def download_selected_sales_invoices_parallel_fixed(selected_invoices=None, from_date=None, to_date=None):
    """
    Simple PDF download without progress tracking (backup method)
    """
    ZIP_FILENAME = "rechnungen.zip"

    # Get invoices
    invoice_list = []
    if selected_invoices:
        if isinstance(selected_invoices, str):
            invoice_list = selected_invoices.split(',')
    elif from_date and to_date:
        invoices = frappe.get_all(
            "Sales Invoice",
            filters={
                "docstatus": 1,
                "posting_date": ["between", [from_date, to_date]]
            },
            fields=["name"]
        )
        invoice_list = [inv.name for inv in invoices]

    if not invoice_list:
        frappe.throw("Keine Rechnungen gefunden")

    zip_buffer = io.BytesIO()

    # Create ZIP file
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for invoice_id in invoice_list:
            try:
                pdf_content = frappe.get_print(
                    "Sales Invoice",
                    invoice_id,
                    "Rechnung",
                    as_pdf=True,
                    no_letterhead=False
                )

                if pdf_content:
                    zipf.writestr(f"{invoice_id}.pdf", pdf_content)

            except Exception as e:
                frappe.log_error(f"Error generating PDF for {invoice_id}: {str(e)}")
                continue

    # Send response
    zip_buffer.seek(0)
    zip_content = zip_buffer.read()

    if len(zip_content) < 100:
        frappe.throw("Fehler beim Erstellen der PDF-Dateien")

    frappe.response["filecontent"] = zip_content
    frappe.response["type"] = "download"
    frappe.response["filename"] = ZIP_FILENAME


@frappe.whitelist()
def download_selected_sales_invoices(selected_invoices=None, from_date=None, to_date=None):
    """
    Legacy function for backward compatibility
    """
    return download_selected_sales_invoices_with_progress(selected_invoices, from_date, to_date)
