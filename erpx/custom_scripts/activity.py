import frappe
from frappe.utils import add_days, today, get_datetime, getdate, flt
import datetime

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
    """Get heatmap data with detailed activity breakdown for specific project (including Google Calendar events)"""
    
    if not project:
        return get_simple_heatmap_data()
    
    try:
        # Get timesheet detailed breakdown by activity type for this specific project
        timesheet_detailed_data = frappe.db.sql(
            """select 
                date(tsd.from_time) as date,
                tsd.activity_type,
                sum(tsd.hours) as hours
            from `tabTimesheet Detail` tsd
            where
                date(tsd.from_time) >= '2024-01-01'
                and date(tsd.from_time) <= '2026-12-31'
                and tsd.project = %(project)s
            group by date(tsd.from_time), tsd.activity_type
            order by tsd.from_time asc, tsd.activity_type asc""",
            {"project": project},
            as_dict=True
        )
        
        # Get total timesheet hours per date
        timesheet_data = frappe.db.sql(
            """select 
                date(tsd.from_time) as date,
                sum(tsd.hours) as total_hours
            from `tabTimesheet Detail` tsd
            where
                date(tsd.from_time) >= '2024-01-01'
                and date(tsd.from_time) <= '2026-12-31'
                and tsd.project = %(project)s
            group by date(tsd.from_time)
            order by tsd.from_time asc""",
            {"project": project},
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
            and date(starts_on) >= '2024-01-01'
            and date(starts_on) <= '2026-12-31'
            and sync_with_google_calendar = 1""",
            {"project": project},
            as_dict=True
        )
            
    except Exception as e:
        frappe.log_error(f"Error in get_project_heatmap_data: {str(e)}")
        return get_simple_heatmap_data()
    
    # If no data for this project, return empty heatmap
    if not timesheet_data and not calendar_events:
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
    chart_start = datetime.date(2024, 7, 8)
    chart_end = datetime.date(2025, 7, 8)
    
    final_data = {}
    final_details = {}
    current_chart_date = chart_start
    
    while current_chart_date <= chart_end:
        chart_timestamp = int(datetime.datetime.combine(current_chart_date, datetime.time()).timestamp())
        actual_date = current_chart_date + datetime.timedelta(days=61)
        
        if actual_date >= datetime.date(2024, 1, 1) and actual_date <= datetime.date(2026, 12, 31):
            actual_timestamp = int(datetime.datetime.combine(actual_date, datetime.time()).timestamp())
            
            # Use the same mapping for both timesheets and calendar events
            final_data[chart_timestamp] = all_data.get(actual_timestamp, 0)
            final_details[chart_timestamp] = activity_details.get(actual_timestamp, {
                'activities': [],
                'total_hours': 0
            })
            
            # Debug logging for days with activities
            activities = final_details[chart_timestamp]['activities']
            if activities:
                actual_date_str = actual_date.strftime('%Y-%m-%d')
                current_chart_date_str = current_chart_date.strftime('%Y-%m-%d')
                frappe.log_error(f"Mapping: actual_date {actual_date_str} (timestamp {actual_timestamp}) -> chart_date {current_chart_date_str} (timestamp {chart_timestamp}): {len(activities)} activities")
        else:
            final_data[chart_timestamp] = 0
            final_details[chart_timestamp] = {'activities': [], 'total_hours': 0}
        
        current_chart_date += datetime.timedelta(days=1)
    
    return {
        'heatmap_data': final_data,
        'activity_details': final_details
    }

def get_simple_heatmap_data():
    """Fallback to simple heatmap data without activity details"""
    
    all_data = dict(
        frappe.db.sql(
            """select unix_timestamp(date(tsd.from_time)), sum(tsd.hours)
        from `tabTimesheet Detail` tsd
        where
            date(tsd.from_time) >= '2024-01-01'
            and date(tsd.from_time) <= '2026-12-31'
        group by date(tsd.from_time)
        order by tsd.from_time asc"""
        )
    )
    
    chart_start = datetime.date(2024, 7, 8)
    chart_end = datetime.date(2025, 7, 8)
    
    final_data = {}
    current_chart_date = chart_start
    
    while current_chart_date <= chart_end:
        chart_timestamp = int(datetime.datetime.combine(current_chart_date, datetime.time()).timestamp())
        actual_date = current_chart_date + datetime.timedelta(days=61)
        
        if actual_date >= datetime.date(2024, 1, 1) and actual_date <= datetime.date(2026, 12, 31):
            actual_timestamp = int(datetime.datetime.combine(actual_date, datetime.time()).timestamp())
            final_data[chart_timestamp] = all_data.get(actual_timestamp, 0)
        else:
            final_data[chart_timestamp] = 0
        
        current_chart_date += datetime.timedelta(days=1)
    
    return final_data

def get_empty_heatmap_data():
    """Return empty heatmap when no project data exists"""
    
    chart_start = datetime.date(2024, 7, 8)
    chart_end = datetime.date(2025, 7, 8)
    
    empty_data = {}
    empty_details = {}
    current_chart_date = chart_start
    
    while current_chart_date <= chart_end:
        chart_timestamp = int(datetime.datetime.combine(current_chart_date, datetime.time()).timestamp())
        empty_data[chart_timestamp] = 0
        empty_details[chart_timestamp] = {'activities': [], 'total_hours': 0}
        current_chart_date += datetime.timedelta(days=1)
    
    return {
        'heatmap_data': empty_data,
        'activity_details': empty_details
    }
