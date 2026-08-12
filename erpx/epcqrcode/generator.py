import io
import base64
from segno import helpers
import frappe
from werkzeug.wrappers import Response
from PIL import Image

@frappe.whitelist()
def get_code():
  pName = frappe.request.args.get('name', default='', type=str)
  pIBAN = frappe.request.args.get('iban', default='', type=str)
  pAmount = frappe.request.args.get('amount', default=0, type=float)
  pText = frappe.request.args.get('text', default='', type=str)
  pReference = frappe.request.args.get('reference', default='', type=str)
  pBIC = frappe.request.args.get('bic', default='', type=str)
  pPurpose = frappe.request.args.get('purpose', default='', type=str)
  pScale = frappe.request.args.get('scale', default=4, type=int)
  pBorder = frappe.request.args.get('border', default=2, type=int)
  qrcode = helpers.make_epc_qr(name=pName, iban=pIBAN, amount=pAmount, text=pText, reference=pReference, bic=pBIC, purpose=pPurpose)
  buffer = io.BytesIO()
  qrcode.save(buffer, kind='png', scale=pScale, border=pBorder)
  buffer.seek(0)
  response = Response()
  response.mimetype = 'image/png'
  response.data = buffer.read()
  return response

def hex_to_rgb(hex_color):
  """Convert hex color to RGB tuple"""
  hex_color = hex_color.lstrip('#')
  if len(hex_color) == 6:
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
  return (0, 0, 0)  # Default black

def color_qr_corners_directly(qr_image, corner_color=(0, 0, 0)):
  """Color corner squares directly by modifying the PNG image"""
  # Convert to RGB if needed
  if qr_image.mode != 'RGB':
    qr_image = qr_image.convert('RGB')

  pixels = qr_image.load()
  width, height = qr_image.size

  # For a QR code with scale=4 and border=2:
  # Each module is 4 pixels, border is 8 pixels
  # Corner finder pattern is 7x7 modules = 28x28 pixels
  # Border adds 8 pixels, so corner is from 8 to 36 pixels

  corner_start = 8  # border pixels
  corner_end = 36   # 8 + (7*4)

  # Top-left corner
  for y in range(corner_start, corner_end):
    for x in range(corner_start, corner_end):
      # Replace black pixels with custom color
      r, g, b = pixels[x, y]
      if r < 128 and g < 128 and b < 128:  # if dark/black
        pixels[x, y] = corner_color

  # Top-right corner
  for y in range(corner_start, corner_end):
    for x in range(width - corner_end, width - corner_start):
      r, g, b = pixels[x, y]
      if r < 128 and g < 128 and b < 128:
        pixels[x, y] = corner_color

  # Bottom-left corner
  for y in range(height - corner_end, height - corner_start):
    for x in range(corner_start, corner_end):
      r, g, b = pixels[x, y]
      if r < 128 and g < 128 and b < 128:
        pixels[x, y] = corner_color

  return qr_image

def get_logo_element(company_name, custom_color):
  """Get logo element - either custom Base64 or empty"""
  try:
    company = frappe.get_doc('Company', company_name)

    if company.get('custom_qr_logo_base64'):
      # Use custom logo from Base64 (PNG or SVG)
      logo_b64 = company.custom_qr_logo_base64.strip()
      # Handle case where it might be wrapped in data URI
      if 'data:' in logo_b64:
        logo_b64 = logo_b64.split(',')[1]

      # Detect format from Base64 header
      mime_type = 'image/png'
      if logo_b64.startswith('PD94'):  # '<?x' in Base64
        mime_type = 'image/svg+xml'

      return f'''<image x="29.5" y="29.5" width="30" height="30" xlink:href="data:{mime_type};base64,{logo_b64}"/>'''
    else:
      # No custom logo - return empty string (QR code only)
      return ''
  except Exception as e:
    frappe.log_error(f"Logo retrieval failed: {str(e)}", "QR Logo Error")
    return ''

@frappe.whitelist()
def get_qr_html(name, iban, amount, reference=None, text=None, bic=None, purpose=None, scale=4, border=2):
  """Generate QR code with company-specific color and logo - scaled down by 1/3 (89x89)"""
  try:
    # Fetch company settings
    company_doc = frappe.get_doc('Company', name)
    custom_color = company_doc.get('custom_qr_color') or '#000000'
    corner_color_rgb = hex_to_rgb(custom_color)

    # Generate QR code as PNG
    qrcode = helpers.make_epc_qr(
      name=name,
      iban=iban,
      amount=float(amount),
      text=text or '',
      reference=reference or '',
      bic=bic or '',
      purpose=purpose or ''
    )
    buffer = io.BytesIO()
    qrcode.save(buffer, kind='png', scale=int(scale), border=int(border))
    buffer.seek(0)

    # Load QR image and color corners
    qr_image = Image.open(buffer).convert('RGB')
    qr_image = color_qr_corners_directly(qr_image, corner_color_rgb)

    # Convert to base64
    qr_output = io.BytesIO()
    qr_image.save(qr_output, format='PNG')
    qr_output.seek(0)
    qr_b64 = base64.b64encode(qr_output.read()).decode('utf-8')

    # Get logo element (custom or default)
    logo_element = get_logo_element(name, custom_color)

    # Create SVG with colored QR and logo
    svg_html = f'''
    <svg width="89" height="89" viewBox="0 0 89 89" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
      <!-- QR Code Background -->
      <image x="0" y="0" width="89" height="89" xlink:href="data:image/png;base64,{qr_b64}"/>

      <!-- Logo (custom or default Dippel) -->
      {logo_element}
    </svg>
    '''

    return svg_html
  except Exception as e:
    frappe.log_error(f"EPC QR Code generation failed: {str(e)}", "EPC QR Code Error")
    return ""
