#!/usr/bin/env python3
"""
Test script for the enhanced tenant prompt engineering system
"""

import asyncio
import json
from minimal_backend import process_tenant_sms, TenantSmsRequest, Context

async def test_enhanced_tenant_prompt():
    """Test the enhanced tenant prompt system with various scenarios"""
    
    print("🧪 Testing Enhanced Tenant Prompt Engineering System")
    print("=" * 60)
    
    # Test scenarios
    test_cases = [
        {
            "name": "Basic Introduction Test",
            "message": "Hi, I'm having an issue with my toilet",
            "context": Context(
                tenant_name="John Doe",
                unit="3A",
                address="123 Main St, Apartment 3A",
                property_name="Sunset Apartments",
                tenant_phone="+1234567890",
                hotline="+1-555-MAINT",
                portal_url="https://tenant-portal.example.com"
            ),
            "phone": "+1234567890"
        },
        {
            "name": "Maintenance Issue with Troubleshooting",
            "message": "My sink is clogged and water is backing up",
            "context": Context(
                tenant_name="Sarah Johnson",
                unit="2B",
                address="456 Oak Ave, Unit 2B",
                property_name="Oak Gardens",
                tenant_phone="+1987654321",
                hotline="+1-555-HELP",
                portal_url="https://oakgardens.portal.com"
            ),
            "phone": "+1987654321"
        },
        {
            "name": "Emergency Issue",
            "message": "There's water leaking from my ceiling and it's getting worse!",
            "context": Context(
                tenant_name="Mike Wilson",
                unit="4C",
                address="789 Pine St, Apt 4C",
                property_name="Pine Heights",
                tenant_phone="+1555123456",
                hotline="+1-555-URGENT",
                portal_url="https://pineheights.portal.com"
            ),
            "phone": "+1555123456"
        },
        {
            "name": "General Question",
            "message": "What's the policy on pets?",
            "context": Context(
                tenant_name="Lisa Chen",
                unit="1A",
                address="321 Elm St, Unit 1A",
                property_name="Elm Manor",
                tenant_phone="+1444333222",
                hotline="+1-555-INFO",
                portal_url="https://elmmanor.portal.com"
            ),
            "phone": "+1444333222"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test Case {i}: {test_case['name']}")
        print("-" * 40)
        print(f"Message: {test_case['message']}")
        print(f"Tenant: {test_case['context'].tenant_name} ({test_case['context'].unit})")
        print(f"Property: {test_case['context'].property_name}")
        
        try:
            # Create request
            request = TenantSmsRequest(
                message=test_case['message'],
                context=test_case['context'],
                phone=test_case['phone']
            )
            
            # Process the request
            response = await process_tenant_sms(request)
            
            print(f"\n🤖 AI Response:")
            print(f"Reply: {response.reply}")
            print(f"Ticket Created: {response.maintenance_ticket_created}")
            if response.ticket_id:
                print(f"Ticket ID: {response.ticket_id}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "="*60)

if __name__ == "__main__":
    asyncio.run(test_enhanced_tenant_prompt())
