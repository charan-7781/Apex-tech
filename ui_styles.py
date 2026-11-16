"""
ui_styles.py
------------
Design System and Modern CSS Styling for SAVE KAROO.
Implements the professional Deep Navy / Royal Blue / Teal / Clean White visual identity.
"""

import textwrap
import streamlit as st

def render_html(html_str: str):
    """Safely renders HTML without Markdown interpreting indented lines as code blocks."""
    cleaned = textwrap.dedent(html_str).strip()
    st.markdown(cleaned, unsafe_allow_html=True)

def get_custom_css() -> str:
    return """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #1e293b;
    }

    /* Top Navigation Header */
    .brand-navbar {
        background: linear-gradient(135deg, #0B192C 0%, #1E3E62 100%);
        color: white;
        padding: 1.25rem 2rem;
        border-radius: 14px;
        margin-bottom: 1.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 10px 25px -5px rgba(11, 25, 44, 0.35);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .brand-title {
        font-size: 1.6rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .brand-tagline {
        font-size: 0.85rem;
        color: #94A3B8;
        margin: 4px 0 0 0;
        letter-spacing: 0.5px;
        font-weight: 500;
    }

    /* Hero Section */
    .hero-banner {
        background: radial-gradient(circle at top right, #1E3E62 0%, #0B192C 100%);
        color: white;
        padding: 3.5rem 2.5rem;
        border-radius: 18px;
        margin-bottom: 2rem;
        text-align: center;
        border: 1px solid rgba(0, 141, 218, 0.2);
        box-shadow: 0 20px 30px -10px rgba(11, 25, 44, 0.4);
    }
    .hero-heading {
        font-size: 2.8rem;
        font-weight: 800;
        line-height: 1.2;
        margin-bottom: 1rem;
        background: linear-gradient(135deg, #ffffff 0%, #93c5fd 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .hero-sub {
        font-size: 1.15rem;
        color: #cbd5e1;
        max-width: 800px;
        margin: 0 auto 2rem auto;
        line-height: 1.6;
    }

    /* KPI / Stat Cards */
    .kpi-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.25rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03);
        text-align: center;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.06);
    }
    .kpi-num {
        font-size: 2.2rem;
        font-weight: 800;
        color: #0B192C;
        margin: 4px 0;
    }
    .kpi-label {
        font-size: 0.8rem;
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Status Badges */
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.3px;
    }
    .badge-submitted { background: #E0F2FE; color: #0284C7; border: 1px solid #BAE6FD; }
    .badge-under-review { background: #FEF3C7; color: #D97706; border: 1px solid #FDE68A; }
    .badge-verified { background: #E0E7FF; color: #4338CA; border: 1px solid #C7D2FE; }
    .badge-assigned { background: #EDE9FE; color: #6D28D9; border: 1px solid #DDD6FE; }
    .badge-action { background: #CFFAFE; color: #0891B2; border: 1px solid #A5F3FC; }
    .badge-investigating { background: #CCFBF1; color: #0F766E; border: 1px solid #99F6E4; }
    .badge-awaiting { background: #FFEDD5; color: #C2410C; border: 1px solid #FED7AA; }
    .badge-resolved { background: #DCFCE7; color: #15803D; border: 1px solid #BBF7D0; }
    .badge-closed { background: #F1F5F9; color: #475569; border: 1px solid #E2E8F0; }
    .badge-rejected { background: #FEE2E2; color: #B91C1C; border: 1px solid #FECACA; }
    .badge-escalated { background: #FFE4E6; color: #BE123C; border: 1px solid #FDA4AF; animation: pulse 2s infinite; }

    /* Stepper Timeline */
    .stepper-box {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1.5rem 0;
    }
    .step-circle {
        width: 34px;
        height: 34px;
        border-radius: 50%;
        margin: 0 auto 8px auto;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.85rem;
    }
    .step-completed { background: #10B981; color: white; }
    .step-active { background: #2563EB; color: white; box-shadow: 0 0 0 5px #BFDBFE; }
    .step-upcoming { background: #E2E8F0; color: #94A3B8; }

    /* Action Log Cards */
    .action-card {
        background: #FFFFFF;
        border-left: 4px solid #2563EB;
        border-radius: 0 8px 8px 0;
        padding: 1rem 1.25rem;
        margin-bottom: 0.75rem;
        border-top: 1px solid #F1F5F9;
        border-right: 1px solid #F1F5F9;
        border-bottom: 1px solid #F1F5F9;
    }
    .action-meta {
        font-size: 0.75rem;
        color: #64748B;
        margin-bottom: 4px;
        display: flex;
        justify-content: space-between;
    }

    /* Code & ID Pill */
    .id-pill {
        font-family: 'JetBrains Mono', monospace;
        background: #0B192C;
        color: #38BDF8;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }

    /* Emergency Strip */
    .emergency-strip {
        background: linear-gradient(90deg, #991B1B 0%, #DC2626 100%);
        color: white;
        padding: 0.75rem 1.25rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-weight: 600;
        font-size: 0.92rem;
    }
</style>
"""

def render_status_badge(status: str) -> str:
    mapping = {
        'SUBMITTED': 'badge-submitted',
        'UNDER REVIEW': 'badge-under-review',
        'VERIFIED': 'badge-verified',
        'ASSIGNED': 'badge-assigned',
        'ACTION INITIATED': 'badge-action',
        'INVESTIGATION IN PROGRESS': 'badge-investigating',
        'AWAITING CITIZEN RESPONSE': 'badge-awaiting',
        'RESOLVED': 'badge-resolved',
        'CLOSED': 'badge-closed',
        'REJECTED': 'badge-rejected',
    }
    css_class = mapping.get(status, 'badge-closed')
    return f'<span class="badge {css_class}">{status}</span>'

def render_escalation_badge() -> str:
    return '<span class="badge badge-escalated">⚡ ESCALATED (ADMIN REVIEW)</span>'

