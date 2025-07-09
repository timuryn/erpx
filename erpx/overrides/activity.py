import frappe
from frappe.utils import add_days, today, get_datetime
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
    """Get heatmap data with detailed activity breakdown for specific project"""
    
    if not project:
        return get_simple_heatmap_data()
    
    try:
        # Get detailed breakdown by activity type for this specific project
        detailed_data = frappe.db.sql(
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
        
        # Get total hours per date for heatmap data
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
            
    except Exception:
        return get_simple_heatmap_data()
    
    # If no timesheet data for this project, return empty heatmap
    if not timesheet_data:
        return get_empty_heatmap_data()
    
    # Convert to lookup dictionaries
    all_data = {}
    activity_details = {}
    
    # Process total hours
    for row in timesheet_data:
        timestamp = int(datetime.datetime.combine(row['date'], datetime.time()).timestamp())
        all_data[timestamp] = row['total_hours']
    
    # Process detailed breakdown
    for row in detailed_data:
        timestamp = int(datetime.datetime.combine(row['date'], datetime.time()).timestamp())
        
        if timestamp not in activity_details:
            activity_details[timestamp] = {
                'activities': [],
                'total_hours': 0
            }
        
        activity_details[timestamp]['activities'].append({
            'type': row['activity_type'] or 'Keine Aktivität',
            'hours': row['hours']
        })
        activity_details[timestamp]['total_hours'] += row['hours']
    
    # Apply date shifting and generate final data
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
            final_data[chart_timestamp] = all_data.get(actual_timestamp, 0)
            final_details[chart_timestamp] = activity_details.get(actual_timestamp, {
                'activities': [],
                'total_hours': 0
            })
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
