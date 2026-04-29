# File: erpx/custom_scripts/get_project_listview_document_counts.py
# Purpose: Batch fetch document counts for Project list view (Dokumente column)

import frappe

@frappe.whitelist()
def get_project_document_counts(project_names=None):
        """
        Fetch document counts for multiple projects.

        Args:
                project_names: List of Project names

        Returns:
                Dict mapping project name -> { AN, AU, LI, RE counts }
        """

        if not project_names:
                project_names = []

        # Handle JSON string input from frontend
        project_names = frappe.parse_json(project_names) if isinstance(project_names, str) else project_names or []

        result = {}

        # Initialize all projects with zero counts
        for pname in project_names:
                result[pname] = {'AN': 0, 'AU': 0, 'LI': 0, 'RE': 0}

        # Early return if no projects
        if not project_names:
                return result

        # Debug logging
        frappe.logger().info(f'get_project_document_counts called with {len(project_names)} projects')
        frappe.logger().info(f'Project names: {project_names[:5]}...')  # First 5

        # ============================================================
        # AN (Angebote) - Count Quotations by custom_projektlink
        # ============================================================
        quotation_counts = frappe.db.sql("""
                SELECT custom_projektlink, COUNT(*) as count
                FROM `tabQuotation`
                WHERE custom_projektlink IN ({})
                AND docstatus != 2
                GROUP BY custom_projektlink
        """.format(','.join(['%s'] * len(project_names))),
        project_names,
        as_dict=True)

        frappe.logger().info(f'Quotations found: {len(quotation_counts)}')

        for row in quotation_counts:
                project_name = row['custom_projektlink']
                if project_name in result:
                        result[project_name]['AN'] = row['count']
                        frappe.logger().info(f'Set {project_name} AN={row["count"]}')

        # ============================================================
        # AU (Aufträge) - Count Sales Orders by project
        # ============================================================
        sales_order_counts = frappe.db.sql("""
                SELECT project, COUNT(*) as count
                FROM `tabSales Order`
                WHERE project IN ({})
                AND docstatus != 2
                GROUP BY project
        """.format(','.join(['%s'] * len(project_names))),
        project_names,
        as_dict=True)

        frappe.logger().info(f'Sales Orders found: {len(sales_order_counts)}')

        for row in sales_order_counts:
                if row['project'] in result:
                        result[row['project']]['AU'] = row['count']
                        frappe.logger().info(f'Set {row["project"]} AU={row["count"]}')

        # ============================================================
        # LI (Lieferscheine) - Count Delivery Notes by project
        # ============================================================
        delivery_note_counts = frappe.db.sql("""
                SELECT project, COUNT(*) as count
                FROM `tabDelivery Note`
                WHERE project IN ({})
                AND docstatus != 2
                GROUP BY project
        """.format(','.join(['%s'] * len(project_names))),
        project_names,
        as_dict=True)

        frappe.logger().info(f'Delivery Notes found: {len(delivery_note_counts)}')

        for row in delivery_note_counts:
                if row['project'] in result:
                        result[row['project']]['LI'] = row['count']
                        frappe.logger().info(f'Set {row["project"]} LI={row["count"]}')

        # ============================================================
        # RE (Rechnungen) - Count Sales Invoices by project
        # ============================================================
        sales_invoice_counts = frappe.db.sql("""
                SELECT project, COUNT(*) as count
                FROM `tabSales Invoice`
                WHERE project IN ({})
                AND docstatus != 2
                GROUP BY project
        """.format(','.join(['%s'] * len(project_names))),
        project_names,
        as_dict=True)

        frappe.logger().info(f'Sales Invoices found: {len(sales_invoice_counts)}')

        for row in sales_invoice_counts:
                if row['project'] in result:
                        result[row['project']]['RE'] = row['count']
                        frappe.logger().info(f'Set {row["project"]} RE={row["count"]}')

        frappe.logger().info(f'Final result keys: {list(result.keys())[:3]}...')  # First 3 project names

        return result
