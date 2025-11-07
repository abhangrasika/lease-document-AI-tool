"""
Quick script to get the most recent thread ID from Agentmail
"""
import asyncio
import os
from backend_modules.agentmail_service import AgentmailClient

async def get_recent_thread():
    """Get the most recent thread ID"""
    client = AgentmailClient()
    
    inbox_id = os.getenv("AGENTMAIL_INBOX_ID", "")
    if not inbox_id:
        print("❌ AGENTMAIL_INBOX_ID not set")
        return
    
    print(f"🔍 Getting most recent thread from inbox: {inbox_id}\n")
    
    # Get all threads (most recent first)
    threads = await client.list_threads(inbox_id=inbox_id)
    
    if not threads or len(threads) == 0:
        print("❌ No threads found in inbox")
        return
    
    # Get the first (most recent) thread
    most_recent = threads[0]
    thread_id = most_recent.get("thread_id") or most_recent.get("id")
    subject = most_recent.get("subject", "No subject")
    message_count = most_recent.get("message_count", 0)
    
    print(f"📧 Most Recent Thread:")
    print(f"   Thread ID: {thread_id}")
    print(f"   Subject: {subject}")
    print(f"   Message Count: {message_count}")
    
    # Get full thread details to show last message info
    full_thread = await client.get_thread(thread_id)
    if full_thread and full_thread.get("messages"):
        messages = full_thread.get("messages", [])
        last_message = messages[-1]
        message_id = last_message.get("message_id") or last_message.get("id")
        sender = last_message.get("from", "")
        
        print(f"\n📬 Last Message:")
        print(f"   Message ID: {message_id}")
        print(f"   From: {sender}")
    
    print(f"\n✅ Thread ID: {thread_id}")
    return thread_id

if __name__ == "__main__":
    thread_id = asyncio.run(get_recent_thread())

