"""
views/officer_view.py
---------------------
Police Officer Portal for SAVE KAROO Public Safety Platform.
Features:
- Assigned Workload Dashboard with Priority Ranking
- Comprehensive Case File Inspector with Evidence Viewer
- Official Enforcement Action Logger (Challans, ANPR Flags, Summons)
- Case Status Transition Manager with Citizen-Visible Update Feeds
- Case Outcome Summary & Closure Logger
"""

import streamlit as st
import datetime
import save_karoo_database as db
import complaint_service as cs
from ui_styles import render_status_badge, render_escalation_badge, render_html

def render_officer_portal(user: dict):
    # Retrieve officer profile
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT po.*, pd.name as department_name, pd.station_code
        FROM police_officers po
        JOIN police_departments pd ON po.department_id = pd.id
        WHERE po.user_id = ?;
    """, (user["id"],))
    officer = cur.fetchone()
    conn.close()

    if not officer:
        st.error("Police Officer credentials profile could not be loaded.")
        return

    st.markdown(f"### 👮 Police Officer Portal: {user['full_name']}")
    st.caption(f"Rank: **{officer['rank']}** • Badge: `{officer['badge_number']}` • Station: **{officer['department_name']}** (`{officer['station_code']}`)")

    # Retrieve assigned cases
    assigned_cases = cs.get_officer_complaints(officer["id"])
    total_assigned = len(assigned_cases)
    critical_cases = sum(1 for c in assigned_cases if c["priority"] in ("CRITICAL", "HIGH"))
    active_cases = sum(1 for c in assigned_cases if c["status"] not in ("RESOLVED", "CLOSED", "REJECTED"))
    resolved_cases = sum(1 for c in assigned_cases if c["status"] in ("RESOLVED", "CLOSED"))

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_html(f"""
        <div class="kpi-card">
            <div class="kpi-label">Total Assigned Cases</div>
            <div class="kpi-num">{total_assigned}</div>
        </div>
        """)
    with k2:
        render_html(f"""
        <div class="kpi-card">
            <div class="kpi-label">Critical / High Priority</div>
            <div class="kpi-num" style="color: #DC2626;">{critical_cases}</div>
        </div>
        """)
    with k3:
        render_html(f"""
        <div class="kpi-card">
            <div class="kpi-label">Active Investigations</div>
            <div class="kpi-num" style="color: #0284C7;">{active_cases}</div>
        </div>
        """)
    with k4:
        render_html(f"""
        <div class="kpi-card">
            <div class="kpi-label">Cases Resolved</div>
            <div class="kpi-num" style="color: #10B981;">{resolved_cases}</div>
        </div>
        """)

    st.markdown("<br>", unsafe_allow_html=True)

    if not assigned_cases:
        st.info("You currently have no complaints assigned to your badge queue. Check with your Police Administrator.")
        return

    # Case Selection
    case_options = [f"{c['id']} - {c['priority']} - {c['category_name']} ({c['status']})" for c in assigned_cases]
    selected_idx = st.selectbox("Select Active Case to Investigate:", range(len(case_options)), format_func=lambda i: case_options[i])
    comp_brief = assigned_cases[selected_idx]
    comp = db.get_complaint_by_id(comp_brief["id"])

    if not comp:
        return

    status_badge = render_status_badge(comp["status"])
    esc_badge = render_escalation_badge() if comp["is_escalated"] else ""

    render_html(f"""
    <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1.5rem; margin: 1rem 0; box-shadow: 0 4px 12px rgba(0,0,0,0.03);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
            <div>
                <span class="id-pill">{comp['id']}</span>
                <span style="font-size: 1.15rem; font-weight: 700; margin-left: 10px;">{comp['category_icon']} {comp['category_name']}</span>
                <span style="margin-left: 10px; font-weight: 700; color: {'#DC2626' if comp['priority']=='CRITICAL' else '#D97706'};">[{comp['priority']} PRIORITY]</span>
            </div>
            <div>{status_badge} {esc_badge}</div>
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; background: #f8fafc; padding: 1rem; border-radius: 8px; font-size: 0.88rem;">
            <div><strong>Complainant:</strong> {comp['citizen_name']} ({comp['citizen_phone']})</div>
            <div><strong>Vehicle Number:</strong> {comp['vehicle_number'] or 'Not Provided'}</div>
            <div><strong>Service Provider:</strong> {comp['service_provider'] or 'Independent'}</div>
            <div><strong>Driver Name:</strong> {comp['driver_name'] or 'Unknown'}</div>
            <div><strong>Trip / Booking ID:</strong> {comp['trip_id'] or 'N/A'}</div>
            <div><strong>Incident Datetime:</strong> {comp['incident_datetime']}</div>
        </div>
        <div style="margin-top: 1rem; font-size: 0.95rem; color: #1e293b;">
            <strong>Incident Factual Narrative:</strong><br>
            <div style="background: #ffffff; border-left: 3px solid #2563EB; padding: 8px 12px; margin-top: 6px; font-style: italic;">
                "{comp['description']}"
            </div>
        </div>
    </div>
    """)

    # Tabs for Officer Investigation Actions
    tab_actions, tab_status, tab_evidence, tab_history = st.tabs([
        "⚡ Record Official Action",
        "🔄 Update Investigation Status",
        "📎 Evidence Documents",
        "⏱️ Full Case Audit Log"
    ])

    # 1. Action Logger
    with tab_actions:
        st.markdown("##### 📝 Record Legal & Enforcement Action")
        st.caption("All actions recorded here become part of the official legal dossier.")

        with st.form(f"form_action_{comp['id']}"):
            action_type = st.selectbox("Action Category *", [
                "NOTICE_91_CRPC (Platform Data Summon)",
                "ANPR_DATABASE_FLAG (Vehicle Surveillance Flag)",
                "DRIVER_POLICE_SUMMON (Summon for In-Person Interrogation)",
                "TRAFFIC_CHALLAN_ISSUED (Motor Vehicles Act Penalty)",
                "SPOT_INSPECTION_CONDUCTED (On-Ground Inspection)",
                "PLATFORM_SUSPENSION_ORDER (Order to Suspend Driver Account)",
                "WARNING_COUNSELING_RECORDED (Formal Warning Issued)",
                "CITIZEN_INTERVIEW_HELD (Complainant Statement Recorded)"
            ])
            action_desc = st.text_area(
                "Action Details & Legal Section Reference *",
                placeholder="e.g. Dispatched official notice to Uber Grievance Officer under Section 91 CrPC requesting GPS telematics and driver Ramesh Gowda's KYC dossier.",
                height=100
            )
            citizen_vis = st.checkbox("Make action visible to complainant on their live tracking timeline", value=True)
            submit_act = st.form_submit_button("💾 Save Action to Official Case Log", type="primary", use_container_width=True)

            if submit_act:
                if not action_desc or len(action_desc.strip()) < 10:
                    st.error("Please provide detailed action particulars (at least 10 characters).")
                else:
                    ok, msg = cs.record_official_action(
                        complaint_id=comp['id'],
                        officer_id=officer["id"],
                        action_type=action_type.split(" ")[0],
                        description=action_desc.strip(),
                        citizen_visible=citizen_vis
                    )
                    if ok:
                        st.success(f"Action successfully recorded! {msg}")
                        st.rerun()
                    else:
                        st.error(msg)

    # 2. Status Progression
    with tab_status:
        st.markdown("##### 🔄 Progress Investigation Status")
        current_status = comp["status"]
        allowed_statuses = [
            "ACTION INITIATED", "INVESTIGATION IN PROGRESS",
            "AWAITING CITIZEN RESPONSE", "RESOLVED", "CLOSED", "REJECTED"
        ]

        with st.form(f"form_status_{comp['id']}"):
            new_status = st.selectbox("Advance Case Status to *", allowed_statuses, index=allowed_statuses.index(current_status) if current_status in allowed_statuses else 0)
            citizen_update = st.text_input(
                "Citizen-Visible Update Notification *",
                value=f"Investigating officer updated status to {new_status}."
            )
            internal_notes = st.text_area("Internal Police Investigation Notes (Confidential)", height=80)
            
            res_notes = ""
            if new_status in ("RESOLVED", "CLOSED"):
                res_notes = st.text_area("Final Outcome & Resolution Summary *", placeholder="e.g. Driver appeared at station. Traffic challan issued under Sec 184 MV Act. Ola compliance confirmed 30-day driver suspension. Complainant satisfied.")

            submit_status = st.form_submit_button("Update Status & Notify Citizen", type="primary", use_container_width=True)
            if submit_status:
                if new_status in ("RESOLVED", "CLOSED") and not res_notes:
                    st.error("Please provide a final outcome summary when marking a case resolved.")
                else:
                    ok, msg = cs.update_complaint_status(
                        complaint_id=comp['id'],
                        new_status=new_status,
                        changed_by_user_id=user["id"],
                        change_notes=internal_notes or f"Status changed to {new_status}",
                        citizen_visible_update=citizen_update,
                        resolution_notes=res_notes if res_notes else None
                    )
                    if ok:
                        st.success("Case status successfully updated!")
                        st.rerun()
                    else:
                        st.error(msg)

    # 3. Evidence
    with tab_evidence:
        st.markdown("##### 📎 Attached Incident Evidence")
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM complaint_evidence WHERE complaint_id = ?;", (comp['id'],))
        evidence_items = cur.fetchall()
        conn.close()

        if not evidence_items:
            st.info("No files were attached by complainant.")
        else:
            for ev in evidence_items:
                render_html(f"""
                <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; margin-bottom: 8px;">
                    <strong>File:</strong> {ev['file_name']} ({ev['file_type']} - {ev['file_size_kb']} KB)<br>
                    <span style="color: #64748B;">{ev['description']}</span>
                </div>
                """)

    # 4. History
    with tab_history:
        st.markdown("##### ⏱️ Full Audit Trail")
        history = db.get_complaint_history(comp['id'])
        for h in history:
            render_html(f"""
            <div class="action-card">
                <div class="action-meta">
                    <span><strong>{h['new_status']}</strong> (Previous: {h['old_status'] or 'None'})</span>
                    <span>{h['created_at']}</span>
                </div>
                <div>{h['citizen_visible_update']}</div>
                <div style="font-size: 0.75rem; color: #64748B; margin-top: 4px;">Internal Note: {h['change_notes']}</div>
            </div>
            """)
