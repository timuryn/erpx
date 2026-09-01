import frappe
from frappe.utils import add_days, today, get_datetime, getdate, flt, strip_html_tags
import datetime
import re

@frappe.whitelist()
def get_heatmap_data():
    """Override default heatmap to show 2 months in future"""

    existing_data = dict(
        frappe.db.sql(
            """select unix_timestamp(date(creation)), count(name)
        from `tabActivity Log`
        where
            date(creation) >= adddate(subdate(curdate(), interval 1 year), interval 2 month)
            and date(creation) <= adddate(curdate(), interval 2 month)
        group by date(creation)
        order by creation asc"""
        )
    )

    start_date = add_days(today(), -365 + 60)
    end_date = add_days(today(), 60)
    current_date = get_datetime(start_date)

    complete_data = {}
    while current_date.strftime('%Y-%m-%d') <= end_date:
        timestamp = int(current_date.timestamp())
        complete_data[timestamp] = existing_data.get(timestamp, 0)
        current_date += datetime.timedelta(days=1)

    return complete_data

@frappe.whitelist()
def get_project_heatmap_data(project=None):
    """Get heatmap data with detailed activity breakdown for specific project
    (including Google Calendar events, project status changes, and task activity)"""

    if not project:
        return get_simple_heatmap_data()

    # Wide, rolling query window (relative to today, not hardcoded calendar dates) —
    # matches the chart's own rolling ~1yr-back / ~2mo-forward span, with slack either side.
    # Keep both a string form (for SQL params) and a date form (for comparing against
    # datetime.date values later, e.g. actual_date in the chart-mapping loop).
    query_start = add_days(today(), -400)
    query_end = add_days(today(), 90)
    query_start_date = getdate(query_start)
    query_end_date = getdate(query_end)

    try:
        # Get timesheet detailed breakdown by activity type for this specific project
        timesheet_detailed_data = frappe.db.sql(
            """select
                date(tsd.from_time) as date,
                tsd.activity_type,
                sum(tsd.hours) as hours
            from `tabTimesheet Detail` tsd
            where
                date(tsd.from_time) >= %(query_start)s
                and date(tsd.from_time) <= %(query_end)s
                and tsd.project = %(project)s
            group by date(tsd.from_time), tsd.activity_type
            order by tsd.from_time asc, tsd.activity_type asc""",
            {"project": project, "query_start": query_start, "query_end": query_end},
            as_dict=True
        )

        # Get total timesheet hours per date
        timesheet_data = frappe.db.sql(
            """select
                date(tsd.from_time) as date,
                sum(tsd.hours) as total_hours
            from `tabTimesheet Detail` tsd
            where
                date(tsd.from_time) >= %(query_start)s
                and date(tsd.from_time) <= %(query_end)s
                and tsd.project = %(project)s
            group by date(tsd.from_time)
            order by tsd.from_time asc""",
            {"project": project, "query_start": query_start, "query_end": query_end},
            as_dict=True
        )

        # Get Google Calendar events linked to this project
        calendar_events = frappe.db.sql(
            """select
                name,
                subject,
                date(starts_on) as event_date,
                starts_on,
                ends_on,
                all_day
            from `tabEvent`
            where custom_projektlink = %(project)s
            and date(starts_on) >= %(query_start)s
            and date(starts_on) <= %(query_end)s
            and sync_with_google_calendar = 1""",
            {"project": project, "query_start": query_start, "query_end": query_end},
            as_dict=True
        )

        # Get project status-change history from the automated
        # "Project status notification" Communications
        status_communications = frappe.db.sql(
            """select creation, content
            from `tabCommunication`
            where reference_doctype = 'Project'
            and reference_name = %(project)s
            and communication_type = 'Automated Message'
            and content like '%%neuen Status%%'
            order by creation asc""",
            {"project": project},
            as_dict=True
        )

        # Get tasks linked to this project. No creation-date filter here — we now
        # anchor task activity on exp_start_date/exp_end_date instead of creation,
        # so filtering by creation date could wrongly exclude a task whose planned
        # dates fall inside the window even if it was created long before/after.
        tasks = frappe.db.sql(
            """select name, subject, status, color, priority, description,
                exp_start_date, exp_end_date, creation, modified
            from `tabTask`
            where project = %(project)s""",
            {"project": project},
            as_dict=True
        )

        # Project documents — Quotation links via custom_projektlink, the others via
        # project (same field mapping the Project listview script already uses).
        quotations = frappe.db.sql(
            """select name, status, creation
            from `tabQuotation`
            where custom_projektlink = %(project)s
            and date(creation) >= %(query_start)s
            and date(creation) <= %(query_end)s""",
            {"project": project, "query_start": query_start, "query_end": query_end},
            as_dict=True
        )
        sales_orders = frappe.db.sql(
            """select name, status, creation
            from `tabSales Order`
            where project = %(project)s
            and date(creation) >= %(query_start)s
            and date(creation) <= %(query_end)s""",
            {"project": project, "query_start": query_start, "query_end": query_end},
            as_dict=True
        )
        delivery_notes = frappe.db.sql(
            """select name, status, creation
            from `tabDelivery Note`
            where project = %(project)s
            and date(creation) >= %(query_start)s
            and date(creation) <= %(query_end)s""",
            {"project": project, "query_start": query_start, "query_end": query_end},
            as_dict=True
        )
        sales_invoices = frappe.db.sql(
            """select name, status, creation
            from `tabSales Invoice`
            where project = %(project)s
            and date(creation) >= %(query_start)s
            and date(creation) <= %(query_end)s""",
            {"project": project, "query_start": query_start, "query_end": query_end},
            as_dict=True
        )

    except Exception as e:
        frappe.log_error(f"Error in get_project_heatmap_data: {str(e)}")
        return get_simple_heatmap_data()

    # If no data for this project, return empty heatmap
    if not timesheet_data and not calendar_events and not status_communications and not tasks \
            and not quotations and not sales_orders and not delivery_notes and not sales_invoices:
        return get_empty_heatmap_data()

    # Convert to lookup dictionaries
    all_data = {}
    activity_details = {}

    # Process timesheet total hours
    for row in timesheet_data:
        timestamp = int(datetime.datetime.combine(row['date'], datetime.time()).timestamp())
        all_data[timestamp] = all_data.get(timestamp, 0) + row['total_hours']

    # Process timesheet detailed breakdown
    for row in timesheet_detailed_data:
        timestamp = int(datetime.datetime.combine(row['date'], datetime.time()).timestamp())

        if timestamp not in activity_details:
            activity_details[timestamp] = {
                'activities': [],
                'total_hours': 0
            }

        activity_details[timestamp]['activities'].append({
            'type': row['activity_type'] or 'Keine Aktivität',
            'hours': row['hours'],
            'source': 'timesheet'
        })

    # Process Google Calendar events
    for event in calendar_events:
        timestamp = int(datetime.datetime.combine(event['event_date'], datetime.time()).timestamp())

        # Calculate event duration
        if event['all_day']:
            # For all-day events, assume 8 hours
            event_hours = 8.0
        else:
            # Calculate duration for timed events
            try:
                start_time = get_datetime(event['starts_on'])
                end_time = get_datetime(event['ends_on'])
                duration = end_time - start_time
                event_hours = duration.total_seconds() / 3600  # Convert to hours
                # Minimum 0.5 hours for very short events
                event_hours = max(event_hours, 0.5)
            except:
                event_hours = 1.0  # Default fallback

        # Add to total hours
        all_data[timestamp] = all_data.get(timestamp, 0) + event_hours

        # Add to activity details
        if timestamp not in activity_details:
            activity_details[timestamp] = {
                'activities': [],
                'total_hours': 0
            }

        # Truncate long event titles for display
        event_title = event['subject'][:40] + "..." if len(event['subject']) > 40 else event['subject']

        activity_details[timestamp]['activities'].append({
            'type': f"📅 {event_title}",
            'hours': event_hours,
            'source': 'calendar',
            'event_name': event['name'],
            'full_subject': event['subject']  # Store the full subject for tooltips
        })

        # Debug logging for calendar events
        frappe.log_error(f"Added calendar event '{event['subject']}' to timestamp {timestamp} ({event['event_date']})")

    # Process project status changes (from automated status-notification Communications)
    status_pattern = re.compile(r'Neuer Status:</strong>\s*([^<]+)<br')
    changed_by_pattern = re.compile(r'Ge\u00e4ndert von:</strong>\s*([^<]+)<br')
    user_full_names = {}  # cache to avoid a repeated User lookup per Communication

    for c in status_communications:
        status_match = status_pattern.search(c['content'])
        if not status_match:
            continue
        new_status = status_match.group(1).strip()
        changed_by_match = changed_by_pattern.search(c['content'])
        changed_by_email = changed_by_match.group(1).strip() if changed_by_match else None

        changed_by = None
        if changed_by_email:
            if changed_by_email not in user_full_names:
                user_full_names[changed_by_email] = frappe.db.get_value(
                    "User", changed_by_email, "full_name"
                )
            # fall back to the email itself if the user has no full_name set
            changed_by = user_full_names[changed_by_email] or changed_by_email

        c_date = get_datetime(c['creation']).date()
        ts = int(datetime.datetime.combine(c_date, datetime.time()).timestamp())

        all_data[ts] = all_data.get(ts, 0) + 0.25
        activity_details.setdefault(ts, {'activities': [], 'total_hours': 0})
        activity_details[ts]['activities'].append({
            'type': f"📌 Status: {new_status}",
            'status': new_status,
            'changed_by': changed_by,
            'hours': 0,
            'source': 'project_status',
        })

    # Process tasks linked to this project — active date range + completed
    MAX_TASK_SPAN_DAYS = 120  # safety cap against a mistakenly huge exp_start/exp_end range

    for t in tasks:
        exp_start = t.get('exp_start_date')
        exp_end = t.get('exp_end_date')
        priority = t.get('priority')

        # description is stored as rich-text HTML — strip tags and keep it short
        # enough for a tooltip, not a full document viewer
        raw_description = t.get('description') or ''
        clean_description = strip_html_tags(raw_description).strip()
        if len(clean_description) > 120:
            clean_description = clean_description[:120].rstrip() + '…'

        if exp_start and exp_end:
            start_d = getdate(exp_start)
            end_d = getdate(exp_end)
            if end_d < start_d:
                start_d, end_d = end_d, start_d
            span_days = (end_d - start_d).days
            if span_days > MAX_TASK_SPAN_DAYS:
                end_d = start_d + datetime.timedelta(days=MAX_TASK_SPAN_DAYS)

            current_d = start_d
            while current_d <= end_d:
                ts = int(datetime.datetime.combine(current_d, datetime.time()).timestamp())
                all_data[ts] = all_data.get(ts, 0) + 0.15
                activity_details.setdefault(ts, {'activities': [], 'total_hours': 0})
                activity_details[ts]['activities'].append({
                    'type': f"🕓 {t['subject']} ({t['status']})",
                    'subject': t['subject'],
                    'task_status': t['status'],
                    'color': t['color'],
                    'priority': priority,
                    'description': clean_description,
                    'hours': 0,
                    'source': 'task_active',
                    'task_name': t['name'],
                })
                current_d += datetime.timedelta(days=1)
        elif exp_start:
            # only a start date is set — mark that single day
            d = getdate(exp_start)
            ts = int(datetime.datetime.combine(d, datetime.time()).timestamp())
            all_data[ts] = all_data.get(ts, 0) + 0.25
            activity_details.setdefault(ts, {'activities': [], 'total_hours': 0})
            activity_details[ts]['activities'].append({
                'type': f"🕓 {t['subject']} ({t['status']}) – Start",
                'subject': t['subject'],
                'task_status': t['status'],
                'is_start_marker': True,
                'color': t['color'],
                'priority': priority,
                'description': clean_description,
                'hours': 0,
                'source': 'task_active',
                'task_name': t['name'],
            })
        else:
            # no exp_start_date/exp_end_date at all — fall back to creation date,
            # same as the original behaviour, so the task still shows up somewhere
            created_date = get_datetime(t['creation']).date()
            created_ts = int(datetime.datetime.combine(created_date, datetime.time()).timestamp())
            all_data[created_ts] = all_data.get(created_ts, 0) + 0.25
            activity_details.setdefault(created_ts, {'activities': [], 'total_hours': 0})
            activity_details[created_ts]['activities'].append({
                'type': f"🆕 {t['subject']}",
                'subject': t['subject'],
                'color': t['color'],
                'priority': priority,
                'description': clean_description,
                'hours': 0,
                'source': 'task_created',
                'task_name': t['name'],
            })

        if t['status'] == 'Completed':
            # proxy — completed_on / closing_date are not populated on this instance,
            # so `modified` is the best available signal for completion date
            completed_date = get_datetime(t['modified']).date()
            completed_ts = int(datetime.datetime.combine(completed_date, datetime.time()).timestamp())
            all_data[completed_ts] = all_data.get(completed_ts, 0) + 0.25
            activity_details.setdefault(completed_ts, {'activities': [], 'total_hours': 0})
            activity_details[completed_ts]['activities'].append({
                'type': f"✅ {t['subject']}",
                'subject': t['subject'],
                'color': t['color'],
                'hours': 0,
                'source': 'task_completed',
                'task_name': t['name'],
            })

    # Process project documents (Quotation, Sales Order, Delivery Note, Sales Invoice),
    # anchored on creation date, each with its own color and a link route matching
    # the Project listview's PROJECT_DOC_TYPES config.
    DOCUMENT_TYPE_CONFIG = [
        (quotations, 'Quotation', '#06b6d4', 'quotation'),
        (sales_orders, 'Sales Order', '#6366f1', 'sales-order'),
        (delivery_notes, 'Delivery Note', '#14b8a6', 'delivery-note'),
        (sales_invoices, 'Sales Invoice', '#ec4899', 'sales-invoice'),
    ]

    for docs, doc_type_label, doc_color, route in DOCUMENT_TYPE_CONFIG:
        for d in docs:
            doc_date = get_datetime(d['creation']).date()
            ts = int(datetime.datetime.combine(doc_date, datetime.time()).timestamp())
            all_data[ts] = all_data.get(ts, 0) + 0.2
            activity_details.setdefault(ts, {'activities': [], 'total_hours': 0})
            activity_details[ts]['activities'].append({
                'type': f"📄 {doc_type_label}: {d['name']}",
                'doc_type': doc_type_label,
                'doc_name': d['name'],
                'doc_status': d.get('status'),
                'color': doc_color,
                'hours': 0,
                'source': 'project_document',
                'route': route,
            })

    # Update total hours in activity details
    for timestamp in activity_details:
        total = sum(activity['hours'] for activity in activity_details[timestamp]['activities'])
        activity_details[timestamp]['total_hours'] = total

    # Debug: Show all activity timestamps before final mapping
    for ts, details in activity_details.items():
        if details['activities']:
            date_from_ts = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
            frappe.log_error(f"Activity data exists at timestamp {ts} (date: {date_from_ts}) with {len(details['activities'])} activities")

    # Apply date shifting and generate final data (same logic for both timesheets and calendar events)
    # Rolling window relative to today (was hardcoded to 2024-07-08..2025-07-08, which silently
    # went stale and dropped all real data once "today" moved past ~Sept 2025)
    chart_end = getdate(add_days(today(), 60))
    chart_start = chart_end - datetime.timedelta(days=365)

    final_data = {}
    final_details = {}
    current_chart_date = chart_start

    while current_chart_date <= chart_end:
        chart_timestamp = int(datetime.datetime.combine(current_chart_date, datetime.time()).timestamp())
        chart_date_str = current_chart_date.strftime('%Y-%m-%d')
        actual_date = current_chart_date + datetime.timedelta(days=61)

        if actual_date >= query_start_date and actual_date <= query_end_date:
            actual_timestamp = int(datetime.datetime.combine(actual_date, datetime.time()).timestamp())

            # Use the same mapping for both timesheets and calendar events.
            # heatmap_data stays keyed by unix timestamp (frappe.Chart requires this),
            # but activity_details is keyed by plain date string ('YYYY-MM-DD') instead —
            # comparing raw epoch integers built server-side (Python, container timezone)
            # against ones rebuilt client-side (JS, browser timezone) is fragile and was
            # silently failing to match whenever the two differed by even one hour.
            final_data[chart_timestamp] = all_data.get(actual_timestamp, 0)
            final_details[chart_date_str] = activity_details.get(actual_timestamp, {
                'activities': [],
                'total_hours': 0
            })

            # Debug logging for days with activities
            activities = final_details[chart_date_str]['activities']
            if activities:
                actual_date_str = actual_date.strftime('%Y-%m-%d')
                frappe.log_error(f"Mapping: actual_date {actual_date_str} (timestamp {actual_timestamp}) -> chart_date {chart_date_str}: {len(activities)} activities")
        else:
            final_data[chart_timestamp] = 0
            final_details[chart_date_str] = {'activities': [], 'total_hours': 0}

        current_chart_date += datetime.timedelta(days=1)

    return {
        'heatmap_data': final_data,
        'activity_details': final_details,
        # exposed so the client script doesn't have to hardcode/duplicate the chart's
        # anchor date and shift — that duplication is what caused the tooltip misalignment
        'chart_start_timestamp': int(datetime.datetime.combine(chart_start, datetime.time()).timestamp()),
        'shift_days': 61,
    }

def get_simple_heatmap_data():
    """Fallback to simple heatmap data without activity details"""

    query_start = add_days(today(), -400)
    query_end = add_days(today(), 90)
    query_start_date = getdate(query_start)
    query_end_date = getdate(query_end)

    all_data = dict(
        frappe.db.sql(
            """select unix_timestamp(date(tsd.from_time)), sum(tsd.hours)
        from `tabTimesheet Detail` tsd
        where
            date(tsd.from_time) >= %(query_start)s
            and date(tsd.from_time) <= %(query_end)s
        group by date(tsd.from_time)
        order by tsd.from_time asc""",
            {"query_start": query_start, "query_end": query_end}
        )
    )

    chart_end = getdate(add_days(today(), 60))
    chart_start = chart_end - datetime.timedelta(days=365)

    final_data = {}
    current_chart_date = chart_start

    while current_chart_date <= chart_end:
        chart_timestamp = int(datetime.datetime.combine(current_chart_date, datetime.time()).timestamp())
        actual_date = current_chart_date + datetime.timedelta(days=61)

        if actual_date >= query_start_date and actual_date <= query_end_date:
            actual_timestamp = int(datetime.datetime.combine(actual_date, datetime.time()).timestamp())
            final_data[chart_timestamp] = all_data.get(actual_timestamp, 0)
        else:
            final_data[chart_timestamp] = 0

        current_chart_date += datetime.timedelta(days=1)

    return final_data

def get_empty_heatmap_data():
    """Return empty heatmap when no project data exists"""

    chart_end = getdate(add_days(today(), 60))
    chart_start = chart_end - datetime.timedelta(days=365)

    empty_data = {}
    empty_details = {}
    current_chart_date = chart_start

    while current_chart_date <= chart_end:
        chart_timestamp = int(datetime.datetime.combine(current_chart_date, datetime.time()).timestamp())
        empty_data[chart_timestamp] = 0
        empty_details[current_chart_date.strftime('%Y-%m-%d')] = {'activities': [], 'total_hours': 0}
        current_chart_date += datetime.timedelta(days=1)

    return {
        'heatmap_data': empty_data,
        'activity_details': empty_details,
        'chart_start_timestamp': int(datetime.datetime.combine(chart_start, datetime.time()).timestamp()),
        'shift_days': 61,
    }
