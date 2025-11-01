"""
Agentmail service for email sending and receiving
Handles both inbox monitoring and email sending for tenant applications
"""

import os
import httpx
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

AGENTMAIL_API_KEY = os.getenv("AGENTMAIL_API_KEY", "")
AGENTMAIL_INBOX_ID = os.getenv("AGENTMAIL_INBOX_ID", "")
AGENTMAIL_API_URL = os.getenv("AGENTMAIL_API_URL", "https://api.agentmail.to")

# Ensure API URL has protocol prefix and is not empty
if not AGENTMAIL_API_URL or not AGENTMAIL_API_URL.strip():
    AGENTMAIL_API_URL = "https://api.agentmail.to"
elif not AGENTMAIL_API_URL.startswith(("http://", "https://")):
    AGENTMAIL_API_URL = f"https://{AGENTMAIL_API_URL.strip()}"

class AgentmailClient:
    """Client for Agentmail API operations"""
    
    def __init__(self):
        self.api_key = (AGENTMAIL_API_KEY or "").strip()
        self.inbox_id = AGENTMAIL_INBOX_ID
        self.api_url = AGENTMAIL_API_URL
        
        # Additional validation - ensure URL is not empty and has protocol
        if not self.api_url or not self.api_url.strip():
            print(f"⚠️ Warning: AGENTMAIL_API_URL is empty, using default")
            self.api_url = "https://api.agentmail.to"
        elif not self.api_url.startswith(("http://", "https://")):
            print(f"⚠️ Warning: AGENTMAIL_API_URL missing protocol, adding https://")
            self.api_url = f"https://{self.api_url.strip()}"
        
        # Final safety check before using
        if not self.api_url.startswith(("http://", "https://")):
            raise ValueError(f"Invalid AGENTMAIL_API_URL: {self.api_url} - must start with http:// or https://")
        
        # Validate API key and create headers
        if not self.api_key:
            print(f"⚠️ Warning: AGENTMAIL_API_KEY is empty - API calls may fail")
            self.headers = {
                "Content-Type": "application/json"
            }
        else:
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
    
    async def list_threads(self, inbox_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List threads from Agentmail
        If inbox_id is provided, lists threads for that inbox only
        If inbox_id is None, lists all threads across the organization
        """
        if not self.api_key:
            print("⚠️ Agentmail credentials not configured")
            return []
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                if inbox_id:
                    # List threads for specific inbox
                    url = f"{self.api_url}/v0/inboxes/{inbox_id}/threads"
                else:
                    # List threads across organization (per API docs: /v0/threads)
                    url = f"{self.api_url}/v0/threads"
                
                # Safety check on constructed URL
                if not url.startswith(("http://", "https://")):
                    raise ValueError(f"Invalid URL constructed: {url} - missing protocol. api_url was: {self.api_url}")
                
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                # Handle both list response format and direct array
                if isinstance(data, dict):
                    return data.get("threads", data.get("data", []))
                return data if isinstance(data, list) else []
        except Exception as e:
            print(f"❌ Error listing Agentmail threads: {e}")
            return []
    
    async def get_thread(self, thread_id: str) -> Dict[str, Any]:
        """
        Get a single thread by ID
        Returns thread with its messages
        """
        if not self.api_key:
            print("⚠️ Agentmail credentials not configured")
            return {}
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Per API docs: /v0/threads/{thread_id}
                url = f"{self.api_url}/v0/threads/{thread_id}"
                
                # Safety check on constructed URL
                if not url.startswith(("http://", "https://")):
                    raise ValueError(f"Invalid URL constructed: {url} - missing protocol. api_url was: {self.api_url}")
                
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"❌ Error getting Agentmail thread: {e}")
            return {}
    
    async def check_inbox(self, user_id: Optional[str] = None, auto_index: bool = True) -> List[Dict[str, Any]]:
        """
        Poll inbox for new threads (conversations)
        Returns list of threads with unread messages
        
        Since Agentmail's list_threads() may not include messages in the response,
        we fetch full thread details for all threads and check for unread messages.
        
        Args:
            user_id: Optional user ID for processing
            auto_index: If True, automatically extract email info
        """
        if not self.api_key or not self.inbox_id:
            print("⚠️ Agentmail credentials not configured")
            return []
        
        try:
            # Get all threads for this inbox
            threads = await self.list_threads(self.inbox_id)
            
            if not threads:
                print("📭 No threads found in inbox")
                return []
            
            print(f"📬 Found {len(threads)} thread(s) in inbox, checking for unread messages...")
            
            # Filter for threads with unread messages
            new_threads = []
            for thread in threads:
                thread_id = thread.get("thread_id") or thread.get("id")
                if not thread_id:
                    continue
                
                # Get full thread details to check for unread messages
                # (list_threads() may not include messages in the response)
                full_thread = await self.get_thread(thread_id)
                if not full_thread:
                    continue
                
                # Check if thread has unread messages
                messages = full_thread.get("messages", [])
                if not messages:
                    # No messages yet, skip
                    continue
                
                unread_messages = [msg for msg in messages if not msg.get("read", False)]
                
                if unread_messages:
                    print(f"📧 Thread {thread_id} has {len(unread_messages)} unread message(s)")
                    
                    # Extract email info if requested
                    if auto_index and user_id:
                        try:
                            extract_result = await self.extract_email_info(
                                thread=full_thread
                            )
                            if extract_result.get("success"):
                                abstracted = extract_result.get("abstracted_info", {})
                                print(f"   ✅ Extracted info: name={abstracted.get('name')}, credit={abstracted.get('credit_score')}, income=${abstracted.get('monthly_income', 0):,.2f}")
                            else:
                                print(f"   ⚠️ Could not extract email info: {extract_result.get('error')}")
                        except Exception as extract_error:
                            print(f"   ⚠️ Error extracting email info: {extract_error}")
                    
                    new_threads.append(full_thread)
            
            print(f"✅ Found {len(new_threads)} thread(s) with unread messages")
            return new_threads
        except Exception as e:
            print(f"❌ Error checking Agentmail inbox: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        reply_to_message_id: Optional[str] = None,
        reply_to_thread_id: Optional[str] = None,
        attachments: List[str] = []
    ) -> Dict[str, Any]:
        """
        Send email via Agentmail API
        If reply_to_thread_id is provided, replies to that thread
        If reply_to_message_id is provided, replies to that specific message
        """
        if not self.api_key or not self.inbox_id:
            print("⚠️ Agentmail credentials not configured")
            return {"success": False, "error": "Agentmail not configured"}
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                if reply_to_thread_id or reply_to_message_id:
                    # Reply to existing thread/message
                    # Per Agentmail docs: Use inboxes.messages.reply with message_id
                    message_id_to_reply = reply_to_message_id
                    thread_id = reply_to_thread_id
                    
                    # If we have thread_id but not message_id, get the last message from thread
                    if thread_id and not message_id_to_reply:
                        print(f"📧 Getting last message from thread {thread_id} for reply")
                        try:
                            thread_details = await self.get_thread(thread_id)
                            if thread_details and thread_details.get("messages"):
                                messages = thread_details.get("messages", [])
                                if messages:
                                    last_message = messages[-1]
                                    message_id_to_reply = last_message.get("message_id") or last_message.get("id")
                                    print(f"   ✅ Found last message: {message_id_to_reply}")
                                else:
                                    print(f"   ⚠️ Thread has no messages, falling back to regular send")
                                    message_id_to_reply = None
                            else:
                                print(f"   ⚠️ Could not get thread details, falling back to regular send")
                                message_id_to_reply = None
                        except Exception as thread_error:
                            print(f"   ⚠️ Error getting thread: {thread_error}, falling back to regular send")
                            message_id_to_reply = None
                    
                    # Use the correct endpoint: /v0/inboxes/{inbox_id}/messages/{message_id}/reply
                    if message_id_to_reply:
                        url = f"{self.api_url}/v0/inboxes/{self.inbox_id}/messages/{message_id_to_reply}/reply"
                    else:
                        # Fallback to regular send if we don't have a valid message_id
                        url = f"{self.api_url}/v0/inboxes/{self.inbox_id}/send"
                    
                    # Convert 'to' to array format per API docs
                    to_array = [to] if isinstance(to, str) else to
                    payload = {
                        "to": to_array,
                        "subject": subject,
                        "text": body,  # API uses 'text' not 'body'
                        "attachments": attachments if attachments else []
                    }
                else:
                    # New message (creates new thread)
                    url = f"{self.api_url}/v0/inboxes/{self.inbox_id}/send"
                    # Convert 'to' to array format per API docs
                    to_array = [to] if isinstance(to, str) else to
                    payload = {
                        "to": to_array,
                        "subject": subject,
                        "text": body,  # API uses 'text' not 'body'
                        "attachments": attachments if attachments else []
                    }
                
                # Final safety check on constructed URL
                if not url.startswith(("http://", "https://")):
                    raise ValueError(f"Invalid URL constructed: {url} - missing protocol. api_url was: {self.api_url}")
                
                response = await client.post(url, headers=self.headers, json=payload)
                
                # If 404 on reply endpoint, fallback to regular send
                if response.status_code == 404 and message_id_to_reply:
                    print(f"⚠️ Reply endpoint returned 404, falling back to regular send email")
                    fallback_url = f"{self.api_url}/v0/inboxes/{self.inbox_id}/send"
                    print(f"   Using fallback URL: {fallback_url}")
                    try:
                        fallback_response = await client.post(fallback_url, headers=self.headers, json=payload)
                        if fallback_response.status_code == 200 or fallback_response.status_code == 201:
                            print(f"✅ Successfully sent email via fallback (regular send)")
                            response = fallback_response
                        else:
                            print(f"   ❌ Fallback also returned {fallback_response.status_code}")
                            response.raise_for_status()
                    except Exception as fallback_error:
                        print(f"   ❌ Fallback error: {fallback_error}")
                        response.raise_for_status()
                else:
                    response.raise_for_status()
                result = response.json()
                return {
                    "success": True,
                    "message_id": result.get("id") or result.get("message_id"),
                    "thread_id": result.get("thread_id")
                }
        except Exception as e:
            print(f"❌ Error sending email via Agentmail: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    async def download_attachment(self, attachment_id: str) -> bytes:
        """Download email attachment"""
        if not self.api_key:
            raise Exception("Agentmail not configured")
        
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                url = f"{self.api_url}/v0/attachments/{attachment_id}/download"
                
                # Safety check on constructed URL
                if not url.startswith(("http://", "https://")):
                    raise ValueError(f"Invalid URL constructed: {url} - missing protocol. api_url was: {self.api_url}")
                
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                return response.content
        except Exception as e:
            print(f"❌ Error downloading attachment: {e}")
            raise
    
    async def extract_email_info(
        self,
        thread: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract email text from thread messages and abstract important info
        
        Args:
            thread: Thread dict from get_thread() which includes messages
        
        Returns:
            Dict with extraction results
        """
        try:
            # Get messages from thread
            messages = thread.get("messages", [])
            if not messages:
                return {"success": False, "error": "No messages in thread"}
            
            # Extract text from all messages in the thread
            email_text_parts = []
            for message in messages:
                # Try text field first, then html, then body
                text = message.get("text") or message.get("html") or message.get("body", "")
                if text:
                    email_text_parts.append(text)
            
            if not email_text_parts:
                return {"success": False, "error": "No text content in messages"}
            
            # Combine all message text
            full_email_text = "\n\n---\n\n".join(email_text_parts)
            
            # Extract important information
            abstracted_info = self._extract_important_info(full_email_text, thread)
            
            return {
                "success": True,
                "abstracted_info": abstracted_info
            }
            
        except Exception as e:
            print(f"❌ Error extracting email info: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    def _extract_important_info(self, email_text: str, thread: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract important information from email text
        Looks for: name, credit score, income, phone, email, employer, etc.
        """
        info = {}
        
        # Extract name - try from senders first, then from email text
        senders = thread.get("senders", [])
        if senders:
            info["name"] = senders[0] if isinstance(senders, list) else senders
        else:
            # Try to extract from email text
            name_patterns = [
                r'(?:name|applicant)[\s:]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                r'^(?:hi|hello|dear)[\s,]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                r'i\s+(?:am|m)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                r'([A-Z][a-z]+\s+[A-Z][a-z]+)',  # First Last pattern
            ]
            for pattern in name_patterns:
                match = re.search(pattern, email_text, re.IGNORECASE | re.MULTILINE)
                if match:
                    info["name"] = match.group(1).strip()
                    break
        
        # Extract credit score
        credit_patterns = [
            r'credit\s+score[:\s]+(\d{3})',
            r'score[:\s]+(\d{3})',
            r'(\d{3})\s+credit',
            r'fico[:\s]+(\d{3})',
        ]
        for pattern in credit_patterns:
            match = re.search(pattern, email_text, re.IGNORECASE)
            if match:
                score = int(match.group(1))
                if 300 <= score <= 850:  # Valid credit score range
                    info["credit_score"] = score
                    break
        
        # Extract income (monthly or annual)
        income_patterns = [
            r'monthly\s+income[:\s$]+(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'income[:\s$]+(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:per\s+month|monthly)',
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:per\s+month|monthly)',
            r'annual\s+income[:\s$]+(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'income[:\s$]+(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:per\s+year|annually)',
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:per\s+year|annually)',
            r'salary[:\s$]+(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'make[:\s$]+(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        ]
        for pattern in income_patterns:
            match = re.search(pattern, email_text, re.IGNORECASE)
            if match:
                income_str = match.group(1).replace(',', '').replace('$', '')
                try:
                    income = float(income_str)
                    # Determine if monthly or annual based on context
                    if 'monthly' in match.group(0).lower() or 'per month' in match.group(0).lower():
                        info["monthly_income"] = income
                        info["annual_income"] = income * 12
                    elif 'annual' in match.group(0).lower() or 'year' in match.group(0).lower():
                        info["annual_income"] = income
                        info["monthly_income"] = income / 12
                    else:
                        # Default assumption: if > 100k, it's annual; otherwise monthly
                        if income > 100000:
                            info["annual_income"] = income
                            info["monthly_income"] = income / 12
                        else:
                            info["monthly_income"] = income
                            info["annual_income"] = income * 12
                    break
                except ValueError:
                    continue
        
        # Extract phone number
        phone_patterns = [
            r'(\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})',
            r'phone[:\s]+(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})',
            r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})',
        ]
        for pattern in phone_patterns:
            match = re.search(pattern, email_text)
            if match:
                info["phone"] = match.group(1).strip()
                break
        
        # Extract email (from thread senders - the sender is who sent us the email)
        if not info.get("email"):
            senders = thread.get("senders", [])
            if senders:
                # senders is an array of email addresses
                if isinstance(senders, list) and len(senders) > 0:
                    info["email"] = senders[0]
                else:
                    info["email"] = str(senders)
        
        # Extract employer
        employer_patterns = [
            r'employer[:\s]+([A-Za-z\s&]+)',
            r'work\s+at[:\s]+([A-Za-z\s&]+)',
            r'company[:\s]+([A-Za-z\s&]+)',
            r'employer\s+name[:\s]+([A-Za-z\s&]+)',
        ]
        for pattern in employer_patterns:
            match = re.search(pattern, email_text, re.IGNORECASE)
            if match:
                info["employer"] = match.group(1).strip()
                break
        
        # Extract property interest (if mentioned)
        property_patterns = [
            r'property[:\s]+(.+)',
            r'address[:\s]+(.+)',
            r'interested\s+in[:\s]+(.+)',
        ]
        for pattern in property_patterns:
            match = re.search(pattern, email_text, re.IGNORECASE)
            if match:
                property_info = match.group(1).strip()
                if len(property_info) < 100:  # Reasonable length
                    info["property_interest"] = property_info
                break
        
        return info
    

# Email templates
def get_approval_email_template(applicant_name: str, property_name: str = "the property") -> tuple[str, str]:
    """Generate approval email subject and body (no scheduling - manager contacts directly)"""
    subject = "Application Approved!"
    
    body = f"""Hi {applicant_name},

Thank you for your application! We're pleased to inform you that your application has been approved.

A property manager will contact you shortly to discuss next steps.

We look forward to working with you!

Best regards,
Property Management Team"""
    
    return subject, body

def get_rejection_email_template(applicant_name: str, property_name: str = "the property") -> tuple[str, str]:
    """Generate rejection email subject and body"""
    subject = f"Application Update - {property_name}"
    
    body = f"""Hi there,

Thank you for your interest in the property. After reviewing your application, we are unable to move forward at this time. We encourage you to apply again in the future.

Best regards,
Property Management Team"""
    
    return subject, body

def get_confirmation_email_template(
    applicant_name: str,
    scheduled_date: str,
    scheduled_time: str,
    property_address: str,
    parking_instructions: Optional[str] = None
) -> tuple[str, str]:
    """Generate confirmation email subject and body"""
    subject = "Property Showing Confirmed"
    
    parking_info = f"\n\nParking Instructions:\n{parking_instructions}" if parking_instructions else ""
    
    body = f"""Hi {applicant_name},

Your property showing has been confirmed!

Date: {scheduled_date}
Time: {scheduled_time}
Address: {property_address}{parking_info}

What to bring:
- Valid ID
- Proof of income (if needed)

If you need to reschedule, please reply to this email as soon as possible.

We look forward to meeting you!

Best regards,
Property Management Team"""
    
    return subject, body

def get_missing_documents_email_template(applicant_name: str, missing_docs: List[str]) -> tuple[str, str]:
    """Generate email requesting missing documents"""
    subject = "Application - Missing Documents"
    
    docs_list = "\n".join([f"- {doc}" for doc in missing_docs])
    
    body = f"""Hi {applicant_name},

Thank you for your application! We need a few more documents to complete your application:

{docs_list}

Please reply to this email with these documents attached.

Thank you,
Property Management Team"""
    
    return subject, body

