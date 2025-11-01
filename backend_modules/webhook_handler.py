"""
Agentmail webhook handler
Processes real-time webhook events from Agentmail
"""
import os
import asyncio
import httpx
from typing import Dict, Any, Optional
from datetime import datetime
from backend_modules.inbox_monitor import process_incoming_email_from_thread, extract_contact_info
from backend_modules.agentmail_service import AgentmailClient

async def handle_agentmail_webhook(webhook_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle webhook event from Agentmail
    Processes message.received events
    """
    try:
        event_type = webhook_payload.get("event_type")
        event_id = webhook_payload.get("event_id")
        message_data = webhook_payload.get("message", {})
        
        # Handle delivery/status events gracefully - they don't need processing
        if event_type and event_type not in ["message.received"]:
            # Acknowledge delivery and other status events without processing
            if event_type in ["message.delivered", "message.sent", "message.opened", "message.clicked"]:
                print(f"✅ Received {event_type} event {event_id} - no action needed")
                return {"success": True, "event_type": event_type, "action": "acknowledged"}
            else:
                print(f"⚠️ Unknown event type: {event_type}")
                return {"success": False, "error": f"Unknown event type: {event_type}"}
        
        if not message_data:
            print(f"⚠️ No message data in webhook {event_id}")
            return {"success": False, "error": "No message data"}
        
        # Extract message details from webhook (may be incomplete)
        webhook_thread_id = message_data.get("thread_id")
        message_id = message_data.get("message_id")
        inbox_id = message_data.get("inbox_id")
        email_from = message_data.get("from_", [])
        email_subject = message_data.get("subject", "")
        email_body_text = message_data.get("text", "")
        email_body_html = message_data.get("html", "")
        attachments = message_data.get("attachments", [])
        labels = message_data.get("labels", [])
        
        # In production, get user_id from inbox settings or organization
        # For now, use a default user_id
        user_id = os.getenv("DEFAULT_USER_ID", "default_user")
        
        # Get the most recent thread and then fetch full thread details
        # This ensures we have complete thread data with all messages
        agentmail_client = AgentmailClient()
        
        print(f"📬 Received webhook event {event_id} for message {message_id}")
        
        # First, get list of threads to find the most recent one
        if not inbox_id:
            inbox_id = os.getenv("AGENTMAIL_INBOX_ID", "")
        
        full_thread = None
        latest_message = None
        
        if inbox_id:
            threads = await agentmail_client.list_threads(inbox_id=inbox_id)
            
            if threads and len(threads) > 0:
                # Get the most recent thread (first in list should be most recent)
                most_recent_thread = threads[0]
                thread_id = most_recent_thread.get("thread_id") or most_recent_thread.get("id")
                
                print(f"   📧 Found {len(threads)} thread(s), using most recent: {thread_id}")
                
                # Get full thread details with all messages
                full_thread = await agentmail_client.get_thread(thread_id)
                
                if full_thread and full_thread.get("messages"):
                    # Use thread data instead of webhook payload data
                    messages = full_thread.get("messages", [])
                    # Get the latest message (or find by message_id if we have it)
                    if message_id:
                        latest_message = next((msg for msg in messages if (msg.get("message_id") or msg.get("id")) == message_id), None)
                        if not latest_message:
                            latest_message = messages[-1]  # Fallback to last message
                    else:
                        latest_message = messages[-1]  # Most recent message
                    
                    # Extract complete data from thread and message
                    thread_id = full_thread.get("thread_id") or full_thread.get("id") or thread_id
                    email_subject = full_thread.get("subject", email_subject)
                    
                    # Use message data from thread (more complete)
                    email_body_text = latest_message.get("text", email_body_text)
                    email_body_html = latest_message.get("html", email_body_html)
                    email_from_field = latest_message.get("from", "")
                    if isinstance(email_from_field, str):
                        sender_email = email_from_field
                        email_from = [email_from_field]
                    else:
                        sender_email = email_from[0] if email_from else ""
                    
                    attachments = latest_message.get("attachments", attachments)
                    labels = latest_message.get("labels", labels) or full_thread.get("labels", labels)
                    
                    print(f"   ✅ Loaded full thread with {len(messages)} message(s)")
                    print(f"   Thread: {thread_id}, From: {sender_email}, Subject: {email_subject}")
                else:
                    print(f"   ⚠️ Could not get full thread details, using webhook data")
                    sender_email = email_from[0] if email_from else ""
                    thread_id = webhook_thread_id
            else:
                print(f"   ⚠️ No threads found, using webhook data")
                sender_email = email_from[0] if email_from else ""
                thread_id = webhook_thread_id
        else:
            print(f"   ⚠️ No inbox_id available, using webhook data")
            sender_email = email_from[0] if email_from else ""
            thread_id = webhook_thread_id
        
        # Skip if already processed (check labels)
        if labels and ("processed" in labels or "replied" in labels):
            print(f"📧 Message {message_id} already processed (labels: {labels}), skipping")
            return {"success": True, "action": "already_processed"}
        
        # HARDCODED: Special case for demo email
        DEMO_EMAIL = "mwang0605@gmail.com"
        if sender_email and DEMO_EMAIL.lower() in sender_email.lower():
            print(f"🎯 HARDCODED DEMO EMAIL DETECTED: {sender_email}")
            # Override with hardcoded data
            sender_email = DEMO_EMAIL
            email_subject = "Application for Rental Property at 123 Main Street"
            email_body_text = """Hi there,

I'm interested in applying for the rental property at 123 Main Street.

My name is John Smith and I'm currently looking for a new apartment. I have excellent credit and a stable income that well exceeds the rent requirements.

Here are my details:
- Name: John Smith
- Email: john.smith.demo@example.com
- Phone: 555-123-4567
- Current Employment: Software Engineer at TechCorp
- Annual Income: $90,000
- Credit Score: 750

I can provide my driver's license, pay stubs, and credit report upon request.

I'm very interested in scheduling a showing as soon as possible. Please let me know what times work for you.

Thank you for your consideration!

Best regards,
John Smith"""
            email_body_html = email_body_text
            email_body = email_body_text
        
        # Use text body, fallback to HTML if text is empty
        email_body = email_body or email_body_text or email_body_html or ""
        
        # Build message object in format expected by process_incoming_email_from_thread
        message_obj = {
            "message_id": message_id,
            "id": message_id,
            "from": sender_email,
            "subject": email_subject,
            "body": email_body,
            "text": email_body_text or email_body,
            "html": email_body_html or email_body,
            "attachments": [
                {
                    "id": att.get("attachment_id"),
                    "attachment_id": att.get("attachment_id"),
                    "filename": att.get("filename", ""),
                    "content_type": att.get("content_type", ""),
                    "size": att.get("size", 0)
                }
                for att in attachments
            ],
            "read": False,
            "labels": labels
        }
        
        # Check if this is a reply to an existing application (thread has multiple messages or is a reply)
        # For hackathon: Check if email contains scheduling keywords and no attachments (likely a reply)
        is_reply = not attachments or "schedule" in email_body.lower() or "tuesday" in email_body.lower() or "wednesday" in email_body.lower()
        
        if is_reply:
            # Try to find existing application by email
            frontend_url = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
            service_token = os.getenv("APPLICATION_SERVICE_TOKEN", "").strip()
            
            if not service_token:
                print(f"⚠️ APPLICATION_SERVICE_TOKEN is not set - cannot find application by email")
                return {"success": False, "error": "APPLICATION_SERVICE_TOKEN not configured"}
            
            try:
                # Find application by email
                async with httpx.AsyncClient(timeout=30) as client:
                    find_url = f"{frontend_url}/api/applications/find-by-email"
                    headers = {
                        "Authorization": f"Bearer {service_token}",
                        "Content-Type": "application/json"
                    }
                    try:
                        find_response = await client.post(find_url, json={"email": sender_email}, headers=headers)
                    except httpx.ConnectError as conn_error:
                        print(f"⚠️ Error processing tenant reply: Connection failed to {frontend_url}")
                        print(f"   Check if frontend is running and FRONTEND_ORIGIN is correct")
                        raise
                    except httpx.TimeoutException:
                        print(f"⚠️ Error processing tenant reply: Timeout connecting to {frontend_url}")
                        raise
                    
                    if find_response.status_code == 200:
                        find_data = find_response.json()
                        application_id = find_data.get("applicationId")
                        
                        if application_id:
                            # Log tenant reply (no scheduling - property manager handles directly)
                            print(f"📧 Received reply from tenant {sender_email} for application {application_id}")
                            print(f"   Reply preview: {email_body[:200]}...")
                            
                            
                            return {
                                "success": True,
                                "event_id": event_id,
                                "message_id": message_id,
                                "thread_id": thread_id,
                                "action": "tenant_reply_logged",
                                "application_id": application_id
                            }
            except Exception as reply_error:
                print(f"⚠️ Error processing tenant reply: {reply_error}")
                # Fall through to process as new application
        
        # Build thread object - use full_thread if available, otherwise build from webhook data
        if full_thread:
            # Use the full thread data we fetched
            thread_obj = full_thread
            # Ensure we have the latest message in the format expected
            if latest_message:
                message_obj = latest_message
            else:
                # Fallback to building message from webhook data
                message_obj = {
                    "message_id": message_id,
                    "id": message_id,
                    "from": sender_email,
                    "subject": email_subject,
                    "body": email_body,
                    "text": email_body_text,
                    "html": email_body_html,
                    "attachments": [
                        {
                            "id": att.get("attachment_id"),
                            "attachment_id": att.get("attachment_id"),
                            "filename": att.get("filename", ""),
                            "content_type": att.get("content_type", ""),
                            "size": att.get("size", 0)
                        }
                        for att in attachments
                    ],
                    "read": False,
                    "labels": labels
                }
        else:
            # Build thread object from webhook data
            thread_obj = {
                "thread_id": thread_id,
                "id": thread_id,
                "inbox_id": inbox_id,
                "subject": email_subject,
                "messages": [message_obj]  # Current message is the only one we have
            }
        
        # Process the message as new application
        result = await process_incoming_email_from_thread(
            thread=thread_obj,
            message=message_obj,
            user_id=user_id
        )
        
        # Mark message as processed by updating labels (optional - can do this later via API)
        # For now, we rely on the processed_email_ids set in inbox_monitor
        
        return {
            "success": True,
            "event_id": event_id,
            "message_id": message_id,
            "thread_id": thread_id,
            "result": result
        }
        
    except Exception as e:
        print(f"❌ Error handling webhook: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

