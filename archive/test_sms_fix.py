#!/usr/bin/env python3
"""
Test script to verify SMS sending functionality
"""
import requests
import json
import os

# Test configuration
BACKEND_URL = "http://localhost:8000"  # Adjust if your backend runs on different port
TEST_PHONE = "+1234567890"  # Replace with a test phone number
TEST_MESSAGE = "Test message from PropAI - SMS fix verification"

def test_sms_send():
    """Test the SMS send endpoint"""
    print("🧪 Testing SMS send endpoint...")
    
    # Test data
    test_data = {
        "to": TEST_PHONE,
        "message": TEST_MESSAGE,
        "property_id": "test_property_123"
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/sms/send",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ SMS send test PASSED")
                print(f"Message SID: {result.get('message_sid')}")
            else:
                print("❌ SMS send test FAILED - success=False")
                print(f"Error: {result.get('error')}")
        else:
            print(f"❌ SMS send test FAILED - HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ SMS send test FAILED - Exception: {e}")

def test_health():
    """Test if backend is running"""
    print("🏥 Testing backend health...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/health")
        print(f"Health check status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Backend is running")
            return True
        else:
            print("❌ Backend health check failed")
            return False
    except Exception as e:
        print(f"❌ Backend not reachable: {e}")
        return False

def test_twilio_config():
    """Test Twilio configuration"""
    print("📱 Testing Twilio configuration...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"Twilio From Number: {stats.get('twilio_from_number')}")
            print(f"Fake Twilio Mode: {stats.get('fake_twilio')}")
            
            if stats.get('fake_twilio'):
                print("⚠️  Running in FAKE Twilio mode - messages won't be sent to real numbers")
            else:
                print("✅ Real Twilio mode - messages will be sent to actual numbers")
        else:
            print("❌ Could not get Twilio config")
    except Exception as e:
        print(f"❌ Error checking Twilio config: {e}")

if __name__ == "__main__":
    print("🚀 Starting SMS functionality test...")
    print("=" * 50)
    
    # Test backend health first
    if not test_health():
        print("\n❌ Backend is not running. Please start it first:")
        print("   python start_backend.py")
        exit(1)
    
    print("\n" + "=" * 50)
    
    # Test Twilio configuration
    test_twilio_config()
    
    print("\n" + "=" * 50)
    
    # Test SMS sending
    test_sms_send()
    
    print("\n" + "=" * 50)
    print("🏁 Test completed!")
    print("\nIf you see 'FAKE Twilio mode', messages are being logged but not sent.")
    print("To send real messages, set USE_FAKE_TWILIO=0 in your environment.")
