"""
test_save_karoo.py
------------------
Comprehensive Automated Test Suite for the SAVE KAROO Public Safety Platform.
Validates:
1. Database integrity & relational constraints.
2. User authentication & role enforcement.
3. Complaint registration with unique ID generation.
4. Complaint status transitions & audit timeline.
5. Officer assignment & official action recording.
6. Automated escalation engine (repeat-offender threshold & SLA breach).
7. Subscriptions, Razorpay test checkout & free-safety rule.
8. Analytics KPIs & report generation.
"""

import unittest
import os
import sqlite3
import save_karoo_database as db
import auth
import complaint_service as cs
import escalation_engine as ee
import subscriptions_service as ss
import analytics_service as asrv
import karoo_ai

class TestSaveKarooPlatform(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Initialize fresh database with seed records
        db.init_db(force_reseed=True)

    def test_01_database_tables_exist(self):
        """Verifies that all 19 relational entities exist in SQLite."""
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cur.fetchall()]
        conn.close()

        required_tables = [
            "users", "districts", "police_departments", "police_officers",
            "complaint_categories", "complaints", "complaint_evidence",
            "complaint_assignments", "complaint_status_history", "complaint_actions",
            "escalation_records", "notifications", "subscription_plans",
            "subscriptions", "payments", "invoices", "support_tickets",
            "audit_logs", "system_settings"
        ]
        for tbl in required_tables:
            self.assertIn(tbl, tables, f"Missing required table: {tbl}")

    def test_02_citizen_registration_and_login(self):
        """Tests citizen signup, password hashing, and authentication."""
        email = "test.citizen.alpha@savekaroo.org"
        phone = "+919988776655"
        pw = "SecureTest@2026"

        success, msg, uid = auth.register_citizen(
            full_name="Alpha Citizen",
            email=email,
            phone=phone,
            password=pw
        )
        self.assertTrue(success, f"Registration failed: {msg}")
        self.assertIsNotNone(uid)

        # Authenticate
        user, auth_msg = auth.authenticate_user(email, pw)
        self.assertIsNotNone(user, f"Auth failed: {auth_msg}")
        self.assertEqual(user["role"], "CITIZEN")
        self.assertEqual(user["status"], "ACTIVE")

        # Verify free plan assignment
        sub = ss.get_user_active_subscription(uid)
        self.assertIsNotNone(sub)
        self.assertEqual(sub["plan_code"], "PLAN_FREE")

    def test_03_police_officer_approval_workflow(self):
        """Tests officer registration requiring Admin approval."""
        email = "test.officer.beta@police.gov.in"
        badge = "KAR-TEST-9988"
        success, msg = auth.register_police_officer_request(
            full_name="Officer Beta",
            email=email,
            phone="+919876543210",
            password="OfficerPassword123",
            badge_number=badge,
            department_id=1,
            rank="Sub-Inspector"
        )
        self.assertTrue(success)

        # Unapproved login attempt should fail
        user, auth_msg = auth.authenticate_user(email, "OfficerPassword123")
        self.assertIsNone(user)
        self.assertIn("pending verification", auth_msg.lower())

        # Admin approves
        pending = auth.get_pending_police_officers()
        target = next((p for p in pending if p["badge_number"] == badge), None)
        self.assertIsNotNone(target)

        appr_ok, appr_msg = auth.approve_police_officer(target["user_id"], admin_user_id=1)
        self.assertTrue(appr_ok)

        # Approved login should now succeed
        user_ok, _ = auth.authenticate_user(email, "OfficerPassword123")
        self.assertIsNotNone(user_ok)
        self.assertEqual(user_ok["status"], "ACTIVE")

    def test_04_complaint_registration_and_tracking(self):
        """Tests full complaint creation with SK-2026-XXXXXX ID generation."""
        success, msg, cid = cs.submit_complaint(
            citizen_id=6, # Priya
            category_id=1,
            priority="HIGH",
            incident_datetime="2026-11-16 19:00:00",
            location="Koramangala 5th Block",
            district="Bengaluru Urban",
            state="Karnataka",
            description="Driver aggressively demanded Rs 200 extra cash beyond app booking and threatened to seize luggage.",
            vehicle_number="KA-03-AB-1234",
            vehicle_type="Hatchback Cab",
            service_provider="Uber",
            driver_name="Harish Kumar",
            trip_id="TRIP-TEST-881"
        )
        self.assertTrue(success)
        self.assertTrue(cid.startswith("SK-2026-"))

        # Verify tracking
        comp = db.get_complaint_by_id(cid)
        self.assertIsNotNone(comp)
        self.assertEqual(comp["status"], "SUBMITTED")
        self.assertEqual(comp["vehicle_number"], "KA-03-AB-1234")

        # Verify history record
        hist = db.get_complaint_history(cid)
        self.assertGreaterEqual(len(hist), 1)
        self.assertEqual(hist[0]["new_status"], "SUBMITTED")

    def test_05_officer_assignment_and_official_action(self):
        """Tests police assignment and official action recording."""
        cid = "SK-2026-000003" # seeded complaint
        assign_ok, assign_msg = cs.assign_officer(
            complaint_id=cid,
            officer_id=1, # Inspector Sharma
            assigned_by_user_id=2, # Police Admin
            instructions="Summon auto driver and verify meter calibration."
        )
        self.assertTrue(assign_ok)

        comp = db.get_complaint_by_id(cid)
        self.assertEqual(comp["status"], "ASSIGNED")

        # Officer logs action
        act_ok, act_msg = cs.record_official_action(
            complaint_id=cid,
            officer_id=1,
            action_type="DRIVER_SUMMON_NOTICE",
            description="Notice issued to Majestic Auto Stand president to present driver for inquiry.",
            citizen_visible=True
        )
        self.assertTrue(act_ok)

        # Status automatically advances to ACTION INITIATED
        comp_after = db.get_complaint_by_id(cid)
        self.assertEqual(comp_after["status"], "ACTION INITIATED")

        # Actions are visible
        actions = db.get_complaint_actions(cid, citizen_visible_only=True)
        self.assertGreaterEqual(len(actions), 1)

    def test_06_escalation_engine(self):
        """Tests escalation sweep for repeat violations and unacted cases."""
        res = ee.run_escalation_audit()
        self.assertIsInstance(res, dict)
        self.assertIn("flagged_count", res)

        # Check records
        recs = ee.get_escalation_records()
        self.assertIsInstance(recs, list)
        self.assertGreaterEqual(len(recs), 1)

    def test_07_subscription_and_razorpay_checkout(self):
        """Tests Razorpay test checkout, plan activation, invoice generation, and free safety guarantee."""
        user_id = 7 # Rahul Verma
        plans = ss.get_all_subscription_plans()
        premium_plan = next(p for p in plans if p["plan_code"] == "PLAN_PREMIUM")

        ok, msg, data = ss.process_mock_payment_and_subscribe(
            user_id=user_id,
            plan_id=premium_plan["id"],
            billing_cycle="MONTHLY"
        )
        self.assertTrue(ok)
        self.assertIn("pay_test_", data["transaction_ref"])

        # Check active sub
        active_sub = ss.get_user_active_subscription(user_id)
        self.assertEqual(active_sub["plan_code"], "PLAN_PREMIUM")

        # Invoices generated
        invoices = ss.get_user_invoices(user_id)
        self.assertGreaterEqual(len(invoices), 1)
        self.assertEqual(invoices[0]["amount_inr"], 199.0)

        # Cancellation rolls back to Free
        c_ok, c_msg = ss.cancel_subscription(user_id)
        self.assertTrue(c_ok)
        reverted_sub = ss.get_user_active_subscription(user_id)
        self.assertEqual(reverted_sub["plan_code"], "PLAN_FREE")

    def test_08_analytics_and_transcripts(self):
        """Tests platform KPI calculations and report generation."""
        kpis = asrv.get_platform_kpi_summary()
        self.assertGreater(kpis["total_complaints"], 0)
        self.assertGreater(kpis["registered_citizens"], 0)

        csv_text = asrv.export_complaints_csv()
        self.assertIn("Complaint ID", csv_text)
        self.assertIn("SK-2026-", csv_text)

        transcript = asrv.generate_citizen_complaint_transcript("SK-2026-000001")
        self.assertIn("SAVE KAROO", transcript)
        self.assertIn("SK-2026-000001", transcript)

    def test_09_karoo_ai_safety_guardrails(self):
        """Verifies KAROO AI emergency detection and safety responses."""
        resp = karoo_ai.get_karoo_ai_response("Help me! I am being attacked right now with a knife!")
        self.assertIn("112", resp)
        self.assertIn("EMERGENCY", resp)

        general_resp = karoo_ai.get_karoo_ai_response("How do I track my complaint?")
        self.assertIn("SK-2026-", general_resp)

if __name__ == "__main__":
    unittest.main()

