"""
Direct database seeding script - creates mock applications directly in database
No API token needed, uses Prisma via subprocess
"""

import asyncio
import os
import subprocess
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Use the first user ID we found
DEFAULT_USER_ID = "cmgk8d5yz0000l104mkwr8j0w"  # Michael Wang

MOCK_APPLICATIONS = [
    {
        "applicantName": "Sarah Johnson",
        "applicantEmail": "sarah.johnson@example.com",
        "applicantPhone": "555-0101",
        "creditScore": 780,
        "monthlyIncome": 7500.0,
        "annualIncome": 90000.0,
        "screeningScore": "green",
        "status": "approved",
        "propertyId": None,
    },
    {
        "applicantName": "Michael Chen",
        "applicantEmail": "michael.chen@example.com",
        "applicantPhone": "555-0102",
        "creditScore": 720,
        "monthlyIncome": 6800.0,
        "annualIncome": 81600.0,
        "screeningScore": "green",
        "status": "awaiting_tenant",
        "propertyId": None,
    },
    {
        "applicantName": "Emily Rodriguez",
        "applicantEmail": "emily.rodriguez@example.com",
        "applicantPhone": "555-0103",
        "creditScore": 695,
        "monthlyIncome": 6200.0,
        "annualIncome": 74400.0,
        "screeningScore": "green",
        "status": "scheduled",
        "propertyId": None,
    },
    {
        "applicantName": "David Kim",
        "applicantEmail": "david.kim@example.com",
        "applicantPhone": "555-0104",
        "creditScore": 650,
        "monthlyIncome": 5500.0,
        "annualIncome": 66000.0,
        "screeningScore": "yellow",
        "status": "under_review",
        "propertyId": None,
    },
    {
        "applicantName": "Jessica Martinez",
        "applicantEmail": "jessica.martinez@example.com",
        "applicantPhone": "555-0105",
        "creditScore": 640,
        "monthlyIncome": 5200.0,
        "annualIncome": 62400.0,
        "screeningScore": "yellow",
        "status": "under_review",
        "propertyId": None,
    },
    {
        "applicantName": "Robert Taylor",
        "applicantEmail": "robert.taylor@example.com",
        "applicantPhone": "555-0106",
        "creditScore": 755,
        "monthlyIncome": 8000.0,
        "annualIncome": 96000.0,
        "screeningScore": "green",
        "status": "approved",
        "propertyId": None,
    },
    {
        "applicantName": "Amanda White",
        "applicantEmail": "amanda.white@example.com",
        "applicantPhone": "555-0107",
        "creditScore": 580,
        "monthlyIncome": 4500.0,
        "annualIncome": 54000.0,
        "screeningScore": "red",
        "status": "rejected",
        "propertyId": None,
    },
    {
        "applicantName": "James Wilson",
        "applicantEmail": "james.wilson@example.com",
        "applicantPhone": "555-0108",
        "creditScore": 710,
        "monthlyIncome": 7200.0,
        "annualIncome": 86400.0,
        "screeningScore": "green",
        "status": "awaiting_tenant",
        "propertyId": None,
    },
    {
        "applicantName": "Lisa Anderson",
        "applicantEmail": "lisa.anderson@example.com",
        "applicantPhone": "555-0109",
        "creditScore": 625,
        "monthlyIncome": 5000.0,
        "annualIncome": 60000.0,
        "screeningScore": "yellow",
        "status": "under_review",
        "propertyId": None,
    },
    {
        "applicantName": "Christopher Lee",
        "applicantEmail": "christopher.lee@example.com",
        "applicantPhone": "555-0110",
        "creditScore": 690,
        "monthlyIncome": 6500.0,
        "annualIncome": 78000.0,
        "screeningScore": "green",
        "status": "approved",
        "propertyId": None,
    },
    {
        "applicantName": "Maria Garcia",
        "applicantEmail": "maria.garcia@example.com",
        "applicantPhone": "555-0111",
        "creditScore": 550,
        "monthlyIncome": 4000.0,
        "annualIncome": 48000.0,
        "screeningScore": "red",
        "status": "rejected",
        "propertyId": None,
    },
    {
        "applicantName": "Daniel Brown",
        "applicantEmail": "daniel.brown@example.com",
        "applicantPhone": "555-0112",
        "creditScore": 740,
        "monthlyIncome": 7800.0,
        "annualIncome": 93600.0,
        "screeningScore": "green",
        "status": "approved",
        "propertyId": None,
    },
    {
        "applicantName": "Jennifer Davis",
        "applicantEmail": "jennifer.davis@example.com",
        "applicantPhone": "555-0113",
        "creditScore": 630,
        "monthlyIncome": 4800.0,
        "annualIncome": 57600.0,
        "screeningScore": "yellow",
        "status": "under_review",
        "propertyId": None,
    },
    {
        "applicantName": "Matthew Thompson",
        "applicantEmail": "matthew.thompson@example.com",
        "applicantPhone": "555-0114",
        "creditScore": 715,
        "monthlyIncome": 7000.0,
        "annualIncome": 84000.0,
        "screeningScore": "green",
        "status": "awaiting_tenant",
        "propertyId": None,
    },
    {
        "applicantName": "Nicole Harris",
        "applicantEmail": "nicole.harris@example.com",
        "applicantPhone": "555-0115",
        "creditScore": 675,
        "monthlyIncome": 6000.0,
        "annualIncome": 72000.0,
        "screeningScore": "green",
        "status": "approved",
        "propertyId": None,
    },
]


def create_app_via_node(user_id: str, app_data: Dict[str, Any], days_ago: int) -> bool:
    """Create application using Node.js/Prisma directly"""
    received_date = (datetime.now() - timedelta(days=days_ago)).isoformat()
    
    script = f"""
const {{ PrismaClient }} = require('@prisma/client');
const prisma = new PrismaClient();

async function createApp() {{
  try {{
    const app = await prisma.tenantApplication.create({{
      data: {{
        userId: '{user_id}',
        propertyId: null,
        applicantName: {json.dumps(app_data['applicantName'])},
        applicantEmail: {json.dumps(app_data['applicantEmail'])},
        applicantPhone: {json.dumps(app_data.get('applicantPhone', ''))},
        emailSubject: 'Mock Tenant Application',
        emailBody: 'Mock application for demo purposes',
        driversLicenseUrl: 'mock://license',
        payStubUrls: ['mock://paystub'],
        creditScoreUrl: 'mock://credit',
        employerName: 'Mock Employer',
        monthlyIncome: {app_data.get('monthlyIncome', 0)},
        annualIncome: {app_data.get('annualIncome', 0)},
        payFrequency: 'monthly',
        creditScore: {app_data.get('creditScore')},
        status: {json.dumps(app_data.get('status', 'pending'))},
        screeningScore: {json.dumps(app_data.get('screeningScore'))},
        screeningNotes: 'Mock application - {app_data.get("screeningScore", "unknown")} screening score',
        receivedAt: new Date('{received_date}')
      }}
    }});
    console.log('SUCCESS:' + app.id);
  }} catch (error) {{
    console.error('ERROR:' + error.message);
  }} finally {{
    await prisma.$disconnect();
  }}
}}

createApp();
"""
    
    try:
        result = subprocess.run(
            ["node", "-e", script],
            cwd="propai-frontend",
            env={**os.environ, "DATABASE_URL": os.getenv("DATABASE_URL", "")},
            capture_output=True,
            text=True,
            timeout=30
        )
        if "SUCCESS:" in result.stdout:
            app_id = result.stdout.split("SUCCESS:")[1].strip()
            return True, app_id
        else:
            return False, result.stderr or result.stdout
    except Exception as e:
        return False, str(e)


def main():
    user_id = os.getenv("DEFAULT_USER_ID", DEFAULT_USER_ID)
    db_url = os.getenv("DATABASE_URL", "")
    
    if not db_url:
        # Try to get from .env.local
        try:
            with open(".env.local", "r") as f:
                for line in f:
                    if line.startswith("DATABASE_URL="):
                        db_url = line.split("=", 1)[1].strip().strip('"')
                        break
        except:
            pass
    
    if not db_url:
        print("❌ ERROR: DATABASE_URL not found")
        print("   Set DATABASE_URL environment variable or ensure .env.local exists")
        return
    
    os.environ["DATABASE_URL"] = db_url
    
    print(f"🌱 Seeding {len(MOCK_APPLICATIONS)} mock applications directly to database...")
    print(f"📊 User ID: {user_id}\n")
    
    successful = 0
    failed = 0
    
    for idx, app_data in enumerate(MOCK_APPLICATIONS):
        days_ago = idx % 14
        
        success, result = create_app_via_node(user_id, app_data, days_ago)
        
        if success:
            successful += 1
            print(f"✅ [{idx+1}/{len(MOCK_APPLICATIONS)}] Created: {app_data['applicantName']} "
                  f"(Credit: {app_data['creditScore']}, Score: {app_data['screeningScore']}, Status: {app_data['status']})")
        else:
            failed += 1
            print(f"❌ [{idx+1}/{len(MOCK_APPLICATIONS)}] Failed: {app_data['applicantName']} - {result[:100]}")
    
    print(f"\n📊 Summary:")
    print(f"   ✅ Successfully created: {successful}")
    print(f"   ❌ Failed: {failed}")
    print(f"\n🎉 {successful} applications created - they should appear on /applications page!")


if __name__ == "__main__":
    main()

