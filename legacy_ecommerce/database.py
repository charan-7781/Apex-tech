"""
database.py
-----------
This file manages our e-commerce store's SQLite database.
A database is like an organized Excel spreadsheet stored directly on your computer.

It manages 3 things:
1. Customer Orders (Order ID, customer name, items, delivery status, tracking number)
2. Product Catalog (Product name, category, price, stock quantity, description)
3. Store Policies / FAQs (Return policy, shipping times, warranty)
"""

import sqlite3
import os
import sys

# Ensure emojis and Unicode print cleanly on Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# The name of our local database file
DB_NAME = "ecommerce.db"


def get_connection():
    """Opens a connection to our SQLite database file."""
    conn = sqlite3.connect(DB_NAME)
    # This row_factory setting allows us to access columns by name (like row['status'])
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Creates the tables and populates them with sample store data.
    This runs automatically when the database is first set up.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Table for Customer Orders
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            customer_name TEXT,
            item_name TEXT,
            status TEXT,
            estimated_delivery TEXT,
            tracking_number TEXT
        )
    """)

    # 2. Table for Product Catalog
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id TEXT PRIMARY KEY,
            name TEXT,
            category TEXT,
            price REAL,
            stock_count INTEGER,
            description TEXT
        )
    """)

    # 3. Table for Store Policies and FAQs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS faqs (
            topic TEXT,
            question TEXT,
            answer TEXT
        )
    """)

    # 1. Indian Customer Sample Orders (10 realistic orders across India)
    cursor.execute("DELETE FROM orders")
    sample_orders = [
        ("ORD-1001", "Aarav Sharma", "Apex Pro Wireless Noise-Canceling Headphones", "Shipped", "Tomorrow by 5:00 PM", "BLUEDART-982341"),
        ("ORD-1002", "Priya Patel", "Tactile RGB Mechanical Keyboard", "Processing", "In 3-5 business days", "Pending"),
        ("ORD-1003", "Rohan Mehta", "ApexView 34-Inch Curved Gaming Monitor", "Delivered", "Delivered yesterday at security gate", "DELHIVERY-771290"),
        ("ORD-1004", "Ananya Iyer", "GaN 65W USB-C 4-Port Fast Charging Hub", "Out for Delivery", "Today by 2:00 PM", "XPRESSBEES-445109"),
        ("ORD-1005", "Vikramaditya Singh", "SoundWave Waterproof Bluetooth Speaker", "Shipped", "Friday by 8:00 PM", "BLUEDART-339812"),
        ("ORD-1006", "Sneha Kulkarni", "PulseFit GPS Smartwatch with Heart Rate Monitor", "Out for Delivery", "Today by 6:00 PM", "DELHIVERY-552194"),
        ("ORD-1007", "Arjun Reddy", "ApexStream 4K Ultra-HD Webcam with Ring Light", "Processing", "Estimated Monday by 4:00 PM", "Pending"),
        ("ORD-1008", "Meera Nambiar", "MagPower 10,000mAh Magnetic Wireless Power Bank", "Delivered", "Delivered 2 days ago (Signed by Reception)", "DTDC-881203"),
        ("ORD-1009", "Aditya Verma", "AeroPrecision Lightweight Wireless Gaming Mouse", "Return Requested", "Reverse pickup scheduled via Delhivery", "RET-IN-991044"),
        ("ORD-1010", "Pooja Nair", "ApexShield Smart Wi-Fi Indoor Security Camera 2K", "Shipped", "In transit - Delivery expected Thursday", "BLUEDART-662301")
    ]
    cursor.executemany("""
        INSERT OR REPLACE INTO orders (order_id, customer_name, item_name, status, estimated_delivery, tracking_number)
        VALUES (?, ?, ?, ?, ?, ?)
    """, sample_orders)

    # 2. Expanded Product Catalog with Indian Rupee (₹) Pricing
    cursor.execute("DELETE FROM products")
    sample_products = [
        ("PROD-01", "Apex Pro Wireless Noise-Canceling Headphones", "Audio", 4999.00, 25, "Over-ear Bluetooth 5.3 headphones with hybrid active noise cancellation, 40-hour battery, and memory foam earcups."),
        ("PROD-02", "Tactile RGB Mechanical Keyboard", "Keyboards & Mice", 3499.00, 14, "Hot-swappable mechanical keyboard with silent tactile switches, per-key RGB backlighting, and detachable braided USB-C cable."),
        ("PROD-03", "ApexView 34-Inch Curved Gaming Monitor", "Displays", 28999.00, 6, "Ultra-wide WQHD (3440x1440) 165Hz curved panel with 1ms response time, HDR400, and AMD FreeSync Premium."),
        ("PROD-04", "GaN 65W USB-C 4-Port Fast Charging Hub", "Accessories", 1899.00, 45, "Compact Gallium Nitride wall charger with 2x USB-C Power Delivery ports and 2x USB-A fast charge ports."),
        ("PROD-05", "CloudRest Memory Foam Wrist Support", "Accessories", 699.00, 0, "Ergonomic cooling gel memory foam wrist cushion designed for standard keyboards. (Currently out of stock)"),
        ("PROD-06", "SoundWave Waterproof Bluetooth Speaker", "Audio", 2499.00, 30, "IPX7 waterproof portable speaker with deep bass, 360-degree sound projection, and 16-hour playtime."),
        ("PROD-07", "ApexStream 4K Ultra-HD Webcam with Ring Light", "Video & Streaming", 4299.00, 18, "Professional 4K streaming webcam with built-in adjustable 3-level ring light, dual stereo microphones, and privacy shutter."),
        ("PROD-08", "AeroPrecision Lightweight Wireless Gaming Mouse", "Keyboards & Mice", 2199.00, 22, "Ultra-light 62g ergonomic gaming mouse with 26K DPI optical sensor, optical switches, and 80-hour battery life."),
        ("PROD-09", "PulseFit GPS Smartwatch with Heart Rate Monitor", "Wearables", 5999.00, 3, "AMOLED touch display smartwatch with continuous SpO2 & heart rate monitoring, sleep tracking, 50+ sport modes, and 7-day battery."),
        ("PROD-10", "StudioBroadcast USB Condenser Microphone", "Audio", 3799.00, 11, "Cardioid studio microphone with zero-latency headphone monitoring, tap-to-mute sensor, and heavy metal desktop stand."),
        ("PROD-11", "MagPower 10,000mAh Magnetic Wireless Power Bank", "Accessories", 2299.00, 35, "MagSafe-compatible portable wireless battery pack with 20W PD fast charging and foldable kickstand."),
        ("PROD-12", "NeoGlow Smart RGB Desk Light Bar with Ambient Sensor", "Smart Home", 1999.00, 20, "Eye-care monitor screen light bar with wireless desktop control dial, asymmetrical optical design, and ambient backlight."),
        ("PROD-13", "TitanShield Ballistic Nylon 16-inch Laptop Backpack", "Accessories", 2499.00, 16, "Water-resistant travel backpack with padded 16-inch laptop compartment, hidden anti-theft pocket, and USB charging pass-through."),
        ("PROD-14", "BreezeCool Aluminum Ergonomic Laptop Stand", "Accessories", 1199.00, 28, "Foldable ventilated aluminum alloy riser with 6 adjustable height levels compatible with laptops up to 17 inches."),
        ("PROD-15", "ApexShield Smart Wi-Fi Indoor Security Camera 2K", "Smart Home", 2799.00, 2, "Pan/tilt 360-degree indoor camera with 2K resolution, AI motion & baby cry detection, night vision, and two-way audio.")
    ]
    cursor.executemany("""
        INSERT OR REPLACE INTO products (product_id, name, category, price, stock_count, description)
        VALUES (?, ?, ?, ?, ?, ?)
    """, sample_products)

    # 3. Store Policies / FAQs with Indian Rupee (₹) and Logistics Details
    cursor.execute("DELETE FROM faqs")
    sample_faqs = [
    (
        "Returns & Refunds",
        "What is your return policy?",
        "We offer a 7-day replacement/return guarantee on all electronic items. "
        "Free reverse pickup is arranged across India via Delhivery/Bluedart, "
        "and refunds are processed to your original payment method or UPI "
        "within 3-5 business days."
    ),
    (
        "Shipping & Delivery",
        "How long does shipping take and what are the rates?",
        "Pan-India standard delivery takes 2-4 business days. "
        "Standard shipping is FREE on orders above ₹499. "
        "Orders below ₹499 have a standard shipping fee of ₹50. "
        "Express 1-2 day delivery is available in major metro cities for ₹99."
    ),
    (
        "Product Warranty & GST",
        "Do products include GST invoice and warranty?",
        "Yes! Every order includes an official GST tax invoice. "
        "All electronic items come with a 1-year brand warranty "
        "valid at authorized service centers across India."
    ),
    (
        "Payment Methods",
        "What payment options are available?",
        "We support UPI (Google Pay, PhonePe, Paytm), Credit & Debit cards, "
        "Net Banking, and Cash on Delivery (COD) for orders up to ₹5,000. "
        "The COD handling fee is not specified in our current policy information."
    ),
    (
        "Price Match Guarantee",
        "Do you price match other Indian retailers?",
        "Yes! We match lower advertised prices from authorized Indian "
        "retailers (Amazon India, Flipkart, Croma) within 7 days of your purchase."
    ),
    (
        "Customer Support Contact",
        "How do I speak with a customer care representative?",
        "You can email care@apextech.in or call our toll-free helpline "
        "at 1800-266-0199 Monday to Saturday from 9:30 AM to 6:30 PM IST."
    )
]

    conn.commit()
    conn.close()


def get_order_details(order_id: str):
    """
    Looks up an order by its ID (e.g. 'ORD-1001').
    Returns a dictionary of order details, or None if not found.
    """
    conn = get_connection()
    cursor = conn.cursor()
    # Clean the input (remove extra spaces and make uppercase)
    clean_id = order_id.strip().upper()
    
    cursor.execute("SELECT * FROM orders WHERE UPPER(order_id) = ?", (clean_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def search_products(keyword: str):
    """
    Searches products whose name or description matches the keyword.
    Returns a list of matching product dictionaries.
    """
    conn = get_connection()
    cursor = conn.cursor()
    search_term = f"%{keyword.strip()}%"
    
    cursor.execute("""
        SELECT * FROM products 
        WHERE name LIKE ? OR description LIKE ? OR category LIKE ?
    """, (search_term, search_term, search_term))
    
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_all_faqs():
    """
    Retrieves all store policies and FAQ answers.
    Returns a list of FAQ dictionaries.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM faqs")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
def get_all_orders():
    """Retrieves all orders from the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders ORDER BY order_id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_order_status(order_id: str, new_status: str):
    """Updates the status of an existing order."""
    conn = get_connection()
    cursor = conn.cursor()
    clean_id = order_id.strip().upper()
    cursor.execute("UPDATE orders SET status = ? WHERE UPPER(order_id) = ?", (new_status, clean_id))
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    return rows_affected > 0


def get_all_products():
    """Retrieves all products in the store catalog."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products ORDER BY category, name")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_store_stats():
    """Calculates live summary statistics for the store dashboard."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM orders")
    total_orders = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'Delivered'")
    delivered_orders = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM orders WHERE status IN ('Shipped', 'Out for Delivery', 'Processing')")
    active_shipments = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM products")
    total_products = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM products WHERE stock_count = 0")
    out_of_stock = cursor.fetchone()[0]

    conn.close()
    return {
        "total_orders": total_orders,
        "delivered_orders": delivered_orders,
        "active_shipments": active_shipments,
        "total_products": total_products,
        "out_of_stock": out_of_stock
    }


# This section allows us to test this file directly in the terminal!
if __name__ == "__main__":
    print("📦 Initializing database and adding sample store data...")
    init_db()
    print("✅ Database initialized successfully!")
    
    print("\n🔍 Testing order lookup for 'ORD-1001':")
    sample_order = get_order_details("ORD-1001")
    print(sample_order)

    print("\n🎧 Testing product search for 'Headphones':")
    sample_products = search_products("Headphones")
    print(sample_products)
