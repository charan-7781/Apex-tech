"""
auth.py
-------
Authentication, Role-Based Access Control (RBAC), and Session Security for SAVE KAROO.
Roles: CITIZEN, POLICE_OFFICER, POLICE_ADMIN, SUPER_ADMIN.
"""

import sqlite3
import re
from typing import Optional, Dict, Any, Tuple
from save_karoo_database import get_connection, hash_password, log_audit

EMAIL_REGEX = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
PHONE_REGEX = r'^\+?[0-9]{10,14}$'

def validate_registration_inputs(name: str, email: str, phone: str, password: str, confirm_pw: str) -> Tuple[bool, str]:
    if not name or len(name.strip()) < 3:
        return False, "Full Name must be at least 3 characters long."
    if not re.match(EMAIL_REGEX, email.strip()):
        return False, "Please enter a valid email address."
    clean_phone = phone.strip().replace(" ", "").replace("-", "")
    if not re.match(PHONE_REGEX, clean_phone):
        return False, "Please enter a valid 10-digit mobile number."
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if password != confirm_pw:
        return False, "Passwords do not match."
    return True, "Valid"

def authenticate_user(email_or_phone: str, password: str) -> Tuple[Optional[Dict[str, Any]], str]:
    """Authenticates user with email/phone and password."""
    conn = get_connection()
    cur = conn.cursor()
    clean_id = email_or_phone.strip()
    pw_hash = hash_password(password)

    cur.execute("""
        SELECT u.*, po.badge_number, po.rank, po.department_id, pd.name as department_name, po.is_verified as officer_verified
        FROM users u
        LEFT JOIN police_officers po ON u.id = po.user_id
        LEFT JOIN police_departments pd ON po.department_id = pd.id
        WHERE (LOWER(u.email) = LOWER(?) OR u.phone = ?) AND u.password_hash = ?;
    """, (clean_id, clean_id, pw_hash))

    row = cur.fetchone()
    conn.close()

    if not row:
        return None, "Invalid email/phone or password."

    user = dict(row)
    if user["status"] == "SUSPENDED":
        return None, "Your account has been suspended. Please contact platform administration."
    if user["status"] == "PENDING_APPROVAL" and user["role"] == "POLICE_OFFICER":
        return None, "Your police officer account is pending verification and approval by the Administrator."

    log_audit(user["id"], "LOGIN_SUCCESS", "AUTH", f"User {user['email']} logged in successfully.")
    return user, "Success"

def register_citizen(
    full_name: str,
    email: str,
    phone: str,
    password: str,
    state: str = "Karnataka",
    district: str = "Bengaluru Urban",
    city: str = "Bengaluru",
    address: str = ""
) -> Tuple[bool, str, Optional[int]]:
    """Registers a new citizen with ACTIVE status and FREE Safety plan."""
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(?);", (email.strip(),))
        if cur.fetchone():
            return False, "An account with this email address already exists.", None

        cur.execute("SELECT id FROM users WHERE phone = ?;", (phone.strip(),))
        if cur.fetchone():
            return False, "An account with this mobile number already exists.", None

        pw_hash = hash_password(password)
        cur.execute("""
            INSERT INTO users (full_name, email, phone, password_hash, role, status, state, district, city, address)
            VALUES (?, ?, ?, ?, 'CITIZEN', 'ACTIVE', ?, ?, ?, ?);
        """, (full_name.strip(), email.strip(), phone.strip(), pw_hash, state, district, city, address))

        user_id = cur.lastrowid

        # Assign Free Citizen Plan
        cur.execute("""
            INSERT INTO subscriptions (user_id, plan_id, billing_cycle, status)
            VALUES (?, 1, 'LIFETIME_FREE', 'ACTIVE');
        """, (user_id,))

        # Welcome notification
        cur.execute("""
            INSERT INTO notifications (user_id, title, message, notification_type)
            VALUES (?, 'Welcome to SAVE KAROO', 'Your citizen public safety account is active. You can report incidents, track cases, and consult KAROO AI at any time.', 'SYSTEM');
        """, (user_id,))

        conn.commit()
        log_audit(user_id, "REGISTER_CITIZEN", "USERS", f"Citizen registered: {email}")
        return True, "Citizen account registered successfully!", user_id

    except Exception as e:
        conn.rollback()
        return False, f"Registration error: {str(e)}", None
    finally:
        conn.close()

def register_police_officer_request(
    full_name: str,
    email: str,
    phone: str,
    password: str,
    badge_number: str,
    department_id: int,
    rank: str,
    state: str = "Karnataka",
    district: str = "Bengaluru Urban"
) -> Tuple[bool, str]:
    """Submits a police officer registration request with PENDING_APPROVAL status."""
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(?);", (email.strip(),))
        if cur.fetchone():
            return False, "An account with this email already exists."

        cur.execute("SELECT id FROM police_officers WHERE badge_number = ?;", (badge_number.strip().upper(),))
        if cur.fetchone():
            return False, "This Police Badge Number is already registered in the system."

        pw_hash = hash_password(password)
        cur.execute("""
            INSERT INTO users (full_name, email, phone, password_hash, role, status, state, district, city)
            VALUES (?, ?, ?, ?, 'POLICE_OFFICER', 'PENDING_APPROVAL', ?, ?, 'Bengaluru');
        """, (full_name.strip(), email.strip(), phone.strip(), pw_hash, state, district))

        user_id = cur.lastrowid

        cur.execute("""
            INSERT INTO police_officers (user_id, badge_number, department_id, rank, is_verified)
            VALUES (?, ?, ?, ?, 0);
        """, (user_id, badge_number.strip().upper(), department_id, rank))

        # Notify Admins of pending approval
        cur.execute("""
            INSERT INTO notifications (user_id, title, message, notification_type)
            SELECT id, 'New Police Account Verification Pending', 'Officer ' || ? || ' (Badge: ' || ? || ') has registered and requires credential verification.', 'SYSTEM'
            FROM users WHERE role IN ('POLICE_ADMIN', 'SUPER_ADMIN');
        """, (full_name, badge_number.strip().upper()))

        conn.commit()
        log_audit(user_id, "POLICE_REGISTER_REQUEST", "OFFICERS", f"Pending approval for badge {badge_number}")
        return True, "Police officer account application submitted! An Administrator will verify your credentials before activation."

    except Exception as e:
        conn.rollback()
        return False, f"Officer registration error: {str(e)}"
    finally:
        conn.close()

def approve_police_officer(officer_user_id: int, admin_user_id: int) -> Tuple[bool, str]:
    """Admin approves officer account to ACTIVE."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE users SET status = 'ACTIVE' WHERE id = ? AND role = 'POLICE_OFFICER';", (officer_user_id,))
        cur.execute("UPDATE police_officers SET is_verified = 1 WHERE user_id = ?;", (officer_user_id,))

        cur.execute("""
            INSERT INTO notifications (user_id, title, message, notification_type)
            VALUES (?, 'Police Account Verified', 'Your police officer portal access has been approved and activated. You can now review and act on assigned complaints.', 'SYSTEM');
        """, (officer_user_id,))

        conn.commit()
        log_audit(admin_user_id, "APPROVE_OFFICER", "OFFICERS", f"Officer ID {officer_user_id} approved.")
        return True, "Officer credentials approved and account activated."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def get_pending_police_officers():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT u.id as user_id, u.full_name, u.email, u.phone, u.created_at,
               po.badge_number, po.rank, pd.name as department_name
        FROM users u
        JOIN police_officers po ON u.id = po.user_id
        JOIN police_departments pd ON po.department_id = pd.id
        WHERE u.role = 'POLICE_OFFICER' AND u.status = 'PENDING_APPROVAL';
    """)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

