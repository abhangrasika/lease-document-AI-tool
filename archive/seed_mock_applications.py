"""
Seed script to create 15 mock tenant applications
This creates demo data for testing and development
"""

import asyncio
import os
import httpx
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Mock application data - varied credit scores, incomes, statuses
MOCK_APPLICATIONS = [
    {
        "applicantName": "Sarah Johnson",
        "applicantEmail": "sarah.johnson@example.com",
        "applicantPhone": "555-0101",
        "creditScore": 780,
        "monthlyIncome": 7500.0,
        "annualIncome": 90000.0,
        "incomeRatio": 3.75,
        "employerName": "TechCorp Inc",
        "screeningScore": "green",
        "status": "approved",
        "propertyId": "property_123",
        "hasLicense": True,
        "hasPayStubs": True,
        "hasCreditReport": True,
    },
    {
        "applicantName": "Michael Chen",
        "applicantEmail": "michael.chen@example.com",
        "applicantPhone": "555-0102",
        "creditScore": 720,
        "monthlyIncome": 6800.0,
        "annualIncome": 81600.0,
        "incomeRatio": 3.40,
        "employerName": "Finance Solutions LLC",
        "screeningScore": "green",
        "status": "awaiting_tenant",
        "propertyId": "property_123",
        "hasLicense": True,
        "hasPayStubs": True,
        "hasCreditReport": True,
    },
    {
        "applicantName": "Emily Rodriguez",
        "applicantEmail": "emily.rodriguez@example.com",
        "applicantPhone": "555-0103",
        "creditScore": 695,
        "monthlyIncome": 6200.0,
        "annualIncome": 74400.0,
        "incomeRatio": 3.10,
        "employerName": "Design Studio Co",
        "screeningScore": "green",
        "status": "scheduled",
        "propertyId": "property_123",
        "hasLicense": True,
        "hasPayStubs": True,
        "hasCreditReport": True,
    },
    {
        "applicantName": "David Kim",
        "applicantEmail": "david.kim@example.com",
        "applicantPhone": "555-0104",
        "creditScore": 650,
        "monthlyIncome": 5500.0,
        "annualIncome": 66000.0,
        "incomeRatio": 2.75,
        "employerName": "Marketing Pro",
        "screeningScore": "yellow",
        "status": "under_review",
        "propertyId": "property_123",
        "hasLicense": True,
        "hasPayStubs": True,
        "hasCreditReport": True,
    },
    {
        "applicantName": "Jessica Martinez",
        "applicantEmail": "jessica.martinez@example.com",
        "applicantPhone": "555-0105",
        "creditScore": 640,
        "monthlyIncome": 5200.0,
        "annualIncome": 62400.0,
        "incomeRatio": 2.60,
        "employerName": "Retail Stores Inc",
        "screeningScore": "yellow",
        "status": "under_review",
        "propertyId": "property_456",
        "hasLicense": True,
        "hasPayStubs": True,
        "hasCreditReport": False,
    },
    {
        "applicantName": "Robert Taylor",
        "applicantEmail": "robert.taylor@example.com",
        "applicantPhone": "555-0106",
        "creditScore": 755,
        "monthlyIncome": 8000.0,
        "annualIncome": 96000.0,
        "incomeRatio": 4.00,
        "employerName": "Software Solutions",
        "screeningScore": "green",
        "status": "approved",
        "propertyId": "property_456",
        "hasLicense": True,
        "hasPayStubs": True,
        "hasCreditReport": True,
    },
    {
        "applicantName": "Amanda White",
        "applicantEmail": "amanda.white@example.com",
        "applicantPhone": "555-0107",
        "creditScore": 580,
        "monthlyIncome": 4500.0,
        "annualIncome": 54000.0,
        "incomeRatio": 2.25,
        "employerName": "Service Industry Co",
        "screeningScore": "red",
        "status": "rejected",
        "propertyId": "property_456",
        "hasLicense": True,
        "hasPayStubs": True,
        "hasCreditReport": True,
    },
    {
        "applicantName": "James Wilson",
        "applicantEmail": "james.wilson@example.com",
        "applicantPhone": "555-0108",
        "creditScore": 710,
        "monthlyIncome": 7200.0,
        "annualIncome": 86400.0,
        "incomeRatio": 3.60,
        "employerName": "Construction Pro",
        "screeningScore": "green",
        "status": "awaiting_tenant",
        "propertyId": "property_789",
        "hasLicense": True,
        "hasPayStubs": True,
        "hasCreditReport": True,
    },
    {
        "applicantName": "Lisa Anderson",
        "applicantEmail": "lisa.anderson@example.com",
        "applicantPhone": "555-0109",
        "creditScore": 625,
        "monthlyIncome": 5000.0,
        "annualIncome": 60000.0,
        "incomeRatio": 2.50,
        "employerName": "Healthcare Services",
        "screeningScore": "yellow",
        "status": "under_review",
        "propertyId": "property_789",
        "hasLicense": True,
        "hasPayStubs": False,
        "hasCreditReport": True,
    },
    {
        "applicantName": "Christopher Lee",
        "applicantEmail": "christopher.lee@example.com",
        "applicantPhone": "555-0110",
        "creditScore": 690,
        "monthlyIncome": 6500.0,
        "annualIncome": 78000.0,
        "incomeRatio": 3.25,
        "employerName": "Legal Associates",
        "screeningScore": "green",
        "status": "approved",
        "propertyId": "property_789",
        "hasLicense": True,
        "hasPayStubs": True,
        "hasCreditReport": True,
    },
    {
        "applicantName": "Maria Garcia",
        "applicantEmail": "maria.garcia@example.com",
        "applicantPhone": "555-0111",
        "creditScore": 550,
        "monthlyIncome": 4000.0,
        "annualIncome": 48000.0,
        "incomeRatio": 2.00,
        "employerName": "Restaurant Group",
        "screeningScore": "red",
        "status": "rejected",
        "propertyId": "property_123",
        "hasLicense": False,
        "hasPayStubs": True,
        "hasCreditReport": True,
    },
    {
        "applicantName": "Daniel Brown",
        "applicantEmail": "daniel.brown@example.com",
        "applicantPhone": "555-0112",
        "creditScore": 740,
        "monthlyIncome": 7800.0,
        "annualIncome": 93600.0,
        "incomeRatio": 3.90,
        "employerName": "Engineering Corp",
        "screeningScore": "green",
        "status": "approved",
        "propertyId": "property_456",
        "hasLicense": True,
        "hasPayStubs": True,
        "hasCreditReport": True,
    },
    {
        "applicantName": "Jennifer Davis",
        "applicantEmail": "jennifer.davis@example.com",
        "applicantPhone": "555-0113",
        "creditScore": 630,
        "monthlyIncome": 4800.0,
        "annualIncome": 57600.0,
        "incomeRatio": 2.40,
        "employerName": "Education Services",
        "screeningScore": "yellow",
        "status": "under_review",
        "propertyId": "property_789",
        "hasLicense": True,
        "hasPayStubs": True,
        "hasCreditReport": False,
    },
    {
        "applicantName": "Matthew Thompson",
        "applicantEmail": "matthew.thompson@example.com",
        "applicantPhone": "555-0114",
        "creditScore": 715,
        "monthlyIncome": 7000.0,
        "annualIncome": 84000.0,
        "incomeRatio": 3.50,
        "employerName": "Media Productions",
        "screeningScore": "green",
        "status": "awaiting_tenant",
        "propertyId": "property_123",
        "hasLicense": True,
        "hasPayStubs": True,
        "hasCreditReport": True,
    },
    {
        "applicantName": "Nicole Harris",
        "applicantEmail": "nicole.harris@example.com",
        "applicantPhone": "555-0115",
        "creditScore": 675,
        "monthlyIncome": 6000.0,
        "annualIncome": 72000.0,
        "incomeRatio": 3.00,
        "employerName": "Consulting Firm",
        "screeningScore": "green",
        "status": "approved",
        "propertyId": "property_456",
        "hasLicense": True,
        "hasPayStubs": True,
        "hasCreditReport": True,
    },
]


async def create_mock_application_in_database(
    user_id: str,
    app_data: Dict[str, Any],
    property_rent: float = 2000.0,
    days_ago: int = 0
) -> Optional[str]:
    """
    Create a mock application in the database via frontend API
    Returns the application ID if successful, None otherwise
    """
    frontend_url = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
    service_token = os.getenv("APPLICATION_SERVICE_TOKEN", "")
    
    if not service_token:
        print(f"⚠️ APPLICATION_SERVICE_TOKEN not set, skipping database creation")
        return None
    
    # Calculate received date
    received_date = datetime.now() - timedelta(days=days_ago)
    
    # Prepare application data for database
    application_data = {
        "userId": user_id,
        "propertyId": app_data.get("propertyId"),
        "applicantName": app_data["applicantName"],
        "applicantEmail": app_data["applicantEmail"],
        "applicantPhone": app_data.get("applicantPhone"),
        "emailSubject": f"Tenant Application - {app_data['applicantName']}",
        "emailBody": f"Mock application for {app_data['applicantName']}",
        "driversLicenseUrl": f"mock://license/{app_data['applicantEmail']}" if app_data.get("hasLicense") else None,
        "payStubUrls": [f"mock://paystub/{app_data['applicantEmail']}"] if app_data.get("hasPayStubs") else [],
        "creditScoreUrl": f"mock://credit/{app_data['applicantEmail']}" if app_data.get("hasCreditReport") else None,
        "licenseName": app_data["applicantName"] if app_data.get("hasLicense") else None,
        "employerName": app_data.get("employerName"),
        "monthlyIncome": app_data.get("monthlyIncome"),
        "annualIncome": app_data.get("annualIncome"),
        "payFrequency": "monthly",
        "creditScore": app_data.get("creditScore"),
        "status": app_data.get("status", "pending"),
        "screeningScore": app_data.get("screeningScore"),
        "screeningNotes": f"Mock application - {app_data.get('screeningScore', 'unknown')} screening score"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            api_url = f"{frontend_url}/api/applications/internal"
            headers = {
                "Authorization": f"Bearer {service_token}",
                "Content-Type": "application/json"
            }
            response = await client.post(api_url, json=application_data, headers=headers)
            response.raise_for_status()
            result = response.json()
            application_id = result.get("application", {}).get("id")
            return application_id
    except Exception as e:
        print(f"⚠️ Error creating application in database: {e}")
        return None


async def seed_mock_applications(user_id: str = None):
    """
    Seed 15 mock applications into the database for demo purposes
    """
    if not user_id:
        user_id = os.getenv("DEFAULT_USER_ID", "demo_user")
    
    print(f"🌱 Seeding {len(MOCK_APPLICATIONS)} mock applications...")
    print(f"📊 User ID: {user_id}\n")
    
    # Check required environment variables
    needs_database = os.getenv("APPLICATION_SERVICE_TOKEN", "")
    
    if not needs_database:
        print("⚠️ WARNING: APPLICATION_SERVICE_TOKEN not set - cannot create applications")
        print("   Set APPLICATION_SERVICE_TOKEN to create applications in database")
        return
    
    db_successful = 0
    db_failed = 0
    
    # Stagger received dates over the past 2 weeks
    for idx, app_data in enumerate(MOCK_APPLICATIONS):
        days_ago = idx % 14  # Distribute over 14 days
        
        # Create in database
        try:
            application_id = await create_mock_application_in_database(
                user_id,
                app_data,
                property_rent=2000.0,
                days_ago=days_ago
            )
            if application_id:
                db_successful += 1
                print(f"✅ [{idx+1}/{len(MOCK_APPLICATIONS)}] {app_data['applicantName']} "
                      f"(Credit: {app_data['creditScore']}, Score: {app_data['screeningScore']}, Status: {app_data['status']})")
            else:
                db_failed += 1
                print(f"⚠️ [{idx+1}/{len(MOCK_APPLICATIONS)}] {app_data['applicantName']} - Failed")
        except Exception as e:
            db_failed += 1
            print(f"❌ [{idx+1}/{len(MOCK_APPLICATIONS)}] {app_data['applicantName']} - {str(e)}")
        
        # Small delay between requests
        await asyncio.sleep(0.5)
    
    print(f"\n📊 Summary:")
    print(f"   📝 Database: ✅ {db_successful} created, ❌ {db_failed} failed")
    
    if db_successful > 0:
        print(f"\n🎉 {db_successful} applications created in database - they should appear on /applications page!")


if __name__ == "__main__":
    import sys
    
    # Allow user_id as command line argument
    user_id = sys.argv[1] if len(sys.argv) > 1 else None
    
    asyncio.run(seed_mock_applications(user_id))

