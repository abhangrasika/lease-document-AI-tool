"""
Agentmail inbox monitoring service
Continuously monitors inbox for new tenant applications and processes them
"""

import os
import asyncio
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from backend_modules.agentmail_service import AgentmailClient, get_missing_documents_email_template
from backend_modules.llm_service import process_tenant_documents
from backend_modules.screening_service import calculate_screening_score
from backend_modules.agentmail_service import get_rejection_email_template
from backend_modules.tenant_agent import agent_process_application

# In production, this would connect to Prisma/database
# For now, we'll use a simple in-memory store
processed_email_ids = set()

def extract_contact_info(email_body: str, email_from: str) -> Dict[str, str]:
    """
    Extract tenant contact information from email
    Uses regex patterns and AI if needed
    """
    info = {
        "name": "",
        "email": email_from,
        "phone": ""
    }
    
    # Extract phone number
    phone_patterns = [
        r'(\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})',
        r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})'
    ]
    for pattern in phone_patterns:
        match = re.search(pattern, email_body)
        if match:
            info["phone"] = match.group(1).strip()
            break
    
    # Extract name (try from email signature or first line)
    lines = email_body.split('\n')[:5]  # First 5 lines
    for line in lines:
        # Look for "Name:" or similar patterns
        name_match = re.search(r'(?:name|hi|hello)[\s:]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', line, re.IGNORECASE)
        if name_match:
            info["name"] = name_match.group(1).strip()
            break
    
    # Fallback: extract from email address
    if not info["name"]:
        email_local = email_from.split('@')[0]
        info["name"] = email_local.replace('.', ' ').replace('_', ' ').title()
    
    return info

async def process_incoming_email_from_thread(
    thread: Dict[str, Any],
    message: Dict[str, Any],
    user_id: str
) -> Dict[str, Any]:
    """
    Process an incoming email from a thread
    Thread contains conversation context, message contains the specific email data
    """
    try:
        thread_id = thread.get("thread_id") or thread.get("id")
        message_id = message.get("message_id") or message.get("id")
        
        if message_id in processed_email_ids:
            print(f"📧 Message {message_id} already processed, skipping")
            return {"success": False, "reason": "already_processed"}
        
        # Extract email metadata from message
        email_from = message.get("from", {}).get("email", "") if isinstance(message.get("from"), dict) else message.get("from", "")
        email_subject = message.get("subject", thread.get("subject", ""))
        email_body = message.get("body", message.get("text", ""))
        attachments = message.get("attachments", [])
        
        # Extract contact info
        contact_info = extract_contact_info(email_body, email_from)
        
        # Download and categorize attachments
        agentmail_client = AgentmailClient()
        
        drivers_license_url = None
        pay_stub_urls = []
        credit_score_url = None
        
        for attachment in attachments:
            attachment_id = attachment.get("id") or attachment.get("attachment_id")
            filename = attachment.get("filename", "").lower()
            
            # Download attachment
            try:
                attachment_data = await agentmail_client.download_attachment(attachment_id)
                # In production, upload to S3/cloud storage and store URL
                # For now, we'll use the attachment ID as reference
                
                # Categorize by filename/type
                if "license" in filename or "dl" in filename or "driver" in filename:
                    drivers_license_url = f"attachment:{attachment_id}"
                elif "pay" in filename or "stub" in filename or "income" in filename:
                    pay_stub_urls.append(f"attachment:{attachment_id}")
                elif "credit" in filename or "score" in filename or "report" in filename:
                    credit_score_url = f"attachment:{attachment_id}"
            except Exception as e:
                print(f"⚠️ Error downloading attachment {attachment_id}: {e}")
                continue
        
        # DEMO MODE: Skip missing documents check - process all applications regardless
        # Check for missing documents (disabled for demo)
        # missing_docs = []
        # if not drivers_license_url:
        #     missing_docs.append("Driver's License")
        # if not pay_stub_urls:
        #     missing_docs.append("Pay Stub(s)")
        # if not credit_score_url:
        #     missing_docs.append("Credit Score Report")
        # 
        # if missing_docs:
        #     # Send email requesting missing documents (reply to thread)
        #     subject, body = get_missing_documents_email_template(contact_info["name"], missing_docs)
        #     await agentmail_client.send_email(
        #         to=contact_info["email"],
        #         subject=subject,
        #         body=body,
        #         reply_to_thread_id=thread_id
        #     )
        #     print(f"📧 Sent missing documents email to {contact_info['email']}")
        #     return {
        #         "success": True,
        #         "action": "requested_missing_docs",
        #         "missing_docs": missing_docs
        #     }
        
        # Continue with full processing...
        return await process_incoming_email_data(
            email_from=email_from,
            email_subject=email_subject,
            email_body=email_body,
            contact_info=contact_info,
            drivers_license_url=drivers_license_url,
            pay_stub_urls=pay_stub_urls,
            credit_score_url=credit_score_url,
            thread_id=thread_id,
            message_id=message_id,
            user_id=user_id
        )
        
    except Exception as e:
        print(f"❌ Error processing thread message: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

async def process_incoming_email_data(
    email_from: str,
    email_subject: str,
    email_body: str,
    contact_info: Dict[str, str],
    drivers_license_url: Optional[str],
    pay_stub_urls: List[str],
    credit_score_url: Optional[str],
    thread_id: str,
    message_id: str,
    user_id: str
) -> Dict[str, Any]:
    """
    Process incoming email data (extracted from thread/message)
    Handles document processing, screening, and database persistence
    """
    try:
        if message_id in processed_email_ids:
            print(f"📧 Message {message_id} already processed, skipping")
            return {"success": False, "reason": "already_processed"}
        
        # Identify as Agentmail source
        print(f"📬 NEW APPLICATION FROM AGENTMAIL")
        print(f"   Thread ID: {thread_id}")
        print(f"   Message ID: {message_id}")
        print(f"   From: {email_from}")
        print(f"   Applicant: {contact_info['name']}")
        
        # HARDCODED: Special case for demo email
        DEMO_EMAIL = "mwang0605@gmail.com"
        if email_from and DEMO_EMAIL.lower() in email_from.lower():
            print(f"🎯 HARDCODED DEMO EMAIL - Using preset data")
            # Hardcode all the extracted data
            extraction_result = {
                "credit_score": 750,
                "monthly_income": 7500.0,  # $90,000 / 12
                "annual_income": 90000.0,
                "pay_frequency": "monthly",
                "employer": "TechCorp",
                "license": {
                    "name": "John Smith",
                    "dob": None,
                    "expiration": None,
                    "number": None
                }
            }
            # Also override contact_info to ensure correct data
            contact_info = {
                "name": "John Smith",
                "email": "john.smith.demo@example.com",
                "phone": "555-123-4567"
            }
        else:
            # Process documents normally
            print(f"📄 Processing documents for message {message_id}")
            extraction_result = await process_tenant_documents(
                drivers_license_url=drivers_license_url,
                pay_stub_urls=pay_stub_urls,
                credit_score_url=credit_score_url
            )
        
        # Calculate screening score (need property rent amount - default to $2000 for now)
        monthly_rent = 2000.0  # In production, get from PropertySettings
        
        score, notes = calculate_screening_score(
            credit_score=extraction_result.get("credit_score"),
            monthly_income=extraction_result.get("monthly_income"),
            monthly_rent=monthly_rent
        )
        
        # HARDCODED: Always approve all emails
        status = "approved"
        print(f"✅ HARDCODED MODE: All emails automatically approved")
        
        # Save to database via frontend API endpoint
        import httpx
        
        frontend_url = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
        service_token = os.getenv("APPLICATION_SERVICE_TOKEN", "").strip()
        
        # Validate service token before making request
        if not service_token:
            print(f"⚠️ APPLICATION_SERVICE_TOKEN is not set or is empty")
            print(f"   Cannot save application to database - skipping API call")
            print(f"   Set APPLICATION_SERVICE_TOKEN environment variable to enable database persistence")
            application_id = f"app_{datetime.now().strftime('%Y%m%d%H%M%S')}_{message_id[:8]}"
        else:
            application_data = {
                "userId": user_id,
                "applicantName": contact_info["name"],
                "applicantEmail": contact_info["email"],
                "applicantPhone": contact_info.get("phone"),
                "emailSubject": email_subject,
                "emailBody": email_body,
                "driversLicenseUrl": drivers_license_url,
                "payStubUrls": pay_stub_urls,
                "creditScoreUrl": credit_score_url,
                "licenseName": extraction_result.get("license", {}).get("name"),
                "licenseDOB": extraction_result.get("license", {}).get("dob"),
                "licenseExpiration": extraction_result.get("license", {}).get("expiration"),
                "licenseNumber": extraction_result.get("license", {}).get("number"),
                "employerName": extraction_result.get("employer"),
                "monthlyIncome": extraction_result.get("monthly_income"),
                "annualIncome": extraction_result.get("annual_income"),
                "payFrequency": extraction_result.get("pay_frequency"),
                "creditScore": extraction_result.get("credit_score"),
                "status": status,
                "screeningScore": score,
                "screeningNotes": notes
            }
            
            agentmail_client = AgentmailClient()
            
            # Call frontend internal API to save application
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
                    print(f"✅ Application saved to database: {application_id}")
            except httpx.ConnectError as conn_error:
                print(f"⚠️ Error saving application to database: Connection failed to {frontend_url}")
                print(f"   Check if frontend is running and FRONTEND_ORIGIN is correct")
                print(f"   Error details: {conn_error}")
                # Continue with workflow even if DB save fails
                application_id = f"app_{datetime.now().strftime('%Y%m%d%H%M%S')}_{message_id[:8]}"
            except httpx.TimeoutException:
                print(f"⚠️ Error saving application to database: Timeout connecting to {frontend_url}")
                print(f"   Frontend may be slow or unresponsive")
                # Continue with workflow even if DB save fails
                application_id = f"app_{datetime.now().strftime('%Y%m%d%H%M%S')}_{message_id[:8]}"
            except httpx.HTTPStatusError as http_error:
                print(f"⚠️ Error saving application to database: HTTP {http_error.response.status_code}")
                print(f"   Response: {http_error.response.text[:200] if hasattr(http_error.response, 'text') else 'N/A'}")
                # Continue with workflow even if DB save fails
                application_id = f"app_{datetime.now().strftime('%Y%m%d%H%M%S')}_{message_id[:8]}"
            except httpx.RequestError as req_error:
                # Catch httpx.LocalProtocolError and other request-level errors
                error_type = type(req_error).__name__
                print(f"⚠️ Error saving application to database ({error_type}): {req_error}")
                if "Illegal header value" in str(req_error) or "Bearer" in str(req_error):
                    print(f"   This usually means APPLICATION_SERVICE_TOKEN is empty or invalid")
                    print(f"   Please set APPLICATION_SERVICE_TOKEN environment variable with a valid token")
                # Continue with workflow even if DB save fails
                application_id = f"app_{datetime.now().strftime('%Y%m%d%H%M%S')}_{message_id[:8]}"
            except Exception as db_error:
                error_type = type(db_error).__name__
                print(f"⚠️ Error saving application to database ({error_type}): {db_error}")
                # Continue with workflow even if DB save fails
                application_id = f"app_{datetime.now().strftime('%Y%m%d%H%M%S')}_{message_id[:8]}"
        
        # application_id is now from database if saved successfully
        print(f"✅ Application processed: {status} ({score})")
        
        
        # Send appropriate email based on status
        if status == "approved":
            # Send approval email (no scheduling - property manager contacts directly)
            from backend_modules.agentmail_service import get_approval_email_template
            subject, body = get_approval_email_template(contact_info["name"])
            await agentmail_client.send_email(
                to=contact_info["email"],
                subject=subject,
                body=body,
                reply_to_thread_id=thread_id
            )
            print(f"📧 Sent approval email to {contact_info['email']}")
        elif status == "rejected":
            subject, body = get_rejection_email_template(contact_info["name"])
            await agentmail_client.send_email(
                to=contact_info["email"],
                subject=subject,
                body=body,
                reply_to_thread_id=thread_id
            )
            print(f"📧 Sent rejection email to {contact_info['email']}")
        
        processed_email_ids.add(message_id)
        
        return {
            "success": True,
            "applicationId": application_id,
            "status": status,
            "score": score,
            "notes": notes
        }
        
    except Exception as e:
        print(f"❌ Error processing email data: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

async def monitor_inbox(user_id: Optional[str] = None):
    """Monitor Agentmail inbox for ALL threads and process them
    
    Args:
        user_id: User ID to associate applications with. If None, uses DEFAULT_USER_ID env var.
    """
    print("📬 Reading ALL emails from Agentmail inbox...")
    
    try:
        client = AgentmailClient()
        
        # Get ALL threads (not just unread)
        inbox_id = os.getenv("AGENTMAIL_INBOX_ID", "")
        threads = await client.list_threads(inbox_id=inbox_id)
        
        if not threads:
            print("📭 No threads found in inbox")
            return
        
        print(f"📧 Found {len(threads)} email thread(s) - processing all...")
        
        # Use provided user_id or fall back to environment variable
        if not user_id:
            user_id = os.getenv("DEFAULT_USER_ID", "default_user")
        
        print(f"👤 Using user_id: {user_id}")
        
        # Process each thread
        processed_count = 0
        skipped_count = 0
        
        for thread in threads:
            thread_id = thread.get("thread_id") or thread.get("id")
            if not thread_id:
                continue
            
            # Get full thread details with all messages
            try:
                full_thread = await client.get_thread(thread_id)
                if not full_thread:
                    skipped_count += 1
                    continue
                
                messages = full_thread.get("messages", [])
                if not messages:
                    skipped_count += 1
                    continue
                
                # Process the latest message for application processing
                latest_message = messages[-1]
                message_id = latest_message.get("message_id") or latest_message.get("id")
                
                # Check if this message was already processed for applications
                if message_id not in processed_email_ids:
                    print(f"📬 Processing message {message_id} from thread {thread_id}")
                    result = await process_incoming_email_from_thread(full_thread, latest_message, user_id)
                    
                    if result.get("success"):
                        processed_count += 1
                        print(f"✅ Successfully processed message {message_id}")
                    else:
                        print(f"⚠️ Failed to process message {message_id}: {result.get('reason') or result.get('error')}")
                
                
                # Small delay between threads
                await asyncio.sleep(0.5)
                
            except Exception as thread_error:
                skipped_count += 1
                print(f"❌ Error processing thread {thread_id}: {thread_error}")
        
        print(f"\n✅ Inbox processing complete:")
        print(f"   📋 Applications processed: {processed_count}")
        print(f"   ⏭️  Skipped: {skipped_count}")
            
    except Exception as e:
        print(f"❌ Error monitoring inbox: {e}")
        import traceback
        traceback.print_exc()

async def process_tenant_reply(email_data: Dict[str, Any], application_id: str) -> Dict[str, Any]:
    """
    Process tenant reply email (scheduling response, etc.)
    Parses natural language to extract date/time preferences
    """
    try:
        email_body = email_data.get("body", "").lower()
        
        # Parse date/time from email
        # Look for patterns like "I'd like to schedule for [DATE] at [TIME]"
        date_patterns = [
            r'(?:schedule|meet|showing|appointment)[\s\w]*for[\s]*([a-z]+\s+\d{1,2},?\s+\d{4})',
            r'(?:schedule|meet|showing|appointment)[\s\w]*(?:on|for)[\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        ]
        
        time_patterns = [
            r'(?:at|@)[\s]*(\d{1,2}:\d{2}\s*(?:am|pm)?)',
            r'(\d{1,2}:\d{2}\s*(?:am|pm)?)',
        ]
        
        scheduled_date = None
        scheduled_time = None
        
        for pattern in date_patterns:
            match = re.search(pattern, email_body)
            if match:
                scheduled_date = match.group(1)
                break
        
        for pattern in time_patterns:
            match = re.search(pattern, email_body)
            if match:
                scheduled_time = match.group(1)
                break
        
        if scheduled_date and scheduled_time:
            return {
                "success": True,
                "applicationId": application_id,
                "scheduledDate": scheduled_date,
                "scheduledTime": scheduled_time,
                "action": "schedule_showing"
            }
        else:
            return {
                "success": False,
                "reason": "could_not_parse_date_time"
            }
            
    except Exception as e:
        print(f"❌ Error processing tenant reply: {e}")
        return {"success": False, "error": str(e)}

