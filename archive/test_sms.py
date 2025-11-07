#!/usr/bin/env python3
"""
Test script for SMS reception
Tests both the webhook endpoint and Twilio integration
"""

import requests
import json
from datetime import datetime

def test_webhook_endpoint(backend_url):
    """Test the SMS webhook endpoint"""
    print(f"🔍 Testing SMS webhook: {backend_url}/sms")
    
    # Test GET request (should return ready message)
    try:
        response = requests.get(f"{backend_url}/sms", timeout=10)
        if response.status_code == 200:
            print("✅ GET /sms endpoint working")
            print(f"   Response: {response.text}")
        else:
            print(f"❌ GET /sms failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ GET /sms failed: {e}")
        return False
    
    # Test POST request (simulate Twilio webhook)
    test_data = {
        "From": "+1234567890",
        "To": "+14709909366",
        "Body": "Hello, this is a test message from Twilio!",
        "MessageSid": "SM123456789",
        "NumMedia": "0",
        "SmsStatus": "received"
    }
    
    try:
        response = requests.post(f"{backend_url}/sms", data=test_data, timeout=10)
        if response.status_code == 200:
            print("✅ POST /sms endpoint working")
            print(f"   Response: {response.text}")
            return True
        else:
            print(f"❌ POST /sms failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ POST /sms failed: {e}")
        return False

def test_ai_chat(backend_url):
    """Test AI chat endpoint"""
    print(f"🤖 Testing AI chat: {backend_url}/pm_chat")
    
    payload = {
        "message": "Hello, this is a test message for the AI assistant",
        "context": {
            "tenant_name": "Test User",
            "unit": "1A",
            "address": "123 Test Street",
            "hotline": "+1-555-0100",
            "property_name": "Test Property"
        }
    }
    
    try:
        response = requests.post(
            f"{backend_url}/pm_chat",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ AI Chat endpoint working")
            print(f"   Response: {data.get('reply', 'No reply')[:100]}...")
            return True
        else:
            print(f"❌ AI Chat failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ AI Chat failed: {e}")
        return False

def test_health(backend_url):
    """Test health endpoint"""
    print(f"🏥 Testing health: {backend_url}/health")
    
    try:
        response = requests.get(f"{backend_url}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Health endpoint working")
            print(f"   Status: {data.get('status', 'unknown')}")
            print(f"   Database: {data.get('database_type', 'unknown')}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 PropAI SMS Testing Suite")
    print("=" * 50)
    
    backend_url = input("Enter your backend URL (e.g., https://prop-ai.onrender.com): ").strip()
    if not backend_url.startswith("http"):
        backend_url = f"https://{backend_url}"
    
    print(f"\nTesting backend: {backend_url}")
    print("-" * 50)
    
    # Run tests
    tests = [
        ("Health Check", lambda: test_health(backend_url)),
        ("AI Chat", lambda: test_ai_chat(backend_url)),
        ("SMS Webhook", lambda: test_webhook_endpoint(backend_url))
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        result = test_func()
        results.append((test_name, result))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(results)}")
    
    if passed == len(results):
        print("🎉 All tests passed! Your backend is ready for SMS testing.")
        print("\n📱 Next steps:")
        print("1. Configure Twilio webhook: https://console.twilio.com")
        print("2. Set webhook URL to: " + backend_url + "/sms")
        print("3. Send a test SMS to: +14709909366")
    else:
        print("⚠️  Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main()
