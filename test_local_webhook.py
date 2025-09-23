#!/usr/bin/env python
"""
Simple webhook test script for local Django server testing.
Tests webhook functionality without ngrok - useful for development.
"""

import json
import hashlib
import hmac
import requests
import sys
import os

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configuration
WEBHOOK_URL = "http://127.0.0.1:8000/api/payments/webhook/"
PAYSTACK_SECRET = "sk_test_your_secret_key_here"

def create_signature(payload_bytes, secret_key):
    """Create HMAC SHA512 signature"""
    return hmac.new(
        secret_key.encode('utf-8'),
        payload_bytes,
        hashlib.sha512
    ).hexdigest()

def test_successful_webhook(reference):
    """Test successful payment webhook"""
    
    webhook_data = {
        "event": "charge.success",
        "data": {
            "id": 987654321,
            "domain": "test",
            "status": "success",
            "reference": reference,
            "amount": 100000,  # ₦1000.00 in kobo
            "message": None,
            "gateway_response": "Successful",
            "paid_at": "2025-01-23T10:30:45.000Z",
            "created_at": "2025-01-23T10:25:00.000Z",
            "channel": "card",
            "currency": "NGN",
            "ip_address": "192.168.1.100",
            "metadata": {},
            "fees": 1500,
            "customer": {
                "id": 123456,
                "first_name": "Test",
                "last_name": "User",
                "email": "test@example.com",
                "customer_code": "CUS_test123",
                "phone": "+2348123456789",
                "metadata": {},
                "risk_action": "default"
            },
            "authorization": {
                "authorization_code": "AUTH_test123",
                "bin": "408408",
                "last4": "4081",
                "exp_month": "12",
                "exp_year": "2030",
                "channel": "card",
                "card_type": "visa",
                "bank": "TEST BANK",
                "country_code": "NG",
                "brand": "visa",
                "reusable": True,
                "signature": "SIG_test123",
                "account_name": None,
            },
            "plan": None,
            "order_id": None,
            "paidAt": "2025-01-23T10:30:45.000Z",
            "createdAt": "2025-01-23T10:25:00.000Z"
        }
    }
    
    # Convert to JSON and create signature
    payload = json.dumps(webhook_data, separators=(',', ':'))
    payload_bytes = payload.encode('utf-8')
    signature = create_signature(payload_bytes, PAYSTACK_SECRET)
    
    headers = {
        'Content-Type': 'application/json',
        'X-Paystack-Signature': signature,
        'User-Agent': 'Paystack/1.0 (+https://paystack.com/)'
    }
    
    print(f"🚀 Testing successful webhook for: {reference}")
    print(f"💰 Amount: ₦{webhook_data['data']['amount']/100:.2f}")
    print(f"📧 Email: {webhook_data['data']['customer']['email']}")
    
    try:
        response = requests.post(WEBHOOK_URL, data=payload, headers=headers, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📄 Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Webhook processed successfully!")
            return True
        else:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR: Django server not running on http://127.0.0.1:8000/")
        print("💡 Start Django server: python manage.py runserver 127.0.0.1:8000")
        return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_invalid_signature(reference):
    """Test webhook with invalid signature"""
    
    webhook_data = {
        "event": "charge.success",
        "data": {
            "reference": reference,
            "status": "success",
            "amount": 50000
        }
    }
    
    payload = json.dumps(webhook_data)
    headers = {
        'Content-Type': 'application/json',
        'X-Paystack-Signature': 'invalid_signature_12345',
        'User-Agent': 'Paystack/1.0'
    }
    
    print(f"🔒 Testing invalid signature for: {reference}")
    
    try:
        response = requests.post(WEBHOOK_URL, data=payload, headers=headers, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📄 Response: {response.text}")
        
        if response.status_code == 403:
            print("✅ SUCCESS: Invalid signature correctly rejected!")
            return True
        else:
            print(f"❌ FAILED: Expected 403, got {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_missing_signature(reference):
    """Test webhook without signature header"""
    
    webhook_data = {
        "event": "charge.success",
        "data": {
            "reference": reference,
            "status": "success",
            "amount": 25000
        }
    }
    
    payload = json.dumps(webhook_data)
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Paystack/1.0'
        # No X-Paystack-Signature header
    }
    
    print(f"📭 Testing missing signature for: {reference}")
    
    try:
        response = requests.post(WEBHOOK_URL, data=payload, headers=headers, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📄 Response: {response.text}")
        
        if response.status_code == 403:
            print("✅ SUCCESS: Missing signature correctly rejected!")
            return True
        else:
            print(f"❌ FAILED: Expected 403, got {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def main():
    """Main test function"""
    
    print("🎯 Django Paystack Local Webhook Tester")
    print("=" * 60)
    
    # Get payment reference to test
    if len(sys.argv) > 1:
        reference = sys.argv[1]
    else:
        reference = input("Enter payment reference to test (or press Enter for example): ").strip()
        if not reference:
            reference = "PAY_20250923123456_TEST123"
            print(f"Using example reference: {reference}")
    
    print(f"🎯 Testing webhook for reference: {reference}")
    print(f"📡 Webhook URL: {WEBHOOK_URL}")
    print()
    
    # Test 1: Valid webhook
    print("=" * 60)
    print("Test 1: Valid webhook with correct signature")
    print("-" * 60)
    success1 = test_successful_webhook(reference)
    
    print()
    
    # Test 2: Invalid signature
    print("=" * 60)
    print("Test 2: Invalid signature (should be rejected)")
    print("-" * 60)
    success2 = test_invalid_signature(reference + "_INVALID")
    
    print()
    
    # Test 3: Missing signature
    print("=" * 60)
    print("Test 3: Missing signature header (should be rejected)")
    print("-" * 60)
    success3 = test_missing_signature(reference + "_NOSIG")
    
    print()
    print("=" * 60)
    print("📊 TEST RESULTS")
    print("=" * 60)
    print(f"✅ Valid webhook: {'PASSED' if success1 else 'FAILED'}")
    print(f"🔒 Invalid signature: {'PASSED' if success2 else 'FAILED'}")
    print(f"📭 Missing signature: {'PASSED' if success3 else 'FAILED'}")
    
    if success1 and success2 and success3:
        print("\n🎉 ALL TESTS PASSED! Webhook system is working correctly.")
        print("\n💡 Next steps:")
        print("   1. Check Django admin panel to verify payment was updated")
        print("   2. Check Django logs for detailed webhook processing")
        print("   3. Set up ngrok for real Paystack webhook testing")
    else:
        print("\n❌ Some tests failed. Check Django server and logs.")

if __name__ == "__main__":
    main()