import frappe
from frappe.utils import add_days, getdate, flt

COMPANY_NAME = "Werbeteam Dippel GmbH"

@frappe.whitelist()
def get_customer_payment_setup(customer, posting_date=None, grand_total=0, company=None):
    """
    Returns complete payment setup for a customer:
    - tc_name, terms text, payment_terms_template, taxes_and_charges
    - pre-calculated payment_schedule rows (with payment_amount)
    - due_date

    Only applies our customer-code mapping when the transaction belongs to
    our own company. For any other company, returns {} so callers fall back
    to ERPNext's normal defaults untouched.
    """
    if not customer:
        return {}

    if company and company != COMPANY_NAME:
        return {}

    grand_total = flt(grand_total)

    # Customer-specific payment configuration
    mapping = {
        "01478": {
            "tc_name": "Zahlung innerhalb von 21 Tagen",
            "terms": "Zahlungsbedingungen: Zahlung innerhalb von 21 Tagen ab Rechnungseingang ohne Abzüge.",
            "payment_terms_template": "21 tagen",
            "taxes_and_charges": "Lieferung oder sonstige Leistung im Inland - WDG",
            "payment_description": "Zahlung innerhalb von 21 Tagen ab Rechnungseingang ohne Abzüge."
        },
        "01381": {
            "tc_name": "Zahlung innerhalb von 21 Tagen",
            "terms": "Zahlungsbedingungen: Zahlung innerhalb von 21 Tagen ab Rechnungseingang ohne Abzüge.",
            "payment_terms_template": "21 tagen",
            "taxes_and_charges": "Lieferung oder sonstige Leistung im Inland - WDG",
            "payment_description": "Zahlung innerhalb von 21 Tagen ab Rechnungseingang ohne Abzüge."
        },
        "01001": {
            "tc_name": "Zahlung innerhalb von 21 Tagen",
            "terms": "Zahlungsbedingungen: Zahlung innerhalb von 21 Tagen ab Rechnungseingang ohne Abzüge.",
            "payment_terms_template": "21 tagen",
            "taxes_and_charges": "Lieferung oder sonstige Leistung im Inland - WDG",
            "payment_description": "Zahlung innerhalb von 21 Tagen ab Rechnungseingang ohne Abzüge."
        },
        "01060": {
            "tc_name": "Zahlung innerhalb von 30 Tagen",
            "terms": "Zahlungsbedingungen: Zahlung innerhalb von 30 Tagen ab Rechnungseingang ohne Abzüge.",
            "payment_terms_template": "30 tagen",
            "taxes_and_charges": "Bauleistungen nach § 13b UStG - WDG",
            "payment_description": "Zahlung innerhalb von 30 Tagen ab Rechnungseingang ohne Abzüge."
        },
        "01791": {
            "tc_name": "5 Tage 3% Skonto",
            "terms": "<p>Zahlung innerhalb 5 Tagen 3% Skonto.</p><p>Zahlung 5-14 Tage voller Betrag.</p>",
            "payment_terms_template": "5 tagen 3% skonto",
            "taxes_and_charges": "Lieferung oder sonstige Leistung im Inland - WDG",
            "payment_description": "Zahlung innerhalb 5 Tagen 3% Skonto. Zahlung 5-14 Tage voller Betrag."
        },
        "01815": {
            "tc_name": "5 Tage 2% Skonto",
            "terms": "<p>Zahlung innerhalb 5 Tagen 2% Skonto.</p><p>Zahlung 5-14 Tage voller Betrag.</p>",
            "payment_terms_template": "5 tagen 2% skonto",
            "taxes_and_charges": "Lieferung oder sonstige Leistung im Inland - WDG",
            "payment_description": "Zahlung innerhalb 5 Tagen 2% Skonto. Zahlung 5-14 Tage voller Betrag."
        }
    }

    defaults = {
        "tc_name": "Zahlung innerhalb von 14 Tagen",
        "terms": "Zahlungsbedingungen: Zahlung innerhalb von 14 Tagen ab Rechnungseingang ohne Abzüge.",
        "payment_terms_template": "14 tagen",
        "taxes_and_charges": "Lieferung oder sonstige Leistung im Inland - WDG",
        "payment_description": "Zahlung innerhalb von 14 Tagen ab Rechnungseingang ohne Abzüge."
    }

    config = mapping.get(customer, defaults)

    # Fetch Terms and Conditions text — fall back to the hardcoded mapping text
    # if the doctype lookup fails, so terms is never silently blank
    terms_text = config.get("terms", "")
    if config.get("tc_name"):
        try:
            tc_doc = frappe.get_doc("Terms and Conditions", config["tc_name"])
            terms_text = tc_doc.terms or terms_text
        except Exception:
            pass

    # Build payment_schedule server-side
    schedule = []
    due_date = None
    base_date = getdate(posting_date) if posting_date else getdate()

    if config.get("payment_terms_template"):
        try:
            template = frappe.get_doc("Payment Terms Template", config["payment_terms_template"])
            for term in template.terms:
                row_due_date = add_days(base_date, term.credit_days or 0)
                payment_amount = flt(grand_total * flt(term.invoice_portion or 0) / 100)
                schedule.append({
                    "payment_term": term.payment_term,
                    "description": term.description or "",
                    "due_date": str(row_due_date),
                    "invoice_portion": term.invoice_portion,
                    "payment_amount": payment_amount,
                    "base_payment_amount": payment_amount,
                    "credit_days": term.credit_days,
                    "mode_of_payment": term.mode_of_payment or ""
                })
            if schedule:
                due_date = schedule[-1]["due_date"]
        except Exception:
            pass

    return {
        "tc_name": config["tc_name"],
        "terms": terms_text,
        "payment_terms_template": config["payment_terms_template"],
        "taxes_and_charges": config["taxes_and_charges"],
        "payment_description": config["payment_description"],
        "due_date": due_date,
        "payment_schedule": schedule
    }
