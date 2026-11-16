"""
app.py
------
ApexTech Enterprise AI Customer Support Suite
Features:
- WhatsApp / iMessage-style Chat (User on RIGHT, AI Bot on LEFT)
- Multi-Tab Navigation:
  1. 💬 AI Support Chat (with quick prompt chips, transcript export, feedback)
  2. 📦 Order Tracking Hub (Visual delivery timeline, cancellation & return actions)
  3. 🛍️ Product Catalog & Stock (Browse items, filter, instant 'Ask Nova' button)
  4. 📊 Manager Dashboard (Live metrics, full orders database, add test order)
  5. ⚙️ AI Settings (OpenAI API key configuration, tone selector, model picker)
"""

import os
import datetime
import importlib
import markdown
from dotenv import load_dotenv
import streamlit as st
import database
import agent

# Force-reload modules and .env so changes are immediately active
load_dotenv(override=True)
importlib.reload(database)
importlib.reload(agent)

# 1. Page Configuration
st.set_page_config(
    page_title="ApexTech | AI Customer Care Suite",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database tables and data
database.init_db()

# 2. Modern Custom CSS Styling (Cohesive Dark/Light Blended Palette)
st.markdown("""
<style>
    /* Global font & smooth transitions */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Header styling */
    .app-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: white;
        padding: 1.25rem 1.75rem;
        border-radius: 14px;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 4px 16px rgba(15, 23, 42, 0.25);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    /* RIGHT-ALIGNED USER CHAT BUBBLE (Refined Vibrant Gradient) */
    .user-bubble-wrapper {
        display: flex;
        justify-content: flex-end;
        margin: 12px 0;
        width: 100%;
    }
    .user-bubble {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        color: #ffffff !important;
        padding: 14px 20px;
        border-radius: 20px 20px 4px 20px;
        max-width: 75%;
        border: 1px solid rgba(191, 219, 254, 0.25);
        box-shadow: 0 4px 16px rgba(37, 99, 235, 0.25);
        font-size: 0.95rem;
        line-height: 1.6;
        word-wrap: break-word;
    }
    .user-bubble-meta {
        font-size: 0.72rem;
        opacity: 0.9;
        text-align: right;
        margin-bottom: 6px;
        font-weight: 700;
        letter-spacing: 0.5px;
        color: #dbeafe;
    }
    .user-bubble p {
        margin: 0 0 6px 0;
        color: #ffffff !important;
    }
    .user-bubble p:last-child {
        margin-bottom: 0;
    }

    /* LEFT-ALIGNED BOT CHAT BUBBLE (Deep Slate Translucent Glass - Blends Neatly!) */
    .bot-bubble-wrapper {
        display: flex;
        justify-content: flex-start;
        margin: 12px 0;
        width: 100%;
    }
    .bot-bubble {
        background: #1e293b;
        color: #e2e8f0 !important;
        padding: 16px 22px;
        border-radius: 20px 20px 20px 4px;
        max-width: 80%;
        border: 1px solid rgba(148, 163, 184, 0.2);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
        font-size: 0.95rem;
        line-height: 1.6;
        word-wrap: break-word;
    }
    .bot-bubble-meta {
        font-size: 0.75rem;
        color: #818cf8;
        font-weight: 700;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 6px;
        letter-spacing: 0.5px;
    }
    .bot-bubble p {
        margin: 0 0 8px 0;
        color: #e2e8f0 !important;
    }
    .bot-bubble p:last-child {
        margin-bottom: 0;
    }
    .bot-bubble strong, .bot-bubble b {
        color: #ffffff !important;
        font-weight: 600;
    }
    .bot-bubble ul, .bot-bubble ol {
        margin: 8px 0;
        padding-left: 20px;
    }
    .bot-bubble li {
        margin-bottom: 4px;
        color: #cbd5e1 !important;
    }
    .bot-bubble code {
        background: rgba(15, 23, 42, 0.8) !important;
        color: #38bdf8 !important;
        padding: 2px 6px;
        border-radius: 4px;
        border: 1px solid rgba(56, 189, 248, 0.25);
        font-size: 0.88em;
    }

    /* Status Pills */
    .status-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
    }
    .status-shipped { background: #e0f2fe; color: #0369a1; }
    .status-delivered { background: #dcfce7; color: #15803d; }
    .status-processing { background: #fef3c7; color: #b45309; }
    .status-transit { background: #f3e8ff; color: #7e22ce; }
    .status-cancelled { background: #fee2e2; color: #b91c1c; }

    /* Metric card */
    .stat-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 18px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        text-align: center;
    }
    .stat-value {
        font-size: 2rem;
        font-weight: 700;
        color: #1e293b;
        margin: 4px 0;
    }
    .stat-label {
        font-size: 0.85rem;
        color: #64748b;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Timeline Stepper */
    .stepper-container {
        display: flex;
        justify-content: space-between;
        margin: 20px 0;
        position: relative;
    }
    .stepper-step {
        text-align: center;
        flex: 1;
        position: relative;
    }
    .step-circle {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        margin: 0 auto 8px auto;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 0.85rem;
    }
    .step-active { background: #2563eb; color: white; box-shadow: 0 0 0 4px #bfdbfe; }
    .step-done { background: #10b981; color: white; }
    .step-pending { background: #e2e8f0; color: #64748b; }
</style>
""", unsafe_allow_html=True)

# 3. Session State Initialization
if "messages" not in st.session_state:
    st.session_state.messages = []

# Automatically clean any old error notices or quota messages out of the active screen
unwanted_phrases = ["RESOURCE_EXHAUSTED", "Google Gemini Notice", "OpenAI API Notice", "Error code:", "[Demo Mode]", "quota exceeded"]
st.session_state.messages = [
    m for m in st.session_state.messages 
    if not any(phrase.lower() in m.get("content", "").lower() for phrase in unwanted_phrases)
]

if not st.session_state.messages:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "👋 Hello! I am **Nova**, your ApexTech customer care specialist (now powered by live **Google Gemini AI**). How can I help you today?\n\nYou can ask me to track an order (e.g. `ORD-1001`), browse products, or inquire about store policies!",
            "time": datetime.datetime.now().strftime("%I:%M %p")
        }
    ]

gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
openai_key = os.getenv("OPENAI_API_KEY", "").strip()
best_key = gemini_key if gemini_key else openai_key

# Ensure session switches to the working Gemini key
if (
    "api_key" not in st.session_state 
    or not st.session_state.api_key 
    or st.session_state.api_key.startswith("sk-")
    or st.session_state.api_key == "your_openai_api_key_here"
):
    st.session_state.api_key = best_key

if "tone" not in st.session_state:
    st.session_state.tone = "Friendly & Warm"

if "model_name" not in st.session_state:
    st.session_state.model_name = "gpt-4o-mini"

if "quick_prompt" not in st.session_state:
    st.session_state.quick_prompt = None


# 4. Helper Function: Render Left/Right Messages
def render_chat_message(role: str, content: str, time_str: str = ""):
    """Renders user messages on the RIGHT and assistant messages on the LEFT."""
    if not time_str:
        time_str = datetime.datetime.now().strftime("%I:%M %p")

    # Convert Markdown to real HTML so bold, lists, and code blocks render properly
    html_content = markdown.markdown(content, extensions=["extra", "nl2br"])

    if role == "user":
        st.markdown(f"""
        <div class="user-bubble-wrapper">
            <div class="user-bubble">
                <div class="user-bubble-meta">YOU • {time_str}</div>
                <div>{html_content}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="bot-bubble-wrapper">
            <div class="bot-bubble">
                <div class="bot-bubble-meta">
                    <span>🛍️</span>
                    <span>NOVA • CUSTOMER CARE</span>
                    <span style="opacity: 0.65; font-weight: normal; margin-left: auto;">{time_str}</span>
                </div>
                <div>{html_content}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# 5. Helper Function: Visual Delivery Timeline
def render_order_timeline(status: str):
    stages = ["Ordered", "Processing", "Shipped", "Out for Delivery", "Delivered"]
    
    current_index = 0
    if status == "Processing":
        current_index = 1
    elif status == "Shipped":
        current_index = 2
    elif status == "Out for Delivery":
        current_index = 3
    elif status == "Delivered":
        current_index = 4
    elif status == "Cancelled":
        st.error("🚫 This order was marked as Cancelled.")
        return

    cols = st.columns(len(stages))
    for i, stage in enumerate(stages):
        with cols[i]:
            if i < current_index:
                st.markdown(f"✅ **{stage}**", help="Completed")
            elif i == current_index:
                st.markdown(f"🔵 **{stage}** *(Current)*")
            else:
                st.markdown(f"⚪ <span style='color: #888;'>{stage}</span>", unsafe_allow_html=True)
    st.progress((current_index + 1) / len(stages))


# 6. Top Header Banner
gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
openai_key = os.getenv("OPENAI_API_KEY", "").strip()
active_key = (st.session_state.get("api_key") or gemini_key or openai_key).strip()

if active_key.startswith("AQ.") or active_key.startswith("AIza") or (gemini_key and active_key == gemini_key):
    mode_badge = '<span class="status-badge status-delivered">🟢 Google Gemini 3 Flash Live</span>'
elif active_key.startswith("sk-") and active_key != "your_openai_api_key_here":
    mode_badge = '<span class="status-badge status-delivered">🟢 OpenAI GPT-4o-mini Live</span>'
else:
    mode_badge = '<span class="status-badge status-processing">🟡 Interactive Demo Mode</span>'

st.markdown(f"""
<div class="app-header">
    <div>
        <h2 style="margin: 0; font-size: 1.6rem; font-weight: 700;">🛍️ ApexTech India • AI Customer Support</h2>
        <p style="margin: 4px 0 0 0; opacity: 0.85; font-size: 0.92rem;">Next-Generation E-Commerce Support (Pan-India Shipping via Bluedart & Delhivery)</p>
    </div>
    <div>
        {mode_badge}
    </div>
</div>
""", unsafe_allow_html=True)


# 7. Sidebar Controls
with st.sidebar:
    st.markdown("### 🏢 ApexTech Center")
    st.caption("E-Commerce AI Operations")

    st.markdown("#### ⚡ Quick Assistance")
    if st.button("📦 Track ORD-1001 (Aarav)", use_container_width=True):
        st.session_state.quick_prompt = "Where is my order ORD-1001?"
    if st.button("🚚 Track ORD-1004 (Ananya)", use_container_width=True):
        st.session_state.quick_prompt = "What is the status of ORD-1004?"
    if st.button("🎧 Search Headphones (₹)", use_container_width=True):
        st.session_state.quick_prompt = "Tell me about your wireless headphones and their price in Rupees."
    if st.button("🔄 7-Day Return & Replacement", use_container_width=True):
        st.session_state.quick_prompt = "What is your return and reverse pickup policy?"
    if st.button("🧑‍💼 Customer Helpline (India)", use_container_width=True):
        st.session_state.quick_prompt = "How can I contact customer care in India?"

    st.divider()

    st.markdown("#### ⚙️ Quick Settings")
    st.session_state.tone = st.selectbox(
        "Agent Voice / Tone:",
        ["Friendly & Warm", "Professional & Formal", "Concise & Fast"],
        index=["Friendly & Warm", "Professional & Formal", "Concise & Fast"].index(st.session_state.tone)
    )

    st.caption(f"Active Tone: **{st.session_state.tone}**")

    st.divider()

    # Chat Transcript Download
    transcript = "\n".join([f"[{m.get('time', '')}] {m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
    st.download_button(
        label="📥 Download Chat Transcript",
        data=transcript,
        file_name="apextech_support_transcript.txt",
        mime="text/plain",
        use_container_width=True
    )

    if st.button("🗑️ Reset Chat", use_container_width=True):
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Conversation reset. Namaste! I'm Nova, how can I assist you today?",
                "time": datetime.datetime.now().strftime("%I:%M %p")
            }
        ]
        st.session_state.quick_prompt = None
        st.rerun()


# 8. Main Multi-Tab Navigation
tab_chat, tab_orders, tab_catalog, tab_manager, tab_settings = st.tabs([
    "💬 Live Support Chat",
    "📦 Order Tracking Hub",
    "🛍️ Product Catalog",
    "📊 Manager Dashboard",
    "⚙️ AI Settings"
])


# ==========================================
# TAB 1: LIVE SUPPORT CHAT (With Right/Left Alignment)
# ==========================================
with tab_chat:
    # Quick prompt pills bar above chat
    st.markdown("##### 💡 Suggested Questions (Click to Ask):")
    pcols = st.columns(5)
    with pcols[0]:
        if st.button("📦 Track ORD-1001 (Aarav)", key="pill_1", use_container_width=True):
            st.session_state.quick_prompt = "Where is order ORD-1001 for Aarav Sharma?"
    with pcols[1]:
        if st.button("🚚 Track ORD-1006 (Sneha)", key="pill_2", use_container_width=True):
            st.session_state.quick_prompt = "What is the delivery update for Sneha Kulkarni's smartwatch (ORD-1006)?"
    with pcols[2]:
        if st.button("🎧 Audio & Mics (₹)", key="pill_3", use_container_width=True):
            st.session_state.quick_prompt = "What wireless headphones and studio microphones do you sell and what are their prices in Rupees?"
    with pcols[3]:
        if st.button("💻 Curved Monitor & Keyboard", key="pill_4", use_container_width=True):
            st.session_state.quick_prompt = "Tell me about your 34-inch curved gaming monitor and mechanical keyboard prices in Rupees."
    with pcols[4]:
        if st.button("🔄 Returns, GST & Warranty", key="pill_5", use_container_width=True):
            st.session_state.quick_prompt = "Do you provide GST tax invoices and what is your return and warranty policy across India?"

    st.markdown("---")

    # Message History Container
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages:
            render_chat_message(
                role=msg["role"],
                content=msg["content"],
                time_str=msg.get("time", "")
            )

    # Input Box at the Bottom
    typed_input = st.chat_input("Type your question here... (e.g. 'Where is order ORD-1003?')")
    
    # Check if a prompt was triggered (either by typing or by clicking a pill)
    active_prompt = st.session_state.quick_prompt if st.session_state.quick_prompt else typed_input
    
    if active_prompt:
        st.session_state.quick_prompt = None
        now_str = datetime.datetime.now().strftime("%I:%M %p")
        
        # 1. Add and render USER message on the RIGHT
        st.session_state.messages.append({
            "role": "user",
            "content": active_prompt,
            "time": now_str
        })
        render_chat_message("user", active_prompt, now_str)

        # 2. Get history for AI context
        history = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages[:-1]
        ]

        # 3. Call AI Agent
        with st.spinner("Nova is consulting the store database..."):
            reply = agent.get_agent_response(
                user_message=active_prompt,
                conversation_history=history,
                api_key_override=st.session_state.api_key,
                tone=st.session_state.tone,
                model_name=st.session_state.model_name
            )

        # 4. Add and render BOT message on the LEFT
        st.session_state.messages.append({
            "role": "assistant",
            "content": reply,
            "time": datetime.datetime.now().strftime("%I:%M %p")
        })
        st.rerun()


# ==========================================
# TAB 2: ORDER TRACKING HUB (Visual Timeline)
# ==========================================
with tab_orders:
    st.subheader("📦 Customer Self-Service Tracking")
    st.write("Look up shipment progress, view courier tracking IDs, or submit return requests.")

    all_orders = database.get_all_orders()
    order_options = [o["order_id"] for o in all_orders]

    col_search, col_select = st.columns([1, 1])
    with col_search:
        typed_order_id = st.text_input("Enter Order ID manually:", placeholder="e.g. ORD-1001").strip().upper()
    with col_select:
        dropdown_order_id = st.selectbox("Or choose an existing order:", ["-- Select --"] + order_options)

    selected_id = typed_order_id if typed_order_id else (dropdown_order_id if dropdown_order_id != "-- Select --" else None)

    if selected_id:
        order_info = database.get_order_details(selected_id)
        if order_info:
            st.success(f"Order **{selected_id}** found for customer **{order_info['customer_name']}**")
            
            # Visual shipment timeline
            st.markdown("#### 🚚 Live Shipment Progress")
            render_order_timeline(order_info["status"])

            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Purchased Item", order_info["item_name"])
            with col_b:
                st.metric("Current Status", order_info["status"])
            with col_c:
                st.metric("Tracking Number", order_info["tracking_number"])

            st.info(f"📅 **Delivery ETA:** {order_info['estimated_delivery']}")

            # Customer Action Buttons
            st.markdown("#### ⚡ Order Actions")
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button("❌ Request Order Cancellation", key=f"cancel_{selected_id}", use_container_width=True):
                    database.update_order_status(selected_id, "Cancelled")
                    st.toast(f"Order {selected_id} has been cancelled.", icon="🚫")
                    st.rerun()
            with btn_col2:
                if st.button("🔄 Request Return / Refund", key=f"return_{selected_id}", use_container_width=True):
                    database.update_order_status(selected_id, "Return Requested")
                    st.toast(f"Return label generated for {selected_id}!", icon="📦")
                    st.rerun()

        else:
            st.error(f"Order `{selected_id}` was not found in our database. Please check your order number.")
    else:
        st.info("👆 Please enter or select an Order ID above to view live tracking.")


# ==========================================
# TAB 3: PRODUCT CATALOG & STOCK
# ==========================================
with tab_catalog:
    st.subheader("🛍️ ApexTech Product Catalog & Stock")
    st.write("Browse electronics and accessories currently in stock.")

    all_products = database.get_all_products()
    categories = sorted(list(set(p["category"] for p in all_products)))

    cat_col, search_col = st.columns([1, 2])
    with cat_col:
        selected_category = st.selectbox("Filter Category:", ["All Categories"] + categories)
    with search_col:
        search_query = st.text_input("Search catalog:", placeholder="Search by name or keyword...")

    filtered_products = all_products
    if selected_category != "All Categories":
        filtered_products = [p for p in filtered_products if p["category"] == selected_category]
    if search_query:
        filtered_products = [p for p in filtered_products if search_query.lower() in p["name"].lower() or search_query.lower() in p["description"].lower()]

    st.write(f"Showing **{len(filtered_products)}** items:")

    # Grid display of products
    for p in filtered_products:
        with st.container():
            c1, c2, c3 = st.columns([3, 1, 1])
            with c1:
                st.markdown(f"### {p['name']}")
                st.caption(f"Category: {p['category']} | ID: `{p['product_id']}`")
                st.write(p["description"])
            with c2:
                st.markdown(f"#### ₹{p['price']:,.0f}")
                if p["stock_count"] > 10:
                    st.markdown(f'<span class="status-badge status-delivered">In Stock ({p["stock_count"]})</span>', unsafe_allow_html=True)
                elif p["stock_count"] > 0:
                    st.markdown(f'<span class="status-badge status-processing">Low Stock ({p["stock_count"]})</span>', unsafe_allow_html=True)
                else:
                    st.markdown('<span class="status-badge status-cancelled">Out of Stock</span>', unsafe_allow_html=True)
            with c3:
                st.write("")
                if st.button("💬 Ask Nova", key=f"ask_prod_{p['product_id']}", use_container_width=True):
                    st.session_state.quick_prompt = f"Can you tell me more about the {p['name']}?"
                    st.rerun()
            st.divider()


# ==========================================
# TAB 4: STORE MANAGER DASHBOARD
# ==========================================
with tab_manager:
    st.subheader("📊 Store Operations & Metrics")
    st.write("Live inventory and order metrics stored in your local SQLite database.")

    stats = database.get_store_stats()
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Total Orders</div>
            <div class="stat-value">{stats['total_orders']}</div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Active Shipments</div>
            <div class="stat-value" style="color: #2563eb;">{stats['active_shipments']}</div>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Delivered</div>
            <div class="stat-value" style="color: #10b981;">{stats['delivered_orders']}</div>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Catalog Products</div>
            <div class="stat-value">{stats['total_products']}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### 📋 All Database Orders")
    all_orders_data = database.get_all_orders()
    st.dataframe(all_orders_data, use_container_width=True)

    st.markdown("### ➕ Add a Test Order")
    with st.expander("Create custom test order in SQLite"):
        with st.form("new_order_form"):
            new_id = st.text_input("New Order ID (e.g. ORD-1005):")
            new_name = st.text_input("Customer Name:")
            new_item = st.text_input("Item Purchased:")
            new_status = st.selectbox("Initial Status:", ["Processing", "Shipped", "Out for Delivery", "Delivered"])
            new_eta = st.text_input("Estimated Delivery:", value="In 2 business days")
            new_trk = st.text_input("Tracking Number:", value="TRK-123456")
            submitted = st.form_submit_button("Save Order to Database")

            if submitted:
                if new_id and new_name and new_item:
                    conn = database.get_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO orders (order_id, customer_name, item_name, status, estimated_delivery, tracking_number)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (new_id.upper(), new_name, new_item, new_status, new_eta, new_trk))
                    conn.commit()
                    conn.close()
                    st.success(f"Order {new_id} added successfully! You can now track it in the chat tab.")
                    st.rerun()
                else:
                    st.error("Please fill out Order ID, Customer Name, and Item.")


# ==========================================
# TAB 5: AI SETTINGS & CONFIGURATION
# ==========================================
with tab_settings:
    st.subheader("⚙️ AI Model & Agent Settings")
    st.write("Customize Nova's intelligence, API credentials, and behavior.")

    st.markdown("#### 🔑 AI Provider API Key")
    key_input = st.text_input(
        "Enter your AI API Key (Google Gemini or OpenAI):",
        value=st.session_state.api_key,
        type="password",
        help="Auto-detects Google Gemini keys (AQ. / AIza) and OpenAI keys (sk-)."
    )
    if st.button("Save API Key"):
        st.session_state.api_key = key_input.strip()
        st.success("API key saved and active!")
        st.rerun()
        st.rerun()

    st.markdown("#### 🧠 AI Model Selection")
    st.session_state.model_name = st.selectbox(
        "Select OpenAI Model:",
        ["gpt-4o-mini", "gpt-4o"],
        index=0,
        help="gpt-4o-mini is ultra-fast, cost-effective, and ideal for customer support."
    )

    st.markdown("#### 🎭 Persona Voice & Communication Style")
    st.session_state.tone = st.radio(
        "Choose Nova's voice:",
        ["Friendly & Warm", "Professional & Formal", "Concise & Fast"],
        index=["Friendly & Warm", "Professional & Formal", "Concise & Fast"].index(st.session_state.tone)
    )

    st.divider()

    st.markdown("#### 🔄 Reset Store Database")
    if st.button("Reset Database to Factory Defaults"):
        if os.path.exists("ecommerce.db"):
            os.remove("ecommerce.db")
        database.init_db()
        st.success("Database reset with default orders and products!")
        st.rerun()
