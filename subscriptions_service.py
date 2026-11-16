"""
subscriptions_service.py
------------------------
Subscription Management, Razorpay Test Integration, and Invoice Generation for SAVE KAROO.
CRITICAL DESIGN RULE:
Essential safety complaint registration, tracking, status updates, and emergency contacts
are 100% FREE for all citizens. Subscriptions apply strictly to optional personal convenience features:
PDF certified transcripts, advanced incident heatmaps, automated SMS/WhatsApp alerts, and enterprise fleet dashboards.
"""

import json
import uuid
import datetime
from typing import List, Dict, Any, Optional, Tuple
from save_karoo_database import get_connection, log_audit

def get_all_subscription_plans() -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM subscription_plans WHERE is_active = 1 ORDER BY price_monthly_inr ASC;")
    rows = cur.fetchall()
    conn.close()
    plans = []
    for r in rows:
        d = dict(r)
        d["features"] = json.loads(d["features_json"])
        plans.append(d)
    return plans

def get_user_active_subscription(user_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT s.*, p.plan_code, p.name as plan_name, p.price_monthly_inr, p.price_annual_inr, p.features_json
        FROM subscriptions s
        JOIN subscription_plans p ON s.plan_id = p.id
        WHERE s.user_id = ? AND s.status = 'ACTIVE'
        ORDER BY s.created_at DESC LIMIT 1;
    """, (user_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        d = dict(row)
        d["features"] = json.loads(d["features_json"])
        return d
    return None

def process_mock_payment_and_subscribe(
    user_id: int,
    plan_id: int,
    billing_cycle: str = "MONTHLY",
    card_mock_last4: str = "4242"
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Simulates Razorpay Test Mode Checkout without storing sensitive card credentials.
    Generates a realistic transaction ref, updates user subscription, and issues a formal tax invoice.
    """
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT * FROM subscription_plans WHERE id = ?;", (plan_id,))
        plan = cur.fetchone()
        if not plan:
            return False, "Selected subscription plan not found.", None

        amount = plan["price_monthly_inr"] if billing_cycle == "MONTHLY" else plan["price_annual_inr"]
        txn_ref = f"pay_test_{uuid.uuid4().hex[:14]}"
        inv_num = f"INV-2026-{uuid.uuid4().hex[:6].upper()}"

        # 1. Expire/Deactivate prior subscription
        cur.execute("UPDATE subscriptions SET status = 'EXPIRED' WHERE user_id = ? AND status = 'ACTIVE';", (user_id,))

        # 2. Insert new subscription
        now = datetime.datetime.now()
        expires = now + datetime.timedelta(days=30 if billing_cycle == "MONTHLY" else 365)
        cur.execute("""
            INSERT INTO subscriptions (user_id, plan_id, billing_cycle, status, starts_at, expires_at)
            VALUES (?, ?, ?, 'ACTIVE', CURRENT_TIMESTAMP, ?);
        """, (user_id, plan_id, billing_cycle, expires.strftime("%Y-%m-%d %H:%M:%S")))
        sub_id = cur.lastrowid

        # 3. Insert payment record
        cur.execute("""
            INSERT INTO payments (subscription_id, user_id, amount_inr, gateway, transaction_ref, status)
            VALUES (?, ?, ?, 'RAZORPAY_TEST', ?, 'SUCCESS');
        """, (sub_id, user_id, amount, txn_ref))
        pay_id = cur.lastrowid

        # 4. Generate invoice
        cur.execute("""
            INSERT INTO invoices (invoice_number, payment_id, user_id, amount_inr, pdf_ref)
            VALUES (?, ?, ?, ?, ?);
        """, (inv_num, pay_id, user_id, amount, f"{inv_num}.pdf"))

        # 5. Send Notification
        cur.execute("""
            INSERT INTO notifications (user_id, title, message, notification_type)
            VALUES (?, 'Subscription Activated: ' || ?, 
                    'Your subscription to ' || ? || ' (₹' || ? || ') is now active. Receipt ' || ? || ' is available.', 'BILLING');
        """, (user_id, plan["name"], plan["name"], amount, inv_num))

        conn.commit()
        log_audit(user_id, "SUBSCRIPTION_UPGRADE", "SUBSCRIPTIONS", f"User subscribed to {plan['name']} (Txn: {txn_ref})")

        return True, "Subscription successfully activated via Razorpay Test Mode!", {
            "transaction_ref": txn_ref,
            "invoice_number": inv_num,
            "amount_inr": amount,
            "plan_name": plan["name"],
            "expires_at": expires.strftime("%d %b %Y")
        }

    except Exception as e:
        conn.rollback()
        return False, f"Payment simulation failed: {str(e)}", None
    finally:
        conn.close()

def cancel_subscription(user_id: int) -> Tuple[bool, str]:
    """Cancels paid subscription and rolls citizen back to Lifetime Free Safety Plan."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE subscriptions SET status = 'CANCELLED' WHERE user_id = ? AND status = 'ACTIVE';", (user_id,))
        # Re-assign Free Plan
        cur.execute("""
            INSERT INTO subscriptions (user_id, plan_id, billing_cycle, status)
            VALUES (?, 1, 'LIFETIME_FREE', 'ACTIVE');
        """, (user_id,))

        cur.execute("""
            INSERT INTO notifications (user_id, title, message, notification_type)
            VALUES (?, 'Subscription Reverted to Free', 'Your plan has been switched back to the Citizen Safety Free Plan. Essential complaint filing and tracking remain completely unaffected and free.', 'BILLING');
        """, (user_id,))

        conn.commit()
        log_audit(user_id, "SUBSCRIPTION_CANCEL", "SUBSCRIPTIONS", f"User {user_id} cancelled paid subscription.")
        return True, "Paid subscription cancelled. Reverted safely to Free Citizen Plan."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def get_user_invoices(user_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT i.*, p.transaction_ref, p.gateway
        FROM invoices i
        JOIN payments p ON i.payment_id = p.id
        WHERE i.user_id = ?
        ORDER BY i.created_at DESC;
    """, (user_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

