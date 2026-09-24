import sqlite3
import os
import json
from datetime import datetime

DB_NAME = os.path.join(os.path.dirname(__file__), 'database.db')

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create Students table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            roll_number TEXT NOT NULL UNIQUE,
            department TEXT,
            semester TEXT,
            phone TEXT,
            student_type TEXT DEFAULT 'Day Scholar',
            address TEXT,
            dietary_pref TEXT DEFAULT 'No Preference',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create Menu Items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS menu_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            rating REAL DEFAULT 4.5,
            is_available INTEGER DEFAULT 1,
            is_veg INTEGER DEFAULT 1,
            image_url TEXT,
            prep_time TEXT DEFAULT '10-15 mins'
        )
    ''')

    # Create Coupons table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS coupons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            description TEXT,
            discount_type TEXT NOT NULL,
            discount_value REAL NOT NULL,
            minimum_order REAL DEFAULT 0,
            maximum_discount REAL DEFAULT 1000,
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create Orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT NOT NULL UNIQUE,
            student_id INTEGER,
            student_name TEXT NOT NULL,
            roll_number TEXT NOT NULL,
            phone TEXT,
            order_type TEXT DEFAULT 'Canteen Pickup',
            pickup_slot TEXT DEFAULT 'Instant Prep',
            delivery_address TEXT,
            payment_method TEXT DEFAULT 'UPI',
            payment_status TEXT DEFAULT 'Paid',
            payment_reference TEXT DEFAULT 'DEMO_REF_1024',
            subtotal REAL NOT NULL,
            discount REAL DEFAULT 0,
            coupon_code TEXT,
            service_fee REAL DEFAULT 5.0,
            total_amount REAL NOT NULL,
            status TEXT DEFAULT 'Pending',
            order_date TEXT,
            order_time TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id)
        )
    ''')

    # Create Order Items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            addons_json TEXT,
            instructions TEXT,
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
        )
    ''')

    # Create Payments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            order_number TEXT NOT NULL,
            student_name TEXT NOT NULL,
            roll_number TEXT NOT NULL,
            payment_method TEXT NOT NULL,
            amount REAL NOT NULL,
            payment_status TEXT DEFAULT 'Paid',
            payment_reference TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
        )
    ''')

    # Create Admin Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')

    # Create Food Reviews table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS food_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            student_name TEXT NOT NULL,
            roll_number TEXT NOT NULL,
            rating INTEGER NOT NULL,
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (item_id) REFERENCES menu_items(id)
        )
    ''')

    # Schema Migrations for existing DB tables
    cursor.execute("PRAGMA table_info(orders)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'payment_status' not in columns:
        cursor.execute("ALTER TABLE orders ADD COLUMN payment_status TEXT DEFAULT 'Paid'")
    if 'payment_reference' not in columns:
        cursor.execute("ALTER TABLE orders ADD COLUMN payment_reference TEXT DEFAULT 'DEMO_REF'")
    if 'coupon_code' not in columns:
        cursor.execute("ALTER TABLE orders ADD COLUMN coupon_code TEXT")
    if 'pickup_slot' not in columns:
        cursor.execute("ALTER TABLE orders ADD COLUMN pickup_slot TEXT DEFAULT 'Instant Prep'")

    cursor.execute("PRAGMA table_info(students)")
    student_cols = [row[1] for row in cursor.fetchall()]
    if 'avatar_url' not in student_cols:
        cursor.execute("ALTER TABLE students ADD COLUMN avatar_url TEXT DEFAULT ''")

    conn.commit()
    conn.close()

    seed_db()

def seed_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Seed Admin User
    cursor.execute("SELECT COUNT(*) FROM admin_users")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO admin_users (username, password) VALUES (?, ?)", ('admin', 'admin123'))

    # Seed Coupons
    cursor.execute("SELECT COUNT(*) FROM coupons")
    if cursor.fetchone()[0] == 0:
        sample_coupons = [
            ("STUDENT10", "Student Special", "Get 10% OFF on all campus orders above ₹100", "percent", 10.0, 100.0, 50.0, 1),
            ("FIRST50", "First Order Offer", "Flat ₹50 OFF on your first canteen order above ₹199", "flat", 50.0, 199.0, 50.0, 1),
            ("SAVE20", "Weekend Feast", "Enjoy 20% OFF on orders above ₹299", "percent", 20.0, 299.0, 100.0, 1),
            ("CANTEEN25", "Mega Campus Savings", "Get 25% OFF on group orders above ₹399", "percent", 25.0, 399.0, 120.0, 1)
        ]
        cursor.executemany('''
            INSERT INTO coupons (code, title, description, discount_type, discount_value, minimum_order, maximum_discount, active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_coupons)

    # Seed 50+ diverse food menu items
    cursor.execute("SELECT COUNT(*) FROM menu_items")
    if cursor.fetchone()[0] < 50:
        cursor.execute("DELETE FROM menu_items") # Clear & reseed complete 52 item list
        sample_menu = [
            ("Veg Deluxe Burger", "Burgers", "Juicy vegetable patty with fresh lettuce, crisp tomatoes & melted cheese.", 60.0, 4.8, 1, 1, "https://images.unsplash.com/photo-1550547660-d9450f859349?w=500&auto=format&fit=crop&q=80", "10-12 mins"),
            ("Crispy Chicken Burger", "Burgers", "Crispy spiced chicken fillet topped with spicy mayo and slaw.", 90.0, 4.9, 1, 0, "https://images.unsplash.com/photo-1615297928064-24977384d0da?w=500&auto=format&fit=crop&q=80", "12-15 mins"),
            ("Double Cheese Beast Burger", "Burgers", "Loaded double patty burger infused with jalapenos & double cheddar cheese.", 110.0, 4.9, 1, 1, "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=500&auto=format&fit=crop&q=80", "12-15 mins"),
            ("Paneer Tikka Burger", "Burgers", "Spiced grilled paneer patty with mint chutney Mayo and crunchy onions.", 85.0, 4.7, 1, 1, "https://images.unsplash.com/photo-1586190848861-99aa4a171e90?w=500&auto=format&fit=crop&q=80", "10-12 mins"),
            ("Spicy Zinger Burger", "Burgers", "Fiery Schezwan spiced chicken burger with extra crispy lettuce.", 95.0, 4.8, 1, 0, "https://images.unsplash.com/photo-1572802419224-296b0aeee0d9?w=500&auto=format&fit=crop&q=80", "12-15 mins"),
            
            ("Margherita Pizza", "Pizza", "Classic mozzarella cheese, fresh basil, and signature tangy tomato sauce.", 140.0, 4.7, 1, 1, "https://images.unsplash.com/photo-1604382354936-07c5d9983bd3?w=500&auto=format&fit=crop&q=80", "15-20 mins"),
            ("Farmhouse Special Pizza", "Pizza", "Loaded with capsicum, sweet corn, mushrooms, olives & double cheese.", 180.0, 4.8, 1, 1, "https://images.unsplash.com/photo-1534308983496-4fabb1a015ee?w=500&auto=format&fit=crop&q=80", "15-20 mins"),
            ("Pepperoni Paradise Pizza", "Pizza", "Rich pepperoni slices layered over melted mozzarella and herbs.", 210.0, 4.9, 1, 0, "https://images.unsplash.com/photo-1628840042765-356cda07504e?w=500&auto=format&fit=crop&q=80", "15-20 mins"),
            ("Paneer Makhani Pizza", "Pizza", "Creamy butter masala sauce topped with cottage cheese & diced capsicum.", 195.0, 4.8, 1, 1, "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=500&auto=format&fit=crop&q=80", "15-20 mins"),
            ("Cheese Burst Corn Pizza", "Pizza", "Oozy liquid cheese stuffed crust loaded with golden sweet corn.", 160.0, 4.7, 1, 1, "https://images.unsplash.com/photo-1574071318508-1cdbab80d002?w=500&auto=format&fit=crop&q=80", "15-20 mins"),
            
            ("Paneer Tikka Roll", "Rolls", "Grilled spiced paneer cubes wrapped in whole wheat laccha paratha.", 70.0, 4.7, 1, 1, "https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?w=500&auto=format&fit=crop&q=80", "8-10 mins"),
            ("Egg Roll Double", "Rolls", "Double egg wrap infused with chopped onions, green chillies & tangy sauce.", 50.0, 4.5, 1, 0, "https://images.unsplash.com/photo-1565299585323-38d6b0865b47?w=500&auto=format&fit=crop&q=80", "5-8 mins"),
            ("Chicken Kathi Wrap", "Rolls", "Juicy tandoori chicken chunks wrapped with pickled onions & mint dip.", 85.0, 4.8, 1, 0, "https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?w=500&auto=format&fit=crop&q=80", "8-10 mins"),
            ("Veg Falafel Wrap", "Rolls", "Crispy chickpea falafel balls with hummus, lettuce & garlic sauce.", 65.0, 4.6, 1, 1, "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=500&auto=format&fit=crop&q=80", "8-10 mins"),
            ("Cheese Corn Roll", "Rolls", "Melted cheese & sweet corn wrapped in a crispy golden roll.", 60.0, 4.5, 1, 1, "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=500&auto=format&fit=crop&q=80", "6-8 mins"),

            ("Hakka Veg Noodles", "Noodles", "Wok-tossed stir fry noodles with colorful bell peppers and spring onion.", 80.0, 4.6, 1, 1, "https://images.unsplash.com/photo-1585032226651-759b368d7246?w=500&auto=format&fit=crop&q=80", "10-12 mins"),
            ("Schezwan Chicken Noodles", "Noodles", "Fiery Schezwan style fried noodles with shredded chicken & veggies.", 110.0, 4.8, 1, 0, "https://images.unsplash.com/photo-1612927601601-6638404737ce?w=500&auto=format&fit=crop&q=80", "12-15 mins"),
            ("Veg Fried Rice", "Noodles", "Classic wok-fried rice cooked with finely chopped vegetables & soy sauce.", 75.0, 4.5, 1, 1, "https://images.unsplash.com/photo-1603133872878-684f208fb84b?w=500&auto=format&fit=crop&q=80", "10-12 mins"),
            ("Chilli Paneer Gravy", "Noodles", "Soft paneer cubes tossed in spicy chilli garlic soya gravy with noodles.", 120.0, 4.7, 1, 1, "https://images.unsplash.com/photo-1567620832903-9fc6debc209f?w=500&auto=format&fit=crop&q=80", "12-15 mins"),
            ("Crispy Veg Manchurian", "Noodles", "Deep fried vegetable balls coated in tangy Schezwan soya sauce.", 95.0, 4.6, 1, 1, "https://images.unsplash.com/photo-1525755662778-989d0524087e?w=500&auto=format&fit=crop&q=80", "10-12 mins"),

            ("North Indian Thali", "Meals", "2 Butter Roti, Paneer Butter Masala, Dal Tadka, Jeera Rice & Gulab Jamun.", 130.0, 4.9, 1, 1, "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=500&auto=format&fit=crop&q=80", "10-15 mins"),
            ("Chicken Biryani Special", "Meals", "Aromatic basmati rice cooked with tender spiced chicken pieces & raita.", 150.0, 4.9, 1, 0, "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500&auto=format&fit=crop&q=80", "10-15 mins"),
            ("Paneer Butter Masala Combo", "Meals", "Rich cottage cheese gravy served with 2 Garlic Naan & Salad.", 140.0, 4.8, 1, 1, "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=500&auto=format&fit=crop&q=80", "12-15 mins"),
            ("Rajma Chawal Bowl", "Meals", "Home-style Punjabi Rajma gravy served over piping hot Basmati Rice.", 85.0, 4.7, 1, 1, "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=500&auto=format&fit=crop&q=80", "8-10 mins"),
            ("Chole Rice Bowl", "Meals", "Spiced Amritsari Chole served with fragrant Jeera Rice & fried chilli.", 85.0, 4.7, 1, 1, "https://images.unsplash.com/photo-1588166524941-3bf61a9c41db?w=500&auto=format&fit=crop&q=80", "8-10 mins"),
            ("Veg Dum Biryani", "Meals", "Layered dum cooked basmati rice with mixed vegetables & saffron aroma.", 120.0, 4.6, 1, 1, "https://images.unsplash.com/photo-1633945274405-b6c8069047b0?w=500&auto=format&fit=crop&q=80", "12-15 mins"),

            ("Masala Dosa Special", "Breakfast", "Crispy golden rice crepe filled with spiced potato masala & sambhar.", 75.0, 4.8, 1, 1, "https://images.unsplash.com/photo-1668236543090-82eba5ee5976?w=500&auto=format&fit=crop&q=80", "8-10 mins"),
            ("Steamed Idli Sambhar", "Breakfast", "Soft fluffy steamed rice cakes served with hot lentil sambhar & coconut chutney.", 45.0, 4.6, 1, 1, "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=500&auto=format&fit=crop&q=80", "5-7 mins"),
            ("Puri Bhaji Plate", "Breakfast", "3 deep fried puffed puris served with spicy potato bhaji & pickle.", 55.0, 4.5, 1, 1, "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=500&auto=format&fit=crop&q=80", "8-10 mins"),
            ("Grilled Veg Sandwich", "Breakfast", "Triple decker toasted sandwich filled with cucumber, tomato, cheese & green chutney.", 50.0, 4.5, 1, 1, "https://images.unsplash.com/photo-1528735602780-2552fd46c7af?w=500&auto=format&fit=crop&q=80", "5-8 mins"),
            ("Aloo Paratha with Butter", "Breakfast", "Whole wheat stuffed potato paratha topped with white butter & curd.", 60.0, 4.8, 1, 1, "https://images.unsplash.com/photo-1626074353765-517a681e40be?w=500&auto=format&fit=crop&q=80", "8-10 mins"),
            ("Indori Poha with Sev", "Breakfast", "Steamed flattened rice seasoned with mustard seeds, turmeric & crunchy ratlami sev.", 35.0, 4.6, 1, 1, "https://images.unsplash.com/photo-1606491956689-2ea866880c84?w=500&auto=format&fit=crop&q=80", "3-5 mins"),
            ("Chole Bhature (2 Pcs)", "Breakfast", "Fluffy puffed fried bhaturas served with spicy chickpeas & pickled onion.", 80.0, 4.8, 1, 1, "https://images.unsplash.com/photo-1626132647523-66f5bf380027?w=500&auto=format&fit=crop&q=80", "10-12 mins"),

            ("Cheese Garlic Bread", "Snacks", "Toasted baguette slices topped with herbs, garlic butter and oozy mozzarella.", 65.0, 4.6, 1, 1, "https://images.unsplash.com/photo-1573140247632-f8fd74997d5c?w=500&auto=format&fit=crop&q=80", "8-10 mins"),
            ("Crispy Peri-Peri Fries", "Snacks", "Golden salted potato fries served with peri-peri seasoning and dip.", 50.0, 4.4, 1, 1, "https://images.unsplash.com/photo-1576107232684-1279f3908594?w=500&auto=format&fit=crop&q=80", "5-7 mins"),
            ("Samosa Chaat Special", "Snacks", "Crushed potato samosas topped with chole, curd, sweet tamarind & green chutney.", 40.0, 4.7, 1, 1, "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=500&auto=format&fit=crop&q=80", "5-7 mins"),
            ("Cheese Corn Balls", "Snacks", "Crispy fried golden spheres stuffed with melted cheese & corn kernels.", 75.0, 4.6, 1, 1, "https://images.unsplash.com/photo-1541592106381-b31e9677c0e5?w=500&auto=format&fit=crop&q=80", "8-10 mins"),
            ("Crispy Steamed Momos", "Snacks", "Steamed veg dumplings served with spicy red Schezwan dip & mayonnaise.", 60.0, 4.7, 1, 1, "https://images.unsplash.com/photo-1625220194771-7ebdea0b70b9?w=500&auto=format&fit=crop&q=80", "8-10 mins"),
            ("Fried Paneer Momos", "Snacks", "Deep fried crispy momos stuffed with paneer & herbs.", 80.0, 4.8, 1, 1, "https://images.unsplash.com/photo-1534422298391-e4f8c172dddb?w=500&auto=format&fit=crop&q=80", "8-10 mins"),
            ("Veg Spring Rolls", "Snacks", "Crispy fried roll sheets loaded with shredded vegetables & dip.", 70.0, 4.5, 1, 1, "https://images.unsplash.com/photo-1544025162-d76694265947?w=500&auto=format&fit=crop&q=80", "6-8 mins"),

            ("Cold Coffee Float", "Drinks", "Rich blended iced espresso topped with a scoop of creamy vanilla ice cream.", 45.0, 4.8, 1, 1, "https://images.unsplash.com/photo-1517701604599-bb29b565090c?w=500&auto=format&fit=crop&q=80", "3-5 mins"),
            ("Fresh Mango Smoothie", "Drinks", "Thick mango puree blended with chilled milk and crushed ice.", 40.0, 4.7, 1, 1, "https://images.unsplash.com/photo-1553530666-ba11a7da3888?w=500&auto=format&fit=crop&q=80", "3-5 mins"),
            ("Iced Lemon Tea", "Drinks", "Refreshing chilled black tea infused with lemon juice & fresh mint.", 35.0, 4.5, 1, 1, "https://images.unsplash.com/photo-1556679343-c7306c1976bc?w=500&auto=format&fit=crop&q=80", "2-4 mins"),
            ("Oreo Thick Shake", "Drinks", "Blended rich chocolate milk with crunchy crushed Oreo biscuits.", 65.0, 4.8, 1, 1, "https://images.unsplash.com/photo-1572490122747-3968b75cc699?w=500&auto=format&fit=crop&q=80", "4-6 mins"),
            ("KitKat Milkshake", "Drinks", "Creamy chocolate shake topped with crispy KitKat fingers & whipped cream.", 70.0, 4.9, 1, 1, "https://images.unsplash.com/photo-1541658016709-82535e94bc69?w=500&auto=format&fit=crop&q=80", "4-6 mins"),
            ("Masala Cutting Chai", "Drinks", "Hot brewed Indian tea infused with cardamom, ginger & spices.", 20.0, 4.9, 1, 1, "https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=500&auto=format&fit=crop&q=80", "2-3 mins"),
            ("Virgin Mojito Mocktail", "Drinks", "Fizzy lime and mint cooler with crushed ice & lemon slices.", 55.0, 4.6, 1, 1, "https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?w=500&auto=format&fit=crop&q=80", "3-5 mins"),

            ("Sizzling Chocolate Brownie", "Desserts", "Warm gooey fudge brownie served with vanilla scoop & hot fudge drizzle.", 75.0, 4.9, 1, 1, "https://images.unsplash.com/photo-1606313564200-e75d5e30476c?w=500&auto=format&fit=crop&q=80", "5-7 mins"),
            ("Gulab Jamun (2 Pcs)", "Desserts", "Warm soft fried milk solid balls soaked in cardamom sugar syrup.", 35.0, 4.7, 1, 1, "https://images.unsplash.com/photo-1599785209707-a456fc1337bb?w=500&auto=format&fit=crop&q=80", "2-3 mins"),
            ("Choco Lava Cake", "Desserts", "Warm chocolate sponge cake with gooey molten chocolate center.", 60.0, 4.8, 1, 1, "https://images.unsplash.com/photo-1606313564200-e75d5e30476c?w=500&auto=format&fit=crop&q=80", "5-7 mins"),
            ("Red Velvet Cupcake", "Desserts", "Moist red velvet sponge topped with rich cream cheese frosting.", 45.0, 4.6, 1, 1, "https://images.unsplash.com/photo-1614707267537-b85aaf00c4b7?w=500&auto=format&fit=crop&q=80", "2-3 mins"),
            ("Vanilla Ice Cream Scoop", "Desserts", "Classic smooth Madagascar vanilla bean ice cream scoop.", 30.0, 4.5, 1, 1, "https://images.unsplash.com/photo-1570197788417-0e82375c9371?w=500&auto=format&fit=crop&q=80", "2-3 mins")
        ]
        cursor.executemany('''
            INSERT INTO menu_items (name, category, description, price, rating, is_available, is_veg, image_url, prep_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_menu)

    # Seed sample order
    cursor.execute("SELECT COUNT(*) FROM orders")
    if cursor.fetchone()[0] == 0:
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%I:%M %p")

        cursor.execute('''
            INSERT INTO students (name, roll_number, department, semester, phone, student_type, address, dietary_pref)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('Raj Kumar', 'CSE001', 'Computer Science & Engineering', '3rd Semester', '+91 9876543210', 'Hostel', 'Hostel Block B, Room 302', 'Vegetarian'))
        student_id = cursor.lastrowid

        cursor.execute('''
            INSERT INTO orders (order_number, student_id, student_name, roll_number, phone, order_type, pickup_slot, delivery_address, payment_method, payment_status, payment_reference, subtotal, discount, coupon_code, service_fee, total_amount, status, order_date, order_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('SC1024', student_id, 'Raj Kumar', 'CSE001', '+91 9876543210', 'Canteen Pickup', 'Instant Prep (10-15 min)', 'Main Canteen Counter', 'UPI', 'Paid', 'DEMO_UPI_98765', 120.0, 10.0, 'STUDENT10', 5.0, 115.0, 'Preparing', date_str, time_str))
        order_id = cursor.lastrowid

        cursor.execute('''
            INSERT INTO order_items (order_id, item_id, item_name, price, quantity, addons_json, instructions)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (order_id, 1, 'Veg Deluxe Burger', 60.0, 2, '["Extra Cheese"]', 'Extra crispy patty please'))

        cursor.execute('''
            INSERT INTO payments (order_id, order_number, student_name, roll_number, payment_method, amount, payment_status, payment_reference)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (order_id, 'SC1024', 'Raj Kumar', 'CSE001', 'UPI', 115.0, 'Paid', 'DEMO_UPI_98765'))

    conn.commit()
    conn.close()

# --- Helper Query Functions ---

def get_student_by_roll(roll_number):
    conn = get_db_connection()
    student = conn.execute("SELECT * FROM students WHERE roll_number = ?", (roll_number,)).fetchone()
    conn.close()
    return student

def save_student(name, roll_number, department, semester, phone, student_type, address, dietary_pref, avatar_url=''):
    conn = get_db_connection()
    cursor = conn.cursor()
    existing = cursor.execute("SELECT id FROM students WHERE roll_number = ?", (roll_number,)).fetchone()
    if existing:
        cursor.execute('''
            UPDATE students
            SET name = ?, department = ?, semester = ?, phone = ?, student_type = ?, address = ?, dietary_pref = ?, avatar_url = ?
            WHERE roll_number = ?
        ''', (name, department, semester, phone, student_type, address, dietary_pref, avatar_url, roll_number))
        student_id = existing['id']
    else:
        cursor.execute('''
            INSERT INTO students (name, roll_number, department, semester, phone, student_type, address, dietary_pref, avatar_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, roll_number, department, semester, phone, student_type, address, dietary_pref, avatar_url))
        student_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return student_id

def get_menu_items(category=None, search=None, veg_only=False):
    conn = get_db_connection()
    query = "SELECT * FROM menu_items WHERE 1=1"
    params = []

    if category and category != 'All':
        query += " AND category = ?"
        params.append(category)

    if search:
        query += " AND (name LIKE ? OR description LIKE ?)"
        params.append(f'%{search}%')
        params.append(f'%{search}%')

    if veg_only:
        query += " AND is_veg = 1"

    query += " ORDER BY id ASC"
    items = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(item) for item in items]

def get_menu_item_by_id(item_id):
    conn = get_db_connection()
    item = conn.execute("SELECT * FROM menu_items WHERE id = ?", (item_id,)).fetchone()
    conn.close()
    return dict(item) if item else None

def add_menu_item(name, category, description, price, rating, is_available, is_veg, image_url, prep_time):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO menu_items (name, category, description, price, rating, is_available, is_veg, image_url, prep_time)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, category, description, float(price), float(rating), int(is_available), int(is_veg), image_url, prep_time))
    item_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return item_id

def update_menu_item(item_id, name, category, description, price, rating, is_available, is_veg, image_url, prep_time):
    conn = get_db_connection()
    conn.execute('''
        UPDATE menu_items
        SET name = ?, category = ?, description = ?, price = ?, rating = ?, is_available = ?, is_veg = ?, image_url = ?, prep_time = ?
        WHERE id = ?
    ''', (name, category, description, float(price), float(rating), int(is_available), int(is_veg), image_url, prep_time, item_id))
    conn.commit()
    conn.close()

def delete_menu_item(item_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM menu_items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()

def toggle_menu_item_availability(item_id):
    conn = get_db_connection()
    conn.execute("UPDATE menu_items SET is_available = CASE WHEN is_available = 1 THEN 0 ELSE 1 END WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()

# --- COUPONS FUNCTIONS ---

def get_active_coupons():
    conn = get_db_connection()
    coupons = conn.execute("SELECT * FROM coupons WHERE active = 1 ORDER BY id ASC").fetchall()
    conn.close()
    return [dict(c) for c in coupons]

def get_all_coupons():
    conn = get_db_connection()
    coupons = conn.execute("SELECT * FROM coupons ORDER BY id ASC").fetchall()
    conn.close()
    return [dict(c) for c in coupons]

def validate_coupon(code, cart_subtotal):
    conn = get_db_connection()
    coupon = conn.execute("SELECT * FROM coupons WHERE UPPER(code) = UPPER(?)", (code,)).fetchone()
    conn.close()

    if not coupon:
        return {'valid': False, 'message': 'Invalid coupon code'}
    
    c = dict(coupon)
    if not c['active']:
        return {'valid': False, 'message': 'This coupon is no longer active'}

    if cart_subtotal < c['minimum_order']:
        return {'valid': False, 'message': f"Minimum order value for {c['code']} is ₹{c['minimum_order']:.0f}"}

    if c['discount_type'] == 'percent':
        calculated_discount = (c['discount_value'] / 100.0) * cart_subtotal
        discount_amount = min(calculated_discount, c['maximum_discount'])
    else:
        discount_amount = min(c['discount_value'], cart_subtotal)

    return {
        'valid': True,
        'code': c['code'],
        'title': c['title'],
        'discount_amount': round(discount_amount, 2),
        'message': f"Coupon {c['code']} applied! You saved ₹{discount_amount:.0f}"
    }

def add_coupon(code, title, description, discount_type, discount_value, minimum_order, maximum_discount, active=1):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO coupons (code, title, description, discount_type, discount_value, minimum_order, maximum_discount, active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (code.upper(), title, description, discount_type, float(discount_value), float(minimum_order), float(maximum_discount), int(active)))
    coupon_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return coupon_id

def toggle_coupon_active(coupon_id):
    conn = get_db_connection()
    conn.execute("UPDATE coupons SET active = CASE WHEN active = 1 THEN 0 ELSE 1 END WHERE id = ?", (coupon_id,))
    conn.commit()
    conn.close()

def delete_coupon(coupon_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM coupons WHERE id = ?", (coupon_id,))
    conn.commit()
    conn.close()

# --- ORDERS & PAYMENTS ---

def create_order(student_name, roll_number, phone, order_type, delivery_address, payment_method, cart_items, discount_amount=0, coupon_code='', payment_reference='DEMO_REF', pickup_slot='Instant Prep (10-15 min)'):
    conn = get_db_connection()
    cursor = conn.cursor()

    subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
    service_fee = 5.0
    total_amount = max(0.0, subtotal - float(discount_amount) + service_fee)

    cursor.execute("SELECT MAX(id) FROM orders")
    max_id = cursor.fetchone()[0] or 1023
    order_number = f"SC{max_id + 1}"

    now = datetime.now()
    order_date = now.strftime("%Y-%m-%d")
    order_time = now.strftime("%I:%M %p")

    student = get_student_by_roll(roll_number)
    student_id = student['id'] if student else None
    payment_status = 'Paid' if payment_method != 'Cash at Canteen' else 'Pending'

    cursor.execute('''
        INSERT INTO orders (order_number, student_id, student_name, roll_number, phone, order_type, pickup_slot, delivery_address, payment_method, payment_status, payment_reference, subtotal, discount, coupon_code, service_fee, total_amount, status, order_date, order_time)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending', ?, ?)
    ''', (order_number, student_id, student_name, roll_number, phone, order_type, pickup_slot, delivery_address, payment_method, payment_status, payment_reference, subtotal, discount_amount, coupon_code, service_fee, total_amount, order_date, order_time))

    order_id = cursor.lastrowid

    for item in cart_items:
        addons = json.dumps(item.get('addons', []))
        instructions = item.get('instructions', '')
        cursor.execute('''
            INSERT INTO order_items (order_id, item_id, item_name, price, quantity, addons_json, instructions)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (order_id, item['id'], item['name'], item['price'], item['quantity'], addons, instructions))

    cursor.execute('''
        INSERT INTO payments (order_id, order_number, student_name, roll_number, payment_method, amount, payment_status, payment_reference)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (order_id, order_number, student_name, roll_number, payment_method, total_amount, payment_status, payment_reference))

    conn.commit()
    conn.close()
    return order_id, order_number

def get_student_orders(roll_number):
    conn = get_db_connection()
    orders = conn.execute("SELECT * FROM orders WHERE roll_number = ? ORDER BY id DESC", (roll_number,)).fetchall()
    result = []
    for order in orders:
        o = dict(order)
        items = conn.execute("SELECT * FROM order_items WHERE order_id = ?", (o['id'],)).fetchall()
        o['items'] = [dict(i) for i in items]
        result.append(o)
    conn.close()
    return result

def get_order_by_id(order_id):
    conn = get_db_connection()
    order = conn.execute("SELECT * FROM orders WHERE id = ? OR order_number = ?", (order_id, str(order_id))).fetchone()
    if not order:
        conn.close()
        return None
    o = dict(order)
    items = conn.execute("SELECT * FROM order_items WHERE order_id = ?", (o['id'],)).fetchall()
    o['items'] = []
    for item in items:
        it = dict(item)
        it['addons'] = json.loads(it['addons_json']) if it['addons_json'] else []
        o['items'].append(it)
    conn.close()
    return o

def get_all_orders(status_filter=None):
    conn = get_db_connection()
    query = "SELECT * FROM orders WHERE 1=1"
    params = []
    if status_filter and status_filter != 'All':
        query += " AND status = ?"
        params.append(status_filter)
    query += " ORDER BY id DESC"
    orders = conn.execute(query, params).fetchall()
    result = []
    for order in orders:
        o = dict(order)
        items = conn.execute("SELECT * FROM order_items WHERE order_id = ?", (o['id'],)).fetchall()
        o['items'] = [dict(i) for i in items]
        result.append(o)
    conn.close()
    return result

def get_kitchen_orders():
    conn = get_db_connection()
    orders = conn.execute("SELECT * FROM orders WHERE status IN ('Pending', 'Preparing') ORDER BY id ASC").fetchall()
    result = []
    for order in orders:
        o = dict(order)
        items = conn.execute("SELECT * FROM order_items WHERE order_id = ?", (o['id'],)).fetchall()
        o['items'] = [dict(i) for i in items]
        result.append(o)
    conn.close()
    return result

def get_live_counter_orders():
    conn = get_db_connection()
    preparing = conn.execute("SELECT order_number, status FROM orders WHERE status = 'Preparing' ORDER BY id DESC LIMIT 10").fetchall()
    ready = conn.execute("SELECT order_number, status FROM orders WHERE status = 'Ready' ORDER BY id DESC LIMIT 10").fetchall()
    conn.close()
    return {
        'preparing': [p['order_number'] for p in preparing],
        'ready': [r['order_number'] for r in ready]
    }

def update_order_status(order_id, new_status):
    conn = get_db_connection()
    conn.execute("UPDATE orders SET status = ? WHERE id = ? OR order_number = ?", (new_status, order_id, str(order_id)))
    if new_status == 'Completed':
        conn.execute("UPDATE orders SET payment_status = 'Paid' WHERE id = ? OR order_number = ?", (order_id, str(order_id)))
        conn.execute("UPDATE payments SET payment_status = 'Paid' WHERE order_id = ? OR order_number = ?", (order_id, str(order_id)))
    conn.commit()
    conn.close()

def get_all_payments():
    conn = get_db_connection()
    payments = conn.execute("SELECT * FROM payments ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(p) for p in payments]

def get_registered_students(search=None):
    conn = get_db_connection()
    query = "SELECT s.*, COUNT(o.id) as total_orders, MAX(o.created_at) as last_order FROM students s LEFT JOIN orders o ON s.roll_number = o.roll_number"
    params = []
    if search:
        query += " WHERE s.name LIKE ? OR s.roll_number LIKE ? OR s.department LIKE ?"
        params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
    query += " GROUP BY s.id ORDER BY s.id DESC"
    students = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(s) for s in students]

def get_admin_stats():
    conn = get_db_connection()
    total_orders = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    pending_orders = conn.execute("SELECT COUNT(*) FROM orders WHERE status IN ('Pending', 'Preparing')").fetchone()[0]
    completed_orders = conn.execute("SELECT COUNT(*) FROM orders WHERE status = 'Completed'").fetchone()[0]
    total_students = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    today_revenue = conn.execute("SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE status != 'Cancelled'").fetchone()[0]
    conn.close()
    return {
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
        'total_students': total_students,
        'today_revenue': round(today_revenue, 2)
    }

def verify_admin_login(username, password):
    conn = get_db_connection()
    admin = conn.execute("SELECT * FROM admin_users WHERE username = ? AND password = ?", (username, password)).fetchone()
    conn.close()
    return admin is not None

def add_food_review(item_id, student_name, roll_number, rating, comment):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO food_reviews (item_id, student_name, roll_number, rating, comment)
        VALUES (?, ?, ?, ?, ?)
    ''', (item_id, student_name, roll_number, int(rating), comment))
    conn.commit()
    conn.close()

def get_food_reviews(item_id):
    conn = get_db_connection()
    reviews = conn.execute("SELECT * FROM food_reviews WHERE item_id = ? ORDER BY id DESC", (item_id,)).fetchall()
    conn.close()
    return [dict(r) for r in reviews]

def get_top_foodies_leaderboard():
    conn = get_db_connection()
    query = '''
        SELECT s.name, s.roll_number, s.department, s.avatar_url,
               COUNT(o.id) as total_orders,
               COALESCE(SUM(o.total_amount), 0) as total_spent
        FROM students s
        LEFT JOIN orders o ON s.roll_number = o.roll_number
        GROUP BY s.id
        ORDER BY total_orders DESC, total_spent DESC
        LIMIT 10
    '''
    foodies = conn.execute(query).fetchall()
    conn.close()
    return [dict(f) for f in foodies]
