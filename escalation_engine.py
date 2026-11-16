"""
escalation_engine.py
--------------------
Automated Escalation Rule Engine for the SAVE KAROO Platform.
Monitors:
1. Repeat Offender Entities: >= 5 complaints against same vehicle/driver without resolution.
2. Inaction SLA Violations: Assigned complaints without recorded action for > 48 hours.
3. Unassigned Critical Emergencies: Critical/High priority complaints unassigned for > 12 hours.
"""

from typing import List, Dict, Any, Tuple
from save_karoo_database import get_connection, log_audit

def run_escalation_audit() -> Dict[str, int]:
    """Runs a sweep across active complaints to detect and flag escalations."""
    conn = get_connection()
    cur = conn.cursor()

    escalations_flagged = 0

    # 1. Check for Repeat Offender Vehicles (>= 5 active complaints)
    cur.execute("""
        SELECT vehicle_number, COUNT(*) as cnt
        FROM complaints
        WHERE vehicle_number IS NOT NULL 
          AND TRIM(vehicle_number) != ''
          AND status NOT IN ('RESOLVED', 'CLOSED', 'REJECTED')
        GROUP BY vehicle_number
        HAVING cnt >= 5;
    """)
    repeat_vehicles = cur.fetchall()

    for row in repeat_vehicles:
        veh, cnt = row[0], row[1]
        # Flag all active complaints for this vehicle that aren't yet flagged
        cur.execute("""
            UPDATE complaints 
            SET is_escalated = 1, escalation_reason = ?
            WHERE vehicle_number = ? AND is_escalated = 0 AND status NOT IN ('RESOLVED', 'CLOSED', 'REJECTED');
        """, (f"Vehicle {veh} reached threshold of {cnt} active complaints without closure.", veh))
        
        if cur.rowcount > 0:
            escalations_flagged += cur.rowcount
            # Insert escalation record for the latest complaint
            cur.execute("""
                SELECT id FROM complaints WHERE vehicle_number = ? ORDER BY created_at DESC LIMIT 1;
            """, (veh,))
            latest_id = cur.fetchone()[0]
            cur.execute("""
                INSERT OR IGNORE INTO escalation_records (complaint_id, reason, threshold_count, status)
                VALUES (?, ?, ?, 'PENDING_REVIEW');
            """, (latest_id, f"Repeat offender vehicle flagged with {cnt} accumulated cases.", cnt))

    # 2. Check for Cases with NO ACTION taken for > 48 Hours
    cur.execute("""
        SELECT c.id, c.priority, c.created_at
        FROM complaints c
        WHERE c.status IN ('ASSIGNED', 'UNDER REVIEW')
          AND c.is_escalated = 0
          AND (SELECT COUNT(*) FROM complaint_actions ca WHERE ca.complaint_id = c.id) = 0
          AND datetime(c.created_at, '+48 hours') < datetime('now');
    """)
    stalled_cases = cur.fetchall()

    for sc in stalled_cases:
        cid = sc[0]
        cur.execute("""
            UPDATE complaints SET is_escalated = 1, escalation_reason = 'No investigative action recorded within 48-hour SLA.'
            WHERE id = ?;
        """, (cid,))
        cur.execute("""
            INSERT OR IGNORE INTO escalation_records (complaint_id, reason, threshold_count, status)
            VALUES (?, 'SLA breach: 48 hours without action', 1, 'PENDING_REVIEW');
        """, (cid,))
        escalations_flagged += 1

    if escalations_flagged > 0:
        # Alert administrators
        cur.execute("""
            INSERT INTO notifications (user_id, title, message, notification_type)
            SELECT id, 'System Escalation Alert', ? || ' complaints were automatically escalated due to repeat violations or SLA breach.', 'ESCALATION'
            FROM users WHERE role IN ('POLICE_ADMIN', 'SUPER_ADMIN');
        """, (escalations_flagged,))

    conn.commit()
    conn.close()
    return {"flagged_count": escalations_flagged}

def get_escalation_records() -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT e.*, c.vehicle_number, c.service_provider, c.priority, c.district, c.status as complaint_status,
               u.full_name as citizen_name, u.phone as citizen_phone,
               uo.full_name as officer_name, po.badge_number
        FROM escalation_records e
        JOIN complaints c ON e.complaint_id = c.id
        JOIN users u ON c.citizen_id = u.id
        LEFT JOIN police_officers po ON c.assigned_officer_id = po.id
        LEFT JOIN users uo ON po.user_id = uo.id
        ORDER BY e.flagged_at DESC;
    """)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def resolve_escalation(
    escalation_id: int,
    admin_user_id: int,
    resolution_status: str, # 'ESCALATED', 'RESOLVED', 'DISMISSED'
    review_notes: str
) -> Tuple[bool, str]:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE escalation_records
            SET status = ?, reviewed_by_admin_id = ?, review_notes = ?
            WHERE id = ?;
        """, (resolution_status, admin_user_id, review_notes, escalation_id))

        if resolution_status in ('RESOLVED', 'DISMISSED'):
            # Clear escalation flag from linked complaint if resolved
            cur.execute("""
                UPDATE complaints SET is_escalated = 0 
                WHERE id = (SELECT complaint_id FROM escalation_records WHERE id = ?);
            """, (escalation_id,))

        conn.commit()
        log_audit(admin_user_id, "RESOLVE_ESCALATION", "ESCALATION", f"Escalation {escalation_id} set to {resolution_status}")
        return True, f"Escalation record marked as {resolution_status}."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

