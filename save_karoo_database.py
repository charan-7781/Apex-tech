"""
save_karoo_database.py
----------------------
Database Architecture & Relational Schema for the SAVE KAROO Public Safety Platform.
Implements 19 relational entities with SQLite, WAL mode, foreign key enforcement,
indexing, migrations, and realistic seed data.
"""

import sqlite3
import hashlib
import json
import os
import datetime
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "save_karoo.db")

def get_connection() -> sqlite3.Connection:
    """Returns a thread-safe connection with row_factory enabled and FKs enforced."""
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn

def hash_password(password: str) -> str:
    """Hashes passwords using SHA-256 with a project salt."""
    salt = "SAVE_KAROO_SECURE_SALT_2026"
    return hashlib.sha256((salt + password).encode('utf-8')).hexdigest()

def init_db(force_reseed: bool = False):
    """Creates all 19 relational tables, indexes, and populates initial seed data."""
    conn = get_connection()
    cur = conn.cursor()

    if force_reseed:
        tables = [
            "audit_logs", "support_tickets", "invoices", "payments", "subscriptions",
            "subscription_plans", "notifications", "escalation_records", "complaint_actions",
            "complaint_status_history", "complaint_assignments", "complaint_evidence",
            "complaints", "complaint_categories", "police_officers", "police_departments",
            "districts", "users", "system_settings"
        ]
        for t in tables:
            cur.execute(f"DROP TABLE IF EXISTS {t};")
        conn.commit()

    # 1. Users Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('CITIZEN', 'POLICE_OFFICER', 'POLICE_ADMIN', 'SUPER_ADMIN')),
        status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE', 'PENDING_APPROVAL', 'SUSPENDED')),
        state TEXT DEFAULT 'Karnataka',
        district TEXT DEFAULT 'Bengaluru Urban',
        city TEXT DEFAULT 'Bengaluru',
        address TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Districts & Jurisdictions
    cur.execute("""
    CREATE TABLE IF NOT EXISTS districts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        state TEXT NOT NULL,
        zone TEXT NOT NULL,
        emergency_helpline TEXT DEFAULT '112',
        women_helpline TEXT DEFAULT '1091',
        traffic_helpline TEXT DEFAULT '1095'
    );
    """)

    # 3. Police Departments / Stations
    cur.execute("""
    CREATE TABLE IF NOT EXISTS police_departments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        district_id INTEGER NOT NULL,
        station_code TEXT UNIQUE NOT NULL,
        contact_phone TEXT NOT NULL,
        address TEXT,
        FOREIGN KEY (district_id) REFERENCES districts(id) ON DELETE CASCADE
    );
    """)

    # 4. Police Officers
    cur.execute("""
    CREATE TABLE IF NOT EXISTS police_officers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        badge_number TEXT UNIQUE NOT NULL,
        department_id INTEGER NOT NULL,
        rank TEXT NOT NULL,
        is_verified INTEGER DEFAULT 0,
        active_case_limit INTEGER DEFAULT 15,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (department_id) REFERENCES police_departments(id) ON DELETE CASCADE
    );
    """)

    # 5. Complaint Categories
    cur.execute("""
    CREATE TABLE IF NOT EXISTS complaint_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        default_priority TEXT DEFAULT 'MEDIUM' CHECK(default_priority IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
        icon TEXT DEFAULT '⚠️'
    );
    """)

    # 6. Core Complaints Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS complaints (
        id TEXT PRIMARY KEY, -- e.g. SK-2026-000001
        citizen_id INTEGER NOT NULL,
        category_id INTEGER NOT NULL,
        priority TEXT NOT NULL DEFAULT 'MEDIUM' CHECK(priority IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
        status TEXT NOT NULL DEFAULT 'SUBMITTED' CHECK(status IN (
            'SUBMITTED', 'UNDER REVIEW', 'VERIFIED', 'ASSIGNED',
            'ACTION INITIATED', 'INVESTIGATION IN PROGRESS',
            'AWAITING CITIZEN RESPONSE', 'RESOLVED', 'CLOSED', 'REJECTED'
        )),
        incident_datetime TIMESTAMP NOT NULL,
        location TEXT NOT NULL,
        district TEXT NOT NULL,
        state TEXT NOT NULL,
        description TEXT NOT NULL,
        vehicle_number TEXT,
        vehicle_type TEXT,
        service_provider TEXT,
        driver_name TEXT,
        trip_id TEXT,
        assigned_officer_id INTEGER,
        is_escalated INTEGER DEFAULT 0,
        escalation_reason TEXT,
        resolution_notes TEXT,
        citizen_feedback_rating INTEGER,
        citizen_feedback_comment TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (citizen_id) REFERENCES users(id) ON DELETE RESTRICT,
        FOREIGN KEY (category_id) REFERENCES complaint_categories(id),
        FOREIGN KEY (assigned_officer_id) REFERENCES police_officers(id)
    );
    """)

    # 7. Complaint Evidence Files
    cur.execute("""
    CREATE TABLE IF NOT EXISTS complaint_evidence (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        complaint_id TEXT NOT NULL,
        file_name TEXT NOT NULL,
        file_type TEXT NOT NULL,
        file_size_kb INTEGER NOT NULL,
        description TEXT,
        storage_url TEXT,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (complaint_id) REFERENCES complaints(id) ON DELETE CASCADE
    );
    """)

    # 8. Complaint Assignments
    cur.execute("""
    CREATE TABLE IF NOT EXISTS complaint_assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        complaint_id TEXT NOT NULL,
        officer_id INTEGER NOT NULL,
        assigned_by_user_id INTEGER NOT NULL,
        instructions TEXT,
        status TEXT DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE', 'REASSIGNED', 'COMPLETED')),
        assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (complaint_id) REFERENCES complaints(id) ON DELETE CASCADE,
        FOREIGN KEY (officer_id) REFERENCES police_officers(id) ON DELETE CASCADE,
        FOREIGN KEY (assigned_by_user_id) REFERENCES users(id)
    );
    """)

    # 9. Complaint Status History (Audit Timeline)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS complaint_status_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        complaint_id TEXT NOT NULL,
        old_status TEXT,
        new_status TEXT NOT NULL,
        changed_by_user_id INTEGER NOT NULL,
        change_notes TEXT,
        citizen_visible_update TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (complaint_id) REFERENCES complaints(id) ON DELETE CASCADE,
        FOREIGN KEY (changed_by_user_id) REFERENCES users(id)
    );
    """)

    # 10. Official Actions Taken
    cur.execute("""
    CREATE TABLE IF NOT EXISTS complaint_actions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        complaint_id TEXT NOT NULL,
        officer_id INTEGER NOT NULL,
        action_type TEXT NOT NULL, -- e.g. Notice Sent, Vehicle Flagged, Driver Summoned, Case Dispatched
        description TEXT NOT NULL,
        citizen_visible INTEGER DEFAULT 1,
        action_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (complaint_id) REFERENCES complaints(id) ON DELETE CASCADE,
        FOREIGN KEY (officer_id) REFERENCES police_officers(id) ON DELETE CASCADE
    );
    """)

    # 11. Escalation Engine Records
    cur.execute("""
    CREATE TABLE IF NOT EXISTS escalation_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        complaint_id TEXT NOT NULL,
        reason TEXT NOT NULL,
        threshold_count INTEGER DEFAULT 5,
        status TEXT DEFAULT 'PENDING_REVIEW' CHECK(status IN ('PENDING_REVIEW', 'ESCALATED', 'DISMISSED', 'RESOLVED')),
        flagged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        reviewed_by_admin_id INTEGER,
        review_notes TEXT,
        FOREIGN KEY (complaint_id) REFERENCES complaints(id) ON DELETE CASCADE,
        FOREIGN KEY (reviewed_by_admin_id) REFERENCES users(id)
    );
    """)

    # 12. In-App Notifications
    cur.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        notification_type TEXT NOT NULL DEFAULT 'SYSTEM' CHECK(notification_type IN ('COMPLAINT', 'STATUS', 'ACTION', 'ESCALATION', 'BILLING', 'SYSTEM')),
        link TEXT,
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # 13. Subscription Plans
    cur.execute("""
    CREATE TABLE IF NOT EXISTS subscription_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plan_code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        price_monthly_inr REAL NOT NULL,
        price_annual_inr REAL NOT NULL,
        features_json TEXT NOT NULL,
        is_active INTEGER DEFAULT 1
    );
    """)

    # 14. Subscriptions
    cur.execute("""
    CREATE TABLE IF NOT EXISTS subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        plan_id INTEGER NOT NULL,
        billing_cycle TEXT NOT NULL CHECK(billing_cycle IN ('MONTHLY', 'ANNUAL', 'LIFETIME_FREE')),
        status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE', 'CANCELLED', 'EXPIRED')),
        starts_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (plan_id) REFERENCES subscription_plans(id)
    );
    """)

    # 15. Payments (Razorpay Test Mode Integration)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subscription_id INTEGER,
        user_id INTEGER NOT NULL,
        amount_inr REAL NOT NULL,
        gateway TEXT DEFAULT 'RAZORPAY_TEST',
        transaction_ref TEXT UNIQUE NOT NULL,
        status TEXT NOT NULL DEFAULT 'SUCCESS' CHECK(status IN ('SUCCESS', 'PENDING', 'FAILED')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (subscription_id) REFERENCES subscriptions(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    """)

    # 16. Invoices
    cur.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_number TEXT UNIQUE NOT NULL,
        payment_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        amount_inr REAL NOT NULL,
        pdf_ref TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (payment_id) REFERENCES payments(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    """)

    # 17. Citizen Support Tickets
    cur.execute("""
    CREATE TABLE IF NOT EXISTS support_tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        subject TEXT NOT NULL,
        category TEXT NOT NULL,
        message TEXT NOT NULL,
        status TEXT DEFAULT 'OPEN' CHECK(status IN ('OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED')),
        admin_response TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    """)

    # 18. Audit Logs (Security & Compliance)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT NOT NULL,
        resource TEXT NOT NULL,
        ip_address TEXT DEFAULT '127.0.0.1',
        details TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    );
    """)

    # 19. System Settings
    cur.execute("""
    CREATE TABLE IF NOT EXISTS system_settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        description TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Optimization Indexes
    cur.execute("CREATE INDEX IF NOT EXISTS idx_complaints_citizen ON complaints(citizen_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_complaints_status ON complaints(status);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_complaints_district ON complaints(district);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_complaints_officer ON complaints(assigned_officer_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id, is_read);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp);")

    conn.commit()

    # Seed data if empty or forced
    user_count = cur.execute("SELECT COUNT(*) FROM users;").fetchone()[0]
    if user_count == 0 or force_reseed:
        seed_initial_data(conn)

    conn.close()

def seed_initial_data(conn: sqlite3.Connection):
    """Inserts foundational seed data: categories, districts, departments, users, seed complaints, plans."""
    cur = conn.cursor()

    # System Settings
    settings = [
        ("escalation_threshold", "5", "Complaints against same entity/station without action before escalation"),
        ("sla_hours_high_priority", "24", "Target resolution SLA for high/critical priority complaints"),
        ("sla_hours_medium_priority", "72", "Target resolution SLA for medium priority complaints"),
        ("emergency_helpline", "112", "National Unified Emergency Response Support System"),
        ("women_safety_helpline", "1091", "24/7 Toll-free Women Safety Helpline"),
        ("platform_mode", "LIVE_DEMO", "Operational mode of the SAVE KAROO platform"),
        ("razorpay_key_id", "rzp_test_SaveKaroo2026", "Razorpay Test Key ID for Premium Subscriptions"),
    ]
    cur.executemany("INSERT OR REPLACE INTO system_settings (key, value, description) VALUES (?, ?, ?);", settings)

    # Districts
    districts = [
        ("Bengaluru Urban", "Karnataka", "South Zone", "112", "1091", "1095"),
        ("Bengaluru Rural", "Karnataka", "South Zone", "112", "1091", "1095"),
        ("Mysuru", "Karnataka", "South Zone", "112", "1091", "1095"),
        ("Mumbai City", "Maharashtra", "West Zone", "112", "1091", "1095"),
        ("New Delhi", "Delhi NCR", "North Zone", "112", "1091", "1095"),
        ("Hyderabad", "Telangana", "South Zone", "112", "1091", "1095"),
        ("Chennai", "Tamil Nadu", "South Zone", "112", "1091", "1095"),
    ]
    cur.executemany("INSERT OR IGNORE INTO districts (name, state, zone, emergency_helpline, women_helpline, traffic_helpline) VALUES (?, ?, ?, ?, ?, ?);", districts)

    # Police Departments
    departments = [
        ("Bengaluru Central Traffic & Safety", 1, "BPS-CT-01", "+91 80 2294 2222", "Infantry Road, Bengaluru"),
        ("Koramangala Law & Order Division", 1, "BPS-KM-02", "+91 80 2294 3456", "80ft Road, Koramangala, Bengaluru"),
        ("Whitefield Tech Corridor Division", 1, "BPS-WF-03", "+91 80 2294 7890", "ITPL Main Road, Whitefield, Bengaluru"),
        ("Indiranagar Transport Wing", 1, "BPS-IN-04", "+91 80 2294 1122", "100ft Road, Indiranagar, Bengaluru"),
        ("Cyber & Women Protection Cell", 1, "BPS-CW-05", "+91 80 2294 9999", "Police Commissionerate, Bengaluru"),
    ]
    cur.executemany("INSERT OR IGNORE INTO police_departments (name, district_id, station_code, contact_phone, address) VALUES (?, ?, ?, ?, ?);", departments)

    # Categories
    categories = [
        ("CAB_MISCONDUCT", "Cab/Taxi Driver Misconduct", "Verbal abuse, intimidation, or misbehaviour by app-cab drivers", "HIGH", "🚖"),
        ("BIKE_TAXI_SAFETY", "Bike Taxi Safety Violation", "Over-speeding, missing helmets, rash maneuvering on two-wheelers", "MEDIUM", "🛵"),
        ("AUTO_OVERCHARGING", "Auto Rickshaw Harassment / Refusal", "Fare refusal, broken meters, extortionate demands, or threats", "MEDIUM", "🛺"),
        ("WOMEN_HARASSMENT", "Harassment & Inappropriate Behaviour", "Stalking, lewd comments, unsafe route deviations during trip", "CRITICAL", "🚨"),
        ("RASH_DRIVING", "Rash & Negligent Driving", "Signal jumping, dangerous driving endangering passenger lives", "HIGH", "⚠️"),
        ("ROUTE_DEVIATION", "Unauthorized Route Deviation", "Taking isolated, suspicious paths against passenger request", "CRITICAL", "🗺️"),
        ("DRUNK_IMPAIRED", "Drunk / Impaired Driving", "Operating commercial passenger vehicle under influence", "CRITICAL", "⛔"),
        ("FARE_SCAM", "Fare Manipulation / Extortion", "Demanding extra cash offline, canceling ride to demand extortion", "LOW", "💸"),
        ("OTHER_SAFETY", "Other Public Transport Safety Issue", "Unlicensed vehicle, lack of safety permits, or broken doors", "MEDIUM", "🛡️"),
    ]
    cur.executemany("INSERT OR IGNORE INTO complaint_categories (code, name, description, default_priority, icon) VALUES (?, ?, ?, ?, ?);", categories)

    # Subscription Plans (Essential safety complaint filing is 100% FREE)
    plans = [
        (
            "PLAN_FREE",
            "Citizen Safety (Free)",
            0.0,
            0.0,
            json.dumps([
                "Unlimited Public Safety Complaint Registration",
                "Real-time Multi-stage Status Tracking",
                "Instant In-App Status & Action Notifications",
                "Access to Emergency Contact Directory & KAROO AI",
                "Standard Complaint History Records"
            ]),
            1
        ),
        (
            "PLAN_PREMIUM",
            "Citizen Safety Pro (Personal)",
            199.0,
            1999.0,
            json.dumps([
                "Everything in Free Safety Plan",
                "Advanced Personal Incident Analytics & Heatmap",
                "Certified PDF Police Complaint Transcripts for Court/Insurance",
                "Priority Review Escalation Badge",
                "Automated SMS & WhatsApp Updates on Actions Taken",
                "Direct Dedicated Support Desk Access"
            ]),
            1
        ),
        (
            "PLAN_ENTERPRISE",
            "Enterprise / Fleet Partner",
            4999.0,
            49990.0,
            json.dumps([
                "Organization Fleet Compliance Dashboard",
                "Multi-driver Incident Audits & Repeat Offender Tracking",
                "Automated Police Inquiry Response Workflows",
                "Dedicated Compliance Account Manager",
                "Quarterly Public Safety Audit Certification"
            ]),
            1
        ),
    ]
    cur.executemany("INSERT OR IGNORE INTO subscription_plans (plan_code, name, price_monthly_inr, price_annual_inr, features_json, is_active) VALUES (?, ?, ?, ?, ?, ?);", plans)

    # Seed Users (All 4 Roles)
    users = [
        # Super Admin
        ("Super Administrator", "superadmin@savekaroo.org", "+919880011001", hash_password("Admin@123"), "SUPER_ADMIN", "ACTIVE", "Karnataka", "Bengaluru Urban", "Bengaluru", "HQ Commissionerate"),
        # Police Administrator
        ("ACP Rajesh Kumar, IPS", "policeadmin.blr@savekaroo.org", "+919880022002", hash_password("PoliceAdmin@123"), "POLICE_ADMIN", "ACTIVE", "Karnataka", "Bengaluru Urban", "Bengaluru", "Central Traffic Headquarters"),
        # Police Officers
        ("Inspector Vikram Sharma", "officer.sharma@police.gov.in", "+919880033003", hash_password("Officer@123"), "POLICE_OFFICER", "ACTIVE", "Karnataka", "Bengaluru Urban", "Bengaluru", "Koramangala Traffic Division"),
        ("Sub-Inspector Deepa Patil", "officer.patil@police.gov.in", "+919880044004", hash_password("Officer@123"), "POLICE_OFFICER", "ACTIVE", "Karnataka", "Bengaluru Urban", "Bengaluru", "Women Safety & Cyber Cell"),
        ("Inspector Mohan Rao", "officer.rao@police.gov.in", "+919880055005", hash_password("Officer@123"), "POLICE_OFFICER", "ACTIVE", "Karnataka", "Bengaluru Urban", "Bengaluru", "Whitefield Division"),
        # Citizens
        ("Priya Sharma", "priya.sharma@gmail.com", "+919880066006", hash_password("Citizen@123"), "CITIZEN", "ACTIVE", "Karnataka", "Bengaluru Urban", "Bengaluru", "#42, 4th Cross, Indiranagar"),
        ("Rahul Verma", "rahul.verma@outlook.com", "+919880077007", hash_password("Citizen@123"), "CITIZEN", "ACTIVE", "Karnataka", "Bengaluru Urban", "Bengaluru", "#108, HSR Layout, Sector 2"),
        ("Ananya Rao", "ananya.rao@example.com", "+919880088008", hash_password("Citizen@123"), "CITIZEN", "ACTIVE", "Karnataka", "Bengaluru Urban", "Bengaluru", "#15, Malleshwaram 8th Main"),
    ]
    cur.executemany("""
    INSERT OR IGNORE INTO users (full_name, email, phone, password_hash, role, status, state, district, city, address)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, users)

    # Link Police Officers to Departments
    police_records = [
        (3, "KAR-POL-7701", 2, "Inspector", 1, 15),
        (4, "KAR-POL-8822", 5, "Sub-Inspector", 1, 15),
        (5, "KAR-POL-9933", 3, "Inspector", 1, 15),
    ]
    cur.executemany("""
    INSERT OR IGNORE INTO police_officers (user_id, badge_number, department_id, rank, is_verified, active_case_limit)
    VALUES (?, ?, ?, ?, ?, ?);
    """, police_records)

    # Add Default Free & Premium Subscriptions
    cur.execute("INSERT OR IGNORE INTO subscriptions (user_id, plan_id, billing_cycle, status) VALUES (6, 2, 'MONTHLY', 'ACTIVE');") # Priya is Premium
    cur.execute("INSERT OR IGNORE INTO subscriptions (user_id, plan_id, billing_cycle, status) VALUES (7, 1, 'LIFETIME_FREE', 'ACTIVE');") # Rahul is Free
    cur.execute("INSERT OR IGNORE INTO subscriptions (user_id, plan_id, billing_cycle, status) VALUES (8, 1, 'LIFETIME_FREE', 'ACTIVE');") # Ananya is Free

    # Add Test Payment & Invoice for Priya's Premium Plan
    cur.execute("""
    INSERT OR IGNORE INTO payments (subscription_id, user_id, amount_inr, gateway, transaction_ref, status)
    VALUES (1, 6, 199.0, 'RAZORPAY_TEST', 'pay_test_SK99283741', 'SUCCESS');
    """)
    cur.execute("""
    INSERT OR IGNORE INTO invoices (invoice_number, payment_id, user_id, amount_inr, pdf_ref)
    VALUES ('INV-2026-0001', 1, 6, 199.0, 'invoice_INV-2026-0001.pdf');
    """)

    # Seed Complaints spanning the full 10-status workflow
    seed_complaints = [
        (
            "SK-2026-000001", 6, 4, "CRITICAL", "INVESTIGATION IN PROGRESS",
            "2026-11-10 22:30:00", "Indiranagar 100ft Road towards Domlur", "Bengaluru Urban", "Karnataka",
            "Driver began making derogatory remarks, demanded additional cash payment, and refused to follow map GPS. Deviated into unlit service lane until passenger demanded to exit vehicle.",
            "KA-01-MJ-4412", "Sedan Cab", "Uber", "Ramesh Gowda", "UBR-9843-IN", 2, 0, None, None
        ),
        (
            "SK-2026-000002", 7, 2, "HIGH", "ACTION INITIATED",
            "2026-11-12 09:15:00", "Silk Board Junction towards HSR Layout", "Bengaluru Urban", "Karnataka",
            "Bike taxi rider had no pillion helmet available, drove on pedestrian footpath to bypass signal, and threatened passenger when asked to slow down.",
            "KA-05-EX-9901", "Bike Taxi", "Rapido", "Suresh Kumar", "RAP-4410", 1, 0, None, None
        ),
        (
            "SK-2026-000003", 8, 3, "MEDIUM", "VERIFIED",
            "2026-11-14 18:00:00", "Majestic Metro Station Auto Stand", "Bengaluru Urban", "Karnataka",
            "Auto rickshaw driver refused meter, demanded Rs 350 for a 3km ride, blocked luggage retrieval and abused pedestrian passengers.",
            "KA-02-B-3312", "Auto Rickshaw", "Direct Stand", "Unknown", None, None, 0, None, None
        ),
        (
            "SK-2026-000004", 6, 5, "HIGH", "RESOLVED",
            "2026-11-05 14:00:00", "Outer Ring Road near Bellandur EcoSpace", "Bengaluru Urban", "Karnataka",
            "Commercial cab driving in excess of 110 kmph in 50 kmph zone, zig-zagging between buses, narrowly missing cyclists.",
            "KA-04-AK-7788", "Hatchback Cab", "Ola Cabs", "Manoj Nayak", "OLA-8832-KA", 1, 0, None,
            "Driver summoned to Koramangala Station. Traffic challan issued under Sec 184 MV Act. Ola compliance team informed; driver account suspended for 30 days."
        ),
        (
            "SK-2026-000005", 7, 1, "HIGH", "UNDER REVIEW",
            "2026-11-15 11:20:00", "Koramangala Sony World Signal", "Bengaluru Urban", "Karnataka",
            "Cab driver demanded cash payment at journey completion despite digital payment confirmation on app. Verbally intimidated passenger and locked doors briefly.",
            "KA-51-MD-1122", "Sedan Cab", "Uber", "Basavaraj", "UBR-7721", None, 0, None, None
        ),
        (
            "SK-2026-000006", 8, 7, "CRITICAL", "ASSIGNED",
            "2026-11-15 23:45:00", "Sarjapur Road Wipro Gate", "Bengaluru Urban", "Karnataka",
            "Driver smelled strongly of alcohol, swerved continuously across median line, and slurred speech during trip.",
            "KA-03-NV-5509", "Sedan Cab", "Ola Cabs", "Pradeep V", "OLA-9901", 3, 0, None, None
        ),
        (
            "SK-2026-000007", 6, 1, "HIGH", "UNDER REVIEW",
            "2026-11-16 17:30:00", "MG Road Metro Station", "Bengaluru Urban", "Karnataka",
            "Fifth unaddressed report regarding driver behaviour and tariff harassment by same operator fleet.",
            "KA-01-MJ-4412", "Sedan Cab", "Uber", "Ramesh Gowda", "UBR-0091", None, 1,
            "Flagged by Escalation Engine: Vehicle KA-01-MJ-4412 associated with 5 separate unacted safety complaints.", None
        ),
    ]

    for c in seed_complaints:
        cur.execute("""
        INSERT OR IGNORE INTO complaints (
            id, citizen_id, category_id, priority, status, incident_datetime,
            location, district, state, description, vehicle_number, vehicle_type,
            service_provider, driver_name, trip_id, assigned_officer_id, is_escalated,
            escalation_reason, resolution_notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, c)

    # Seed Escalation Record for SK-2026-000007
    cur.execute("""
    INSERT OR IGNORE INTO escalation_records (complaint_id, reason, threshold_count, status)
    VALUES ('SK-2026-000007', 'Vehicle KA-01-MJ-4412 associated with 5 separate unacted safety complaints.', 5, 'PENDING_REVIEW');
    """)

    # Seed Evidence for SK-2026-000001
    cur.execute("""
    INSERT OR IGNORE INTO complaint_evidence (complaint_id, file_name, file_type, file_size_kb, description, storage_url)
    VALUES ('SK-2026-000001', 'trip_screenshot_route_deviation.png', 'image/png', 245, 'Screenshot showing driver off-route GPS path into dark bypass', 'evidence_sample_01.png');
    """)

    # Seed Status History for SK-2026-000001
    status_history_samples = [
        ("SK-2026-000001", None, "SUBMITTED", 6, "Complaint submitted by citizen", "Complaint successfully filed. ID: SK-2026-000001. Verification queue assigned.", "2026-11-10 22:30:00"),
        ("SK-2026-000001", "SUBMITTED", "UNDER REVIEW", 2, "Admin preliminary review", "Complaint reviewed by Police Admin. Incident matches priority criteria.", "2026-11-11 08:30:00"),
        ("SK-2026-000001", "UNDER REVIEW", "ASSIGNED", 2, "Assigned to Women Safety Cell", "Assigned to Sub-Inspector Deepa Patil (Badge KAR-POL-8822), Cyber & Women Protection Cell.", "2026-11-11 09:15:00"),
        ("SK-2026-000001", "ASSIGNED", "ACTION INITIATED", 4, "Notice issued to platform", "Official notice sent to Uber Grievance Officer seeking driver KYC & trip telemetry.", "2026-11-11 14:00:00"),
        ("SK-2026-000001", "ACTION INITIATED", "INVESTIGATION IN PROGRESS", 4, "Platform provided driver contact", "Uber response received. Driver Ramesh Gowda summon notice issued for appearance at station.", "2026-11-12 11:00:00"),
    ]
    cur.executemany("""
    INSERT OR IGNORE INTO complaint_status_history (complaint_id, old_status, new_status, changed_by_user_id, change_notes, citizen_visible_update, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?);
    """, status_history_samples)

    # Seed Official Actions for SK-2026-000001
    actions_samples = [
        ("SK-2026-000001", 2, "PLATFORM_SUMMON_NOTICE", "Notice dispatched under Section 91 CrPC to Uber India Technologies Pvt Ltd for trip route data & driver KYC.", 1, "2026-11-11 14:30:00"),
        ("SK-2026-000001", 2, "VEHICLE_DATABASE_FLAG", "Vehicle KA-01-MJ-4412 flagged in Bengaluru Automated Number Plate Recognition (ANPR) system for movement tracking.", 1, "2026-11-12 10:00:00"),
    ]
    cur.executemany("""
    INSERT OR IGNORE INTO complaint_actions (complaint_id, officer_id, action_type, description, citizen_visible, action_timestamp)
    VALUES (?, ?, ?, ?, ?, ?);
    """, actions_samples)

    # Seed Notifications
    notifications_samples = [
        (6, "Complaint Verified & Assigned", "Your complaint SK-2026-000001 has been assigned to SI Deepa Patil (Women Safety Cell).", "COMPLAINT", "SK-2026-000001", 0),
        (6, "Official Action Recorded", "Official notice issued to Uber India regarding vehicle KA-01-MJ-4412.", "ACTION", "SK-2026-000001", 0),
        (7, "Complaint Assigned to Officer", "Your complaint SK-2026-000002 has been assigned to Inspector Vikram Sharma.", "COMPLAINT", "SK-2026-000002", 0),
        (2, "Escalation Alert Flagged", "Vehicle KA-01-MJ-4412 has reached the 5-complaint threshold without resolution. Administrative review required.", "ESCALATION", "SK-2026-000007", 0),
    ]
    cur.executemany("""
    INSERT OR IGNORE INTO notifications (user_id, title, message, notification_type, link, is_read)
    VALUES (?, ?, ?, ?, ?, ?);
    """, notifications_samples)

    # Seed Audit Log
    cur.execute("""
    INSERT OR IGNORE INTO audit_logs (user_id, action, resource, ip_address, details)
    VALUES (1, 'SYSTEM_INIT', 'DATABASE', '127.0.0.1', 'SAVE KAROO relational schema initialized with seed records.');
    """)

    conn.commit()

# ==========================================
# Database Query Helpers (Robust, Typed)
# ==========================================

def get_next_complaint_id() -> str:
    """Generates unique formatted ID: SK-2026-000001"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM complaints;")
    count = cur.fetchone()[0] + 1
    conn.close()
    year = datetime.datetime.now().year
    return f"SK-{year}-{count:06d}"

def get_complaint_by_id(complaint_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT c.*, cat.name as category_name, cat.icon as category_icon,
               u.full_name as citizen_name, u.phone as citizen_phone, u.email as citizen_email,
               po.badge_number, uo.full_name as officer_name, uo.phone as officer_phone,
               pd.name as department_name
        FROM complaints c
        JOIN complaint_categories cat ON c.category_id = cat.id
        JOIN users u ON c.citizen_id = u.id
        LEFT JOIN police_officers po ON c.assigned_officer_id = po.id
        LEFT JOIN users uo ON po.user_id = uo.id
        LEFT JOIN police_departments pd ON po.department_id = pd.id
        WHERE c.id = ?;
    """, (complaint_id.strip().upper(),))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def get_complaint_history(complaint_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT h.*, u.full_name as changed_by_name, u.role as changed_by_role
        FROM complaint_status_history h
        JOIN users u ON h.changed_by_user_id = u.id
        WHERE h.complaint_id = ?
        ORDER BY h.created_at ASC;
    """, (complaint_id.strip().upper(),))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_complaint_actions(complaint_id: str, citizen_visible_only: bool = False) -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    sql = """
        SELECT a.*, u.full_name as officer_name, po.badge_number, po.rank
        FROM complaint_actions a
        JOIN police_officers po ON a.officer_id = po.id
        JOIN users u ON po.user_id = u.id
        WHERE a.complaint_id = ?
    """
    if citizen_visible_only:
        sql += " AND a.citizen_visible = 1"
    sql += " ORDER BY a.action_timestamp DESC;"
    cur.execute(sql, (complaint_id.strip().upper(),))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_all_complaint_categories() -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM complaint_categories ORDER BY id ASC;")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_all_districts() -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM districts ORDER BY name ASC;")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_user_notifications(user_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT 20;", (user_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def mark_notifications_read(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ?;", (user_id,))
    conn.commit()
    conn.close()

def log_audit(user_id: Optional[int], action: str, resource: str, details: str, ip: str = "127.0.0.1"):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO audit_logs (user_id, action, resource, ip_address, details)
        VALUES (?, ?, ?, ?, ?);
    """, (user_id, action, resource, ip, details))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db(force_reseed=True)
    print("✅ SAVE KAROO Database successfully initialized and seeded with all 19 entities.")
