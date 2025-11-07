#!/usr/bin/env python3
"""
Test script for the new messaging system with two distinct Groq Llama 4 calls:
1. Tenant SMS processing with maintenance ticket creation
2. Frontend AI assistant for property managers
"""

import asyncio
import httpx
import json
from datetime import datetime

# Backend URL
BACKEND_URL = "http://localhost:8000"

async def test_tenant_sms_processing():
    """Test tenant SMS processing with maintenance ticket creation"""
    print("🧪 Testing Tenant SMS Processing...")
    
    # Test maintenance-related message
    maintenance_request = {
        "message": "Hi, my toilet is overflowing and water is leaking everywhere! This is urgent!",
        "context": {
            "tenant_name": "John Doe",
            "unit": "3A",
            "address": "123 Main St, Apartment 3A",
            "property_name": "Sunset Apartments",
            "tenant_phone": "+1234567890"
        },
        "phone": "+1234567890",
        "media_urls": ["data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k="]
    }
    
    # Test duplicate detection
    duplicate_request = {
        "message": "The toilet is still overflowing, when will someone come fix it?",
        "context": {
            "tenant_name": "John Doe",
            "unit": "3A",
            "address": "123 Main St, Apartment 3A",
            "property_name": "Sunset Apartments",
            "tenant_phone": "+1234567890"
        },
        "phone": "+1234567890"
    }
    
    # Test ticket closure
    closure_request = {
        "message": "Close all the tickets I fixed it",
        "context": {
            "tenant_name": "John Doe",
            "unit": "3A",
            "address": "123 Main St, Apartment 3A",
            "property_name": "Sunset Apartments",
            "tenant_phone": "+1234567890"
        },
        "phone": "+1234567890"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            # Test 1: Initial maintenance request
            print("\n📝 Test 1: Initial maintenance request")
            response = await client.post(
                f"{BACKEND_URL}/tenant_sms",
                json=maintenance_request,
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            
            print(f"✅ Response: {result['reply']}")
            print(f"🎫 Ticket created: {result['maintenance_ticket_created']}")
            if result.get('ticket_id'):
                print(f"🎫 Ticket ID: {result['ticket_id']}")
            
            # Test 2: Duplicate detection
            print("\n📝 Test 2: Duplicate detection")
            response = await client.post(
                f"{BACKEND_URL}/tenant_sms",
                json=duplicate_request,
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            
            print(f"✅ Response: {result['reply']}")
            print(f"🎫 Ticket created: {result['maintenance_ticket_created']}")
            
            # Test 3: Ticket closure
            print("\n📝 Test 3: Ticket closure request")
            response = await client.post(
                f"{BACKEND_URL}/tenant_sms",
                json=closure_request,
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            
            print(f"✅ Response: {result['reply']}")
            print(f"🎫 Ticket created: {result['maintenance_ticket_created']}")
                
        except Exception as e:
            print(f"❌ Error testing tenant SMS: {e}")

async def test_property_manager_ai():
    """Test frontend AI assistant for property managers"""
    print("\n🧪 Testing Property Manager AI Assistant...")
    
    # Test property manager query
    pm_request = {
        "message": "Can you give me a summary of this property and any maintenance issues?",
        "context": {
            "tenant_name": "John Doe",
            "unit": "3A",
            "address": "123 Main St, Apartment 3A",
            "property_name": "Sunset Apartments",
            "tenant_phone": "+1234567890",
            "hotline": "+1-555-MAINT",
            "portal_url": "https://tenant-portal.example.com"
        },
        "phone": "+1234567890"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BACKEND_URL}/pm_chat",
                json=pm_request,
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            
            print(f"✅ PM AI Response: {result['reply']}")
                
        except Exception as e:
            print(f"❌ Error testing PM AI: {e}")

async def test_maintenance_tickets():
    """Test maintenance ticket retrieval"""
    print("\n🧪 Testing Maintenance Tickets...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BACKEND_URL}/maintenance_tickets")
            response.raise_for_status()
            result = response.json()
            
            print(f"✅ Found {len(result['tickets'])} maintenance tickets")
            for ticket in result['tickets']:
                print(f"   - #{ticket['id']} ({ticket['priority']}) - {ticket['issue_description'][:50]}...")
                
        except Exception as e:
            print(f"❌ Error testing maintenance tickets: {e}")

async def test_property_context():
    """Test property context retrieval"""
    print("\n🧪 Testing Property Context...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BACKEND_URL}/property_context/+1234567890")
            response.raise_for_status()
            result = response.json()
            
            print(f"✅ Property context retrieved")
            print(f"   - Total tickets: {result['total_tickets']}")
            print(f"   - Open tickets: {result['open_tickets']}")
            print(f"   - SMS history: {len(result['sms_history'])} messages")
                
        except Exception as e:
            print(f"❌ Error testing property context: {e}")

async def main():
    """Run all tests"""
    print("🚀 Testing New Messaging System")
    print("=" * 50)
    
    # Test backend health first
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BACKEND_URL}/health")
            if response.status_code == 200:
                print("✅ Backend is running")
            else:
                print("❌ Backend health check failed")
                return
        except Exception as e:
            print(f"❌ Cannot connect to backend: {e}")
            return
    
    # Run tests
    await test_tenant_sms_processing()
    await test_property_manager_ai()
    await test_maintenance_tickets()
    await test_property_context()
    
    print("\n🎉 Testing complete!")

if __name__ == "__main__":
    asyncio.run(main())
