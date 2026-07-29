import frappe

@frappe.whitelist()
def get_analysis(date_filter="Current Year", year=None):
    """API endpoint for sales invoice analysis - Paid and Unpaid invoices with deductions"""

    # Build date condition based on filter type
    if date_filter == "Last Three Months":
        date_condition = "si.posting_date >= DATE_SUB(CURDATE(), INTERVAL 3 MONTH)"
    elif date_filter == "Last 12 Months":
        date_condition = "si.posting_date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)"
    elif date_filter == "Last Year":
        date_condition = "YEAR(si.posting_date) = YEAR(CURDATE()) - 1"
    elif date_filter == "Custom Year" and year:
        # Handle both single year (2025) and range (2025-2026)
        if '-' in str(year):
            try:
                years = str(year).split('-')
                start_year = int(years[0].strip())
                end_year = int(years[1].strip())
                date_condition = f"YEAR(si.posting_date) >= {start_year} AND YEAR(si.posting_date) <= {end_year}"
            except (ValueError, IndexError):
                date_condition = "YEAR(si.posting_date) = YEAR(CURDATE())"
        else:
            try:
                date_condition = f"YEAR(si.posting_date) = {int(year)}"
            except ValueError:
                date_condition = "YEAR(si.posting_date) = YEAR(CURDATE())"
    else:  # Current Year
        date_condition = "YEAR(si.posting_date) = YEAR(CURDATE())"

    query = f"""
        SELECT
            DATE_FORMAT(si.posting_date, '%Y-%m') AS month,
            SUM(CASE
                WHEN si.status NOT IN ('Paid', 'Return', 'Credit Note Issued') AND si.is_return = 0
                THEN si.net_total
                ELSE 0
            END) AS unbezahlter_nettobetrag,
            SUM(CASE
                WHEN si.status = 'Paid' AND si.is_return = 0
                THEN si.net_total - IFNULL(deductions.total_deductions, 0)
                ELSE 0
            END) AS bezahlter_nettobetrag,
            SUM(si.net_total + IFNULL(si.total_taxes_and_charges, 0)) AS brutto_betrag
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
        WHERE si.docstatus = 1
          AND {date_condition}
        GROUP BY month

        UNION ALL

        SELECT
            'Total' AS month,
            SUM(CASE
                WHEN si.status NOT IN ('Paid', 'Return', 'Credit Note Issued') AND si.is_return = 0
                THEN si.net_total
                ELSE 0
            END) AS unbezahlter_nettobetrag,
            SUM(CASE
                WHEN si.status = 'Paid' AND si.is_return = 0
                THEN si.net_total - IFNULL(deductions.total_deductions, 0)
                ELSE 0
            END) AS bezahlter_nettobetrag,
            SUM(si.net_total + IFNULL(si.total_taxes_and_charges, 0)) AS brutto_betrag
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
        WHERE si.docstatus = 1
          AND {date_condition}

        ORDER BY
            CASE
                WHEN month = 'Total' THEN 2
                ELSE 1
            END,
            STR_TO_DATE(CONCAT(month, '-01'), '%Y-%m-%d') ASC
    """

    return frappe.db.sql(query, as_dict=True)

@frappe.whitelist()
def get_item_analysis(item_code, date_filter="Current Year", year=None):
    """API endpoint for item revenue analysis by month"""
    
    # Build date condition based on filter type
    if date_filter == "Last Three Months":
        date_condition = "si.posting_date >= DATE_SUB(CURDATE(), INTERVAL 3 MONTH)"
    elif date_filter == "Last 12 Months":
        date_condition = "si.posting_date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)"
    elif date_filter == "Last Year":
        date_condition = "YEAR(si.posting_date) = YEAR(CURDATE()) - 1"
    elif date_filter == "Custom Year" and year:
        # Handle both single year (2025) and range (2025-2026)
        if '-' in str(year):
            try:
                years = str(year).split('-')
                start_year = int(years[0].strip())
                end_year = int(years[1].strip())
                date_condition = f"YEAR(si.posting_date) >= {start_year} AND YEAR(si.posting_date) <= {end_year}"
            except (ValueError, IndexError):
                date_condition = "YEAR(si.posting_date) = YEAR(CURDATE())"
        else:
            try:
                date_condition = f"YEAR(si.posting_date) = {int(year)}"
            except ValueError:
                date_condition = "YEAR(si.posting_date) = YEAR(CURDATE())"
    else:  # Current Year
        date_condition = "YEAR(si.posting_date) = YEAR(CURDATE())"

    query = f"""
        SELECT
            DATE_FORMAT(si.posting_date, '%%Y-%%m') AS month,
            SUM(sii.amount) AS total_amount,
            SUM(sii.qty) AS total_qty
        FROM `tabSales Invoice` si
        INNER JOIN `tabSales Invoice Item` sii ON si.name = sii.parent
        WHERE sii.item_code = %s
        AND si.docstatus = 1
        AND {date_condition}
        GROUP BY month
        
        UNION ALL
        
        SELECT
            'Total' AS month,
            SUM(sii.amount) AS total_amount,
            SUM(sii.qty) AS total_qty
        FROM `tabSales Invoice` si
        INNER JOIN `tabSales Invoice Item` sii ON si.name = sii.parent
        WHERE sii.item_code = %s
        AND si.docstatus = 1
        AND {date_condition}
        
        ORDER BY
            CASE
                WHEN month = 'Total' THEN 2
                ELSE 1
            END,
            STR_TO_DATE(CONCAT(month, '-01'), '%%Y-%%m-%%d') ASC
    """

    return frappe.db.sql(query, (item_code, item_code), as_dict=True)





"""
Add this function to: apps/erpx/erpx/custom_scripts/sales_invoice_chart.py
This new endpoint analyzes project profitability: hours worked vs. revenue earned
"""

@frappe.whitelist()
def get_project_revenue_analysis(created_by="ak@dippelwerbung.de", date_filter="Current Year", year=None):
    """
    API endpoint for project profitability analysis
    Hours calculated from project creation to modified date (8 hours per day)
    """

    # Build date condition for project creation date
    if date_filter == "Last Three Months":
        date_condition = "p.creation >= DATE_SUB(CURDATE(), INTERVAL 3 MONTH)"
    elif date_filter == "Last 12 Months":
        date_condition = "p.creation >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)"
    elif date_filter == "Last Year":
        date_condition = "YEAR(p.creation) = YEAR(CURDATE()) - 1"
    elif date_filter == "Custom Year" and year:
        if '-' in str(year):
            try:
                years = str(year).split('-')
                start_year = int(years[0].strip())
                end_year = int(years[1].strip())
                date_condition = f"YEAR(p.creation) >= {start_year} AND YEAR(p.creation) <= {end_year}"
            except (ValueError, IndexError):
                date_condition = "YEAR(p.creation) = YEAR(CURDATE())"
        else:
            try:
                date_condition = f"YEAR(p.creation) = {int(year)}"
            except ValueError:
                date_condition = "YEAR(p.creation) = YEAR(CURDATE())"
    else:  # Current Year
        date_condition = "YEAR(p.creation) = YEAR(CURDATE())"

    query = f"""
        SELECT
            p.name AS project_name,
            p.project_name AS project_title,
            p.status AS project_status,
            p.modified AS end_date,
            p.creation AS start_date,
            -- Calculate hours from project creation to modified date (8 hours per day), minimum 8 hours
            GREATEST(
                ROUND((DATEDIFF(p.modified, p.creation) + 1) * 8),
                8
            ) AS actual_hours,
            -- Sum of netto from linked sales invoices
            COALESCE(SUM(si.net_total), 0) AS netto_revenue,
            -- Sum of brutto from linked sales invoices
            COALESCE(SUM(si.net_total + IFNULL(si.total_taxes_and_charges, 0)), 0) AS brutto_revenue,
            -- Invoice count
            COUNT(DISTINCT si.name) AS invoice_count,
            -- Calculate revenue per hour
            CASE
                WHEN GREATEST(
                    ROUND((DATEDIFF(p.modified, p.creation) + 1) * 8),
                    8
                ) > 0
                    THEN ROUND(COALESCE(SUM(si.net_total), 0) / GREATEST(
                        ROUND((DATEDIFF(p.modified, p.creation) + 1) * 8),
                        8
                    ), 2)
                ELSE 0
            END AS revenue_per_hour
        FROM `tabProject` p
        LEFT JOIN `tabSales Invoice` si ON si.project = p.name AND si.docstatus = 1
        WHERE p.owner = %s
          AND p.status = 'Completed'
          AND {date_condition}
        GROUP BY p.name
        ORDER BY p.creation DESC
    """

    return frappe.db.sql(query, (created_by,), as_dict=True)


@frappe.whitelist()
def get_project_efficiency_summary(created_by="ak@dippelwerbung.de", date_filter="Current Year", year=None):
    """
    Summary statistics for all projects
    Hours calculated from project creation to modified date
    """

    # Build date condition
    if date_filter == "Last Three Months":
        date_condition = "p.creation >= DATE_SUB(CURDATE(), INTERVAL 3 MONTH)"
    elif date_filter == "Last 12 Months":
        date_condition = "p.creation >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)"
    elif date_filter == "Last Year":
        date_condition = "YEAR(p.creation) = YEAR(CURDATE()) - 1"
    elif date_filter == "Custom Year" and year:
        if '-' in str(year):
            try:
                years = str(year).split('-')
                start_year = int(years[0].strip())
                end_year = int(years[1].strip())
                date_condition = f"YEAR(p.creation) >= {start_year} AND YEAR(p.creation) <= {end_year}"
            except (ValueError, IndexError):
                date_condition = "YEAR(p.creation) = YEAR(CURDATE())"
        else:
            try:
                date_condition = f"YEAR(p.creation) = {int(year)}"
            except ValueError:
                date_condition = "YEAR(p.creation) = YEAR(CURDATE())"
    else:  # Current Year
        date_condition = "YEAR(p.creation) = YEAR(CURDATE())"

    query = f"""
        SELECT
            COUNT(DISTINCT p.name) AS total_projects,
            COALESCE(ROUND(SUM(
                GREATEST(
                    ROUND((DATEDIFF(p.modified, p.creation) + 1) * 8),
                    8
                )
            )), 0) AS total_hours,
            COALESCE(SUM(si.net_total), 0) AS total_netto,
            COALESCE(SUM(si.net_total + IFNULL(si.total_taxes_and_charges, 0)), 0) AS total_brutto,
            CASE
                WHEN COALESCE(SUM(
                    GREATEST(
                        ROUND((DATEDIFF(p.modified, p.creation) + 1) * 8),
                        8
                    )
                ), 0) > 0
                    THEN ROUND(COALESCE(SUM(si.net_total), 0) / COALESCE(SUM(
                        GREATEST(
                            ROUND((DATEDIFF(p.modified, p.creation) + 1) * 8),
                            8
                        )
                    ), 1), 2)
                ELSE 0
            END AS avg_revenue_per_hour
        FROM `tabProject` p
        LEFT JOIN `tabSales Invoice` si ON si.project = p.name AND si.docstatus = 1
        WHERE p.owner = %s
          AND p.status = 'Completed'
          AND {date_condition}
    """

    return frappe.db.sql(query, (created_by,), as_dict=True)
