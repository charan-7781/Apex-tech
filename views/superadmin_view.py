"""
views/superadmin_view.py
------------------------
Super Admin Portal for SAVE KAROO Public Safety Platform.
Features:
- Platform Governance & Overall KPI Dashboard
- Police Officer Credential Verification & Approval Engine
- Dynamic Escalation Threshold & SLA Configuration
- Subscription Plan Pricing Controls
- Immutable Security & Compliance Audit Log Viewer
"""

import streamlit as st
import save_karoo_database as db
import auth
import analytics_service as asrv
from ui_styles import render_status_badge, render_html

def render_superadmin_portal(user: dict):
    st.markdown(f"### 👑 Super Admin Platform Governance: {user['full_name']}")
    st.caption("Role: **SUPER ADMIN** • Root Platform Access • System Security, Verification & Audit Authority")

    # Platform KPI Summary
    kpi = asrv.get_platform_kpi_summary()
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        render_html(f"""
        <div class="kpi-card">
            <div class="kpi-label">Registered Citizens</div>
            <div class="kpi-num">{kpi['registered_citizens']}</div>
        </div>
        """)
    with k2:
        render_html(f"""
        <div class="kpi-card">
            <div class="kpi-label">Verified Police</div>
            <div class="kpi-num" style="color: #0284C7;">{kpi['verified_officers']}</div>
        </div>
        """)
    with k3:
        render_html(f"""
        <div class="kpi-card">
            <div class="kpi-label">Pending Police Approvals</div>
            <div class="kpi-num" style="color: {'#DC2626' if kpi['pending_officer_approvals']>0 else '#10B981'};">{kpi['pending_officer_approvals']}</div>
        </div>
        """)
    with k4:
        render_html(f"""
        <div class="kpi-card">
            <div class="kpi-label">Total Complaints</div>
            <div class="kpi-num">{kpi['total_complaints']}</div>
        </div>
        """)
    with k5:
        render_html(f"""
        <div class="kpi-card">
            <div class="kpi-label">Subscription Revenue</div>
            <div class="kpi-num" style="color: #10B981;">₹{kpi['total_subscription_revenue']:,.0f}</div>
        </div>
        """)

    st.markdown("<br>", unsafe_allow_html=True)

    tab_approval, tab_config, tab_audit = st.tabs([
        "🛡️ Police Account Approvals",
        "⚙️ Escalation Rules & System Config",
        "📜 Security Audit Trail"
    ])

    # 1. Police Account Approvals
    with tab_approval:
        st.markdown("#### 🛡️ Police Officer Credential Verification Queue")
        st.write("To prevent unauthorized impersonation of police authorities, officers must submit badge numbers and receive Super Admin verification before portal activation.")

        pending = auth.get_pending_police_officers()
        if not pending:
            st.success("✅ No police officer accounts currently pending verification.")
        else:
            for p in pending:
                render_html(f"""
                <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1rem; margin-bottom: 0.75rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong>{p['rank']} {p['full_name']}</strong> • Badge: <code>{p['badge_number']}</code><br>
                            <span style="font-size: 0.85rem; color: #64748B;">Department: {p['department_name']} • Mobile: {p['phone']} • Email: {p['email']}</span>
                        </div>
                        <span class="badge badge-under-review">PENDING APPROVAL</span>
                    </div>
                </div>
                """)

                if st.button(f"Approve & Activate Officer (Badge {p['badge_number']})", key=f"appr_{p['user_id']}", type="primary"):
                    ok, msg = auth.approve_police_officer(p["user_id"], user["id"])
                    if ok:
                        st.success(msg)
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(msg)

    # 2. System Settings & Escalation Config
    with tab_config:
        st.markdown("#### ⚙️ Configurable System Rules & Escalation Thresholds")
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM system_settings;")
        settings = {r["key"]: r["value"] for r in cur.fetchall()}
        conn.close()

        with st.form("form_sys_config"):
            c_thresh = st.number_input(
                "Repeat Offender Vehicle Threshold (Complaints before auto-escalation) *",
                min_value=2, max_value=20,
                value=int(settings.get("escalation_threshold", 5))
            )
            c_sla_high = st.number_input(
                "Target SLA for High/Critical Cases (Hours without action before escalation) *",
                min_value=6, max_value=72,
                value=int(settings.get("sla_hours_high_priority", 24))
            )
            c_helpline = st.text_input(
                "National Unified Emergency Number",
                value=settings.get("emergency_helpline", "112")
            )
            c_women_helpline = st.text_input(
                "Toll-free Women Safety Helpline",
                value=settings.get("women_safety_helpline", "1091")
            )

            submit_cfg = st.form_submit_button("💾 Save System Configuration", type="primary", use_container_width=True)
            if submit_cfg:
                conn = db.get_connection()
                cur = conn.cursor()
                cur.execute("UPDATE system_settings SET value = ?, updated_at = CURRENT_TIMESTAMP WHERE key = 'escalation_threshold';", (str(c_thresh),))
                cur.execute("UPDATE system_settings SET value = ?, updated_at = CURRENT_TIMESTAMP WHERE key = 'sla_hours_high_priority';", (str(c_sla_high),))
                cur.execute("UPDATE system_settings SET value = ?, updated_at = CURRENT_TIMESTAMP WHERE key = 'emergency_helpline';", (c_helpline,))
                cur.execute("UPDATE system_settings SET value = ?, updated_at = CURRENT_TIMESTAMP WHERE key = 'women_safety_helpline';", (c_women_helpline,))
                conn.commit()
                conn.close()
                db.log_audit(user["id"], "UPDATE_CONFIG", "SETTINGS", f"Threshold set to {c_thresh}, SLA set to {c_sla_high}h")
                st.success("System settings updated successfully!")
                st.rerun()

    # 3. Security Audit Trail
    with tab_audit:
        st.markdown("#### 📜 Immutable Security & Compliance Audit Log")
        st.caption("Records all authentication attempts, status changes, assignments, and escalations.")

        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT a.*, u.full_name, u.role
            FROM audit_logs a
            LEFT JOIN users u ON a.user_id = u.id
            ORDER BY a.timestamp DESC
            LIMIT 50;
        """)
        logs = cur.fetchall()
        conn.close()

        for l in logs:
            render_html(f"""
            <div style="background: #ffffff; border-left: 3px solid #64748B; padding: 8px 12px; margin-bottom: 6px; font-size: 0.85rem; border-top: 1px solid #f1f5f9; border-right: 1px solid #f1f5f9; border-bottom: 1px solid #f1f5f9;">
                <span style="font-weight: 700; color: #0B192C;">[{l['action']}]</span> 
                <span>{l['resource']}</span> • 
                <span style="color: #64748B;">User: {l['full_name'] or 'System'} ({l['role'] or 'N/A'}) • IP: {l['ip_address']} • {l['timestamp']}</span>
                <div style="color: #334155; margin-top: 2px;">{l['details']}</div>
            </div>
            """)
