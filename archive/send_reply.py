"""
Script to send a reply to the most recent thread
"""
import asyncio
import os
import sys
from backend_modules.agentmail_service import AgentmailClient

async def send_reply(thread_id=None, reply_body=None):
    """Send a reply to a thread"""
    client = AgentmailClient()
    
    inbox_id = os.getenv("AGENTMAIL_INBOX_ID", "")
    if not inbox_id:
        print("❌ AGENTMAIL_INBOX_ID not set")
        print("   Set it with: export AGENTMAIL_INBOX_ID=screening@agentmail.to")
        return
    
    # If thread_id provided, use it; otherwise get most recent
    if thread_id:
        print(f"📧 Using provided Thread ID: {thread_id}\n")
    else:
        # Get the most recent thread
        print(f"🔍 Getting most recent thread...")
        threads = await client.list_threads(inbox_id=inbox_id)
        
        if not threads or len(threads) == 0:
            print("❌ No threads found in inbox")
            return
        
        most_recent = threads[0]
        thread_id = most_recent.get("thread_id") or most_recent.get("id")
        subject = most_recent.get("subject", "No subject")
        
        print(f"📧 Most Recent Thread:")
        print(f"   Thread ID: {thread_id}")
        print(f"   Subject: {subject}\n")
    
    # Get full thread to get the last message
    print(f"📬 Getting thread details...")
    full_thread = await client.get_thread(thread_id)
    
    if not full_thread or not full_thread.get("messages"):
        print("❌ Could not get thread messages")
        return
    
    messages = full_thread.get("messages", [])
    last_message = messages[-1]
    message_id = last_message.get("message_id") or last_message.get("id")
    sender = last_message.get("from", "")
    
    # Get subject from thread or message
    subject = full_thread.get("subject") or last_message.get("subject") or "No subject"
    
    print(f"   Last Message ID: {message_id}")
    print(f"   From: {sender}")
    print(f"   Subject: {subject}\n")
    
    # Get reply details from user or use defaults
    reply_to_email = sender
    reply_subject = f"Re: {subject}"
    
    # Default reply body - user can customize via function param or command line
    if not reply_body:
        reply_body = """Hi there,

Thank you for your interest! We'd love to schedule a showing with you.

Please let me know what times work best for you.

Best regards,
Property Management Team"""
    
    # Allow command line args for customization
    if len(sys.argv) > 1 and not reply_body:
        reply_body = sys.argv[1]
    
    print(f"📤 Sending reply...")
    print(f"   To: {reply_to_email}")
    print(f"   Subject: {reply_subject}")
    print(f"   Body: {reply_body[:50]}...\n")
    
    # Send the reply using message_id
    result = await client.send_email(
        to=reply_to_email,
        subject=reply_subject,
        body=reply_body,
        reply_to_message_id=message_id,
        reply_to_thread_id=thread_id
    )
    
    if result.get("success"):
        print(f"✅ Reply sent successfully!")
        print(f"   Message ID: {result.get('message_id')}")
        print(f"   Thread ID: {result.get('thread_id')}")
    else:
        print(f"❌ Failed to send reply: {result.get('error')}")

if __name__ == "__main__":
    # Usage:
    # python send_reply.py                              # Reply to most recent thread with default message
    # python send_reply.py "Your custom message"       # Reply to most recent with custom message
    # python send_reply.py --thread-id <id>             # Reply to specific thread
    # python send_reply.py --thread-id <id> "Message"   # Reply to specific thread with custom message
    
    thread_id = None
    reply_body = None
    
    # Parse command line args
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--thread-id" and i + 1 < len(args):
            thread_id = args[i + 1]
            i += 2
        else:
            # Assume it's the reply body
            reply_body = args[i]
            i += 1
    
    asyncio.run(send_reply(thread_id=thread_id, reply_body=reply_body))

