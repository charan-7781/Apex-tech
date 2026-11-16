"""
views/citizen_view.py
---------------------
Citizen Portal for SAVE KAROO Public Safety Platform.
Features:
- Live Complaint Overview Cards
- 6-Step Multi-Stage Guided Complaint Registration Wizard
- Real-Time Complaint Tracking with 10-Stage Stepper Timeline
- Official Actions Log & Downloadable Certified Complaint Transcripts
- In-App Notifications Feed
- Subscription Management with Razorpay Test Mode Simulation
"""

import streamlit as st
import datetime
import save_karoo_database as db
import complaint_service as cs
import subscriptions_service as ss
import analytics_service as asrv
from ui_styles import render_status_badge, render_escalation_badge, render_html

def render_timeline_stepper(status: str):
    """Visual horizontal stepper for the 10-stage complaint lifecycle."""
    stages = [
        "SUBMITTED", "UNDER REVIEW", "VERIFIED", "ASSIGNED",
        "ACTION INITIATED", "INVESTIGATION IN PROGRESS", "RESOLVED"
    ]
    
    current_idx = 0
    if status == "SUBMITTED":
        current_idx = 0
    elif status == "UNDER REVIEW":
        current_idx = 1
    elif status == "VERIFIED":
        current_idx = 2
    elif status == "ASSIGNED":
        current_idx = 3
    elif status == "ACTION INITIATED":
        current_idx = 4
    elif status in ("INVESTIGATION IN PROGRESS", "AWAITING CITIZEN RESPONSE"):
        current_idx = 5
    elif status in ("RESOLVED", "CLOSED"):
        current_idx = 6
    elif status == "REJECTED":
        st.error("🚫 This complaint was reviewed and closed as Rejected / Non-Jurisdictional.")
        return

    cols = st.columns(len(stages))
    for i, s in enumerate(stages):
        with cols[i]:
            if i < current_idx:
                render_html(f"<div class='step-circle step-completed'>✓</div><div style='text-align: center; font-size: 0.72rem; font-weight: 700; color: #10B981;'>{s}</div>")
            elif i == current_idx:
                render_html(f"<div class='step-circle step-active'>●</div><div style='text-align: center; font-size: 0.72rem; font-weight: 800; color: #2563EB;'>{s}</div>")
            else:
                render_html(f"<div class='step-circle step-upcoming'>○</div><div style='text-align: center; font-size: 0.72rem; color: #94A3B8;'>{s}</div>")
    st.progress((current_idx + 1) / len(stages))

def render_citizen_portal(user: dict):
    st.markdown(f"### 👋 Namaste, {user['full_name']}")
    st.caption(f"Citizen Public Safety Portal • Registered Mobile: {user['phone']} • District: {user['district']}")

    # Overview Metrics
    complaints = cs.get_citizen_complaints(user["id"])
    total_filed = len(complaints)
    under_review = sum(1 for c in complaints if c["status"] in ("SUBMITTED", "UNDER REVIEW", "VERIFIED"))
    active_inquiries = sum(1 for c in complaints if c["status"] in ("ASSIGNED", "ACTION INITIATED", "INVESTIGATION IN PROGRESS"))
    resolved = sum(1 for c in complaints if c["status"] in ("RESOLVED", "CLOSED"))

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        render_html(f"""
        <div class="kpi-card">
            <div class="kpi-label">Total Complaints Filed</div>
            <div class="kpi-num">{total_filed}</div>
        </div>
        """)
    with m2:
        render_html(f"""
        <div class="kpi-card">
            <div class="kpi-label">In Verification Queue</div>
            <div class="kpi-num" style="color: #D97706;">{under_review}</div>
        </div>
        """)
    with m3:
        render_html(f"""
        <div class="kpi-card">
            <div class="kpi-label">Police Inquiries Active</div>
            <div class="kpi-num" style="color: #0284C7;">{active_inquiries}</div>
        </div>
        """)
    with m4:
        render_html(f"""
        <div class="kpi-card">
            <div class="kpi-label">Resolved with Action</div>
            <div class="kpi-num" style="color: #10B981;">{resolved}</div>
        </div>
        """)

    st.markdown("<br>", unsafe_allow_html=True)

    tab_report, tab_track, tab_notif, tab_subs, tab_help = st.tabs([
        "📝 File New Complaint",
        "📦 My Complaints & Live Tracking",
        "🔔 Notifications",
        "💳 Safety Subscriptions",
        "🛡️ Emergency Resources"
    ])

    # ==========================================
    # TAB 1: 6-STEP COMPLAINT REGISTRATION WIZARD
    # ==========================================
    with tab_report:
        st.markdown("#### 🚨 Report Public Safety Incident")
        st.write("Complete the multi-step verification form below. Once filed, your complaint receives an immutable ID and enters the police dispatch queue.")

        with st.form("form_citizen_complaint"):
            # Step 1: Category & Priority
            st.markdown("##### Step 1: Incident Category & Urgency")
            categories = db.get_all_complaint_categories()
            cat_options = {f"{c['icon']} {c['name']}": c['id'] for c in categories}
            selected_cat_str = st.selectbox("Select Incident Category *", list(cat_options.keys()))
            selected_cat_id = cat_options[selected_cat_str]

            p_col1, p_col2 = st.columns(2)
            with p_col1:
                priority = st.selectbox("Urgency Priority *", ["LOW", "MEDIUM", "HIGH", "CRITICAL"], index=1)
            with p_col2:
                incident_date = st.date_input("Date of Incident *", value=datetime.date.today())
                incident_time = st.time_input("Approximate Time *", value=datetime.datetime.now().time())

            st.divider()

            # Step 2: Vehicle & Transit Details
            st.markdown("##### Step 2: Commercial Vehicle & Driver Details")
            v_col1, v_col2, v_col3 = st.columns(3)
            with v_col1:
                vehicle_no = st.text_input("Vehicle Registration No. (e.g. KA-01-MJ-4412)", placeholder="KA-01-AB-1234").strip()
            with v_col2:
                vehicle_type = st.selectbox("Vehicle Type", ["Sedan Cab", "Hatchback Cab", "Auto Rickshaw", "Bike Taxi", "Bus", "Private Car", "Other"])
            with v_col3:
                provider = st.selectbox("Service Provider / Platform", ["Uber", "Ola Cabs", "Rapido", "Direct Auto Stand", "BMTC / State Bus", "Private Taxi", "Other"])

            v_col4, v_col5 = st.columns(2)
            with v_col4:
                driver_name = st.text_input("Driver Name (if known)", placeholder="e.g. Ramesh Gowda")
            with v_col5:
                trip_id = st.text_input("Trip ID / Booking Ref (if applicable)", placeholder="e.g. UBR-984210")

            st.divider()

            # Step 3: Location & Incident Narrative
            st.markdown("##### Step 3: Incident Location & Factual Narrative")
            l_col1, l_col2, l_col3 = st.columns(3)
            with l_col1:
                location = st.text_input("Exact Location / Route Taken *", placeholder="e.g. Indiranagar 100ft road towards Domlur flyover")
            with l_col2:
                districts = db.get_all_districts()
                dist_names = [d["name"] for d in districts]
                district = st.selectbox("Jurisdiction District *", dist_names, index=dist_names.index(user["district"]) if user["district"] in dist_names else 0)
            with l_col3:
                state = st.text_input("State", value="Karnataka", disabled=True)

            description = st.text_area(
                "Detailed Incident Description * (Minimum 15 characters)",
                placeholder="Describe factually what occurred: language used, unauthorized route deviation, overcharging threats, reckless driving, or harassment. Avoid exaggeration.",
                height=130
            )

            st.divider()

            # Step 4: Evidence Documentation
            st.markdown("##### Step 4: Supporting Evidence (Screenshots / Receipts)")
            evidence_desc = st.text_input("Description of Attached Evidence (Optional)", placeholder="e.g. Trip route GPS screenshot showing unauthorized deviation")
            uploaded_file = st.file_uploader("Upload Evidence Image or Document (PNG, JPG, PDF up to 10MB)", type=["png", "jpg", "jpeg", "pdf"])

            st.divider()

            # Step 5 & 6: Complainant Details & Consent
            st.markdown("##### Step 5: Complainant Verification & Submission")
            st.info(f"Filing as **{user['full_name']}** (Mobile: `{user['phone']}`, Email: `{user['email']}`). Your personal contact details are protected under platform privacy rules and never exposed to the accused driver.")
            consent = st.checkbox("I declare that the information provided above is true and factual to the best of my knowledge.", value=True)

            submitted = st.form_submit_button("🚀 Submit Official Safety Complaint", use_container_width=True, type="primary")

            if submitted:
                if not consent:
                    st.error("Please confirm the factual declaration before submitting.")
                elif not location or len(location.strip()) < 3:
                    st.error("Please provide the exact incident location.")
                elif not description or len(description.strip()) < 15:
                    st.error("Please provide a detailed factual description (at least 15 characters).")
                else:
                    inc_datetime_str = f"{incident_date} {incident_time.strftime('%H:%M:%S')}"
                    evidence_list = []
                    if uploaded_file:
                        evidence_list.append({
                            "name": uploaded_file.name,
                            "type": uploaded_file.type,
                            "size": round(uploaded_file.size / 1024),
                            "desc": evidence_desc or "User uploaded evidence",
                            "url": f"evidence_{uploaded_file.name}"
                        })

                    ok, msg, cid = cs.submit_complaint(
                        citizen_id=user["id"],
                        category_id=selected_cat_id,
                        priority=priority,
                        incident_datetime=inc_datetime_str,
                        location=location,
                        district=district,
                        state="Karnataka",
                        description=description,
                        vehicle_number=vehicle_no if vehicle_no else None,
                        vehicle_type=vehicle_type,
                        service_provider=provider,
                        driver_name=driver_name if driver_name else None,
                        trip_id=trip_id if trip_id else None,
                        evidence_files=evidence_list
                    )
                    if ok:
                        st.success(f"🎉 Complaint successfully registered! Tracking ID: **{cid}**")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"Error filing complaint: {msg}")

    # ==========================================
    # TAB 2: MY COMPLAINTS & LIVE TRACKING
    # ==========================================
    with tab_track:
        st.markdown("#### 📦 My Complaint Dossiers & Live Stepper Timeline")
        if not complaints:
            st.info("You have not filed any complaints yet. Use the 'File New Complaint' tab above.")
        else:
            complaint_ids = [c["id"] for c in complaints]
            selected_cid = st.selectbox("Select Complaint to Inspect:", complaint_ids)

            comp = db.get_complaint_by_id(selected_cid)
            if comp:
                status_badge = render_status_badge(comp["status"])
                esc_badge = render_escalation_badge() if comp["is_escalated"] else ""

                render_html(f"""
                <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1.5rem; margin: 1rem 0; box-shadow: 0 4px 12px rgba(0,0,0,0.03);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <span class="id-pill">{comp['id']}</span>
                            <span style="font-size: 1.15rem; font-weight: 700; margin-left: 10px;">{comp['category_icon']} {comp['category_name']}</span>
                        </div>
                        <div>{status_badge} {esc_badge}</div>
                    </div>
                    <div style="margin-top: 1rem; color: #475569; font-size: 0.95rem;">
                        <strong>Incident:</strong> "{comp['description']}"
                    </div>
                </div>
                """)

                # Visual Timeline Stepper
                st.markdown("##### 📍 10-Stage Investigation Timeline Stepper")
                render_timeline_stepper(comp["status"])

                st.markdown("<br>", unsafe_allow_html=True)

                # Official Actions Log
                actions = db.get_complaint_actions(comp['id'], citizen_visible_only=True)
                st.markdown("##### 👮 Official Police Actions Recorded")
                if not actions:
                    st.info("No formal enforcement actions have been logged yet. The assigned investigating officer will record summons, challans, or inspection reports here.")
                else:
                    for a in actions:
                        render_html(f"""
                        <div class="action-card">
                            <div class="action-meta">
                                <span><strong>{a['action_type']}</strong> • Logged by {a['officer_name']} ({a['rank']}, Badge: {a['badge_number']})</span>
                                <span>{a['action_timestamp']}</span>
                            </div>
                            <div style="font-size: 0.92rem; color: #1e293b;">{a['description']}</div>
                        </div>
                        """)

                # Download Certified PDF/Text Transcript
                st.markdown("##### 📄 Export Official Records")
                transcript = asrv.generate_citizen_complaint_transcript(comp['id'])
                st.download_button(
                    label=f"📥 Download Certified Complaint Transcript ({comp['id']})",
                    data=transcript,
                    file_name=f"SAVE_KAROO_Transcript_{comp['id']}.txt",
                    mime="text/plain",
                    use_container_width=True
                )

    # ==========================================
    # TAB 3: NOTIFICATIONS CENTER
    # ==========================================
    with tab_notif:
        st.markdown("#### 🔔 In-App Safety Notifications")
        notifications = db.get_user_notifications(user["id"])
        if st.button("Mark All Notifications as Read", use_container_width=True):
            db.mark_notifications_read(user["id"])
            st.rerun()

        if not notifications:
            st.info("No notifications at this time.")
        else:
            for n in notifications:
                unread_marker = "🔵 " if not n["is_read"] else ""
                render_html(f"""
                <div style="background: {'#f0fdf4' if not n['is_read'] else '#ffffff'}; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px 16px; margin-bottom: 8px;">
                    <div style="font-weight: 700; font-size: 0.9rem; color: #0B192C;">{unread_marker}{n['title']}</div>
                    <div style="font-size: 0.85rem; color: #334155; margin-top: 4px;">{n['message']}</div>
                    <div style="font-size: 0.72rem; color: #64748B; margin-top: 4px;">{n['created_at']}</div>
                </div>
                """)

    # ==========================================
    # TAB 4: SAFETY SUBSCRIPTIONS & RAZORPAY TEST
    # ==========================================
    with tab_subs:
        st.markdown("#### 💳 Safety Subscriptions & Convenience Features")
        active_sub = ss.get_user_active_subscription(user["id"])
        if active_sub:
            st.success(f"Active Plan: **{active_sub['plan_name']}** ({active_sub['billing_cycle']}) • Status: `{active_sub['status']}`")

        st.info("🛡️ **REMINDER:** Standard complaint registration and police tracking are 100% FREE. Subscriptions apply strictly to optional certified transcripts, personal analytics heatmaps, and priority alerts.")

        sub_col1, sub_col2 = st.columns(2)
        with sub_col1:
            render_html("""
            <div class="kpi-card" style="text-align: left; height: 100%;">
                <div class="badge badge-assigned">UPGRADE OPTION</div>
                <h4>Citizen Safety Pro (₹199 / mo)</h4>
                <ul style="font-size: 0.85rem; line-height: 1.8;">
                    <li>Certified PDF transcripts with official digital seal</li>
                    <li>Automated WhatsApp / SMS status alerts</li>
                    <li>Personal transit danger zone heatmap</li>
                    <li>Priority review escalation badge</li>
                </ul>
            </div>
            """)

            if st.button("💳 Subscribe to Citizen Pro (Razorpay Test Mode)", use_container_width=True, type="primary"):
                plans = ss.get_all_subscription_plans()
                pro_plan = next((p for p in plans if p["plan_code"] == "PLAN_PREMIUM"), None)
                if pro_plan:
                    ok, msg, res = ss.process_mock_payment_and_subscribe(user["id"], pro_plan["id"], "MONTHLY")
                    if ok:
                        st.success(f"Payment successful! Txn Ref: `{res['transaction_ref']}` • Invoice: `{res['invoice_number']}`")
                        st.balloons()
                        st.rerun()

        with sub_col2:
            render_html("""
            <div class="kpi-card" style="text-align: left; height: 100%;">
                <div class="badge badge-resolved">FREE LIFETIME</div>
                <h4>Citizen Safety Basic (₹0)</h4>
                <ul style="font-size: 0.85rem; line-height: 1.8;">
                    <li>Unlimited public safety complaint registration</li>
                    <li>10-stage real-time timeline tracking</li>
                    <li>In-app notifications on all officer actions</li>
                    <li>KAROO AI assistant & 112 emergency routing</li>
                </ul>
            </div>
            """)

            if active_sub and active_sub["plan_code"] != "PLAN_FREE":
                if st.button("Cancel Paid Subscription & Revert to Free", use_container_width=True):
                    ok, msg = ss.cancel_subscription(user["id"])
                    st.info(msg)
                    st.rerun()

        st.markdown("##### 🧾 Invoices & Payment Receipts")
        invoices = ss.get_user_invoices(user["id"])
        if not invoices:
            st.caption("No invoices generated yet.")
        else:
            for inv in invoices:
                st.markdown(f"📄 **Invoice {inv['invoice_number']}** • Amount: ₹{inv['amount_inr']:.2f} • Gateway: `{inv['gateway']}` • Date: {inv['created_at']}")

    # ==========================================
    # TAB 5: EMERGENCY DIRECTORY
    # ==========================================
    with tab_help:
        st.markdown("#### 🚨 Indian Emergency & Public Safety Directory")
        render_html("""
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; margin-top: 1rem;">
            <div class="kpi-card" style="border-left: 4px solid #DC2626;">
                <div style="font-size: 1.8rem; font-weight: 800; color: #DC2626;">112</div>
                <div style="font-weight: 700;">National Emergency Response</div>
                <div style="font-size: 0.8rem; color: #64748B;">All-India Police, Fire & Medical</div>
            </div>
            <div class="kpi-card" style="border-left: 4px solid #9333EA;">
                <div style="font-size: 1.8rem; font-weight: 800; color: #9333EA;">1091</div>
                <div style="font-weight: 700;">Women Safety Helpline</div>
                <div style="font-size: 0.8rem; color: #64748B;">24/7 Dedicated Support</div>
            </div>
            <div class="kpi-card" style="border-left: 4px solid #2563EB;">
                <div style="font-size: 1.8rem; font-weight: 800; color: #2563EB;">1095</div>
                <div style="font-weight: 700;">Traffic Police Control</div>
                <div style="font-size: 0.8rem; color: #64748B;">Commercial Transit Emergencies</div>
            </div>
            <div class="kpi-card" style="border-left: 4px solid #D97706;">
                <div style="font-size: 1.8rem; font-weight: 800; color: #D97706;">1930</div>
                <div style="font-weight: 700;">National Cyber Crime</div>
                <div style="font-size: 0.8rem; color: #64748B;">Digital Fraud & Extortion</div>
            </div>
        </div>
        """)
