#!/usr/bin/env python3
"""
Test script to verify backend CORS configuration
"""
import requests
import json

def test_cors():
    backend_url = "https://prop-ai.onrender.com"
    frontend_origin = "https://ten8link.vercel.app"
    
    print(f"Testing CORS for {frontend_origin} -> {backend_url}")
    
    # Test 1: Health check
    try:
        response = requests.get(f"{backend_url}/health")
        print(f"✅ Health check: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return
    
    # Test 2: CORS preflight
    try:
        headers = {
            'Origin': frontend_origin,
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type'
        }
        response = requests.options(f"{backend_url}/pm_chat", headers=headers)
        print(f"✅ CORS preflight: {response.status_code}")
        print(f"   CORS headers: {dict(response.headers)}")
        
        # Check if CORS headers are present
        cors_origin = response.headers.get('Access-Control-Allow-Origin')
        if cors_origin:
            print(f"   ✅ CORS Origin: {cors_origin}")
        else:
            print(f"   ❌ No CORS Origin header")
            
    except Exception as e:
        print(f"❌ CORS preflight failed: {e}")
    
    # Test 3: Actual request
    try:
        headers = {
            'Origin': frontend_origin,
            'Content-Type': 'application/json'
        }
        payload = {
            "message": "Hello test",
            "context": {
                "tenant_name": "Test User",
                "unit": "1A", 
                "address": "123 Test St",
                "hotline": "+1-555-0100",
                "portal_url": "https://portal.example.com/login",
                "property_name": "Test Property",
                "tenant_phone": "+1234567890"
            },
            "phone": "+1234567890"
        }
        print(f"   Sending payload: {payload}")
        response = requests.post(f"{backend_url}/pm_chat", 
                               headers=headers, 
                               json=payload)
        print(f"✅ AI Chat request: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ AI Chat request failed: {e}")

if __name__ == "__main__":
    test_cors()
