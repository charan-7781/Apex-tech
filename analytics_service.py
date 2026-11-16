"""
analytics_service.py
--------------------
Real-Time Database Aggregations, Performance Metrics, and Export Generators for SAVE KAROO.
All metrics are computed directly from live SQLite database records.
"""

from typing import Dict, Any, List
import io
import csv
from save_karoo_database import get_connection

def get_platform_kpi_summary() -> Dict[str, Any]:
    """Computes comprehensive top-level KPIs for Police Administrators and Super Admins."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM complaints;")
    total_complaints = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM complaints WHERE status IN ('RESOLVED', 'CLOSED');")
    resolved_complaints = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM complaints WHERE status IN ('ACTION INITIATED', 'INVESTIGATION IN PROGRESS');")
    active_inquiries = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM complaints WHERE status IN ('SUBMITTED', 'UNDER REVIEW');")
    pending_review = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM complaints WHERE assigned_officer_id IS NULL AND status NOT IN ('RESOLVED', 'CLOSED', 'REJECTED');")
    unassigned_cases = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM complaints WHERE is_escalated = 1 AND status NOT IN ('RESOLVED', 'CLOSED', 'REJECTED');")
    escalated_cases = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM users WHERE role = 'CITIZEN';")
    registered_citizens = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM police_officers WHERE is_verified = 1;")
    verified_officers = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM users WHERE role = 'POLICE_OFFICER' AND status = 'PENDING_APPROVAL';")
    pending_officer_approvals = cur.fetchone()[0]

    cur.execute("SELECT COALESCE(SUM(amount_inr), 0) FROM payments WHERE status = 'SUCCESS';")
    total_subscription_revenue = cur.fetchone()[0]

    conn.close()

    resolution_rate = round((resolved_complaints / total_complaints * 100), 1) if total_complaints > 0 else 0.0

    return {
        "total_complaints": total_complaints,
        "resolved_complaints": resolved_complaints,
        "active_inquiries": active_inquiries,
        "pending_review": pending_review,
        "unassigned_cases": unassigned_cases,
        "escalated_cases": escalated_cases,
        "resolution_rate": resolution_rate,
        "registered_citizens": registered_citizens,
        "verified_officers": verified_officers,
        "pending_officer_approvals": pending_officer_approvals,
        "total_subscription_revenue": total_subscription_revenue,
    }

def get_complaints_by_category() -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT cat.name, cat.icon, COUNT(c.id) as count
        FROM complaint_categories cat
        LEFT JOIN complaints c ON cat.id = c.category_id
        GROUP BY cat.id, cat.name, cat.icon
        ORDER BY count DESC;
    """)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_complaints_by_district() -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT district, COUNT(*) as count
        FROM complaints
        GROUP BY district
        ORDER BY count DESC;
    """)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_complaints_by_provider() -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COALESCE(service_provider, 'Independent / Direct') as provider, COUNT(*) as count
        FROM complaints
        GROUP BY provider
        ORDER BY count DESC;
    """)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_officer_workload_summary() -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT po.id, po.badge_number, po.rank, u.full_name as officer_name, pd.name as department_name,
               COUNT(c.id) as total_assigned,
               SUM(CASE WHEN c.status IN ('RESOLVED', 'CLOSED') THEN 1 ELSE 0 END) as resolved_count,
               SUM(CASE WHEN c.status NOT IN ('RESOLVED', 'CLOSED', 'REJECTED') THEN 1 ELSE 0 END) as active_count
        FROM police_officers po
        JOIN users u ON po.user_id = u.id
        LEFT JOIN police_departments pd ON po.department_id = pd.id
        LEFT JOIN complaints c ON po.id = c.assigned_officer_id
        WHERE po.is_verified = 1
        GROUP BY po.id
        ORDER BY active_count DESC;
    """)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def export_complaints_csv() -> str:
    """Generates an exportable CSV of complaints for administrative record keeping."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT c.id, c.status, c.priority, cat.name as category, c.vehicle_number,
               c.service_provider, c.driver_name, c.district, c.incident_datetime,
               u.full_name as citizen_name, u.phone as citizen_phone,
               po.badge_number as officer_badge, c.created_at
        FROM complaints c
        JOIN complaint_categories cat ON c.category_id = cat.id
        JOIN users u ON c.citizen_id = u.id
        LEFT JOIN police_officers po ON c.assigned_officer_id = po.id
        ORDER BY c.created_at DESC;
    """)
    rows = cur.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Complaint ID", "Status", "Priority", "Category", "Vehicle Number",
        "Service Provider", "Driver Name", "District", "Incident Date/Time",
        "Citizen Name", "Citizen Mobile", "Assigned Officer Badge", "Registered Timestamp"
    ])
    for r in rows:
        writer.writerow(list(r))
    return output.getvalue()

def generate_citizen_complaint_transcript(complaint_id: str) -> str:
    """Generates a formal, printable text transcript for a citizen's complaint."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT c.*, cat.name as category_name, u.full_name as citizen_name, u.phone as citizen_phone, u.email as citizen_email,
               po.badge_number, uo.full_name as officer_name, pd.name as department_name
        FROM complaints c
        JOIN complaint_categories cat ON c.category_id = cat.id
        JOIN users u ON c.citizen_id = u.id
        LEFT JOIN police_officers po ON c.assigned_officer_id = po.id
        LEFT JOIN users uo ON po.user_id = uo.id
        LEFT JOIN police_departments pd ON po.department_id = pd.id
        WHERE c.id = ?;
    """, (complaint_id,))
    comp = cur.fetchone()

    if not comp:
        conn.close()
        return "Complaint not found."

    cur.execute("SELECT * FROM complaint_status_history WHERE complaint_id = ? ORDER BY created_at ASC;", (complaint_id,))
    history = cur.fetchall()

    cur.execute("SELECT * FROM complaint_actions WHERE complaint_id = ? ORDER BY action_timestamp ASC;", (complaint_id,))
    actions = cur.fetchall()
    conn.close()

    txt = f"""================================================================================
🛡️ SAVE KAROO — PUBLIC SAFETY COMPLAINT RECORD & AUDIT TRANSCRIPT
================================================================================
COMPLAINT TRACKING ID : {comp['id']}
DATE REGISTERED       : {comp['created_at']}
STATUS                : {comp['status']}
PRIORITY              : {comp['priority']}

1. CITIZEN INFORMATION:
   Name      : {comp['citizen_name']}
   Contact   : {comp['citizen_phone']} | {comp['citizen_email']}

2. INCIDENT SPECIFICATIONS:
   Category        : {comp['category_name']}
   Date & Time     : {comp['incident_datetime']}
   Location        : {comp['location']}, {comp['district']}, {comp['state']}
   Vehicle Number  : {comp['vehicle_number'] or 'Not Provided'}
   Vehicle Type    : {comp['vehicle_type'] or 'N/A'}
   Provider / App  : {comp['service_provider'] or 'Direct Commercial'}
   Driver Name     : {comp['driver_name'] or 'Unknown'}
   Trip / Booking  : {comp['trip_id'] or 'N/A'}

3. INCIDENT DESCRIPTION:
   "{comp['description']}"

4. JURISDICTION & ASSIGNMENT:
   Assigned Officer : {comp['officer_name'] or 'Awaiting Assignment'} (Badge: {comp['badge_number'] or 'N/A'})
   Department       : {comp['department_name'] or 'Central Safety Queue'}

5. OFFICIAL ACTIONS TAKEN:
"""
    if actions:
        for a in actions:
            txt += f"   - [{a['action_timestamp']}] {a['action_type']}: {a['description']}\n"
    else:
        txt += "   - No formal actions recorded yet.\n"

    txt += "\n6. AUDIT STATUS TIMELINE:\n"
    for h in history:
        txt += f"   - [{h['created_at']}] {h['new_status']}: {h['citizen_visible_update']}\n"

    if comp['resolution_notes']:
        txt += f"\n7. CASE OUTCOME & RESOLUTION NOTES:\n   {comp['resolution_notes']}\n"

    txt += """================================================================================
DISCLAIMER: This electronic transcript was generated by the SAVE KAROO platform.
For immediate emergencies, contact National Emergency Helpline: 112 or Women Helpline: 1091.
================================================================================
"""
    return txt

