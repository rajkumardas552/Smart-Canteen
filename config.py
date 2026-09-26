import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'smart_canteen_secret_key_2026_prod')
    
    # Razorpay Payment Gateway Credentials
    # Replace these with your live credentials when publishing (e.g. in environment variables or .env)
    RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', 'rzp_test_SmartCanteen2026')
    RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', 'SmartCanteenSecretKey2026')
    
    # Campus UPI Credentials for Direct Dynamic QR Code Payment
    CANTEEN_UPI_ID = os.environ.get('CANTEEN_UPI_ID', 'smartcanteen@okaxis')
    CANTEEN_NAME = os.environ.get('CANTEEN_NAME', 'Smart Campus Canteen')
    
    # Payment Mode: 'test' or 'live'
    PAYMENT_MODE = os.environ.get('PAYMENT_MODE', 'test')
