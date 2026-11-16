"""
complaint_service.py
--------------------
Complaint Management, Status Lifecycle, Evidence Handling, and Officer Action Tracking.
Enforces the 10-stage complaint lifecycle:
1. SUBMITTED
2. UNDER REVIEW
3. VERIFIED
4. ASSIGNED
5. ACTION INITIATED
6. INVESTIGATION IN PROGRESS
7. AWAITING CITIZEN RESPONSE
8. RESOLVED
9. CLOSED
10. REJECTED
"""

import datetime
from typing import List, Dict, Any, Optional, Tuple
from save_karoo_database import get_connection, log_audit, get_next_complaint_id

VALID_STATUSES = [
    'SUBMITTED', 'UNDER REVIEW', 'VERIFIED', 'ASSIGNED',
    'ACTION INITIATED', 'INVESTIGATION IN PROGRESS',
    'AWAITING CITIZEN RESPONSE', 'RESOLVED', 'CLOSED', 'REJECTED'
]

def submit_complaint(
    citizen_id: int,
    category_id: int,
    priority: str,
    incident_datetime: str,
    location: str,
    district: str,
    state: str,
    description: str,
    vehicle_number: Optional[str] = None,
    vehicle_type: Optional[str] = None,
    service_provider: Optional[str] = None,
    driver_name: Optional[str] = None,
    trip_id: Optional[str] = None,
    evidence_files: Optional[List[Dict[str, Any]]] = None
) -> Tuple[bool, str, Optional[str]]:
    """Submits a new citizen complaint and kicks off the audit lifecycle."""
    if not description or len(description.strip()) < 15:
        return False, "Please provide a detailed incident description (at least 15 characters).", None
    if not location or len(location.strip()) < 3:
        return False, "Please specify the incident location.", None

    conn = get_connection()
    cur = conn.cursor()

    try:
        complaint_id = get_next_complaint_id()
        clean_vehicle = vehicle_number.strip().upper() if vehicle_number else None

        cur.execute("""
            INSERT INTO complaints (
                id, citizen_id, category_id, priority, status,
                incident_datetime, location, district, state, description,
                vehicle_number, vehicle_type, service_provider, driver_name, trip_id
            ) VALUES (?, ?, ?, ?, 'SUBMITTED', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            complaint_id, citizen_id, category_id, priority,
            incident_datetime, location.strip(), district, state, description.strip(),
            clean_vehicle, vehicle_type, service_provider, driver_name, trip_id
        ))

        # Initial Status History
        cur.execute("""
            INSERT INTO complaint_status_history (
                complaint_id, old_status, new_status, changed_by_user_id,
                change_notes, citizen_visible_update
            ) VALUES (?, NULL, 'SUBMITTED', ?, 'Complaint submitted by citizen',
                      'Your complaint has been registered with ID ' || ? || '. It has entered the administrative verification queue.');
        """, (complaint_id, citizen_id, complaint_id))

        # Evidence files
        if evidence_files:
            for ef in evidence_files:
                cur.execute("""
                    INSERT INTO complaint_evidence (complaint_id, file_name, file_type, file_size_kb, description, storage_url)
                    VALUES (?, ?, ?, ?, ?, ?);
                """, (complaint_id, ef.get("name", "evidence"), ef.get("type", "image"), ef.get("size", 100), ef.get("desc", ""), ef.get("url", "")))

        # Citizen Notification
        cur.execute("""
            INSERT INTO notifications (user_id, title, message, notification_type, link)
            VALUES (?, 'Complaint Filed Successfully', 'Your complaint ' || ? || ' has been recorded. Track progress under My Complaints.', 'COMPLAINT', ?);
        """, (citizen_id, complaint_id, complaint_id))

        # Check for vehicle-based escalation rule (if >= 5 complaints for same vehicle)
        if clean_vehicle:
            cur.execute("""
                SELECT COUNT(*) FROM complaints 
                WHERE vehicle_number = ? AND status NOT IN ('RESOLVED', 'CLOSED', 'REJECTED');
            """, (clean_vehicle,))
            v_count = cur.fetchone()[0]
            if v_count >= 5:
                # Trigger escalation
                cur.execute("""
                    UPDATE complaints SET is_escalated = 1, escalation_reason = ? WHERE id = ?;
                """, (f"Vehicle {clean_vehicle} has accumulated {v_count} active complaints.", complaint_id))
                
                cur.execute("""
                    INSERT INTO escalation_records (complaint_id, reason, threshold_count, status)
                    VALUES (?, ?, ?, 'PENDING_REVIEW');
                """, (complaint_id, f"Vehicle {clean_vehicle} reached {v_count} complaints threshold.", v_count))

                # Alert Police Administrators
                cur.execute("""
                    INSERT INTO notifications (user_id, title, message, notification_type, link)
                    SELECT id, 'High Escalation Alert: Repeated Offender Vehicle', 
                           'Vehicle ' || ? || ' has reached ' || ? || ' active safety complaints. Immediate intervention required.',
                           'ESCALATION', ?
                    FROM users WHERE role IN ('POLICE_ADMIN', 'SUPER_ADMIN');
                """, (clean_vehicle, v_count, complaint_id))

        conn.commit()
        log_audit(citizen_id, "SUBMIT_COMPLAINT", "COMPLAINTS", f"Complaint {complaint_id} filed by citizen {citizen_id}")
        return True, "Complaint successfully registered!", complaint_id

    except Exception as e:
        conn.rollback()
        return False, f"Failed to submit complaint: {str(e)}", None
    finally:
        conn.close()

def update_complaint_status(
    complaint_id: str,
    new_status: str,
    changed_by_user_id: int,
    change_notes: str,
    citizen_visible_update: str,
    resolution_notes: Optional[str] = None
) -> Tuple[bool, str]:
    """Updates complaint status and logs audit timeline entry."""
    if new_status not in VALID_STATUSES:
        return False, f"Invalid status: {new_status}"

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT status, citizen_id FROM complaints WHERE id = ?;", (complaint_id,))
        row = cur.fetchone()
        if not row:
            return False, "Complaint not found."

        old_status, citizen_id = row[0], row[1]

        sql = "UPDATE complaints SET status = ?, updated_at = CURRENT_TIMESTAMP"
        params = [new_status]
        if resolution_notes:
            sql += ", resolution_notes = ?"
            params.append(resolution_notes)
        sql += " WHERE id = ?;"
        params.append(complaint_id)

        cur.execute(sql, params)

        # Record Status History
        cur.execute("""
            INSERT INTO complaint_status_history (
                complaint_id, old_status, new_status, changed_by_user_id,
                change_notes, citizen_visible_update
            ) VALUES (?, ?, ?, ?, ?, ?);
        """, (complaint_id, old_status, new_status, changed_by_user_id, change_notes, citizen_visible_update))

        # Notify Citizen
        cur.execute("""
            INSERT INTO notifications (user_id, title, message, notification_type, link)
            VALUES (?, 'Complaint Status Updated', 'Your complaint ' || ? || ' status changed to ' || ? || ': ' || ?, 'STATUS', ?);
        """, (citizen_id, complaint_id, new_status, citizen_visible_update, complaint_id))

        conn.commit()
        log_audit(changed_by_user_id, "UPDATE_STATUS", "COMPLAINTS", f"{complaint_id}: {old_status} -> {new_status}")
        return True, "Status updated successfully."

    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def assign_officer(
    complaint_id: str,
    officer_id: int,
    assigned_by_user_id: int,
    instructions: str = ""
) -> Tuple[bool, str]:
    """Assigns an officer to a complaint and notifies parties."""
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT id, user_id, badge_number FROM police_officers WHERE id = ?;", (officer_id,))
        officer = cur.fetchone()
        if not officer:
            return False, "Officer not found."

        officer_user_id = officer[1]
        badge = officer[2]

        cur.execute("""
            UPDATE complaints SET assigned_officer_id = ?, status = 'ASSIGNED', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?;
        """, (officer_id, complaint_id))

        cur.execute("""
            INSERT INTO complaint_assignments (complaint_id, officer_id, assigned_by_user_id, instructions, status)
            VALUES (?, ?, ?, ?, 'ACTIVE');
        """, (complaint_id, officer_id, assigned_by_user_id, instructions))

        # Status timeline update
        cur.execute("""
            INSERT INTO complaint_status_history (
                complaint_id, old_status, new_status, changed_by_user_id,
                change_notes, citizen_visible_update
            ) VALUES (?, 'VERIFIED', 'ASSIGNED', ?, ?, 'Assigned to Investigating Officer (Badge: ' || ? || '). Preliminary inquiries underway.');
        """, (complaint_id, assigned_by_user_id, f"Assigned to officer badge {badge}", badge))

        # Notify Officer
        cur.execute("""
            INSERT INTO notifications (user_id, title, message, notification_type, link)
            VALUES (?, 'New Case Assigned', 'You have been assigned complaint ' || ? || '. Please review incident details and record action.', 'COMPLAINT', ?);
        """, (officer_user_id, complaint_id, complaint_id))

        conn.commit()
        log_audit(assigned_by_user_id, "ASSIGN_OFFICER", "COMPLAINTS", f"{complaint_id} assigned to Officer {officer_id}")
        return True, f"Complaint assigned to Officer (Badge {badge}) successfully."

    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def record_official_action(
    complaint_id: str,
    officer_id: int,
    action_type: str,
    description: str,
    citizen_visible: bool = True
) -> Tuple[bool, str]:
    """Records an official investigation action (Challan, Summon, Warning, Inspection)."""
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO complaint_actions (complaint_id, officer_id, action_type, description, citizen_visible)
            VALUES (?, ?, ?, ?, ?);
        """, (complaint_id, officer_id, action_type, description, 1 if citizen_visible else 0))

        # Ensure complaint is marked as ACTION INITIATED if it was ASSIGNED
        cur.execute("SELECT status, citizen_id FROM complaints WHERE id = ?;", (complaint_id,))
        row = cur.fetchone()
        if row and row[0] in ('ASSIGNED', 'VERIFIED'):
            cur.execute("""
                UPDATE complaints SET status = 'ACTION INITIATED', updated_at = CURRENT_TIMESTAMP WHERE id = ?;
            """, (complaint_id,))
            cur.execute("""
                INSERT INTO complaint_status_history (
                    complaint_id, old_status, new_status, changed_by_user_id, change_notes, citizen_visible_update
                ) VALUES (?, ?, 'ACTION INITIATED', (SELECT user_id FROM police_officers WHERE id = ?), 'Officer logged official action', ?);
            """, (complaint_id, row[0], officer_id, f"Official action taken: {action_type} - {description}"))

        if row and citizen_visible:
            cur.execute("""
                INSERT INTO notifications (user_id, title, message, notification_type, link)
                VALUES (?, 'Official Action Recorded on Your Case', 'Investigating officer recorded action on ' || ? || ': ' || ?, 'ACTION', ?);
            """, (row[1], complaint_id, action_type, complaint_id))

        conn.commit()
        log_audit(None, "RECORD_ACTION", "ACTIONS", f"Action {action_type} recorded on {complaint_id}")
        return True, "Official action recorded successfully in police audit log."

    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def get_citizen_complaints(citizen_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT c.*, cat.name as category_name, cat.icon as category_icon,
               po.badge_number, u.full_name as officer_name
        FROM complaints c
        JOIN complaint_categories cat ON c.category_id = cat.id
        LEFT JOIN police_officers po ON c.assigned_officer_id = po.id
        LEFT JOIN users u ON po.user_id = u.id
        WHERE c.citizen_id = ?
        ORDER BY c.created_at DESC;
    """, (citizen_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_officer_complaints(officer_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT c.*, cat.name as category_name, cat.icon as category_icon,
               u.full_name as citizen_name, u.phone as citizen_phone, u.email as citizen_email
        FROM complaints c
        JOIN complaint_categories cat ON c.category_id = cat.id
        JOIN users u ON c.citizen_id = u.id
        WHERE c.assigned_officer_id = ?
        ORDER BY CASE c.priority WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'MEDIUM' THEN 3 ELSE 4 END, c.created_at DESC;
    """, (officer_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_all_complaints(
    status: Optional[str] = None,
    district: Optional[str] = None,
    category_id: Optional[int] = None,
    priority: Optional[str] = None,
    search: Optional[str] = None,
    unassigned_only: bool = False,
    escalated_only: bool = False
) -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()

    sql = """
        SELECT c.*, cat.name as category_name, cat.icon as category_icon,
               u.full_name as citizen_name, u.phone as citizen_phone,
               po.badge_number, uo.full_name as officer_name, pd.name as department_name,
               (SELECT COUNT(*) FROM complaint_actions ca WHERE ca.complaint_id = c.id) as action_count
        FROM complaints c
        JOIN complaint_categories cat ON c.category_id = cat.id
        JOIN users u ON c.citizen_id = u.id
        LEFT JOIN police_officers po ON c.assigned_officer_id = po.id
        LEFT JOIN users uo ON po.user_id = uo.id
        LEFT JOIN police_departments pd ON po.department_id = pd.id
        WHERE 1=1
    """
    params = []

    if status and status != "ALL":
        sql += " AND c.status = ?"
        params.append(status)
    if district and district != "ALL":
        sql += " AND c.district = ?"
        params.append(district)
    if category_id:
        sql += " AND c.category_id = ?"
        params.append(category_id)
    if priority and priority != "ALL":
        sql += " AND c.priority = ?"
        params.append(priority)
    if unassigned_only:
        sql += " AND c.assigned_officer_id IS NULL AND c.status NOT IN ('RESOLVED', 'CLOSED', 'REJECTED')"
    if escalated_only:
        sql += " AND c.is_escalated = 1"
    if search:
        sql += " AND (c.id LIKE ? OR c.vehicle_number LIKE ? OR u.full_name LIKE ? OR c.service_provider LIKE ?)"
        s = f"%{search.strip()}%"
        params.extend([s, s, s, s])

    sql += " ORDER BY c.created_at DESC;"
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

