from app import app
import database

def test_all_routes():
    database.init_db()
    client = app.test_client()

    print("Testing Student Flow...")
    assert client.get('/').status_code == 200
    assert client.post('/login', data={'name': 'Raj Kumar', 'roll_number': 'CSE001'}, follow_redirects=True).status_code == 200
    assert client.get('/home').status_code == 200
    assert client.get('/menu').status_code == 200

    print("Testing AI Assistant CanteenBot API...")
    res = client.post('/api/ai-assistant', json={'message': 'budget under 100'})
    assert res.status_code == 200, f"AI assistant failed: {res.status_code}"
    assert 'reply' in res.json, "AI response missing reply key"

    print("Testing Live Rush & Activity Feed APIs...")
    res = client.get('/api/live-rush')
    assert res.status_code == 200 and 'rush_text' in res.json
    res = client.get('/api/live-feed')
    assert res.status_code == 200 and 'feed' in res.json

    print("Testing Canteen Touchscreen Kiosk (/kiosk)...")
    res = client.get('/kiosk')
    assert res.status_code == 200, f"Kiosk mode failed: {res.status_code}"

    print("Testing 1-Tap Reorder & Cart Operations...")
    res = client.get('/reorder/1', follow_redirects=True)
    assert res.status_code == 200

    print("Testing Razorpay Payment Gateway APIs...")
    res_rzp = client.post('/api/create-razorpay-order')
    assert res_rzp.status_code == 200 and res_rzp.json['status'] == 'success'

    res_verify = client.post('/api/verify-razorpay-payment', json={
        'razorpay_payment_id': 'pay_test_998877',
        'razorpay_order_id': res_rzp.json['order_id'],
        'razorpay_signature': 'test_signature',
        'phone': '9876543210',
        'order_type': 'Canteen Pickup',
        'pickup_slot': 'Slot 1: 10:30 AM Break'
    })
    assert res_verify.status_code == 200 and res_verify.json['status'] == 'success'

    # Re-add item for UPI test
    client.get('/reorder/1', follow_redirects=True)
    print("Testing Dynamic UPI QR Payment API...")
    res_upi = client.post('/api/verify-upi-qr-payment', json={
        'transaction_ref': 'UPI_QR_887766',
        'phone': '9876543210',
        'order_type': 'Hostel Delivery',
        'pickup_slot': 'Slot 2: 01:15 PM Lunch Break',
        'delivery_address': 'Block B, Room 101'
    })
    assert res_upi.status_code == 200 and res_upi.json['status'] == 'success'

    # Re-add item for standard place-order test
    client.get('/reorder/1', follow_redirects=True)
    res = client.post('/place-order', data={
        'phone': '+91 9876543210',
        'order_type': 'Canteen Pickup',
        'pickup_slot': 'Slot 2: 01:15 PM Lunch Break',
        'delivery_address': 'Main Canteen Counter',
        'payment_method': 'Cash at Canteen'
    }, follow_redirects=True)
    assert res.status_code == 200

    assert client.get('/order-success/SC1024').status_code == 200
    assert client.get('/orders').status_code == 200
    assert client.get('/profile').status_code == 200
    assert client.get('/settings').status_code == 200

    print("Testing Admin, KDS & TV Counter...")
    client.post('/admin-login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
    assert client.get('/live-counter').status_code == 200
    assert client.get('/kitchen').status_code == 200
    assert client.get('/admin').status_code == 200
    assert client.get('/admin/orders').status_code == 200
    assert client.get('/admin/offers').status_code == 200
    assert client.get('/admin/payments').status_code == 200

    print("ALL ULTIMATE PAYMENT GATEWAYS & ROUTES PASSED 100% CLEANLY!")

if __name__ == '__main__':
    test_all_routes()
