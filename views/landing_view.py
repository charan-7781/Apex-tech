"""
views/landing_view.py
---------------------
Public Homepage for SAVE KAROO Public Safety Platform.
Features:
- Emergency Dispatch Banner (112, 1091, 1095)
- Safety-First Hero with Action CTAs
- Real-time Verified Platform Statistics from SQLite
- Interactive Public Complaint Tracker with Audit Timeline
- How It Works Architecture
- Subscription Transparency (Safety Complaint Filing is 100% FREE)
- Emergency Resource Directory & Contact
"""

import streamlit as st
import datetime
import analytics_service as asrv
import save_karoo_database as db
from ui_styles import render_status_badge, render_escalation_badge, render_html

def render_landing_page():
    # Emergency Helpline Top Banner
    render_html("""
    <div class="emergency-strip">
        <div>🚨 <strong>IN IMMEDIATE DANGER?</strong> Call National Unified Emergency <strong>112</strong> or Women Helpline <strong>1091</strong> immediately.</div>
        <div style="font-size: 0.85rem; opacity: 0.95;">All-India Police Response: 24/7 Toll-Free</div>
    </div>
    """)

    # Hero Banner
    render_html("""
    <div class="hero-banner">
        <div style="display: inline-block; background: rgba(0, 141, 218, 0.25); border: 1px solid #008DDA; padding: 4px 16px; border-radius: 9999px; font-size: 0.82rem; font-weight: 700; color: #38BDF8; margin-bottom: 1.25rem; letter-spacing: 0.5px;">
            🛡️ NATIONAL CITIZEN PROTECTION & TRANSIT SAFETY PLATFORM
        </div>
        <h1 class="hero-heading">REPORT. TRACK. ESCALATE.<br>STAY SAFE.</h1>
        <p class="hero-sub">
            The independent, transparent public safety platform connecting citizens, authorized police investigators, and safety administrators. 
            Hold commercial transit operators accountable and track official police inquiries from submission to verified resolution.
        </p>
    </div>
    """)

    # Live Database Platform KPIs
    kpi = asrv.get_platform_kpi_summary()
    kcol1, kcol2, kcol3, kcol4 = st.columns(4)
    with kcol1:
        render_html(f"""
        <div class="kpi-card">
            <div class="kpi-label">Total Complaints Handled</div>
            <div class="kpi-num">{kpi['total_complaints']}</div>
            <div style="font-size: 0.75rem; color: #10B981; font-weight: 600;">Verified Database Records</div>
        </div>
        """)
    with kcol2:
        render_html(f"""
        <div class="kpi-card">
            <div class="kpi-label">Active Police Inquiries</div>
            <div class="kpi-num" style="color: #0284C7;">{kpi['active_inquiries']}</div>
            <div style="font-size: 0.75rem; color: #64748B;">Under Active Investigation</div>
        </div>
        """)
    with kcol3:
        render_html(f"""
        <div class="kpi-card">
            <div class="kpi-label">Cases Resolved</div>
            <div class="kpi-num" style="color: #10B981;">{kpi['resolved_complaints']}</div>
            <div style="font-size: 0.75rem; color: #10B981; font-weight: 600;">Action & Challans Recorded</div>
        </div>
        """)
    with kcol4:
        render_html(f"""
        <div class="kpi-card">
            <div class="kpi-label">Resolution Rate</div>
            <div class="kpi-num" style="color: #6366F1;">{kpi['resolution_rate']}%</div>
            <div style="font-size: 0.75rem; color: #64748B;">Platform Accountability Index</div>
        </div>
        """)

    st.markdown("<br>", unsafe_allow_html=True)

    # Public Complaint Tracking & Search Bar
    st.markdown("### 🔍 Track Any Complaint in Real-Time")
    st.caption("Enter your unique tracking ID (e.g. `SK-2026-000001`, `SK-2026-000004`, or `SK-2026-000007`) to view public investigation milestones.")

    t_col1, t_col2 = st.columns([3, 1])
    with t_col1:
        search_id = st.text_input("Enter Complaint ID:", placeholder="e.g. SK-2026-000001", label_visibility="collapsed")
    with t_col2:
        track_btn = st.button("🔎 Track Incident", use_container_width=True, type="primary")

    render_html("""
    <div style="font-size: 0.82rem; color: #64748B; margin-top: 4px;">
        Try sample IDs: 
        <span style="color: #2563EB; font-weight: 600;">SK-2026-000001</span> (Investigation In Progress) • 
        <span style="color: #2563EB; font-weight: 600;">SK-2026-000004</span> (Resolved with Challan) • 
        <span style="color: #DC2626; font-weight: 600;">SK-2026-000007</span> (Escalated Vehicle)
    </div>
    """)

    active_lookup_id = search_id.strip().upper() if search_id else (st.session_state.get("public_track_id"))
    if track_btn and search_id:
        st.session_state.public_track_id = search_id.strip().upper()
        active_lookup_id = search_id.strip().upper()

    if active_lookup_id:
        comp = db.get_complaint_by_id(active_lookup_id)
        if comp:
            st.markdown(f"#### 📄 Public Case File: `{comp['id']}`")
            status_badge = render_status_badge(comp["status"])
            esc_badge = render_escalation_badge() if comp["is_escalated"] else ""

            render_html(f"""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 4px 12px rgba(0,0,0,0.03);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <div>
                        <span style="font-size: 1.2rem; font-weight: 700; color: #0B192C;">{comp['category_icon']} {comp['category_name']}</span>
                        <div style="color: #64748b; font-size: 0.85rem; margin-top: 2px;">Reported on {comp['created_at']} in {comp['district']}, {comp['state']}</div>
                    </div>
                    <div>
                        {status_badge} {esc_badge}
                    </div>
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; background: #f8fafc; padding: 1rem; border-radius: 8px; font-size: 0.9rem;">
                    <div><strong>Vehicle:</strong> {comp['vehicle_number'] or 'Not Provided'}</div>
                    <div><strong>Provider:</strong> {comp['service_provider'] or 'Independent'}</div>
                    <div><strong>Location:</strong> {comp['location']}</div>
                    <div><strong>Assigned Officer:</strong> {comp['officer_name'] or 'Pending Assignment'} ({comp['badge_number'] or 'N/A'})</div>
                </div>
            </div>
            """)

            # Public Timeline
            history = db.get_complaint_history(comp['id'])
            if history:
                st.markdown("##### ⏱️ Official Action & Status Timeline")
                for h in history:
                    render_html(f"""
                    <div class="action-card">
                        <div class="action-meta">
                            <span><strong>{h['new_status']}</strong> • Updated by {h['changed_by_name']} ({h['changed_by_role']})</span>
                            <span>{h['created_at']}</span>
                        </div>
                        <div style="font-size: 0.92rem; color: #1e293b;">{h['citizen_visible_update']}</div>
                    </div>
                    """)

            if comp["resolution_notes"]:
                st.success(f"**Case Resolution Summary:** {comp['resolution_notes']}")
        else:
            st.error(f"Complaint ID '{active_lookup_id}' was not found in the public registry. Please check the tracking number.")

    st.markdown("---")

    # How SAVE KAROO Works
    st.markdown("### ⚙️ How SAVE KAROO Protects Citizens")
    hcol1, hcol2, hcol3, hcol4 = st.columns(4)
    with hcol1:
        render_html("""
        <div class="kpi-card" style="text-align: left; height: 100%;">
            <div style="font-size: 2rem;">1️⃣</div>
            <div style="font-weight: 700; font-size: 1.05rem; margin: 8px 0; color: #0B192C;">Report Incident</div>
            <p style="font-size: 0.85rem; color: #64748B; line-height: 1.5;">
                Citizen submits trip details, driver identity, vehicle number, and evidence through our multi-step secure form.
            </p>
        </div>
        """)
    with hcol2:
        render_html("""
        <div class="kpi-card" style="text-align: left; height: 100%;">
            <div style="font-size: 2rem;">2️⃣</div>
            <div style="font-weight: 700; font-size: 1.05rem; margin: 8px 0; color: #0B192C;">Police Assignment</div>
            <p style="font-size: 0.85rem; color: #64748B; line-height: 1.5;">
                Jurisdictional police officers are assigned to verify incident facts, issue platform summons, and document findings.
            </p>
        </div>
        """)
    with hcol3:
        render_html("""
        <div class="kpi-card" style="text-align: left; height: 100%;">
            <div style="font-size: 2rem;">3️⃣</div>
            <div style="font-weight: 700; font-size: 1.05rem; margin: 8px 0; color: #0B192C;">Escalation Engine</div>
            <p style="font-size: 0.85rem; color: #64748B; line-height: 1.5;">
                If 5+ complaints accumulate against the same vehicle/driver or cases stall past 48h, auto-escalation notifies Super Admins.
            </p>
        </div>
        """)
    with hcol4:
        render_html("""
        <div class="kpi-card" style="text-align: left; height: 100%;">
            <div style="font-size: 2rem;">4️⃣</div>
            <div style="font-weight: 700; font-size: 1.05rem; margin: 8px 0; color: #0B192C;">Enforcement & Closure</div>
            <p style="font-size: 0.85rem; color: #64748B; line-height: 1.5;">
                Officers record official challans, ANPR flags, or platform suspensions, providing citizens an immutable certified transcript.
            </p>
        </div>
        """)

    st.markdown("<br>", unsafe_allow_html=True)

    # Subscription Transparency Section
    st.markdown("### 💳 Subscription Plans & Safety Guarantee")
    st.info("🛡️ **CRITICAL COMMITMENT:** Filing safety complaints, tracking cases, receiving police updates, and emergency support will ALWAYS be 100% FREE for all citizens. Subscriptions apply strictly to optional personal convenience features and enterprise fleet auditing.")

    scol1, scol2, scol3 = st.columns(3)
    with scol1:
        render_html("""
        <div class="kpi-card" style="text-align: left; border: 2px solid #10B981;">
            <div class="badge badge-resolved">FREE FOREVER</div>
            <h3 style="margin: 8px 0 4px 0; color: #0B192C;">Citizen Safety</h3>
            <div style="font-size: 2rem; font-weight: 800; color: #10B981;">₹0 <span style="font-size: 0.9rem; font-weight: 500; color: #64748B;">/ month</span></div>
            <hr style="margin: 12px 0;">
            <ul style="font-size: 0.85rem; color: #334155; padding-left: 20px; line-height: 1.8;">
                <li>Unlimited safety complaint registration</li>
                <li>Real-time multi-stage status tracking</li>
                <li>In-app status & police action updates</li>
                <li>Emergency helpline directory & KAROO AI</li>
                <li>Standard incident history records</li>
            </ul>
        </div>
        """)
    with scol2:
        render_html("""
        <div class="kpi-card" style="text-align: left; border: 2px solid #2563EB;">
            <div class="badge badge-assigned">POPULAR</div>
            <h3 style="margin: 8px 0 4px 0; color: #0B192C;">Citizen Safety Pro</h3>
            <div style="font-size: 2rem; font-weight: 800; color: #2563EB;">₹199 <span style="font-size: 0.9rem; font-weight: 500; color: #64748B;">/ month</span></div>
            <hr style="margin: 12px 0;">
            <ul style="font-size: 0.85rem; color: #334155; padding-left: 20px; line-height: 1.8;">
                <li>Everything in Free Safety Plan</li>
                <li>Certified PDF Police Transcripts (for court/insurance)</li>
                <li>Personal incident heatmap & danger zones</li>
                <li>Priority review escalation badge</li>
                <li>Automated SMS & WhatsApp action alerts</li>
            </ul>
        </div>
        """)
    with scol3:
        render_html("""
        <div class="kpi-card" style="text-align: left;">
            <div class="badge badge-under-review">ENTERPRISE</div>
            <h3 style="margin: 8px 0 4px 0; color: #0B192C;">Fleet & Transport Partner</h3>
            <div style="font-size: 2rem; font-weight: 800; color: #0B192C;">₹4,999 <span style="font-size: 0.9rem; font-weight: 500; color: #64748B;">/ month</span></div>
            <hr style="margin: 12px 0;">
            <ul style="font-size: 0.85rem; color: #334155; padding-left: 20px; line-height: 1.8;">
                <li>Organization fleet compliance dashboard</li>
                <li>Driver safety audit & repeat-offender alerts</li>
                <li>Automated police notice response workflow</li>
                <li>Quarterly public safety certification badge</li>
                <li>Dedicated compliance account manager</li>
            </ul>
        </div>
        """)

    st.markdown("<br>", unsafe_allow_html=True)

    # Frequently Asked Questions (FAQ)
    st.markdown("### ❓ Frequently Asked Questions")
    with st.expander("Is SAVE KAROO officially affiliated with the Police Department?"):
        st.write("SAVE KAROO is an independent public-safety complaint management and citizen advocacy platform designed to bridge citizens, authorized police investigators, and transit administrators. It does not replace emergency 112 services.")
    with st.expander("Do I have to pay to file a complaint or track an investigation?"):
        st.write("No. Essential complaint submission, real-time tracking, police updates, and emergency directory access are completely FREE. Optional paid subscriptions provide convenience features like certified PDF court transcripts and personal analytics.")
    with st.expander("What happens when a vehicle accumulates 5 complaints?"):
        st.write("Our automated Escalation Engine continuously monitors vehicle registration numbers and drivers. When 5 or more complaints are logged against the same vehicle without closure, the system flags the entity and triggers high-priority alerts for Police Administrators to intervene.")

    # Footer
    render_html("""
    <div style="border-top: 1px solid #e2e8f0; margin-top: 3rem; padding: 2rem 0; text-align: center; color: #64748b; font-size: 0.85rem;">
        <p><strong>SAVE KAROO Public Safety Platform</strong> • REPORT. TRACK. ESCALATE. STAY SAFE.</p>
        <p>Emergency Helplines: National Unified Emergency: <strong>112</strong> | Women Safety: <strong>1091</strong> | Traffic Police: <strong>1095</strong></p>
        <p>© 2026 SAVE KAROO Platform Prototype. Built for citizen protection and transparent public safety accountability.</p>
    </div>
    """)
