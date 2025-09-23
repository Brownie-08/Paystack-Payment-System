#!/usr/bin/env python3
"""
Webhook testing script for Django Paystack Payment integration.

This script helps test webhook functionality locally using ngrok.
"""

import hashlib
import hmac
import json
import requests
import sys
from datetime import datetime

# Configuration
NGROK_URL = "https://your-ngrok-url.ngrok.io"  # Replace with your ngrok URL
WEBHOOK_ENDPOINT = "/api/payments/webhook/"
PAYSTACK_SECRET_KEY = "sk_test_your_secret_key_here"  # Replace with your Paystack secret key
PAYSTACK_PUBLIC_KEY = "pk_test_your_public_key_here"  # Replace with your Paystack public key


def generate_signature(payload_bytes, secret_key):
    """Generate HMAC SHA512 signature for webhook payload."""
    return hmac.new(
        secret_key.encode('utf-8'),
        payload_bytes,
        hashlib.sha512
    ).hexdigest()


def create_test_webhook_payload(reference="PAY_TEST_123", status="success"):
    """Create a test webhook payload."""
    return {
        "event": "charge.success",
        "data": {
            "reference": reference,
            "status": status,
            "amount": 100000,  # 1000 NGN in kobo
            "currency": "NGN",
            "paid_at": datetime.now().isoformat() + "Z",
            "created_at": datetime.now().isoformat() + "Z",
            "channel": "card",
            "ip_address": "127.0.0.1",
            "customer": {
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "User"
            },
            "authorization": {
                "authorization_code": "AUTH_test123",
                "bin": "408408",
                "last4": "4081",
                "exp_month": "12",
                "exp_year": "2030",
                "channel": "card",
                "card_type": "visa",
                "bank": "Test Bank",
                "country_code": "NG",
                "brand": "visa",
                "reusable": True,
                "signature": "SIG_test123"
            }
        }
    }


def send_webhook(ngrok_url, payload, secret_key):
    """Send a test webhook to the specified URL."""
    url = f"{ngrok_url.rstrip('/')}{WEBHOOK_ENDPOINT}"
    
    # Convert payload to JSON bytes
    payload_json = json.dumps(payload)
    payload_bytes = payload_json.encode('utf-8')
    
    # Generate signature
    signature = generate_signature(payload_bytes, secret_key)
    
    # Prepare headers
    headers = {
        'Content-Type': 'application/json',
        'x-paystack-signature': signature,
        'User-Agent': 'Paystack/1.0 (+https://paystack.com)'
    }
    
    print(f"🚀 Sending webhook to: {url}")
    print(f"📦 Payload: {payload_json}")
    print(f"🔐 Signature: {signature}")
    print("-" * 60)
    
    try:
        response = requests.post(url, data=payload_bytes, headers=headers, timeout=30)
        
        print(f"✅ Response Status: {response.status_code}")
        print(f"📨 Response Headers: {dict(response.headers)}")
        print(f"📄 Response Content: {response.text}")
        
        if response.status_code == 200:
            print("🎉 Webhook sent successfully!")
        else:
            print(f"❌ Webhook failed with status {response.status_code}")
            
        return response.status_code == 200
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending webhook: {e}")
        return False


def test_invalid_signature(ngrok_url):
    """Test webhook with invalid signature."""
    url = f"{ngrok_url.rstrip('/')}{WEBHOOK_ENDPOINT}"
    payload = create_test_webhook_payload("PAY_INVALID_SIG")
    payload_json = json.dumps(payload)
    payload_bytes = payload_json.encode('utf-8')
    
    # Use wrong signature
    headers = {
        'Content-Type': 'application/json',
        'x-paystack-signature': 'invalid_signature_123',
        'User-Agent': 'Paystack/1.0 (+https://paystack.com)'
    }
    
    print("🔒 Testing invalid signature...")
    
    try:
        response = requests.post(url, data=payload_bytes, headers=headers, timeout=30)
        
        if response.status_code == 403:
            print("✅ Invalid signature correctly rejected with 403")
            return True
        else:
            print(f"❌ Expected 403, got {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error testing invalid signature: {e}")
        return False


def test_missing_signature(ngrok_url):
    """Test webhook without signature header."""
    url = f"{ngrok_url.rstrip('/')}{WEBHOOK_ENDPOINT}"
    payload = create_test_webhook_payload("PAY_NO_SIG")
    payload_json = json.dumps(payload)
    payload_bytes = payload_json.encode('utf-8')
    
    # Headers without signature
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Paystack/1.0 (+https://paystack.com)'
    }
    
    print("📭 Testing missing signature...")
    
    try:
        response = requests.post(url, data=payload_bytes, headers=headers, timeout=30)
        
        if response.status_code == 403:
            print("✅ Missing signature correctly rejected with 403")
            return True
        else:
            print(f"❌ Expected 403, got {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error testing missing signature: {e}")
        return False


def main():
    """Main testing function."""
    print("🎯 Django Paystack Webhook Tester")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        ngrok_url = sys.argv[1]
    else:
        ngrok_url = input("Enter your ngrok URL (e.g., https://abc123.ngrok.io): ").strip()
    
    if not ngrok_url:
        print("❌ No ngrok URL provided")
        sys.exit(1)
    
    if not ngrok_url.startswith(('http://', 'https://')):
        print("❌ Please include http:// or https:// in the URL")
        sys.exit(1)
    
    print(f"🌐 Testing webhook at: {ngrok_url}")
    print()
    
    # Test 1: Valid webhook
    print("Test 1: Valid webhook with correct signature")
    success1 = send_webhook(ngrok_url, create_test_webhook_payload(), PAYSTACK_SECRET_KEY)
    print()
    
    # Test 2: Invalid signature
    print("Test 2: Invalid signature")
    success2 = test_invalid_signature(ngrok_url)
    print()
    
    # Test 3: Missing signature
    print("Test 3: Missing signature header")
    success3 = test_missing_signature(ngrok_url)
    print()
    
    # Test 4: Different event type
    print("Test 4: Different event type")
    different_payload = create_test_webhook_payload()
    different_payload["event"] = "transfer.success"
    success4 = send_webhook(ngrok_url, different_payload, PAYSTACK_SECRET_KEY)
    print()
    
    # Summary
    print("📊 Test Summary")
    print("-" * 30)
    print(f"✅ Valid webhook: {'PASS' if success1 else 'FAIL'}")
    print(f"🔒 Invalid signature: {'PASS' if success2 else 'FAIL'}")
    print(f"📭 Missing signature: {'PASS' if success3 else 'FAIL'}")
    print(f"🔄 Different event: {'PASS' if success4 else 'FAIL'}")
    
    total_passed = sum([success1, success2, success3, success4])
    print(f"\n🎯 Tests passed: {total_passed}/4")
    
    if total_passed == 4:
        print("🎉 All tests passed! Your webhook is working correctly.")
    else:
        print("⚠️ Some tests failed. Please check your webhook implementation.")


if __name__ == "__main__":
    main()