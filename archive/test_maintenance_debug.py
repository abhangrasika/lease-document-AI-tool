#!/usr/bin/env python3
"""
Debug script to test maintenance ticket creation and retrieval
"""

import asyncio
import httpx
import json

# Backend URL
BACKEND_URL = "http://localhost:8000"

async def test_maintenance_flow():
    """Test the complete maintenance flow"""
    print("🔍 Testing Maintenance Ticket Flow")
    print("=" * 50)
    
    async with httpx.AsyncClient() as client:
        try:
            # 1. Check current state
            print("\n1. Checking current backend state...")
            response = await client.get(f"{BACKEND_URL}/debug/maintenance")
            response.raise_for_status()
            debug_info = response.json()
            
            print(f"   Maintenance tickets: {len(debug_info['maintenance_tickets'])}")
            print(f"   Phone mappings: {len(debug_info['phone_to_property'])}")
            print(f"   SMS threads: {len(debug_info['sms_messages'])}")
            
            if debug_info['phone_to_property']:
                print(f"   Phone mappings: {debug_info['phone_to_property']}")
            
            # 2. Test tenant SMS processing
            print("\n2. Testing tenant SMS processing...")
            tenant_request = {
                "message": "My toilet is broken and water is leaking everywhere! This is urgent!",
                "context": {
                    "tenant_name": "John Doe",
                    "unit": "3A",
                    "address": "123 Main St, Apartment 3A",
                    "property_name": "Sunset Apartments",
                    "tenant_phone": "+1234567890"
                },
                "phone": "+1234567890",
                "media_urls": []
            }
            
            response = await client.post(
                f"{BACKEND_URL}/tenant_sms",
                json=tenant_request,
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            
            print(f"   Response: {result['reply']}")
            print(f"   Ticket created: {result['maintenance_ticket_created']}")
            if result.get('ticket_id'):
                print(f"   Ticket ID: {result['ticket_id']}")
            
            # 3. Check maintenance tickets
            print("\n3. Checking maintenance tickets...")
            response = await client.get(f"{BACKEND_URL}/maintenance_tickets")
            response.raise_for_status()
            tickets_response = response.json()
            
            print(f"   Total tickets: {len(tickets_response['tickets'])}")
            for ticket in tickets_response['tickets']:
                print(f"   - #{ticket['id']} ({ticket['priority']}) - {ticket['issue_description'][:50]}...")
                print(f"     Tenant: {ticket['tenant_name']} ({ticket['tenant_phone']})")
                print(f"     Property: {ticket['property_name']} - Unit {ticket['unit']}")
            
            # 4. Check updated debug info
            print("\n4. Checking updated backend state...")
            response = await client.get(f"{BACKEND_URL}/debug/maintenance")
            response.raise_for_status()
            debug_info = response.json()
            
            print(f"   Maintenance tickets: {len(debug_info['maintenance_tickets'])}")
            print(f"   Phone mappings: {len(debug_info['phone_to_property'])}")
            
            if debug_info['maintenance_tickets']:
                print("\n   Latest ticket details:")
                latest_ticket = debug_info['maintenance_tickets'][-1]
                print(f"   - ID: {latest_ticket['id']}")
                print(f"   - Tenant: {latest_ticket['tenant_name']} ({latest_ticket['tenant_phone']})")
                print(f"   - Property: {latest_ticket['property_name']}")
                print(f"   - Issue: {latest_ticket['issue_description']}")
                print(f"   - Priority: {latest_ticket['priority']}")
                print(f"   - Status: {latest_ticket['status']}")
            
        except Exception as e:
            print(f"❌ Error: {e}")

async def test_property_sync():
    """Test property syncing"""
    print("\n🔄 Testing Property Sync")
    print("=" * 30)
    
    # Sample properties data
    properties = [
        {
            "id": "prop_123",
            "name": "Sunset Apartments",
            "phone": "+1234567890",
            "context": {
                "tenant_name": "John Doe",
                "unit": "3A",
                "address": "123 Main St, Apartment 3A",
                "property_name": "Sunset Apartments",
                "tenant_phone": "+1234567890"
            }
        },
        {
            "id": "prop_456",
            "name": "Downtown Loft",
            "phone": "+1987654321",
            "context": {
                "tenant_name": "Jane Smith",
                "unit": "2B",
                "address": "456 Oak Ave, Loft 2B",
                "property_name": "Downtown Loft",
                "tenant_phone": "+1987654321"
            }
        }
    ]
    
    async with httpx.AsyncClient() as client:
        try:
            print("Syncing properties to backend...")
            response = await client.post(
                f"{BACKEND_URL}/sync/properties",
                json=properties,
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            
            print(f"✅ Synced {result['synced']} properties")
            
            # Check debug info after sync
            response = await client.get(f"{BACKEND_URL}/debug/maintenance")
            response.raise_for_status()
            debug_info = response.json()
            
            print(f"Phone mappings after sync: {debug_info['phone_to_property']}")
            
        except Exception as e:
            print(f"❌ Error syncing properties: {e}")

async def main():
    """Run all tests"""
    print("🚀 Maintenance Debug Test")
    print("=" * 50)
    
    # Test property sync first
    await test_property_sync()
    
    # Then test maintenance flow
    await test_maintenance_flow()
    
    print("\n🎉 Debug test complete!")

if __name__ == "__main__":
    asyncio.run(main())
