from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import database
import random
import os
import re
import hmac
import hashlib
from datetime import datetime
from config import Config

try:
    import razorpay
    razorpay_client = razorpay.Client(auth=(Config.RAZORPAY_KEY_ID, Config.RAZORPAY_KEY_SECRET))
except Exception:
    razorpay_client = None

app = Flask(__name__)
app.config.from_object(Config)

# Auto-initialize DB for WSGI / Gunicorn Cloud deployment
try:
    database.init_db()
except Exception as e:
    print("Database initialization on import:", e)

@app.before_request
def setup_db():
    if not hasattr(app, 'db_initialized'):
        database.init_db()
        app.db_initialized = True

def is_student_logged_in():
    return 'student_roll' in session and session['student_roll']

def is_admin_logged_in():
    return session.get('admin_logged_in', False)

def get_cart_summary():
    cart = session.get('cart', [])
    total_count = sum(item['quantity'] for item in cart)
    subtotal = sum(item['price'] * item['quantity'] for item in cart)
    return cart, total_count, round(subtotal, 2)

# --- STUDENT ROUTES ---

@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if is_student_logged_in():
        student = database.get_student_by_roll(session['student_roll'])
        if student and student['department']:
            return redirect(url_for('home'))
        return redirect(url_for('student_details'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        roll_number = request.form.get('roll_number', '').strip().upper()

        if not name or not roll_number:
            flash('Please enter both Name and Roll Number.', 'danger')
            return render_template('login.html')

        session['student_name'] = name
        session['student_roll'] = roll_number
        if 'cart' not in session:
            session['cart'] = []

        student = database.get_student_by_roll(roll_number)
        if student and student['department']:
            return redirect(url_for('home'))
        else:
            database.save_student(name, roll_number, '', '', '', 'Day Scholar', '', 'No Preference')
            return redirect(url_for('student_details'))

    return render_template('login.html')

@app.route('/student-details', methods=['GET', 'POST'])
def student_details():
    if not is_student_logged_in():
        return redirect(url_for('login'))

    roll_number = session['student_roll']
    student = database.get_student_by_roll(roll_number)

    if request.method == 'POST':
        name = request.form.get('name', session.get('student_name', ''))
        department = request.form.get('department', '')
        semester = request.form.get('semester', '')
        phone = request.form.get('phone', '')
        student_type = request.form.get('student_type', 'Day Scholar')
        address = request.form.get('address', '')
        dietary_pref = request.form.get('dietary_pref', 'No Preference')
        avatar_url = request.form.get('avatar_url', '')

        database.save_student(name, roll_number, department, semester, phone, student_type, address, dietary_pref, avatar_url)
        session['student_name'] = name
        flash('Profile & Avatar updated successfully!', 'success')
        return redirect(url_for('home'))

    return render_template('student_details.html', student=student, session_name=session.get('student_name'), session_roll=roll_number)

@app.route('/home')
def home():
    if not is_student_logged_in():
        return redirect(url_for('login'))

    roll_number = session['student_roll']
    student = database.get_student_by_roll(roll_number)

    hour = datetime.now().hour
    if 5 <= hour < 11:
        time_greeting = "Morning Energy 🥐"
        time_sub = "Fresh Idli, Samosa, Poha & Hot Chai ready!"
    elif 11 <= hour < 16:
        time_greeting = "Lunch Time 🍛"
        time_sub = "Hot North Indian Thali & Biryani special"
    else:
        time_greeting = "Canteen Charcha ☕"
        time_sub = "Crispy French Fries, Burgers & Shakes"
    
    categories = [
        {'name': 'Burgers', 'icon': '🍔'},
        {'name': 'Pizza', 'icon': '🍕'},
        {'name': 'Rolls', 'icon': '🌯'},
        {'name': 'Noodles', 'icon': '🍜'},
        {'name': 'Meals', 'icon': '🍛'},
        {'name': 'Snacks', 'icon': '🥪'},
        {'name': 'Drinks', 'icon': '🥤'},
        {'name': 'Desserts', 'icon': '🍰'}
    ]

    popular_items = database.get_menu_items()[:8]
    active_coupons = database.get_active_coupons()
    
    student_orders = database.get_student_orders(roll_number)
    last_order = student_orders[0] if student_orders else None

    _, cart_count, _ = get_cart_summary()

    return render_template('index.html', student=student, time_greeting=time_greeting, time_sub=time_sub, categories=categories, popular_items=popular_items, coupons=active_coupons, last_order=last_order, cart_count=cart_count)

@app.route('/reorder/<int:order_id>')
def reorder(order_id):
    if not is_student_logged_in():
        return redirect(url_for('login'))

    order = database.get_order_by_id(order_id)
    if not order:
        flash('Order not found.', 'danger')
        return redirect(url_for('home'))

    cart = []
    for item in order['items']:
        menu_item = database.get_menu_item_by_id(item['item_id'])
        img = menu_item['image_url'] if menu_item else 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=500&auto=format&fit=crop&q=80'
        cart.append({
            'id': item['item_id'],
            'name': item['item_name'],
            'price': item['price'],
            'quantity': item['quantity'],
            'image_url': img,
            'addons': item.get('addons', []),
            'instructions': item.get('instructions', '')
        })

    session['cart'] = cart
    flash(f"Re-ordered items from #{order['order_number']} added to cart!", 'success')
    return redirect(url_for('cart'))

@app.route('/menu')
def menu():
    if not is_student_logged_in():
        return redirect(url_for('login'))

    selected_category = request.args.get('category', 'All')
    search_query = request.args.get('search', '')
    veg_only = request.args.get('veg', '0') == '1'
    filter_pill = request.args.get('pill', 'all')

    all_items = database.get_menu_items(category=selected_category, search=search_query, veg_only=veg_only)
    
    # Filter pill logic
    items = []
    if filter_pill == 'under50':
        items = [i for i in all_items if i['price'] <= 50]
    elif filter_pill == 'protein':
        items = [i for i in all_items if any(k in i['name'].lower() or k in (i['description'] or '').lower() for k in ['paneer', 'chicken', 'egg', 'thali'])]
    elif filter_pill == 'jain':
        items = [i for i in all_items if i['is_veg'] == 1 and 'onion' not in (i['description'] or '').lower()]
    elif filter_pill == 'spicy':
        items = [i for i in all_items if any(k in i['name'].lower() or k in (i['description'] or '').lower() for k in ['schezwan', 'spicy', 'crispy', 'tikka'])]
    else:
        items = all_items

    categories = ['All', 'Breakfast', 'Meals', 'Snacks', 'Fast Food', 'Drinks', 'Desserts', 'Burgers', 'Pizza', 'Rolls', 'Noodles']
    
    cart = session.get('cart', [])
    cart_quantities = {item['id']: item['quantity'] for item in cart}
    cart_items, cart_count, cart_subtotal = get_cart_summary()

    return render_template('menu.html', items=items, categories=categories, selected_category=selected_category, search_query=search_query, veg_only=veg_only, filter_pill=filter_pill, cart_quantities=cart_quantities, cart_items=cart_items, cart_count=cart_count, cart_subtotal=cart_subtotal)

@app.route('/food-details/<int:item_id>')
def food_details(item_id):
    if not is_student_logged_in():
        return redirect(url_for('login'))

    item = database.get_menu_item_by_id(item_id)
    if not item:
        flash('Item not found.', 'danger')
        return redirect(url_for('menu'))

    reviews = database.get_food_reviews(item_id)
    _, cart_count, _ = get_cart_summary()
    return render_template('food_details.html', item=item, reviews=reviews, cart_count=cart_count)

@app.route('/api/add-review', methods=['POST'])
def api_add_review():
    if not is_student_logged_in():
        return jsonify({'success': False, 'message': 'Please login to submit a review'})

    data = request.json or {}
    item_id = int(data.get('item_id', 0))
    rating = int(data.get('rating', 5))
    comment = data.get('comment', '').strip()

    student_name = session.get('student_name', 'Student')
    roll_number = session.get('student_roll', '')

    database.add_food_review(item_id, student_name, roll_number, rating, comment)
    return jsonify({'success': True, 'message': 'Review submitted successfully!'})

@app.route('/leaderboard')
def leaderboard():
    if not is_student_logged_in():
        return redirect(url_for('login'))

    foodies = database.get_top_foodies_leaderboard()
    _, cart_count, _ = get_cart_summary()
    return render_template('leaderboard.html', foodies=foodies, cart_count=cart_count)

@app.route('/admin/analytics')
def admin_analytics():
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))

    stats = database.get_admin_stats()
    return render_template('admin_analytics.html', stats=stats)

@app.route('/cart')
def cart():
    if not is_student_logged_in():
        return redirect(url_for('login'))

    cart_items = session.get('cart', [])
    subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
    
    discount = session.get('discount', 0.0)
    applied_code = session.get('applied_coupon', '')

    if applied_code:
        res = database.validate_coupon(applied_code, subtotal)
        if res['valid']:
            discount = res['discount_amount']
            session['discount'] = discount
        else:
            discount = 0.0
            session['discount'] = 0.0
            session.pop('applied_coupon', None)
            flash(res['message'], 'warning')

    service_fee = 5.0 if cart_items else 0.0
    total = max(0.0, subtotal - discount + service_fee)
    active_coupons = database.get_active_coupons()
    _, cart_count, _ = get_cart_summary()

    return render_template('cart.html', cart_items=cart_items, subtotal=subtotal, discount=discount, applied_coupon=applied_code, service_fee=service_fee, total=total, coupons=active_coupons, cart_count=cart_count)

@app.route('/apply-promo', methods=['POST'])
def apply_promo():
    code = request.form.get('promo_code', '').strip().upper()
    cart_items = session.get('cart', [])
    subtotal = sum(item['price'] * item['quantity'] for item in cart_items)

    res = database.validate_coupon(code, subtotal)
    if res['valid']:
        session['discount'] = res['discount_amount']
        session['applied_coupon'] = res['code']
        flash(res['message'], 'success')
    else:
        session['discount'] = 0.0
        session.pop('applied_coupon', None)
        flash(res['message'], 'danger')
    return redirect(url_for('cart'))

@app.route('/remove-promo', methods=['POST'])
def remove_promo():
    session['discount'] = 0.0
    session.pop('applied_coupon', None)
    flash('Coupon removed.', 'info')
    return redirect(url_for('cart'))

@app.route('/checkout')
def checkout():
    if not is_student_logged_in():
        return redirect(url_for('login'))

    cart_items = session.get('cart', [])
    if not cart_items:
        flash('Your cart is empty!', 'warning')
        return redirect(url_for('menu'))

    student = database.get_student_by_roll(session['student_roll'])
    subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
    discount = session.get('discount', 0.0)
    service_fee = 5.0
    total = max(0.0, subtotal - discount + service_fee)

    pickup_slots = [
        "Instant Prep (10-15 min)",
        "Slot 1: 10:30 AM Break",
        "Slot 2: 01:15 PM Lunch Break",
        "Slot 3: 03:30 PM Tea Break",
        "Slot 4: 05:00 PM Evening Break"
    ]

    _, cart_count, _ = get_cart_summary()
    return render_template(
        'checkout.html', 
        student=student, 
        cart_items=cart_items, 
        subtotal=subtotal, 
        discount=discount, 
        applied_coupon=session.get('applied_coupon'), 
        service_fee=service_fee, 
        total=total, 
        pickup_slots=pickup_slots, 
        cart_count=cart_count,
        razorpay_key_id=Config.RAZORPAY_KEY_ID,
        canteen_upi_id=Config.CANTEEN_UPI_ID,
        canteen_name=Config.CANTEEN_NAME,
        payment_mode=Config.PAYMENT_MODE
    )

@app.route('/api/create-razorpay-order', methods=['POST'])
def create_razorpay_order():
    if not is_student_logged_in():
        return jsonify({'status': 'error', 'message': 'Unauthorized. Please login.'}), 401

    cart_items = session.get('cart', [])
    if not cart_items:
        return jsonify({'status': 'error', 'message': 'Cart is empty'}), 400

    subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
    discount = session.get('discount', 0.0)
    service_fee = 5.0
    total = max(0.0, subtotal - discount + service_fee)
    amount_in_paise = int(round(total * 100))

    rand_order_num = f"RZP_{random.randint(100000, 999999)}"

    # Try creating order via Razorpay SDK if live key provided
    rzp_order_id = f"order_{hashlib.md5(rand_order_num.encode()).hexdigest()[:14]}"
    if razorpay_client and Config.RAZORPAY_KEY_ID and not Config.RAZORPAY_KEY_ID.startswith('rzp_test_SmartCanteen'):
        try:
            rzp_order = razorpay_client.order.create({
                'amount': amount_in_paise,
                'currency': 'INR',
                'payment_capture': 1,
                'notes': {
                    'student_roll': session.get('student_roll'),
                    'canteen': Config.CANTEEN_NAME
                }
            })
            rzp_order_id = rzp_order['id']
        except Exception as e:
            print("Razorpay API order create fallback:", e)

    student = database.get_student_by_roll(session.get('student_roll'))
    
    return jsonify({
        'status': 'success',
        'key_id': Config.RAZORPAY_KEY_ID,
        'order_id': rzp_order_id,
        'amount': amount_in_paise,
        'currency': 'INR',
        'canteen_name': Config.CANTEEN_NAME,
        'student_name': student['name'] if student else session.get('student_name', ''),
        'student_phone': student['phone'] if student and student['phone'] else '9876543210',
        'student_roll': session.get('student_roll')
    })

@app.route('/api/verify-razorpay-payment', methods=['POST'])
def verify_razorpay_payment():
    if not is_student_logged_in():
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    data = request.json or request.form
    razorpay_payment_id = data.get('razorpay_payment_id')
    razorpay_order_id = data.get('razorpay_order_id')
    razorpay_signature = data.get('razorpay_signature')

    order_type = data.get('order_type', 'Canteen Pickup')
    pickup_slot = data.get('pickup_slot', 'Instant Prep (10-15 min)')
    delivery_address = data.get('delivery_address', 'Main Canteen Counter')
    phone = data.get('phone', '')
    payment_method = data.get('payment_method', 'Razorpay Gateway')

    cart_items = session.get('cart', [])
    if not cart_items:
        return jsonify({'status': 'error', 'message': 'Cart is empty'}), 400

    # Signature verification
    signature_valid = True
    if razorpay_client and Config.RAZORPAY_KEY_SECRET and razorpay_signature and Config.PAYMENT_MODE == 'live':
        try:
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            }
            razorpay_client.utility.verify_payment_signature(params_dict)
            signature_valid = True
        except Exception as e:
            signature_valid = False

    if not signature_valid:
        return jsonify({'status': 'error', 'message': 'Payment Signature Verification Failed'}), 400

    student_name = session.get('student_name', '')
    roll_number = session.get('student_roll', '')
    discount_amount = session.get('discount', 0.0)
    coupon_code = session.get('applied_coupon', '')
    payment_ref = razorpay_payment_id or f"PAY_RZP_{random.randint(100000, 999999)}"

    order_id, order_number = database.create_order(
        student_name, roll_number, phone, order_type, delivery_address, payment_method, cart_items, discount_amount, coupon_code, payment_ref, pickup_slot
    )

    session['cart'] = []
    session['discount'] = 0.0
    session.pop('applied_coupon', None)

    return jsonify({
        'status': 'success',
        'order_number': order_number,
        'redirect_url': url_for('order_success', order_id=order_number)
    })

@app.route('/api/verify-upi-qr-payment', methods=['POST'])
def verify_upi_qr_payment():
    if not is_student_logged_in():
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    data = request.json or request.form
    transaction_ref = data.get('transaction_ref') or f"UPI_QR_{random.randint(100000, 999999)}"
    order_type = data.get('order_type', 'Canteen Pickup')
    pickup_slot = data.get('pickup_slot', 'Instant Prep (10-15 min)')
    delivery_address = data.get('delivery_address', 'Main Canteen Counter')
    phone = data.get('phone', '')

    cart_items = session.get('cart', [])
    if not cart_items:
        return jsonify({'status': 'error', 'message': 'Cart is empty'}), 400

    student_name = session.get('student_name', '')
    roll_number = session.get('student_roll', '')
    discount_amount = session.get('discount', 0.0)
    coupon_code = session.get('applied_coupon', '')

    order_id, order_number = database.create_order(
        student_name, roll_number, phone, order_type, delivery_address, 'Dynamic UPI QR', cart_items, discount_amount, coupon_code, transaction_ref, pickup_slot
    )

    session['cart'] = []
    session['discount'] = 0.0
    session.pop('applied_coupon', None)

    return jsonify({
        'status': 'success',
        'order_number': order_number,
        'redirect_url': url_for('order_success', order_id=order_number)
    })

@app.route('/place-order', methods=['POST'])
def place_order():
    if not is_student_logged_in():
        return redirect(url_for('login'))

    cart_items = session.get('cart', [])
    if not cart_items:
        flash('Your cart is empty!', 'warning')
        return redirect(url_for('menu'))

    student_name = session.get('student_name', '')
    roll_number = session.get('student_roll', '')
    phone = request.form.get('phone', '')
    order_type = request.form.get('order_type', 'Canteen Pickup')
    pickup_slot = request.form.get('pickup_slot', 'Instant Prep (10-15 min)')
    delivery_address = request.form.get('delivery_address', 'Main Canteen Counter')
    payment_method = request.form.get('payment_method', 'UPI')
    discount_amount = session.get('discount', 0.0)
    coupon_code = session.get('applied_coupon', '')

    rand_id = random.randint(10000, 99999)
    if payment_method == 'UPI':
        payment_reference = f"DEMO_UPI_{rand_id}"
    elif payment_method in ['Credit / Debit Card', 'Card']:
        payment_reference = f"DEMO_CARD_{rand_id}"
    elif payment_method == 'Campus Wallet':
        payment_reference = f"DEMO_WALLET_{rand_id}"
    elif payment_method == 'Net Banking':
        payment_reference = f"DEMO_NB_{rand_id}"
    else:
        payment_reference = f"CASH_COUNTER_{rand_id}"

    order_id, order_number = database.create_order(
        student_name, roll_number, phone, order_type, delivery_address, payment_method, cart_items, discount_amount, coupon_code, payment_reference, pickup_slot
    )

    session['cart'] = []
    session['discount'] = 0.0
    session.pop('applied_coupon', None)

    return redirect(url_for('order_success', order_id=order_number))

@app.route('/order-success/<order_id>')
def order_success(order_id):
    if not is_student_logged_in():
        return redirect(url_for('login'))

    order = database.get_order_by_id(order_id)
    if not order:
        flash('Order not found.', 'danger')
        return redirect(url_for('home'))

    _, cart_count, _ = get_cart_summary()
    return render_template('order_success.html', order=order, cart_count=cart_count)

@app.route('/orders')
def orders():
    if not is_student_logged_in():
        return redirect(url_for('login'))

    status_filter = request.args.get('status', 'All')
    student_orders = database.get_student_orders(session['student_roll'])

    if status_filter != 'All':
        if status_filter == 'Ongoing':
            student_orders = [o for o in student_orders if o['status'] in ['Pending', 'Preparing', 'Ready']]
        else:
            student_orders = [o for o in student_orders if o['status'] == status_filter]

    _, cart_count, _ = get_cart_summary()
    return render_template('orders.html', orders=student_orders, status_filter=status_filter, cart_count=cart_count)

@app.route('/order-details/<order_id>')
def order_details(order_id):
    if not is_student_logged_in():
        return redirect(url_for('login'))

    order = database.get_order_by_id(order_id)
    if not order:
        flash('Order not found.', 'danger')
        return redirect(url_for('orders'))

    _, cart_count, _ = get_cart_summary()
    return render_template('order_details.html', order=order, cart_count=cart_count)

@app.route('/profile')
def profile():
    if not is_student_logged_in():
        return redirect(url_for('login'))

    student = database.get_student_by_roll(session['student_roll'])
    student_orders = database.get_student_orders(session['student_roll'])

    _, cart_count, _ = get_cart_summary()
    return render_template('profile.html', student=student, total_orders=len(student_orders), cart_count=cart_count)

@app.route('/settings')
def settings():
    if not is_student_logged_in():
        return redirect(url_for('login'))

    student = database.get_student_by_roll(session['student_roll'])
    _, cart_count, _ = get_cart_summary()
    return render_template('settings.html', student=student, cart_count=cart_count)

@app.route('/logout')
def logout():
    session.pop('student_name', None)
    session.pop('student_roll', None)
    session.pop('cart', None)
    session.pop('discount', None)
    session.pop('applied_coupon', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

# --- CANTEEN TOUCHSCREEN KIOSK MODE ---

@app.route('/kiosk')
def kiosk():
    items = database.get_menu_items()
    categories = ['All', 'Burgers', 'Pizza', 'Rolls', 'Noodles', 'Meals', 'Snacks', 'Drinks', 'Desserts']
    return render_template('kiosk.html', items=items, categories=categories)

# --- AI ASSISTANT API ENDPOINT ---

@app.route('/api/ai-assistant', methods=['POST'])
def api_ai_assistant():
    data = request.json or {}
    user_msg = (data.get('message') or '').strip().lower()

    all_items = database.get_menu_items()
    matched_items = []
    reply_text = ""

    # Parse budget
    budget_match = re.search(r'(\d+)', user_msg)
    max_budget = float(budget_match.group(1)) if budget_match and ('under' in user_msg or 'below' in user_msg or 'less' in user_msg or 'rs' in user_msg or 'rupee' in user_msg or '₹' in user_msg) else None

    if max_budget:
        matched_items = [i for i in all_items if i['price'] <= max_budget]
        reply_text = f"Here are delicious campus food items under ₹{max_budget:.0f}:"
    elif 'protein' in user_msg or 'healthy' in user_msg or 'gym' in user_msg:
        matched_items = [i for i in all_items if any(k in i['name'].lower() or k in (i['description'] or '').lower() for k in ['paneer', 'chicken', 'egg', 'thali'])]
        reply_text = "Here are high-protein & nutritious recommendations for you:"
    elif 'jain' in user_msg:
        matched_items = [i for i in all_items if i['is_veg'] == 1 and 'onion' not in (i['description'] or '').lower()]
        reply_text = "Here are 100% Jain-friendly options without onions or garlic:"
    elif 'spicy' in user_msg or 'hot' in user_msg:
        matched_items = [i for i in all_items if any(k in i['name'].lower() or k in (i['description'] or '').lower() for k in ['schezwan', 'spicy', 'crispy', 'tikka'])]
        reply_text = "Here are our top spicy & flavorful campus favorites:"
    elif 'sweet' in user_msg or 'dessert' in user_msg:
        matched_items = [i for i in all_items if i['category'] == 'Desserts' or 'sweet' in i['name'].lower()]
        reply_text = "Satisfy your sweet tooth with these desserts:"
    elif 'drink' in user_msg or 'chai' in user_msg or 'coffee' in user_msg:
        matched_items = [i for i in all_items if i['category'] == 'Drinks']
        reply_text = "Here are refreshing campus beverages & coffee floats:"
    else:
        matched_items = all_items[:4]
        reply_text = "Hey! I'm CanteenBot 🤖. Here are our top trending student specials today:"

    items_payload = [{
        'id': i['id'],
        'name': i['name'],
        'price': i['price'],
        'rating': i['rating'],
        'image_url': i['image_url']
    } for i in matched_items[:4]]

    return jsonify({
        'reply': reply_text,
        'items': items_payload
    })

# --- LIVE TV DISPLAY BOARD & KITCHEN DISPLAY ROUTES ---

@app.route('/live-counter')
def live_counter():
    tokens = database.get_live_counter_orders()
    return render_template('live_counter.html', tokens=tokens)

@app.route('/api/live-counter')
def api_live_counter():
    tokens = database.get_live_counter_orders()
    return jsonify(tokens)

@app.route('/kitchen')
def kitchen():
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))
    orders = database.get_kitchen_orders()
    return render_template('kitchen.html', orders=orders)

# --- CART API ENDPOINTS ---

@app.route('/api/cart/add', methods=['POST'])
def api_cart_add():
    data = request.json or {}
    item_id = int(data.get('item_id', 0))
    quantity = int(data.get('quantity', 1))
    addons = data.get('addons', [])
    instructions = data.get('instructions', '')

    item = database.get_menu_item_by_id(item_id)
    if not item:
        return jsonify({'success': False, 'message': 'Item not found'}), 404

    cart = session.get('cart', [])
    found = False
    for cart_item in cart:
        if cart_item['id'] == item_id and cart_item.get('addons') == addons:
            cart_item['quantity'] += quantity
            found = True
            break

    if not found:
        extra = 0
        if 'Extra Cheese' in addons: extra += 10
        if 'Extra Sauce' in addons: extra += 5
        if 'Extra Paneer' in addons: extra += 20

        cart.append({
            'id': item['id'],
            'name': item['name'],
            'price': item['price'] + extra,
            'quantity': quantity,
            'image_url': item['image_url'],
            'addons': addons,
            'instructions': instructions
        })

    session['cart'] = cart
    session.modified = True
    _, count, subtotal = get_cart_summary()
    return jsonify({'success': True, 'cart_count': count, 'subtotal': subtotal})

@app.route('/api/cart/update', methods=['POST'])
def api_cart_update():
    data = request.json or {}
    item_id = int(data.get('item_id', 0))
    action = data.get('action')
    set_qty = int(data.get('quantity', 1))

    cart = session.get('cart', [])
    new_cart = []

    for item in cart:
        if item['id'] == item_id:
            if action == 'increase':
                item['quantity'] += 1
                new_cart.append(item)
            elif action == 'decrease':
                item['quantity'] -= 1
                if item['quantity'] > 0:
                    new_cart.append(item)
            elif action == 'set':
                if set_qty > 0:
                    item['quantity'] = set_qty
                    new_cart.append(item)
        else:
            new_cart.append(item)

    session['cart'] = new_cart
    session.modified = True
    _, count, subtotal = get_cart_summary()
    return jsonify({'success': True, 'cart_count': count, 'subtotal': subtotal})

@app.route('/api/cart/remove', methods=['POST'])
def api_cart_remove():
    data = request.json or {}
    item_id = int(data.get('item_id', 0))

    cart = session.get('cart', [])
    session['cart'] = [item for item in cart if item['id'] != item_id]
    session.modified = True

    _, count, subtotal = get_cart_summary()
    return jsonify({'success': True, 'cart_count': count, 'subtotal': subtotal})

@app.route('/api/live-rush')
def api_live_rush():
    # Calculate live canteen rush status from pending & preparing orders
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM orders WHERE status IN ('Pending', 'Preparing')")
    count = cursor.fetchone()[0]
    conn.close()

    if count <= 3:
        status_code = 'low'
        text = '🟢 Low Rush (~5m)'
        prep_est = '5-8 mins'
    elif count <= 8:
        status_code = 'moderate'
        text = '🟡 Moderate Rush (~12m)'
        prep_est = '10-15 mins'
    else:
        status_code = 'peak'
        text = '🔴 Peak Rush (~20m)'
        prep_est = '20-25 mins'

    return jsonify({
        'status': status_code,
        'rush_text': text,
        'active_orders': count,
        'prep_est': prep_est
    })

@app.route('/api/live-feed')
def api_live_feed():
    # Return recent campus orders & trending items for live activity ticker
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT student_name, roll_number, total_amount, created_at FROM orders ORDER BY id DESC LIMIT 5")
    recent = cursor.fetchall()
    conn.close()

    feed_items = []
    for r in recent:
        feed_items.append(f"🔥 <b>{r['student_name']} ({r['roll_number']})</b> placed order of ₹{r['total_amount']:.0f}")

    feed_items.append("⚡ <b>Cold Coffee Float</b> & <b>Paneer Roll</b> trending on campus now!")
    feed_items.append("👨‍🍳 Counter #1 & #2 operating at peak speed")
    feed_items.append("🎉 Promo <b>STUDENT10</b> active for 10% OFF")

    return jsonify({'feed': feed_items})

# --- ADMIN ROUTES ---

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if is_admin_logged_in():
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if database.verify_admin_login(username, password):
            session['admin_logged_in'] = True
            session['admin_username'] = username
            flash('Welcome to Admin Dashboard', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials!', 'danger')

    return render_template('admin_login.html')

@app.route('/admin')
def admin_dashboard():
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))

    stats = database.get_admin_stats()
    live_orders = database.get_all_orders()
    return render_template('admin.html', stats=stats, orders=live_orders)

@app.route('/admin/orders')
def admin_orders():
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))

    status_filter = request.args.get('status', 'All')
    orders = database.get_all_orders(status_filter=status_filter)
    stats = database.get_admin_stats()
    return render_template('admin_orders.html', orders=orders, status_filter=status_filter, stats=stats)

@app.route('/admin/update-order-status/<order_id>', methods=['POST'])
def admin_update_order_status(order_id):
    if not is_admin_logged_in():
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    new_status = request.form.get('status') or (request.json or {}).get('status')
    if not new_status:
        return jsonify({'success': False, 'message': 'Status required'}), 400

    database.update_order_status(order_id, new_status)
    flash(f'Order #{order_id} status updated to {new_status}.', 'success')

    if request.is_json:
        return jsonify({'success': True, 'order_id': order_id, 'new_status': new_status})
    return redirect(request.referrer or url_for('admin_dashboard'))

@app.route('/admin/students')
def admin_students():
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))

    search_query = request.args.get('search', '')
    students = database.get_registered_students(search=search_query)
    return render_template('admin_students.html', students=students, search_query=search_query)

@app.route('/admin/menu')
def admin_menu():
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))

    category_filter = request.args.get('category', 'All')
    items = database.get_menu_items(category=category_filter)
    categories = ['All', 'Burgers', 'Pizza', 'Rolls', 'Noodles', 'Meals', 'Snacks', 'Drinks', 'Desserts']
    return render_template('admin_menu.html', items=items, categories=categories, selected_category=category_filter)

@app.route('/admin/add-menu-item', methods=['POST'])
def admin_add_menu_item():
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))

    name = request.form.get('name')
    category = request.form.get('category')
    description = request.form.get('description')
    price = float(request.form.get('price', 0))
    rating = float(request.form.get('rating', 4.5))
    is_available = 1 if request.form.get('is_available') == 'on' else 0
    is_veg = 1 if request.form.get('is_veg') == 'on' else 0
    image_url = request.form.get('image_url') or 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=500&auto=format&fit=crop&q=80'
    prep_time = request.form.get('prep_time', '10-15 mins')

    database.add_menu_item(name, category, description, price, rating, is_available, is_veg, image_url, prep_time)
    flash(f'Menu item "{name}" added successfully.', 'success')
    return redirect(url_for('admin_menu'))

@app.route('/admin/edit-menu-item/<int:item_id>', methods=['POST'])
def admin_edit_menu_item(item_id):
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))

    name = request.form.get('name')
    category = request.form.get('category')
    description = request.form.get('description')
    price = float(request.form.get('price', 0))
    rating = float(request.form.get('rating', 4.5))
    is_available = 1 if request.form.get('is_available') == 'on' else 0
    is_veg = 1 if request.form.get('is_veg') == 'on' else 0
    image_url = request.form.get('image_url')
    prep_time = request.form.get('prep_time', '10-15 mins')

    database.update_menu_item(item_id, name, category, description, price, rating, is_available, is_veg, image_url, prep_time)
    flash(f'Menu item #{item_id} updated successfully.', 'success')
    return redirect(url_for('admin_menu'))

@app.route('/admin/delete-menu-item/<int:item_id>', methods=['POST'])
def admin_delete_menu_item(item_id):
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))

    database.delete_menu_item(item_id)
    flash(f'Menu item #{item_id} deleted.', 'info')
    return redirect(url_for('admin_menu'))

@app.route('/admin/toggle-menu-item/<int:item_id>', methods=['POST'])
def admin_toggle_menu_item(item_id):
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))

    database.toggle_menu_item_availability(item_id)
    flash('Item availability updated.', 'info')
    return redirect(url_for('admin_menu'))

@app.route('/admin/offers')
def admin_offers():
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))

    coupons = database.get_all_coupons()
    return render_template('admin_offers.html', coupons=coupons)

@app.route('/admin/add-coupon', methods=['POST'])
def admin_add_coupon():
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))

    code = request.form.get('code')
    title = request.form.get('title')
    description = request.form.get('description')
    discount_type = request.form.get('discount_type', 'percent')
    discount_value = float(request.form.get('discount_value', 0))
    minimum_order = float(request.form.get('minimum_order', 0))
    maximum_discount = float(request.form.get('maximum_discount', 100))
    active = 1 if request.form.get('active') == 'on' else 0

    try:
        database.add_coupon(code, title, description, discount_type, discount_value, minimum_order, maximum_discount, active)
        flash(f'Coupon {code.upper()} created successfully.', 'success')
    except Exception as e:
        flash(f'Error adding coupon: {str(e)}', 'danger')

    return redirect(url_for('admin_offers'))

@app.route('/admin/toggle-coupon/<int:coupon_id>', methods=['POST'])
def admin_toggle_coupon(coupon_id):
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))

    database.toggle_coupon_active(coupon_id)
    flash('Coupon status updated.', 'info')
    return redirect(url_for('admin_offers'))

@app.route('/admin/delete-coupon/<int:coupon_id>', methods=['POST'])
def admin_delete_coupon(coupon_id):
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))

    database.delete_coupon(coupon_id)
    flash('Coupon deleted.', 'info')
    return redirect(url_for('admin_offers'))

@app.route('/admin/payments')
def admin_payments():
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))

    payments = database.get_all_payments()
    return render_template('admin_payments.html', payments=payments)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    flash('Admin logged out successfully.', 'info')
    return redirect(url_for('admin_login'))

@app.route('/api/admin/live-orders')
def api_admin_live_orders():
    if not is_admin_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401
    orders = database.get_all_orders()
    stats = database.get_admin_stats()
    return jsonify({'orders': orders, 'stats': stats})

if __name__ == '__main__':
    database.init_db()
    app.run(debug=True, port=5000)
