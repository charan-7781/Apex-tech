"""
views/admin_view.py
-------------------
Police Administrator Portal for SAVE KAROO Public Safety Platform.
Features:
- Precinct Operational Overview KPIs
- Officer Assignment & Workload Rebalancing Engine
- Escalation & SLA Inaction Monitor
- Interactive Database Analytics Charts
- Official Complaint Register CSV Data Export
"""

import streamlit as st
import pandas as pd
import save_karoo_database as db
import complaint_service as cs
import escalation_engine as ee
import analytics_service as asrv
from ui_styles import render_status_badge, render_escalation_badge, render_html

def render_admin_portal(user: dict):
    st.markdown(f"### 🏢 Police Administrator Portal: {user['full_name']}")
    st.caption(f"Role: **POLICE ADMINISTRATOR** • Jurisdiction: **{user['district']}, {user['state']}** • Operational Command Center")

    # Platform KPIs
    kpi = asrv.get_platform_kpi_summary()
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        render_html(f"""
        <div class="kpi-card">
            <div class="kpi-label">Total Received</div>
            <div class="kpi-num">{kpi['total_complaints']}</div>
        </div>
        """)
    with k2:
        render_html(f"""
        <div class="kpi-card">
            <div class="kpi-label">Awaiting Assignment</div>
            <div class="kpi-num" style="color: #D97706;">{kpi['unassigned_cases']}</div>
        </div>
        """)
    with k3:
        render_html(f"""
        <div class="kpi-card">
            <div class="kpi-label">Active Inquiries</div>
            <div class="kpi-num" style="color: #0284C7;">{kpi['active_inquiries']}</div>
        </div>
        """)
    with k4:
        render_html(f"""
        <div class="kpi-card">
            <div class="kpi-label">Escalated Violations</div>
            <div class="kpi-num" style="color: #DC2626;">{kpi['escalated_cases']}</div>
        </div>
        """)
    with k5:
        render_html(f"""
        <div class="kpi-card">
            <div class="kpi-label">Resolved Rate</div>
            <div class="kpi-num" style="color: #10B981;">{kpi['resolution_rate']}%</div>
        </div>
        """)

    st.markdown("<br>", unsafe_allow_html=True)

    tab_assign, tab_escalation, tab_all, tab_analytics = st.tabs([
        "📋 Officer Assignment Queue",
        "⚡ Escalation & SLA Monitor",
        "📂 All Complaints Master Register",
        "📊 Precinct Analytics & Reports"
    ])

    # 1. Officer Assignment Queue
    with tab_assign:
        st.markdown("#### 📋 Unassigned & Pending Review Cases")
        st.write("Assign verified complaints to investigating officers based on precinct workload limits.")

        unassigned = cs.get_all_complaints(unassigned_only=True)
        if not unassigned:
            st.success("✅ All active complaints in jurisdiction have been assigned to investigating officers.")
        else:
            u_options = [f"{c['id']} - [{c['priority']}] {c['category_name']} ({c['district']})" for c in unassigned]
            sel_u_idx = st.selectbox("Select Complaint to Assign:", range(len(u_options)), format_func=lambda i: u_options[i])
            target_comp = unassigned[sel_u_idx]

            render_html(f"""
            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
                <strong>Incident ID:</strong> {target_comp['id']} • <strong>Priority:</strong> {target_comp['priority']}<br>
                <strong>Vehicle:</strong> {target_comp['vehicle_number'] or 'N/A'} • <strong>Provider:</strong> {target_comp['service_provider'] or 'Direct'}<br>
                <strong>Factual Narrative:</strong> "{target_comp['description']}"
            </div>
            """)

            # Available verified officers
            workload = asrv.get_officer_workload_summary()
            if not workload:
                st.warning("No verified police officers available for assignment.")
            else:
                officer_map = {f"{w['rank']} {w['officer_name']} (Badge: {w['badge_number']}, Active Cases: {w['active_count']})": w['id'] for w in workload}
                chosen_off_str = st.selectbox("Assign to Investigating Officer *", list(officer_map.keys()))
                chosen_off_id = officer_map[chosen_off_str]
                instructions = st.text_input("Special Investigation Instructions (Optional)", placeholder="e.g. Issue Section 91 notice to platform immediately.")

                if st.button("🚀 Confirm Assignment to Officer", type="primary", use_container_width=True):
                    ok, msg = cs.assign_officer(
                        complaint_id=target_comp['id'],
                        officer_id=chosen_off_id,
                        assigned_by_user_id=user["id"],
                        instructions=instructions
                    )
                    if ok:
                        st.success(msg)
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(msg)

    # 2. Escalation & SLA Monitor
    with tab_escalation:
        st.markdown("#### ⚡ SAVE KAROO Escalation & Accountability Monitor")
        st.caption("Automatically detects vehicles/drivers with >= 5 active unacted complaints or cases breaching the 48-hour SLA.")

        if st.button("🔍 Run Live Escalation Audit Sweep Now", use_container_width=True):
            res = ee.run_escalation_audit()
            st.toast(f"Escalation sweep complete: {res['flagged_count']} records flagged.", icon="⚡")
            st.rerun()

        recs = ee.get_escalation_records()
        if not recs:
            st.info("No active escalated violations detected.")
        else:
            for r in recs:
                render_html(f"""
                <div style="background: #ffffff; border-left: 4px solid #DC2626; border-radius: 0 8px 8px 0; padding: 1.25rem; margin-bottom: 1rem; border-top: 1px solid #fee2e2; border-right: 1px solid #fee2e2; border-bottom: 1px solid #fee2e2;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span class="id-pill" style="background: #7F1D1D; color: #FCA5A5;">ESCALATION REF #{r['id']}</span>
                        <span class="badge badge-escalated">{r['status']}</span>
                    </div>
                    <div style="margin-top: 8px; font-weight: 700; color: #991B1B;">
                        Case ID: {r['complaint_id']} • Vehicle: {r['vehicle_number'] or 'N/A'} • Provider: {r['service_provider'] or 'Direct'}
                    </div>
                    <div style="font-size: 0.88rem; color: #374151; margin-top: 4px;">
                        <strong>Escalation Reason:</strong> {r['reason']}
                    </div>
                    <div style="font-size: 0.78rem; color: #6B7280; margin-top: 4px;">
                        Flagged at: {r['flagged_at']} • Complainant: {r['citizen_name']} ({r['citizen_phone']})
                    </div>
                </div>
                """)

                c_act1, c_act2 = st.columns(2)
                with c_act1:
                    if st.button(f"Mark Escalation Resolved ({r['id']})", key=f"res_esc_{r['id']}", use_container_width=True):
                        ee.resolve_escalation(r['id'], user['id'], 'RESOLVED', 'Admin reviewed and verified enforcement action was completed.')
                        st.success("Escalation resolved.")
                        st.rerun()
                with c_act2:
                    if st.button(f"Dismiss Escalation ({r['id']})", key=f"dis_esc_{r['id']}", use_container_width=True):
                        ee.resolve_escalation(r['id'], user['id'], 'DISMISSED', 'Admin determined complaint does not warrant high escalation.')
                        st.info("Escalation dismissed.")
                        st.rerun()

    # 3. Master Register
    with tab_all:
        st.markdown("#### 📂 Master Jurisdictional Complaint Dossiers")
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            f_status = st.selectbox("Filter Status:", ["ALL", "SUBMITTED", "UNDER REVIEW", "ASSIGNED", "ACTION INITIATED", "INVESTIGATION IN PROGRESS", "RESOLVED", "CLOSED", "REJECTED"])
        with f_col2:
            f_priority = st.selectbox("Filter Priority:", ["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"])
        with f_col3:
            search_query = st.text_input("Search ID / Vehicle / Name:", placeholder="e.g. KA-01 or Ramesh")

        all_cases = cs.get_all_complaints(
            status=f_status,
            priority=f_priority,
            search=search_query
        )

        st.caption(f"Showing **{len(all_cases)}** complaints matching criteria:")
        for c in all_cases:
            s_badge = render_status_badge(c["status"])
            e_badge = render_escalation_badge() if c["is_escalated"] else ""
            render_html(f"""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px 16px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span class="id-pill">{c['id']}</span>
                    <strong>{c['category_icon']} {c['category_name']}</strong> • Vehicle: <code>{c['vehicle_number'] or 'N/A'}</code> ({c['service_provider'] or 'Independent'})
                    <div style="font-size: 0.8rem; color: #64748B; margin-top: 2px;">
                        Complainant: {c['citizen_name']} • Assigned: {c['officer_name'] or 'Unassigned'} • Date: {c['created_at']}
                    </div>
                </div>
                <div>{s_badge} {e_badge}</div>
            </div>
            """)

    # 4. Analytics & Reports
    with tab_analytics:
        st.markdown("#### 📊 Real-Time Jurisdictional Analytics")
        st.caption("Computed directly from live SQLite database records.")

        a_col1, a_col2 = st.columns(2)
        with a_col1:
            st.markdown("##### Complaints by Category")
            cat_data = asrv.get_complaints_by_category()
            df_cat = pd.DataFrame(cat_data)
            if not df_cat.empty:
                st.bar_chart(df_cat.set_index("name")["count"], color="#2563EB")

        with a_col2:
            st.markdown("##### Complaints by Commercial Provider")
            prov_data = asrv.get_complaints_by_provider()
            df_prov = pd.DataFrame(prov_data)
            if not df_prov.empty:
                st.bar_chart(df_prov.set_index("provider")["count"], color="#0891B2")

        st.divider()

        st.markdown("##### 📥 Export Official Records")
        csv_data = asrv.export_complaints_csv()
        st.download_button(
            label="📥 Download Complete Complaint Register (CSV)",
            data=csv_data,
            file_name="SAVE_KAROO_Precinct_Complaint_Register.csv",
            mime="text/csv",
            use_container_width=True
        )
