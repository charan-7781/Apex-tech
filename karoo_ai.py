"""
karoo_ai.py
-----------
KAROO AI — The Public Safety & Citizen Guidance Assistant.
Strict Safety Guidelines:
- Identifies clearly as an AI assistant.
- NEVER claims to be a police officer or government official.
- NEVER makes legal conclusions or determines guilt.
- Prominently directs emergency situations to emergency services (112, 1091).
- Assists citizens in structuring incident details, identifying evidence, and navigating tracking.
"""

import os
import re
from typing import List, Dict, Any

SAFETY_DISCLAIMER = (
    "🚨 **EMERGENCY NOTICE:** If you are in immediate danger or witnessing an ongoing crime, "
    "do NOT wait for a web response. Call **112** (National Emergency Response) or **1091** (Women's Helpline) immediately!"
)

SYSTEM_PROMPT = """You are KAROO AI, an intelligent, empathetic public safety and citizen guidance assistant for the SAVE KAROO platform.
Your purpose is to:
1. Help citizens articulate incident descriptions clearly and identify essential details (vehicle number, driver name, route, timestamps, evidence).
2. Guide users on how to report complaints and track their status.
3. Explain complaint lifecycle stages (Submitted -> Verified -> Assigned -> Action Initiated -> Resolved).
4. Direct urgent emergency situations to Indian emergency helplines: 112 (All Emergencies), 1091 (Women Safety), 1095 (Traffic Police).

STRICT CONSTRAINTS:
- You are an AI assistant. NEVER claim to be a police officer or legal authority.
- NEVER declare someone guilty or make definitive legal determinations.
- NEVER claim that an investigation has verified or dismissed a claim autonomously.
- Always remain supportive, professional, calm, and objective.
"""

def detect_emergency_keywords(user_text: str) -> bool:
    emergency_terms = [
        "kidnap", "danger right now", "attacking me", "attack right now",
        "gun", "knife", "rape", "assaulting now", "immediate help", "dying", "help right now"
    ]
    lower = user_text.lower()
    return any(term in lower for term in emergency_terms)

def get_karoo_ai_response(
    user_message: str,
    conversation_history: List[Dict[str, str]] = None,
    api_key_override: str = None
) -> str:
    """Generates an empathetic, safety-conscious response from KAROO AI."""
    # Check for immediate danger emergency first
    if detect_emergency_keywords(user_message):
        return (
            f"{SAFETY_DISCLAIMER}\n\n"
            "**IMMEDIATE ACTION REQUIRED:** Please step into a well-lit, populated area or store, alert bystanders, "
            "and immediately dial **112** on your mobile phone. Your immediate physical safety is paramount."
        )

    # Check for live Google Gemini Key
    gemini_key = api_key_override or os.getenv("GEMINI_API_KEY", "").strip()

    if gemini_key and (gemini_key.startswith("AQ.") or gemini_key.startswith("AIza")):
        try:
            from google import genai
            client = genai.Client(api_key=gemini_key)
            
            prompt_content = f"{SYSTEM_PROMPT}\n\n"
            if conversation_history:
                for msg in conversation_history[-4:]:
                    role = "User" if msg["role"] == "user" else "Assistant"
                    prompt_content += f"{role}: {msg['content']}\n"
            prompt_content += f"User: {user_message}\nAssistant:"

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt_content
            )
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            # Fall back cleanly to safety knowledge base
            pass

    # High-quality offline knowledge base for public safety
    lower = user_message.lower()

    if any(k in lower for k in ["track", "status", "check my complaint", "where is"]):
        return (
            "🔍 **Tracking Your Complaint:**\n\n"
            "You can track your complaint anytime on SAVE KAROO:\n"
            "1. Enter your tracking ID (e.g., `SK-2026-000001`) in the **Track Complaint** search bar above.\n"
            "2. If logged into your Citizen Portal, visit the **My Complaints** tab to see your visual timeline.\n"
            "3. The 10 lifecycle stages progress from *Submitted* ➔ *Under Review* ➔ *Assigned* ➔ *Action Initiated* ➔ *Resolved*.\n\n"
            "Every action taken by assigned investigating officers is documented in your live timeline!"
        )

    if any(k in lower for k in ["how to report", "file a complaint", "register", "submit"]):
        return (
            "📝 **How to File a Safety Complaint on SAVE KAROO:**\n\n"
            "1. Click **'Report an Incident'** on the top menu or inside your Citizen Dashboard.\n"
            "2. **Step 1 - Category:** Select the incident type (e.g., Cab Misconduct, Bike Taxi Safety, Auto Overcharging, Harassment).\n"
            "3. **Step 2 - Vehicle & Driver:** Enter the vehicle registration number (e.g., `KA-01-MJ-4412`), platform (Uber, Ola, Rapido), and driver name if known.\n"
            "4. **Step 3 - Incident Details:** Provide the date, time, exact landmark/route, and a factual description.\n"
            "5. **Step 4 - Evidence:** Attach ride receipt screenshots, trip GPS maps, photos, or audio recordings.\n"
            "6. Submit to instantly receive your official tracking ID (`SK-2026-XXXXXX`)."
        )

    if any(k in lower for k in ["evidence", "proof", "screenshot", "photo"]):
        return (
            "📎 **Recommended Evidence for Public Safety Inquiries:**\n\n"
            "Providing verifiable evidence significantly accelerates police review:\n"
            "- **Ride Booking Screenshot:** Showing the trip ID, driver name, vehicle registration number, and assigned route.\n"
            "- **GPS Navigation Divergence:** A screenshot of your map if the driver took an unauthorized or unsafe deviation.\n"
            "- **Receipt / Digital Invoice:** Proof of extortionate cash demands beyond app fare.\n"
            "- **Photographs / Dashcam Footage:** Pictures of vehicle condition or license plates.\n\n"
            "*Note: All evidence is securely encrypted and only accessible to authorized investigating officers.*"
        )

    if any(k in lower for k in ["escalation", "repeat", "5 complaints", "unacted"]):
        return (
            "⚡ **SAVE KAROO Escalation Concept:**\n\n"
            "To prevent safety complaints from being ignored, SAVE KAROO features an automated **Escalation Engine**:\n"
            "- If **5 or more complaints** accumulate against the same vehicle or commercial driver without recorded action, the system automatically flags the entity for administrative review.\n"
            "- Police Administrators and Super Admins receive high-priority alerts with full incident dossiers.\n"
            "- Cases exceeding SLA response windows (48 hours) are automatically highlighted in red on precinct dashboards."
        )

    if any(k in lower for k in ["free", "cost", "subscription", "pricing", "money", "fee"]):
        return (
            "🛡️ **Our Sacred Rule: Safety is 100% Free:**\n\n"
            "**Filing safety complaints, tracking cases, receiving police action updates, and accessing emergency resources are 100% FREE for all citizens forever.**\n\n"
            "Optional subscriptions apply strictly to convenience features:\n"
            "- **Citizen Pro (₹199/mo):** Certified PDF complaint transcripts for court/insurance, personal incident heatmaps, and priority desk support.\n"
            "- **Enterprise / Fleet Plan:** For transport fleet companies conducting compliance audits across their drivers."
        )

    return (
        "Namaste! I am **KAROO AI**, your public safety assistant. I can help you:\n\n"
        "1. Understand how to document and report a commercial transit or safety incident.\n"
        "2. Check the evidence needed for effective investigation.\n"
        "3. Explain complaint lifecycle statuses and tracking.\n"
        "4. Learn about our automated repeat-offender escalation rules.\n\n"
        "How can I assist you right now? *(Remember: For life-threatening emergencies, call **112** immediately).* "
    )

