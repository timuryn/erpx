import re
import io
import pdfkit
import tempfile
from pypdf import PdfReader
from urllib.parse import urljoin
from bs4 import BeautifulSoup

# Set the internal base URL for resource loading (inside Docker)
BASE_URL = "http://frappe:8000"

def make_urls_absolute(html):
    """Convert relative URLs to absolute URLs for proper resource loading"""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(["link", "script", "img"]):
        attr = "href" if tag.name == "link" else "src"
        if tag.has_attr(attr):
            if tag[attr].startswith("/") and not tag[attr].startswith("//"):
                tag[attr] = urljoin(BASE_URL, tag[attr])
    return str(soup)

def get_pdf(html, options=None, output=None):
    """
    Custom PDF generation with URL fixes and proper header/footer handling
    """
    # Fix URLs for Docker environment
    html = make_urls_absolute(html)
    
    # Clean problematic CSS variables that cause rendering issues
    html = re.sub(r'var\(--bs-[^)]+\)', '#333333', html)  # Bootstrap variables
    html = re.sub(r'var\(--primary[^)]*\)', '#0d6efd', html)  # Primary color variables
    
    # Use Frappe's built-in option preparation for proper header/footer handling
    from frappe.utils.pdf import prepare_options
    html, processed_options = prepare_options(html, options)
    
    # Set up safe PDF generation options
    safe_options = {
        'page-size': 'A4',
        'encoding': "UTF-8",
        'load-error-handling': 'ignore',
        'load-media-error-handling': 'ignore',
        'print-media-type': '',
        'enable-local-file-access': '',
        'disable-smart-shrinking': '',
    }
    
    # Merge options with Frappe's processed options taking precedence
    final_options = {**safe_options, **processed_options}
    
    # Set consistent margins (matching Frappe's default behavior)
    if not final_options.get("margin-right"):
        final_options["margin-right"] = "0mm"
    if not final_options.get("margin-left"):
        final_options["margin-left"] = "0mm"

    try:
        # Generate PDF using wkhtmltopdf
        with tempfile.NamedTemporaryFile(suffix=".pdf") as temp_pdf:
            pdfkit.from_string(html, temp_pdf.name, options=final_options)
            temp_pdf.seek(0)
            filedata = temp_pdf.read()

        # Verify PDF was created successfully
        reader = PdfReader(io.BytesIO(filedata))
        
        # Clean up temporary header/footer files
        from frappe.utils.pdf import cleanup
        cleanup(final_options)

        return filedata

    except Exception as e:
        # Clean up on error
        try:
            from frappe.utils.pdf import cleanup
            cleanup(final_options)
        except:
            pass
        raise e
