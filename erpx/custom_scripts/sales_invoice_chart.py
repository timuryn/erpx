import frappe

@frappe.whitelist()
def get_analysis(date_filter="Current Year", year=None):
    """API endpoint for sales invoice analysis"""
    
    if date_filter == "Last Three Months":
        date_condition = "si.posting_date >= DATE_SUB(CURDATE(), INTERVAL 3 MONTH)"
    elif date_filter == "Last Year":
        date_condition = "YEAR(si.posting_date) = YEAR(CURDATE()) - 1"
    elif date_filter == "Custom Year" and year:
        date_condition = f"YEAR(si.posting_date) = {int(year)}"
    else:  # Current Year
        date_condition = "YEAR(si.posting_date) = YEAR(CURDATE())"
    
    query = f"""
        SELECT 
            DATE_FORMAT(si.posting_date, '%Y-%m') AS month,
            SUM(CASE WHEN si.status NOT IN ('Paid', 'Return', 'Credit Note Issued') THEN si.net_total ELSE 0 END) AS unbezahlter_nettobetrag,
            SUM(CASE WHEN si.status IN ('Paid', 'Return', 'Credit Note Issued') THEN si.net_total - IFNULL(deductions.total_deductions, 0) ELSE 0 END) AS bezahlter_nettobetrag,
            SUM(si.net_total) AS umsatz_nettobetraege,
            SUM(CASE WHEN si.status IN ('Paid', 'Return', 'Credit Note Issued') THEN IFNULL(deductions.total_deductions, 0) ELSE 0 END) AS bezahlter_abzuege,
            SUM(CASE WHEN si.status NOT IN ('Paid', 'Return', 'Credit Note Issued') THEN si.net_total ELSE 0 END) + 
            SUM(CASE WHEN si.status IN ('Paid', 'Return', 'Credit Note Issued') THEN si.net_total - IFNULL(deductions.total_deductions, 0) ELSE 0 END) AS netto_nach_abzuegen
        FROM `tabSales Invoice` si
        LEFT JOIN (
            SELECT 
                per.reference_name,
                SUM(d.amount) AS total_deductions
            FROM `tabPayment Entry Reference` per 
            JOIN `tabPayment Entry` pe ON pe.name = per.parent AND pe.docstatus = 1
            JOIN `tabPayment Entry Deduction` d ON d.parent = pe.name
            WHERE per.reference_doctype = 'Sales Invoice'
            GROUP BY per.reference_name
        ) deductions ON deductions.reference_name = si.name
        WHERE si.docstatus != 0
          AND {date_condition}
        GROUP BY month
        UNION ALL
        SELECT 
            'Total' AS month,
            SUM(CASE WHEN si.status NOT IN ('Paid', 'Return', 'Credit Note Issued') THEN si.net_total ELSE 0 END) AS unbezahlter_nettobetrag,
            SUM(CASE WHEN si.status IN ('Paid', 'Return', 'Credit Note Issued') THEN si.net_total - IFNULL(deductions.total_deductions, 0) ELSE 0 END) AS bezahlter_nettobetrag,
            SUM(si.net_total) AS umsatz_nettobetraege,
            SUM(CASE WHEN si.status IN ('Paid', 'Return', 'Credit Note Issued') THEN IFNULL(deductions.total_deductions, 0) ELSE 0 END) AS bezahlter_abzuege,
            SUM(si.net_total) - SUM(IFNULL(deductions.total_deductions, 0)) AS netto_nach_abzuegen
        FROM `tabSales Invoice` si
        LEFT JOIN (
            SELECT 
                per.reference_name,
                SUM(d.amount) AS total_deductions
            FROM `tabPayment Entry Reference` per 
            JOIN `tabPayment Entry` pe ON pe.name = per.parent AND pe.docstatus = 1
            JOIN `tabPayment Entry Deduction` d ON d.parent = pe.name
            WHERE per.reference_doctype = 'Sales Invoice'
            GROUP BY per.reference_name
        ) deductions ON deductions.reference_name = si.name
        WHERE si.docstatus != 0
          AND {date_condition}
        ORDER BY 
            CASE 
                WHEN month = 'Total' THEN 2
                ELSE 1
            END,
            STR_TO_DATE(CONCAT(month, '-01'), '%Y-%m-%d') ASC
    """
    
    return frappe.db.sql(query, as_dict=True)
