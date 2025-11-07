"""
Quick test script to verify Agentmail connection
Tests that emails are being read from Agentmail
"""

import asyncio
import os
from backend_modules.agentmail_service import AgentmailClient

async def test_agentmail():
    """Test Agentmail connection"""
    
    # Check credentials
    agentmail_key = os.getenv("AGENTMAIL_API_KEY", "")
    inbox_id = os.getenv("AGENTMAIL_INBOX_ID", "")
    
    print("🔍 Testing Agentmail Connection\n")
    
    # Test 1: Check Agentmail connection
    print("1️⃣ Testing Agentmail connection...")
    agentmail_client = AgentmailClient()
    if not agentmail_key:
        print("   ❌ AGENTMAIL_API_KEY not set")
    else:
        threads = await agentmail_client.list_threads(inbox_id=inbox_id)
        print(f"   ✅ Connected - Found {len(threads)} email thread(s)")
        if threads:
            for idx, thread in enumerate(threads[:5], 1):
                thread_id = thread.get("thread_id") or thread.get("id")
                subject = thread.get("subject", "No subject")
                print(f"      {idx}. {subject[:50]}...")
    
    print("\n✅ Test complete!")
    print("\n💡 Tip: When webhooks are set up, emails will be processed automatically!")

if __name__ == "__main__":
    asyncio.run(test_agentmail())

