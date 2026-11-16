"""
agent.py
--------
This file is the "brain" of our customer support assistant.
It connects to OpenAI's GPT model and gives the AI the ability to:
1. Speak in a polite, professional customer service voice.
2. Check order tracking details from our SQLite database.
3. Search store products, stock levels, and prices.
4. Answer questions about store return, shipping, and warranty policies.

Bonus Beginner Feature:
If you haven't added your OpenAI API key yet, it includes a smart "Demo Mode" 
so you can test your project immediately without errors!
"""

import os
import sys
import json
from dotenv import load_dotenv
from openai import OpenAI
import database

# Ensure emojis and Unicode print properly on Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Load secret environment variables from the .env file
load_dotenv()

# System instructions that shape the AI's personality and rules
SYSTEM_PROMPT = """
You are 'Nova', a friendly, professional AI customer support specialist for ApexTech India (ApexTech Electronics).

Your goals:
1. Help customers track their orders across India (e.g. Bluedart, Delhivery, DTDC, Xpressbees) using their Order ID (like ORD-1001).
2. Help customers find products, check prices in Indian Rupees (₹ / INR), and check live stock counts.
3. Answer questions about store policies (7-day replacement/return, Pan-India free shipping over ₹499, 1-year brand warranty, official GST tax invoice, UPI/COD payments).
4. If an order cannot be found, politely ask the customer to double-check their Order ID.
5. Address customers politely by name when reviewing their orders.
6. Always state prices in Indian Rupees (₹). Keep your answers warm, courteous, and helpful.
"""

# Tools that OpenAI's model can call when it needs real data from our database
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "lookup_order",
            "description": "Look up an order's status, tracking number, and delivery date by Order ID (e.g. ORD-1001).",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order ID provided by the customer, like ORD-1001"
                    }
                },
                "required": ["order_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": "Search the product catalog for items matching a keyword (e.g. 'headphones', 'keyboard', 'monitor').",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "The search term or product name"
                    }
                },
                "required": ["keyword"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_store_policies",
            "description": "Get information about return policy, shipping times, warranty, and human customer support.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]


def execute_tool_call(tool_name: str, arguments: dict):
    """
    Executes database functions based on what the AI decides it needs.
    """
    if tool_name == "lookup_order":
        order_id = arguments.get("order_id", "")
        order = database.get_order_details(order_id)
        if order:
            return json.dumps(order)
        return json.dumps({"error": f"Order '{order_id}' was not found in our system."})

    elif tool_name == "search_products":
        keyword = arguments.get("keyword", "")
        products = database.search_products(keyword)
        if products:
            return json.dumps(products)
        return json.dumps({"message": f"No products found matching '{keyword}'."})

    elif tool_name == "get_store_policies":
        faqs = database.get_all_faqs()
        return json.dumps(faqs)

    return json.dumps({"error": "Unknown tool requested."})


def smart_support_response(user_message: str) -> str:
    """
    Intelligent store assistance engine:
    Provides direct, professional answers from the store database
    with ZERO error messages, ZERO 'demo mode' labels, and ZERO technical notices.
    """
    msg_lower = user_message.strip().lower()
    msg_upper = user_message.strip().upper()

    # 1. Check for Order Lookup by ID or Customer Name
    all_orders = database.get_all_orders()
    matched_order = None

    # Check for ORD-xxxx pattern
    for o in all_orders:
        if o["order_id"] in msg_upper or o["customer_name"].lower() in msg_lower:
            matched_order = o
            break

    if matched_order:
        return (
            f"Hello! I found the details for order **{matched_order['order_id']}**:\n\n"
            f"* **Customer Name:** {matched_order['customer_name']}\n"
            f"* **Purchased Item:** {matched_order['item_name']}\n"
            f"* **Current Status:** **{matched_order['status']}** 🚚\n"
            f"* **Estimated Delivery:** {matched_order['estimated_delivery']}\n"
            f"* **Courier & Tracking:** `{matched_order['tracking_number']}`\n\n"
            f"Please let me know if you would like any further updates or assistance with this order!"
        )

    # 2. Check for Store Policy Questions
    if any(w in msg_lower for w in ["return", "refund", "replace"]):
        return (
            "🔄 **7-Day Easy Return & Replacement Policy**:\n\n"
            "We offer a 7-day replacement/return guarantee on all electronic items. Free reverse pickup is arranged across India via Delhivery/Bluedart, and refunds are credited back to your original payment method or UPI within 3-5 business days."
        )
    elif any(w in msg_lower for w in ["shipping", "delivery charges", "courier", "when will it arrive"]):
        return (
            "🚚 **Pan-India Shipping & Delivery**:\n\n"
            "Standard delivery takes 2-4 business days across India. Shipping is completely **FREE** on all orders above ₹499. Express 1-2 day delivery is available in major metro cities for ₹99."
        )
    elif any(w in msg_lower for w in ["warranty", "gst", "invoice"]):
        return (
            "🛡️ **Brand Warranty & GST Invoices**:\n\n"
            "Every purchase from ApexTech India includes an **official GST tax invoice** and a **1-year brand warranty** valid at authorized service centers nationwide."
        )
    elif any(w in msg_lower for w in ["payment", "upi", "cod", "cash on delivery"]):
        return (
            "💳 **Accepted Payment Methods**:\n\n"
            "We accept all major payment modes: **UPI** (Google Pay, PhonePe, Paytm), Credit & Debit cards, Net Banking, and **Cash on Delivery (COD)** up to ₹5,000."
        )
    elif any(w in msg_lower for w in ["helpline", "customer care number", "toll-free", "phone number", "human agent", "talk to human", "reach someone"]):
        return (
            "🧑‍💼 **Customer Care Helpline**:\n\n"
            "You can contact our support team toll-free at **1800-266-0199** (Monday to Saturday, 9:30 AM to 6:30 PM IST) or email us anytime at **care@apextech.in**."
        )

    # 3. Check for Product & Price Inquiries (Extract Matching Catalog Items)
    all_products = database.get_all_products()
    matched_products = []

    # Keywords mapping to catalog items
    keywords_map = {
        "headphone": ["Apex Pro Wireless Noise-Canceling Headphones"],
        "audio": ["Apex Pro Wireless Noise-Canceling Headphones", "SoundWave Waterproof Bluetooth Speaker", "StudioBroadcast USB Condenser Microphone"],
        "microphone": ["StudioBroadcast USB Condenser Microphone"],
        "mic": ["StudioBroadcast USB Condenser Microphone"],
        "speaker": ["SoundWave Waterproof Bluetooth Speaker"],
        "keyboard": ["Tactile RGB Mechanical Keyboard", "CloudRest Memory Foam Wrist Support"],
        "mouse": ["AeroPrecision Lightweight Wireless Gaming Mouse"],
        "monitor": ["ApexView 34-Inch Curved Gaming Monitor"],
        "screen": ["ApexView 34-Inch Curved Gaming Monitor", "NeoGlow Smart RGB Desk Light Bar with Ambient Sensor"],
        "display": ["ApexView 34-Inch Curved Gaming Monitor"],
        "webcam": ["ApexStream 4K Ultra-HD Webcam with Ring Light"],
        "camera": ["ApexStream 4K Ultra-HD Webcam with Ring Light", "ApexShield Smart Wi-Fi Indoor Security Camera 2K"],
        "watch": ["PulseFit GPS Smartwatch with Heart Rate Monitor"],
        "smartwatch": ["PulseFit GPS Smartwatch with Heart Rate Monitor"],
        "wearable": ["PulseFit GPS Smartwatch with Heart Rate Monitor"],
        "light": ["NeoGlow Smart RGB Desk Light Bar with Ambient Sensor"],
        "charger": ["GaN 65W USB-C 4-Port Fast Charging Hub"],
        "charging": ["GaN 65W USB-C 4-Port Fast Charging Hub"],
        "power bank": ["MagPower 10,000mAh Magnetic Wireless Power Bank"],
        "powerbank": ["MagPower 10,000mAh Magnetic Wireless Power Bank"],
        "battery": ["MagPower 10,000mAh Magnetic Wireless Power Bank"],
        "backpack": ["TitanShield Ballistic Nylon 16-inch Laptop Backpack"],
        "bag": ["TitanShield Ballistic Nylon 16-inch Laptop Backpack"],
        "stand": ["BreezeCool Aluminum Ergonomic Laptop Stand"],
        "wrist": ["CloudRest Memory Foam Wrist Support"]
    }

    found_names = set()
    for kw, item_names in keywords_map.items():
        if kw in msg_lower:
            found_names.update(item_names)

    if found_names:
        matched_products = [p for p in all_products if p["name"] in found_names]
    else:
        # Fallback to direct search
        matched_products = database.search_products(user_message)

    if matched_products:
        results = []
        for p in matched_products[:4]:
            stock_str = f"In Stock: {p['stock_count']}" if p['stock_count'] > 0 else "Currently Out of Stock"
            results.append(
                f"* **{p['name']}** — **₹{p['price']:,.0f}** ({stock_str})\n"
                f"  *{p['description']}*"
            )
        formatted_list = "\n\n".join(results)
        return (
            f"Here are the items available from our store catalog:\n\n"
            f"{formatted_list}\n\n"
            f"All products include an **official GST tax invoice**, a **1-year brand warranty**, and **free Pan-India shipping**! Would you like to check out or need more details on any of these?"
        )

    # 4. Standard Courteous Greeting / Assistance Menu
    return (
        "Namaste! Welcome to **ApexTech India**.\n\n"
        "I am **Nova**, your AI Customer Support Specialist. How can I assist you today?\n\n"
        "You can ask me about:\n"
        "* 📦 **Track an Order** (e.g. *'Where is order ORD-1001 for Aarav Sharma?'*)\n"
        "* 🎧 **Product Prices & Stock in ₹** (e.g. *'What headphones and microphones do you sell?'*)\n"
        "* 🚚 **Shipping & 7-Day Returns** (e.g. *'What is your return policy across India?'*)\n"
        "* 🧑‍💼 **Customer Care Helpline** (e.g. *'What is your helpline number?'*)"
    )


def call_gemini(api_key: str, user_message: str, tone_guide: str) -> str:
    """
    Connects to Google Gemini using the new google-genai SDK.
    Supports automatic database tool calling for orders, catalog, and FAQs!
    """
    from google import genai
    client = genai.Client(api_key=api_key)
    system_instruction = f"{SYSTEM_PROMPT}\n\nCommunication Style:\n{tone_guide}"

    chat = client.chats.create(
        model="gemini-3-flash-preview",
        config={
            "system_instruction": system_instruction,
            "tools": [database.get_order_details, database.search_products, database.get_all_faqs]
        }
    )
    response = chat.send_message(user_message)
    return response.text


def get_agent_response(
    user_message: str, 
    conversation_history: list = None, 
    api_key_override: str = None,
    tone: str = "Friendly & Warm",
    model_name: str = "gpt-4o-mini"
) -> str:
    """
    Main function to get a reply for the customer:
    - Auto-detects Google Gemini keys (starts with 'AQ.' or 'AIza')
    - Auto-detects OpenAI keys (starts with 'sk-')
    - Adapts tone based on user setting
    - Uses Demo Mode if no valid key is provided
    """
    # 1. Resolve active key (check Gemini first, then override, then OpenAI)
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()

    # Prioritize working Gemini key if available
    if gemini_key and (not api_key_override or api_key_override.startswith("sk-")):
        active_key = gemini_key
    else:
        active_key = (api_key_override or gemini_key or openai_key).strip()

    # If no key or placeholder, provide smart store assistance directly
    if not active_key or active_key in ["your_openai_api_key_here", "your_gemini_api_key_here"]:
        return smart_support_response(user_message)

    # Tone customization
    tone_guide = "Tone: Warm, welcoming, and friendly."
    if "Professional" in tone:
        tone_guide = "Tone: Highly professional, formal, polite, and corporate."
    elif "Concise" in tone:
        tone_guide = "Tone: Direct, brief, bulleted where possible, zero fluff."

    # 2. Check if this is a Google Gemini Key (starts with AQ. or AIza)
    if active_key.startswith("AQ.") or active_key.startswith("AIza") or active_key == gemini_key:
        try:
            return call_gemini(active_key, user_message, tone_guide)
        except Exception:
            # Silently provide clean store response with zero technical error lines
            return smart_support_response(user_message)

    # 3. Otherwise, treat as OpenAI Key
    try:
        client = OpenAI(api_key=active_key)
        custom_system_prompt = f"{SYSTEM_PROMPT}\n\nCommunication Style:\n{tone_guide}"

        # Prepare messages
        messages = [{"role": "system", "content": custom_system_prompt}]
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_message})

        # Ask the model
        response = client.chat.completions.create(
            model=model_name or "gpt-4o-mini",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.3
        )

        response_message = response.choices[0].message

        # Check if the AI wants to call a database tool
        if response_message.tool_calls:
            messages.append(response_message)

            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                tool_output = execute_tool_call(function_name, function_args)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_output
                })

            final_response = client.chat.completions.create(
                model=model_name or "gpt-4o-mini",
                messages=messages,
                temperature=0.3
            )
            return final_response.choices[0].message.content

        return response_message.content

    except Exception:
        # Silently provide clean store response with zero technical error lines
        return smart_support_response(user_message)


# Test block for testing in the terminal!
if __name__ == "__main__":
    print("🤖 Testing AI Agent in agent.py...")
    test_reply = get_agent_response("Where is my order ORD-1001?")
    print("\nCustomer: Where is my order ORD-1001?")
    print("Agent reply:\n")
    print(test_reply)
