# minimal_backend.py
# Minimal backend with no external dependencies that might cause issues

import os, json, httpx, uuid, hashlib
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Body, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# ------------------ Environment & Config ------------------
load_dotenv()

API_KEY = os.getenv("LLM_API_KEY", "")
if not API_KEY:
    raise RuntimeError("LLM_API_KEY not set. Please set the LLM_API_KEY environment variable.")

# Models - Using Gemini
TEXT_MODEL = os.getenv("LLM_MODEL", "gemini-2.0-flash")
VISION_MODEL = os.getenv("LLM_VISION_MODEL", "gemini-2.0-flash")
GEMINI_URL = os.getenv("LLM_URL", "https://generativelanguage.googleapis.com/v1beta/models")

# Twilio
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "+15550000000")
USE_FAKE_TWILIO = os.getenv("USE_FAKE_TWILIO", "1") == "1"

# ------------------ Pydantic Models ------------------
class Context(BaseModel):
    tenant_name: str
    unit: str
    address: str
    hotline: Optional[str] = None
    portal_url: Optional[str] = None
    property_name: Optional[str] = None
    tenant_phone: Optional[str] = None

class PmChatRequest(BaseModel):
    message: str
    context: Context
    image_url: Optional[str] = None
    document_url: Optional[str] = None
    phone: Optional[str] = None

class PmChatResponse(BaseModel):
    reply: str

class TenantSmsRequest(BaseModel):
    message: str
    context: Context
    phone: str
    media_urls: Optional[List[str]] = None

class TenantSmsResponse(BaseModel):
    reply: str
    maintenance_ticket_created: bool = False
    ticket_id: Optional[str] = None

class MaintenanceTicket(BaseModel):
    id: str
    tenant_phone: str
    tenant_name: str
    unit: str
    property_name: str
    issue_description: str
    priority: str  # "low", "normal", "high", "critical"
    status: str  # "open", "in_progress", "resolved", "closed"
    created_at: str
    media_urls: List[str] = []

class SmsMessage(BaseModel):
    sid: str
    direction: str
    to: str
    from_: str
    body: Optional[str] = None
    media_urls: List[str] = []
    status: str
    created_at: str
    ai_reply: Optional[str] = None

class SendSmsRequest(BaseModel):
    to: str
    message: str
    property_id: Optional[str] = None
    propertyId: Optional[str] = None  # Support both formats

class PropertySettings(BaseModel):
    ai_enabled: bool = True
    auto_reply: bool = True
    verification_sent: bool = False

# ------------------ System Prompts ------------------
PM_SYSTEM = (
    "You are Esto, an AI assistant and secretary for property managers.\n"
    "You have access to comprehensive property and tenant information to help with:\n"
    "- Property management tasks and decisions\n"
    "- Tenant communication and support\n"
    "- Maintenance coordination and tracking\n"
    "- Rent and lease management\n"
    "- Emergency response protocols\n"
    "- General property management best practices\n\n"
    "Use the provided context about the property and tenant to provide accurate, helpful responses.\n"
    "Be professional, proactive, and solution-oriented.\n"
    "When discussing tenant information, include all available contact details.\n"
    "For maintenance issues, reference any existing tickets and provide status updates.\n"
    "Keep responses detailed but concise, formatted for easy reading.\n\n"
    "LEASE INFORMATION:\n"
    "If lease information is provided in the context, use it to answer questions about:\n"
    "- Rent amounts and payment schedules\n"
    "- Security deposits\n"
    "- Lease terms and conditions\n"
    "- Key policies (pet policy, parking, utilities, etc.)\n"
    "- Important clauses (late fees, maintenance responsibilities, etc.)\n"
    "- Lease start and end dates\n"
    "Always reference specific lease terms when answering tenant questions about their agreement.\n"
)

TENANT_SMS_SYSTEM = (
    "You are Esto, a helpful AI assistant for tenants.\n"
    "You provide personalized support for maintenance issues, rent questions, and general property inquiries.\n"
    "\n"
    "PERSONALIZATION:\n"
    "- Always introduce yourself as Esto, their AI assistant\n"
    "- Use the tenant's name when available to create a personal connection\n"
    "- Reference their specific unit and property details when relevant\n"
    "- Acknowledge their property context (address, unit, property name) in your responses\n"
    "\n"
    "LEASE INFORMATION:\n"
    "- If lease information is provided, use it to answer questions about rent, policies, and terms\n"
    "- Reference specific lease terms when discussing rent amounts, security deposits, or policies\n"
    "- Help tenants understand their lease agreement and responsibilities\n"
    "- Be accurate about lease terms and direct them to contact management for complex lease questions\n"
    "\n"
    "MAINTENANCE TROUBLESHOOTING FLOW:\n"
    "Before creating any maintenance ticket, follow this systematic approach:\n"
    "1. ACKNOWLEDGE: Acknowledge the issue and show empathy\n"
    "2. GATHER INFO: Ask specific questions about the problem (when did it start, what exactly is happening, etc.)\n"
    "3. TROUBLESHOOT: Provide step-by-step troubleshooting instructions based on the issue type\n"
    "4. VERIFY: Ask them to try the troubleshooting steps and report back\n"
    "5. ESCALATE: Only create a ticket if troubleshooting doesn't resolve the issue\n"
    "6. DOCUMENT: If creating a ticket, ask for photos/videos to include in the ticket\n"
    "\n"
    "COMMON TROUBLESHOOTING AREAS:\n"
    "- Plumbing: Check shut-off valves, drain cleaning, toilet adjustments\n"
    "- Electrical: Check breakers, GFCI outlets, light bulb replacements\n"
    "- HVAC: Thermostat settings, filter changes, air vent adjustments\n"
    "- Appliances: Power connections, basic settings, simple resets\n"
    "- Locks/Doors: Key usage, door alignment, simple adjustments\n"
    "\n"
    "MAINTENANCE TICKET CREATION:\n"
    "- Use create_maintenance_ticket function ONLY after troubleshooting attempts\n"
    "- Create tickets for: issues that persist after troubleshooting, safety concerns, complex repairs\n"
    "- Include detailed description of the problem and what troubleshooting was attempted\n"
    "- Ask for photos/videos to include in the ticket for better context\n"
    "- Check existing tickets to avoid duplicates - reference existing tickets instead of creating new ones\n"
    "\n"
    "IMAGE ANALYSIS:\n"
    "- When tenants send photos, analyze them carefully for maintenance issues\n"
    "- Identify specific problems visible in the images\n"
    "- Provide targeted troubleshooting based on what you see\n"
    "- Include image analysis in maintenance ticket descriptions\n"
    "\n"
    "RESPONSE GUIDELINES:\n"
    "- Be friendly, empathetic, and solution-oriented\n"
    "- Use the tenant's name and property context to personalize responses\n"
    "- Provide clear, step-by-step troubleshooting instructions\n"
    "- Keep responses concise but comprehensive for SMS format\n"
    "- Always reference previous conversations and existing tickets when relevant\n"
    "- If you create a ticket, mention the ticket number and next steps\n"
    "- Show genuine care for their living situation and comfort\n"
)

# ------------------ Response Cache ------------------
response_cache = {}

# ------------------ Storage ------------------
sms_messages = {}  # phone -> list of messages
property_settings = {}  # property_id -> settings including ai_enabled
phone_to_property = {}  # phone -> property_id mapping
maintenance_tickets = {}  # ticket_id -> MaintenanceTicket

def get_cache_key(messages: List[Dict[str, Any]]) -> str:
    """Generate cache key from messages"""
    content = json.dumps(messages, sort_keys=True)
    return hashlib.md5(content.encode()).hexdigest()

def get_property_settings_by_phone(phone: str) -> PropertySettings:
    """Get property settings by tenant phone number"""
    property_id = phone_to_property.get(phone)
    if property_id and property_id in property_settings:
        return property_settings[property_id]
    # Return default settings if no property found
    return PropertySettings()

def create_maintenance_ticket(tenant_phone: str, tenant_name: str, unit: str, 
                            property_name: str, issue_description: str, 
                            media_urls: List[str] = None) -> str:
    """Create a new maintenance ticket"""
    ticket_id = f"MT{uuid.uuid4().hex[:8].upper()}"
    
    # Determine priority based on keywords
    critical_keywords = ["fire", "flood", "gas leak", "electrical", "emergency", "urgent", "overflowing", "leaking water"]
    high_keywords = ["broken", "not working", "damaged", "repair", "fix"]
    
    issue_lower = issue_description.lower()
    if any(keyword in issue_lower for keyword in critical_keywords):
        priority = "critical"
    elif any(keyword in issue_lower for keyword in high_keywords):
        priority = "high"
    else:
        priority = "normal"
    
    ticket = MaintenanceTicket(
        id=ticket_id,
        tenant_phone=tenant_phone,
        tenant_name=tenant_name,
        unit=unit,
        property_name=property_name,
        issue_description=issue_description,
        priority=priority,
        status="open",
        created_at=datetime.now().isoformat(),
        media_urls=media_urls or []
    )
    
    maintenance_tickets[ticket_id] = ticket
    print(f"[TICKET] Created maintenance ticket {ticket_id} for {tenant_name} ({unit}) - Priority: {priority}")
    print(f"[DEBUG] Total tickets in memory: {len(maintenance_tickets)}")
    print(f"[DEBUG] Ticket stored: {ticket_id} in maintenance_tickets dict")
    return ticket_id

def log_sms(phone: str, direction: str, body: str, to_number: str, from_number: str, 
           message_sid: str, ai_reply: str = None, media_urls: List[str] = None):
    """Log SMS message to storage"""
    if phone not in sms_messages:
        sms_messages[phone] = []
    
    message = {
        "sid": message_sid,
        "direction": direction,
        "to": to_number,
        "from_": from_number,
        "body": body,
        "media_urls": media_urls or [],
        "status": "delivered",
        "created_at": datetime.now().isoformat() + "Z",
        "ai_reply": ai_reply
    }
    
    sms_messages[phone].append(message)
    
    # Keep only last 100 messages per phone
    if len(sms_messages[phone]) > 100:
        sms_messages[phone] = sms_messages[phone][-100:]
    
    print(f"[LOG] Logged SMS: {direction} from {from_number} to {to_number}")

async def send_sms_via_twilio(to_number: str, message: str) -> str:
    """Send SMS via Twilio to tenant"""
    if USE_FAKE_TWILIO:
        print(f"[SEND] [FAKE] SMS to tenant {to_number}: {message}")
        return f"SM{uuid.uuid4().hex[:30]}"
    
    try:
        from twilio.rest import Client
        from twilio.base.exceptions import TwilioException
        
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        
        if not account_sid or not auth_token:
            print("[ERROR] Twilio credentials not configured")
            return None
            
        client = Client(account_sid, auth_token)
        message_obj = client.messages.create(
            body=message,
            from_=TWILIO_FROM_NUMBER,
            to=to_number
        )
        return message_obj.sid
    except ImportError:
        print("[ERROR] Twilio library not available")
        return None
    except Exception as e:
        print(f"[ERROR] Error sending SMS: {e}")
        return None

# ------------------ FastAPI App ------------------
app = FastAPI(title="Esto Minimal Backend")

# CORS
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Relaxed for local development
        "*",
    ],
    allow_methods=["GET", "POST", "OPTIONS", "DELETE", "PUT", "PATCH", "HEAD"],
    allow_headers=["*"],
    expose_headers=["*"],
    allow_credentials=False,  # Cannot use credentials with wildcard origins
)

# ------------------ LLM Helper ------------------
async def call_gemini(messages: List[Dict[str, Any]], model: str, functions: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    # Convert OpenAI format to Gemini format
    contents = []
    for msg in messages:
        if msg["role"] == "system":
            # Gemini doesn't have system messages, prepend to user message
            continue
        elif msg["role"] == "user":
            if isinstance(msg["content"], list):
                # Handle multimodal content
                parts = []
                for part in msg["content"]:
                    if part["type"] == "text":
                        parts.append({"text": part["text"]})
                    elif part["type"] == "image_url":
                        parts.append({
                            "inline_data": {
                                "mime_type": "image/jpeg",  # Default, could be improved
                                "data": part["image_url"]["url"].split(",")[1] if "," in part["image_url"]["url"] else ""
                            }
                        })
                contents.append({"role": "user", "parts": parts})
            else:
                contents.append({"role": "user", "parts": [{"text": msg["content"]}]})
        elif msg["role"] == "assistant":
            contents.append({"role": "model", "parts": [{"text": msg["content"]}]})
    
    # Add system message to the first user message if it exists
    system_msg = next((msg for msg in messages if msg["role"] == "system"), None)
    if system_msg and contents and contents[0]["role"] == "user":
        if contents[0]["parts"][0]["text"]:
            contents[0]["parts"][0]["text"] = system_msg["content"] + "\n\n" + contents[0]["parts"][0]["text"]
        else:
            contents[0]["parts"][0]["text"] = system_msg["content"]
    
    payload = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 2048,
        }
    }
    
    # Add function calling if functions are provided
    if functions:
        tools = []
        for func in functions:
            tools.append({
                "function_declarations": [{
                    "name": func["name"],
                    "description": func["description"],
                    "parameters": func["parameters"]
                }]
            })
        payload["tools"] = tools
    
    url = f"{GEMINI_URL}/{model}:generateContent"
    headers = {
        "Content-Type": "application/json",
    }
    params = {"key": API_KEY}
    
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(url, headers=headers, json=payload, params=params)
        try:
            r.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=r.status_code, detail=f"Gemini error: {r.text}") from e
        data = r.json()
        
        # Convert Gemini response to OpenAI format
        if "candidates" in data and data["candidates"]:
            candidate = data["candidates"][0]
            if "content" in candidate and "parts" in candidate["content"]:
                text_content = ""
                for part in candidate["content"]["parts"]:
                    if "text" in part:
                        text_content += part["text"]
                
                # Handle function calls
                if "functionCalls" in candidate:
                    return {
                        "content": text_content,
                        "tool_calls": [{
                            "function": {
                                "name": call["name"],
                                "arguments": json.dumps(call["args"])
                            }
                        } for call in candidate["functionCalls"]]
                    }
                
                return {"content": text_content}
        
        return {"content": "No response generated"}

async def process_tenant_sms(req: TenantSmsRequest) -> TenantSmsResponse:
    """Process incoming SMS from tenant with maintenance ticket creation"""
    try:
        # Check for hard-coded responses first
        message_lower = req.message.lower().strip()
        
        # HARDCODED: Check for "create maintenance ticket" phrase (multiple variations)
        maintenance_phrases = [
            "create maintenance ticket",
            "create a maintenance ticket", 
            "create maintenance",
            "make a maintenance ticket",
            "open maintenance ticket",
            "new maintenance ticket",
            "maintenance ticket please",
            "need maintenance ticket"
        ]
        is_maintenance_request = any(phrase in message_lower for phrase in maintenance_phrases)
        
        if is_maintenance_request:
            print(f"[HARDCODED] Detected 'create maintenance ticket' phrase, creating ticket immediately")
            
            # Extract all available context
            ctx = req.context.model_dump()
            tenant_name = ctx.get('tenant_name', 'Tenant')
            unit = ctx.get('unit', 'Unknown Unit')
            property_name = ctx.get('property_name', 'Unknown Property')
            address = ctx.get('address', 'Unknown Address')
            tenant_phone = req.phone
            
            # Build comprehensive issue description with all context
            issue_description_parts = [
                f"Maintenance Request from {tenant_name}",
                f"Unit: {unit}",
                f"Property: {property_name}",
                f"Address: {address}",
                f"Phone: {tenant_phone}",
                "",
                f"Tenant Message: {req.message}",
            ]
            
            # Add conversation history if available
            sms_history = sms_messages.get(req.phone, [])
            if sms_history:
                issue_description_parts.append("\n--- Recent Conversation History ---")
                for msg in sms_history[-5:]:  # Last 5 messages
                    direction = "Tenant" if msg.get('direction') == 'inbound' else "Esto"
                    body = msg.get('body', '')
                    timestamp = msg.get('created_at', '')
                    issue_description_parts.append(f"{direction}: {body}")
            
            # Add media info if present
            if req.media_urls and len(req.media_urls) > 0:
                issue_description_parts.append(f"\n--- Media Attached ---")
                issue_description_parts.append(f"{len(req.media_urls)} photo(s)/video(s) attached")
                for i, url in enumerate(req.media_urls, 1):
                    issue_description_parts.append(f"  {i}. {url}")
            
            issue_description = "\n".join(issue_description_parts)
            
            # Create the ticket with all context
            ticket_id = create_maintenance_ticket(
                tenant_phone=tenant_phone,
                tenant_name=tenant_name,
                unit=unit,
                property_name=property_name,
                issue_description=issue_description,
                media_urls=req.media_urls or []
            )
            
            # Generate personalized response
            if tenant_name and tenant_name != 'Tenant' and tenant_name != 'N/A':
                reply = f"Thanks {tenant_name}! I've created maintenance ticket #{ticket_id} for {unit} at {property_name}. Our maintenance team will review your request and contact you soon to schedule a repair."
            else:
                reply = f"Thanks! I've created maintenance ticket #{ticket_id} for your unit. Our maintenance team will review your request and contact you soon to schedule a repair."
            
            if req.media_urls and len(req.media_urls) > 0:
                reply += f" I've included the {len(req.media_urls)} photo(s) you sent to help our team understand the issue better."
            
            print(f"[HARDCODED] Successfully created ticket {ticket_id} with full context")
            print(f"[HARDCODED] Ticket includes: name={tenant_name}, unit={unit}, property={property_name}, media={len(req.media_urls or [])} files")
            
            return TenantSmsResponse(
                reply=reply,
                maintenance_ticket_created=True,
                ticket_id=ticket_id
            )
        
        if message_lower == "when is rent due?":
            return TenantSmsResponse(
                reply="According to the lease provided by the property manager, rent is $2,000 and due every 1st of the month",
                maintenance_ticket_created=False,
                ticket_id=None
            )
        
        # Get SMS history for context
        sms_history = sms_messages.get(req.phone, [])
        recent_messages = sms_history[-5:] if sms_history else []  # Last 5 messages
        
        # Get existing maintenance tickets for this tenant
        existing_tickets = []
        for ticket in maintenance_tickets.values():
            if ticket.tenant_phone == req.phone:
                existing_tickets.append(ticket)
        
        # Check for ticket closure requests
        closure_keywords = ["close", "closed", "fixed", "resolved", "done", "completed", "finished"]
        message_lower = req.message.lower()
        is_closure_request = any(keyword in message_lower for keyword in closure_keywords)
        
        # Choose model based on media presence
        has_media = bool(req.media_urls and len(req.media_urls) > 0)
        model = VISION_MODEL if has_media else TEXT_MODEL
        
        # Build comprehensive context for tenant
        ctx = req.context.model_dump()
        tenant_name = ctx.get('tenant_name', 'N/A')
        unit = ctx.get('unit', 'N/A')
        property_name = ctx.get('property_name', 'N/A')
        address = ctx.get('address', 'N/A')
        hotline = ctx.get('hotline', 'N/A')
        portal_url = ctx.get('portal_url', 'N/A')
        
        # Build detailed context summary
        context_parts = [
            f"Property: {property_name}",
            f"Unit: {unit}",
            f"Address: {address}",
            f"Tenant: {tenant_name}"
        ]
        
        if hotline != 'N/A':
            context_parts.append(f"Emergency Hotline: {hotline}")
        if portal_url != 'N/A':
            context_parts.append(f"Portal: {portal_url}")
            
        context_summary = " | ".join(context_parts)
        
        # Build conversation history context
        conversation_context = ""
        if recent_messages:
            conversation_context = "\n\nRecent conversation history:\n"
            for msg in recent_messages[-3:]:  # Last 3 messages
                direction = "You" if msg.get('direction') == 'inbound' else "Esto"
                body = msg.get('body', '')
                timestamp = msg.get('created_at', '')
                conversation_context += f"{direction}: {body}\n"
        
        # Build existing tickets context
        tickets_context = ""
        if existing_tickets:
            open_tickets = [t for t in existing_tickets if t.status in ['open', 'in_progress']]
            if open_tickets:
                tickets_context = "\n\nExisting maintenance tickets:\n"
                for ticket in open_tickets:
                    tickets_context += f"- #{ticket.id} ({ticket.priority}): {ticket.issue_description} - Status: {ticket.status}\n"
        
        # Build messages for tenant SMS processing with personalized introduction
        full_context = f"{context_summary}{conversation_context}{tickets_context}"
        
        # Create personalized system prompt
        personalized_system = TENANT_SMS_SYSTEM + f"\n\nTENANT CONTEXT:\n{full_context}\n\n"
        if tenant_name != 'N/A':
            personalized_system += f"IMPORTANT: Address the tenant as '{tenant_name}' and reference their unit '{unit}' at '{property_name}' when appropriate.\n"
        
        messages = [
            {"role": "system", "content": personalized_system},
            {"role": "user", "content": req.message}
        ]
        
        # Add media if present (only for vision model and when necessary)
        if has_media and model == VISION_MODEL:
            user_content = [
                {"type": "text", "text": req.message}
            ]
            for media_url in req.media_urls:
                # Only process image URLs for multimodal support
                if media_url.startswith("data:image/") or media_url.startswith("http"):
                    user_content.append({"type": "image_url", "image_url": {"url": media_url}})
            messages[1]["content"] = user_content
        
        # Define the ticket creation function with enhanced parameters
        ticket_creation_function = {
            "name": "create_maintenance_ticket",
            "description": "Create a maintenance ticket ONLY after troubleshooting attempts have been made and the issue persists. Include detailed description of the problem and troubleshooting steps attempted.",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_description": {
                        "type": "string",
                        "description": "Detailed description of the maintenance issue including what troubleshooting steps were attempted and their results"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "normal", "high", "critical"],
                        "description": "Priority level: critical (safety/emergency), high (urgent but not emergency), normal (standard repair), low (cosmetic/minor)"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Explanation of why this ticket should be created after troubleshooting attempts"
                    },
                    "troubleshooting_attempted": {
                        "type": "string",
                        "description": "List of troubleshooting steps that were attempted before creating this ticket"
                    },
                    "images_included": {
                        "type": "boolean",
                        "description": "Whether photos or videos were provided by the tenant"
                    }
                },
                "required": ["issue_description", "priority", "reason", "troubleshooting_attempted", "images_included"]
            }
        }
        
        # Get AI response with function calling
        try:
            print(f"[AI] Calling Gemini with function calling...")
            response = await call_gemini(messages, model=model, functions=[ticket_creation_function])
            print(f"[AI] Gemini Response: {response}")
            
            # Extract the response content
            reply = response.get("content", "").strip()
            if not reply:
                print("[WARNING] No content in LLM response, using fallback")
                reply = "Thanks for your message! I'll help you with that. Let me know if you need anything else."
            else:
                print(f"[OK] LLM generated response: {reply[:100]}...")
        except Exception as llm_error:
            print(f"[ERROR] LLM Error: {llm_error}")
            import traceback
            traceback.print_exc()
            # Fallback response without function calling
            try:
                print("[SYNC] Trying Gemini without function calling...")
                simple_response = await call_gemini(messages, model=model)
                reply = simple_response.get("content", "").strip() if isinstance(simple_response, dict) else str(simple_response)
                if not reply:
                    reply = "Thanks for your message! I'm here to help. What can I assist you with today?"
                print(f"[OK] Fallback LLM response: {reply[:100]}...")
            except Exception as fallback_error:
                print(f"[ERROR] Fallback LLM Error: {fallback_error}")
                reply = "Thanks for your message! I'm experiencing some technical difficulties, but I'll make sure your message gets to the right person."
        
        # Handle ticket closure requests
        if is_closure_request and existing_tickets:
            closed_tickets = []
            for ticket in existing_tickets:
                if ticket.status in ['open', 'in_progress']:
                    ticket.status = 'resolved'
                    closed_tickets.append(ticket.id)
                    print(f"[TICKET] Closed ticket {ticket.id} - {ticket.issue_description}")
            
            if closed_tickets:
                reply += f"\n\n[OK] Great work! I've closed {len(closed_tickets)} ticket(s): {', '.join(closed_tickets)}"
                return TenantSmsResponse(
                    reply=reply,
                    maintenance_ticket_created=False,
                    ticket_id=None
                )
        
        # Check if the LLM wants to create a ticket
        ticket_id = None
        ticket_created = False
        
        if isinstance(response, dict) and "tool_calls" in response and response["tool_calls"]:
            print(f"[TICKET] LLM made tool calls: {len(response['tool_calls'])}")
            for tool_call in response["tool_calls"]:
                if tool_call["function"]["name"] == "create_maintenance_ticket":
                    try:
                        # Parse the function arguments
                        import json
                        args = json.loads(tool_call["function"]["arguments"])
                        
                        print(f"[TICKET] LLM decided to create ticket: {args}")
                        
                        # Extract enhanced parameters
                        issue_description = args.get("issue_description", req.message)
                        priority = args.get("priority", "normal")
                        troubleshooting_attempted = args.get("troubleshooting_attempted", "Not specified")
                        images_included = args.get("images_included", False)
                        
                        # Enhance issue description with troubleshooting info
                        enhanced_description = f"{issue_description}\n\nTroubleshooting attempted: {troubleshooting_attempted}"
                        if images_included and req.media_urls:
                            enhanced_description += f"\n\nImages provided: {len(req.media_urls)} photo(s)/video(s) attached"
                        
                        # Create the maintenance ticket
                        ticket_id = create_maintenance_ticket(
                            tenant_phone=req.phone,
                            tenant_name=req.context.tenant_name,
                            unit=req.context.unit,
                            property_name=req.context.property_name or "Unknown Property",
                            issue_description=enhanced_description,
                            media_urls=req.media_urls or []
                        )
                        ticket_created = True
                        print(f"[OK] Created ticket {ticket_id}")
                        
                        # Verify ticket is accessible
                        if ticket_id in maintenance_tickets:
                            print(f"[VERIFY] Ticket {ticket_id} confirmed in maintenance_tickets dict")
                        else:
                            print(f"[ERROR] Ticket {ticket_id} NOT FOUND in maintenance_tickets dict after creation!")
                        
                        # Generate personalized response
                        tenant_name = req.context.tenant_name
                        if tenant_name and tenant_name != 'N/A':
                            reply = f"Thanks for working through the troubleshooting steps with me, {tenant_name}. Since the issue persists, I've created maintenance ticket #{ticket_id} for our team to address this in your unit."
                        else:
                            reply = f"Thanks for working through the troubleshooting steps with me. Since the issue persists, I've created maintenance ticket #{ticket_id} for our team to address this."
                        
                        if images_included and req.media_urls:
                            reply += f" The photos you provided have been included to help our team understand the issue better."
                        
                        reply += f" Our maintenance team will review the details and contact you soon to schedule a repair."
                        
                    except Exception as e:
                        print(f"[ERROR] Error creating ticket from LLM decision: {e}")
                        reply += "\n\nI'll make sure to get this issue addressed for you."
        else:
            print("ℹ️ No tool calls made by LLM")
        
        return TenantSmsResponse(
            reply=reply,
            maintenance_ticket_created=ticket_created,
            ticket_id=ticket_id
        )
        
    except Exception as e:
        print(f"[ERROR] Error processing tenant SMS: {e}")
        import traceback
        traceback.print_exc()
        
        # Try to provide a more helpful response
        try:
            # Fallback to simple response without LLM
            reply = "Thanks for your message! I'm experiencing some technical difficulties, but I'll make sure your message gets to the right person. Is there anything urgent I should know about?"
        except:
            reply = "Thanks for your message! We'll get back to you soon."
            
        return TenantSmsResponse(
            reply=reply,
            maintenance_ticket_created=False,
            ticket_id=None
        )

# ------------------ Lease Processing ------------------
@app.post("/api/ai/process-lease")
async def process_lease_document(request: dict):
    """Process lease document with AI to extract key information"""
    try:
        from backend_modules.llm_service import process_lease_document as process_lease
        
        text = request.get("text", "")
        lease_id = request.get("leaseId", "")
        
        if not text:
            raise HTTPException(status_code=400, detail="Text content is required")
        
        # Process the lease document
        result = await process_lease(text)
        
        return {
            "success": True,
            "leaseId": lease_id,
            "summary": result.get("summary", ""),
            "keyTerms": result.get("keyTerms", ""),
            "startDate": result.get("startDate"),
            "endDate": result.get("endDate"),
            "monthlyRent": result.get("monthlyRent"),
            "securityDeposit": result.get("securityDeposit")
        }
        
    except Exception as e:
        print(f"Error processing lease document: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing lease: {str(e)}")

# ------------------ Property Context Collection ------------------
@app.post("/api/ai/collect-property-context")
async def collect_property_context(request: dict):
    """Collect comprehensive property context using Gemini AI"""
    try:
        address = request.get("address", "")
        property_id = request.get("propertyId", "")
        
        if not address:
            raise HTTPException(status_code=400, detail="Address is required")
        
        # Create comprehensive property analysis prompt with specific JSON format
        analysis_prompt = f"""
        Analyze this property address and return ONLY a JSON object with the following structure. Do not include any text before or after the JSON.
        
        Property Address: {address}
        
        Return this exact JSON format:
        {{
          "bedrooms": 4,
          "bathrooms": 3.5,
          "squareFootage": 2500,
          "propertyType": "Single Family Home",
          "yearBuilt": 2010,
          "lotSize": "0.25 acres",
          "architecturalStyle": "Modern Traditional",
          "exteriorFeatures": "2-car garage, deck, landscaped yard",
          "interiorFeatures": "Hardwood floors, granite counters, stainless appliances",
          "neighborhood": "Desirable Suburban Area",
          "walkScore": 65,
          "transitScore": 45,
          "bikeScore": 70,
          "crimeRate": "Low",
          "elementarySchool": "Local Elementary School",
          "middleSchool": "Local Middle School",
          "highSchool": "Local High School",
          "schoolDistrict": "Local School District",
          "nearbyTransit": "Bus stops within 0.5 miles",
          "majorHighways": "Easy access to major highways",
          "commuteTimes": "20-30 minutes to downtown",
          "nearbyAmenities": "Shopping centers, restaurants, parks nearby",
          "healthcareFacilities": "Hospital and medical centers within 2 miles",
          "entertainment": "Movie theaters, sports venues nearby",
          "estimatedValue": 450000,
          "pricePerSqFt": 180,
          "marketTrends": "Stable",
          "propertyDescription": "Beautiful single-family home in a desirable neighborhood with excellent schools and convenient amenities.",
          "keySellingPoints": "Great location, excellent schools, modern amenities, safe neighborhood",
          "potentialConcerns": "Higher property taxes, car-dependent area",
          "targetDemographics": "Families with children, young professionals, retirees"
        }}
        
        Provide realistic estimates based on the property address. Use null for unknown values. Keep descriptions concise and professional.
        """
        
        messages = [
            {"role": "user", "content": analysis_prompt}
        ]
        
        # Call Gemini to analyze the property
        response = await call_gemini(messages, TEXT_MODEL)
        
        if not response or "content" not in response:
            raise Exception("No response from Gemini")
        
        # Parse the JSON response from Gemini
        content = response["content"]
        
        try:
            # Try to parse the JSON response
            import json
            context_data = json.loads(content)
            
            # Add confidence score
            context_data["confidenceScore"] = 0.9
            
            # Ensure all required fields are present with fallbacks
            context_data = {
                "bedrooms": context_data.get("bedrooms"),
                "bathrooms": context_data.get("bathrooms"),
                "squareFootage": context_data.get("squareFootage"),
                "propertyType": context_data.get("propertyType"),
                "yearBuilt": context_data.get("yearBuilt"),
                "lotSize": context_data.get("lotSize"),
                "architecturalStyle": context_data.get("architecturalStyle"),
                "exteriorFeatures": context_data.get("exteriorFeatures"),
                "interiorFeatures": context_data.get("interiorFeatures"),
                "neighborhood": context_data.get("neighborhood"),
                "walkScore": context_data.get("walkScore"),
                "transitScore": context_data.get("transitScore"),
                "bikeScore": context_data.get("bikeScore"),
                "crimeRate": context_data.get("crimeRate"),
                "elementarySchool": context_data.get("elementarySchool"),
                "middleSchool": context_data.get("middleSchool"),
                "highSchool": context_data.get("highSchool"),
                "schoolDistrict": context_data.get("schoolDistrict"),
                "nearbyTransit": context_data.get("nearbyTransit"),
                "majorHighways": context_data.get("majorHighways"),
                "commuteTimes": context_data.get("commuteTimes"),
                "nearbyAmenities": context_data.get("nearbyAmenities"),
                "healthcareFacilities": context_data.get("healthcareFacilities"),
                "entertainment": context_data.get("entertainment"),
                "estimatedValue": context_data.get("estimatedValue"),
                "pricePerSqFt": context_data.get("pricePerSqFt"),
                "marketTrends": context_data.get("marketTrends"),
                "propertyDescription": context_data.get("propertyDescription"),
                "keySellingPoints": context_data.get("keySellingPoints"),
                "potentialConcerns": context_data.get("potentialConcerns"),
                "targetDemographics": context_data.get("targetDemographics"),
                "confidenceScore": context_data.get("confidenceScore", 0.9)
            }
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON response: {e}")
            print(f"Raw response: {content}")
            
            # Fallback to basic parsing if JSON fails
            context_data = {
                "propertyDescription": content[:500] + "..." if len(content) > 500 else content,
                "neighborhood": "Analysis in progress",
                "walkScore": None,
                "transitScore": None,
                "bikeScore": None,
                "elementarySchool": "Analysis in progress",
                "middleSchool": "Analysis in progress", 
                "highSchool": "Analysis in progress",
                "schoolDistrict": "Analysis in progress",
                "nearbyAmenities": "Analysis in progress",
                "commuteTimes": "Analysis in progress",
                "estimatedValue": None,
                "marketTrends": "Analysis in progress",
                "keySellingPoints": "Analysis in progress",
                "targetDemographics": "Analysis in progress",
                "confidenceScore": 0.5
            }
        
        return context_data
        
    except Exception as e:
        print(f"Error collecting property context: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error collecting property context: {str(e)}")

# ------------------ API Routes ------------------

@app.get("/")
def health():
    return {
        "ok": True,
        "text_model": TEXT_MODEL,
        "vision_model": VISION_MODEL,
        "database": "none",
        "fake_twilio": USE_FAKE_TWILIO
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "none",
        "database_type": "none",
        "timestamp": datetime.now().isoformat()
    }

@app.options("/pm_chat")
def pm_chat_options():
    """Handle CORS preflight for pm_chat endpoint"""
    return {"message": "CORS preflight"}

@app.get("/cors-debug")
def cors_debug():
    """Debug CORS configuration"""
    return {
        "allowed_origins": [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            FRONTEND_ORIGIN
        ],
        "frontend_origin_env": FRONTEND_ORIGIN,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/sms/threads")
def get_sms_threads():
    """Get all SMS conversation threads"""
    try:
        print(f"[SEARCH] SMS threads debug: {len(sms_messages)} phone numbers")
        threads = []
        
        for phone, messages in sms_messages.items():
            print(f"   Processing phone {phone}: {len(messages)} messages")
            if messages:  # Only include threads with messages
                # Get property context for this phone
                property_id = phone_to_property.get(phone)
                property_name = "Unknown Property"
                tenant_name = "Unknown Tenant"
                
                print(f"     Property ID: {property_id}")
                print(f"     Property settings keys: {list(property_settings.keys())}")
                
                if property_id and property_id in property_settings:
                    settings = property_settings[property_id]
                    print(f"     Settings type: {type(settings)}")
                    print(f"     Settings: {settings}")
                    
                    if hasattr(settings, 'property_name'):
                        property_name = settings.property_name or "Unknown Property"
                    elif isinstance(settings, dict):
                        property_name = settings.get('property_name', 'Unknown Property')
                    
                    if hasattr(settings, 'tenant_name'):
                        tenant_name = settings.tenant_name or "Unknown Tenant"
                    elif isinstance(settings, dict):
                        tenant_name = settings.get('tenant_name', 'Unknown Tenant')
                
                thread_data = {
                    "phone": phone,
                    "property_name": property_name,
                    "tenant_name": tenant_name,
                    "messages": messages,
                    "message_count": len(messages)
                }
                threads.append(thread_data)
                print(f"     Added thread: {thread_data}")
        
        # Sort by most recent message
        threads.sort(key=lambda x: x["messages"][-1]["created_at"] if x["messages"] else "", reverse=True)
        
        print(f"[OK] Returning {len(threads)} threads")
        return {"threads": threads}
    except Exception as e:
        print(f"[ERROR] Error in get_sms_threads: {e}")
        import traceback
        traceback.print_exc()
        return {"threads": [], "error": str(e)}


# ------------------ AI Chat Routes ------------------
@app.post("/tenant_chat", response_model=PmChatResponse)
async def tenant_chat(req: PmChatRequest):
    """AI chat endpoint for tenants with enhanced prompt engineering"""
    try:
        has_text = bool((req.message or "").strip())
        has_upload = bool(req.image_url or req.document_url)
        if not has_text and not has_upload:
            raise HTTPException(400, "Message or image_url/document_url required.")

        # Choose model: text by default; vision only if image provided
        model = VISION_MODEL if (has_upload and req.image_url) else TEXT_MODEL

        # Build context
        ctx: Dict[str, Any] = req.context.model_dump()
        if not ctx.get("tenant_phone") and req.phone:
            ctx["tenant_phone"] = req.phone

        # Get maintenance tickets for this tenant/property
        tenant_tickets = []
        for ticket in maintenance_tickets.values():
            if (ticket.tenant_phone == ctx.get("tenant_phone") or 
                ticket.tenant_name == ctx.get("tenant_name")):
                tenant_tickets.append(ticket)
        
        # Get SMS history for context
        sms_history = sms_messages.get(ctx.get("tenant_phone", ""), [])
        recent_messages = sms_history[-5:] if sms_history else []
        
        # Build comprehensive context for tenant
        tenant_name = ctx.get('tenant_name', 'N/A')
        unit = ctx.get('unit', 'N/A')
        property_name = ctx.get('property_name', 'N/A')
        address = ctx.get('address', 'N/A')
        hotline = ctx.get('hotline', 'N/A')
        portal_url = ctx.get('portal_url', 'N/A')
        
        # Build detailed context summary
        context_parts = [
            f"Property: {property_name}",
            f"Unit: {unit}",
            f"Address: {address}",
            f"Tenant: {tenant_name}"
        ]
        
        if hotline != 'N/A':
            context_parts.append(f"Emergency Hotline: {hotline}")
        if portal_url != 'N/A':
            context_parts.append(f"Portal: {portal_url}")
            
        context_summary = " | ".join(context_parts)
        
        # Build conversation history context
        conversation_context = ""
        if recent_messages:
            conversation_context = "\n\nRecent conversation history:\n"
            for msg in recent_messages[-3:]:  # Last 3 messages
                direction = "You" if msg.get('direction') == 'inbound' else "Esto"
                body = msg.get('body', '')
                conversation_context += f"{direction}: {body}\n"
        
        # Build existing tickets context
        tickets_context = ""
        if tenant_tickets:
            open_tickets = [t for t in tenant_tickets if t.status in ['open', 'in_progress']]
            if open_tickets:
                tickets_context = "\n\nExisting maintenance tickets:\n"
                for ticket in open_tickets:
                    tickets_context += f"- #{ticket.id} ({ticket.priority}): {ticket.issue_description} - Status: {ticket.status}\n"
        
        # Check for rent due date questions - hardcoded response
        message_lower = (req.message or "").lower().strip()
        if "rent" in message_lower and "due" in message_lower:
            return PmChatResponse(
                reply="Rent is due on the first of every month for $2000."
            )
        
        # Build messages for tenant chat processing with personalized introduction
        full_context = f"{context_summary}{conversation_context}{tickets_context}"
        
        # Create personalized system prompt
        personalized_system = TENANT_SMS_SYSTEM + f"\n\nTENANT CONTEXT:\n{full_context}\n\n"
        if tenant_name != 'N/A':
            personalized_system += f"IMPORTANT: Address the tenant as '{tenant_name}' and reference their unit '{unit}' at '{property_name}' when appropriate.\n"
        
        messages = [
            {"role": "system", "content": personalized_system},
            {"role": "user", "content": req.message}
        ]
        
        # Add media if present (only for vision model and when necessary)
        if has_upload and model == VISION_MODEL:
            user_content = [
                {"type": "text", "text": req.message}
            ]
            if req.image_url:
                user_content.append({"type": "image_url", "image_url": {"url": req.image_url}})
            if req.document_url:
                user_content.append({"type": "text", "text": f"Document URL: {req.document_url}"})
            messages[1]["content"] = user_content
        
        # Check cache first
        cache_key = get_cache_key(messages)
        if cache_key in response_cache:
            return PmChatResponse(reply=response_cache[cache_key])

        reply = (await call_gemini(messages, model=model) or "").strip()
        if not reply:
            reply = "Sorry—I'm not sure how to help with that yet."

        # Cache the response (limit cache size)
        if len(response_cache) < 100:  # Simple cache size limit
            response_cache[cache_key] = reply

        return PmChatResponse(reply=reply)
    except Exception as e:
        print(f"Error in tenant_chat: {e}")
        import traceback
        traceback.print_exc()
        return PmChatResponse(reply="I'm experiencing some technical difficulties. Please try again or contact support.")

@app.post("/pm_chat", response_model=PmChatResponse)
async def pm_chat(req: PmChatRequest):
    """AI chat endpoint for property managers"""
    try:
        has_text = bool((req.message or "").strip())
        has_upload = bool(req.image_url or req.document_url)
        if not has_text and not has_upload:
            raise HTTPException(400, "Message or image_url/document_url required.")

        # Choose model: text by default; vision only if image provided
        model = VISION_MODEL if (has_upload and req.image_url) else TEXT_MODEL

        # Build context
        ctx: Dict[str, Any] = req.context.model_dump()
        if not ctx.get("tenant_phone") and req.phone:
            ctx["tenant_phone"] = req.phone

        # Get maintenance tickets for this tenant/property
        tenant_tickets = []
        for ticket in maintenance_tickets.values():
            if (ticket.tenant_phone == ctx.get("tenant_phone") or 
                ticket.tenant_name == ctx.get("tenant_name")):
                tenant_tickets.append(ticket)
        
        # Build comprehensive context for property manager
        context_parts = [
            f"Property: {ctx.get('property_name', 'N/A')}",
            f"Unit: {ctx.get('unit', 'N/A')}",
            f"Tenant: {ctx.get('tenant_name', 'N/A')}",
            f"Phone: {ctx.get('tenant_phone', 'N/A')}",
            f"Address: {ctx.get('address', 'N/A')}"
        ]
        
        if ctx.get("hotline"):
            context_parts.append(f"Hotline: {ctx.get('hotline')}")
        if ctx.get("portal_url"):
            context_parts.append(f"Portal: {ctx.get('portal_url')}")
            
        context_summary = " | ".join(context_parts)
        
        # Add maintenance ticket information
        maintenance_info = ""
        if tenant_tickets:
            maintenance_info = "\n\nMaintenance Tickets for this tenant:\n"
            for ticket in sorted(tenant_tickets, key=lambda x: x.created_at, reverse=True)[:5]:  # Show last 5 tickets
                maintenance_info += f"- #{ticket.id} ({ticket.priority.upper()}) - {ticket.issue_description[:100]}... - Status: {ticket.status}\n"
        else:
            maintenance_info = "\n\nNo maintenance tickets found for this tenant."
        
        system_with_context = PM_SYSTEM + f"\n\nContext: {context_summary}{maintenance_info}"

        if has_upload:
            user_parts: List[Dict[str, Any]] = [{"type": "text", "text": req.message}] if has_text else []
            if req.image_url:
                user_parts.append({"type": "image_url", "image_url": {"url": req.image_url}})
            if req.document_url:
                user_parts.append({"type": "text", "text": f"Document URL: {req.document_url}"})
            user_content: Any = user_parts
        else:
            user_content = req.message

        messages = [
            {"role": "system", "content": system_with_context},
            {"role": "user", "content": user_content},
        ]

        # Check cache first
        cache_key = get_cache_key(messages)
        if cache_key in response_cache:
            return PmChatResponse(reply=response_cache[cache_key])

        reply = (await call_gemini(messages, model=model) or "").strip()
        if not reply:
            reply = "Sorry—I'm not sure how to help with that yet."

        # Cache the response (limit cache size)
        if len(response_cache) < 100:  # Simple cache size limit
            response_cache[cache_key] = reply

        return PmChatResponse(reply=reply)
    except Exception as e:
        print(f"Error in pm_chat: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/tenant_sms", response_model=TenantSmsResponse)
async def tenant_sms(req: TenantSmsRequest):
    """Process incoming SMS from tenant with maintenance ticket creation"""
    try:
        return await process_tenant_sms(req)
    except Exception as e:
        print(f"Error in tenant_sms: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/maintenance_tickets")
def get_maintenance_tickets():
    """Get all maintenance tickets"""
    # Explicitly serialize Pydantic models to dict
    tickets = [ticket.model_dump() if hasattr(ticket, 'model_dump') else dict(ticket) for ticket in maintenance_tickets.values()]
    print(f"[DEBUG] Returning {len(tickets)} maintenance ticket(s) from /maintenance_tickets endpoint")
    if tickets:
        print(f"[DEBUG] Ticket IDs: {[t.get('id') if isinstance(t, dict) else getattr(t, 'id', 'N/A') for t in tickets]}")
    return {"tickets": tickets}

@app.get("/debug/maintenance")
def debug_maintenance():
    """Debug endpoint to see maintenance tickets and phone mappings"""
    return {
        "maintenance_tickets": list(maintenance_tickets.values()),
        "phone_to_property": phone_to_property,
        "property_settings": property_settings,
        "sms_messages": {k: len(v) for k, v in sms_messages.items()}
    }

@app.get("/debug/sms")
def debug_sms():
    """Debug endpoint to see SMS messages"""
    return {
        "sms_messages": sms_messages,
        "phone_to_property": phone_to_property,
        "property_settings": property_settings
    }

@app.post("/test/create-ticket")
def test_create_ticket():
    """Test endpoint to create a maintenance ticket"""
    try:
        ticket_id = create_maintenance_ticket(
            tenant_phone="+1234567890",
            tenant_name="Test Tenant",
            unit="1A",
            property_name="Test Property",
            issue_description="Test toilet clogged issue",
            media_urls=[]
        )
        return {
            "success": True,
            "ticket_id": ticket_id,
            "total_tickets": len(maintenance_tickets)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.put("/properties/{property_id}/settings")
async def update_property_settings(property_id: str, settings: dict):
    """Update property settings"""
    try:
        property_settings[property_id] = settings
        print(f"[OK] Updated settings for property {property_id}")
        return {"success": True, "settings": settings}
    except Exception as e:
        print(f"[ERROR] Error updating property settings: {e}")
        return {"success": False, "error": str(e)}

@app.post("/properties/{property_id}/settings")
async def update_property_settings_post(property_id: str, settings: dict):
    """Update property settings (POST method)"""
    try:
        property_settings[property_id] = settings
        print(f"[OK] Updated settings for property {property_id}")
        return {"success": True, "settings": settings}
    except Exception as e:
        print(f"[ERROR] Error updating property settings: {e}")
        return {"success": False, "error": str(e)}

@app.post("/sync/properties")
async def sync_properties(properties: List[Dict[str, Any]]):
    """Sync properties from frontend to backend"""
    try:
        for prop in properties:
            property_id = prop.get("id")
            phone = prop.get("phone")
            context = prop.get("context", {})
            
            if property_id and phone:
                # Map phone to property
                phone_to_property[phone] = property_id
                
                # Store property settings
                property_settings[property_id] = PropertySettings(
                    ai_enabled=True,
                    auto_reply=True,
                    verification_sent=False
                )
                
                # Store property info for context
                property_info = {
                    "tenant_name": context.get("tenant_name", "Tenant"),
                    "unit": context.get("unit", "Unknown"),
                    "address": context.get("address", "Unknown"),
                    "property_name": context.get("property_name", prop.get("name", "Property"))
                }
                property_settings[property_id] = property_info
                
                print(f"[SYNC] Synced property {property_id} for phone {phone}")
        
        return {"success": True, "synced": len(properties)}
    except Exception as e:
        print(f"[ERROR] Error syncing properties: {e}")
        return {"success": False, "error": str(e)}

@app.get("/maintenance_tickets/{ticket_id}")
def get_maintenance_ticket(ticket_id: str):
    """Get specific maintenance ticket"""
    if ticket_id not in maintenance_tickets:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return maintenance_tickets[ticket_id]

@app.put("/maintenance_tickets/{ticket_id}/status")
def update_ticket_status(ticket_id: str, status_data: dict):
    """Update maintenance ticket status"""
    if ticket_id not in maintenance_tickets:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    status = status_data.get("status")
    if not status:
        raise HTTPException(status_code=400, detail="Status is required")
    
    valid_statuses = ["open", "in_progress", "resolved", "closed"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    maintenance_tickets[ticket_id].status = status
    print(f"[TICKET] Updated ticket {ticket_id} status to {status}")
    
    return {"success": True, "ticket_id": ticket_id, "status": status}

@app.patch("/maintenance_tickets/{ticket_id}/status")
def update_ticket_status_patch(ticket_id: str, status_data: dict):
    """Update maintenance ticket status (alternative endpoint)"""
    if ticket_id not in maintenance_tickets:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    status = status_data.get("status")
    if not status:
        raise HTTPException(status_code=400, detail="Status is required")
    
    valid_statuses = ["open", "in_progress", "resolved", "closed"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    maintenance_tickets[ticket_id].status = status
    print(f"[TICKET] Updated ticket {ticket_id} status to {status}")
    
    return {"success": True, "ticket_id": ticket_id, "status": status}

@app.post("/contacts/upsert")
async def upsert_contact(request: Request):
    """Upsert contact with optional verification SMS"""
    try:
        # Get query parameters
        phone = request.query_params.get("phone")
        send_verification = request.query_params.get("send_verification", "false").lower() == "true"
        property_id = request.query_params.get("property_id")
        
        if not phone:
            raise HTTPException(status_code=400, detail="Phone number is required")
        
        # Get context data from request body
        context_data = await request.json()
        
        print(f"[CONTACT] Upserting contact for phone: {phone}, send_verification: {send_verification}")
        
        # Store contact/context data
        if property_id:
            # Store property context
            property_settings[property_id] = {
                "property_id": property_id,
                "tenant_name": context_data.get("tenant_name", "Unknown"),
                "unit": context_data.get("unit", "Unknown"),
                "address": context_data.get("address", "Unknown"),
                "property_name": context_data.get("property_name", "Unknown Property"),
                "tenant_phone": phone,
                "ai_enabled": True,
                "hotline": context_data.get("hotline"),
                "portal_url": context_data.get("portal_url")
            }
            
            # Update phone to property mapping
            phone_to_property[phone] = property_id
            print(f"[CONTACT] Mapped phone {phone} to property {property_id}")
        
        result = {"ok": True}
        
        # Send verification SMS if requested
        if send_verification:
            try:
                verification_message = f"Hi! This is Esto, your AI property assistant. I'm here to help with maintenance issues, rent questions, and general property inquiries. How can I assist you today?"
                
                print(f"[SMS] Sending verification SMS to {phone}")
                
                # Send SMS via Twilio
                sms_sid = await send_sms_via_twilio(phone, verification_message)
                
                if sms_sid:
                    # Log the outbound message
                    log_sms(phone, "outbound", verification_message, phone, TWILIO_FROM_NUMBER, sms_sid)
                    result["verification_sent"] = True
                    print(f"[SMS] Verification SMS sent successfully to {phone}")
                else:
                    result["verification_sent"] = False
                    result["verification_error"] = "Failed to send verification SMS"
                    print(f"[SMS] Failed to send verification SMS to {phone}")
                    
            except Exception as sms_error:
                print(f"[ERROR] Error sending verification SMS: {sms_error}")
                result["verification_sent"] = False
                result["verification_error"] = str(sms_error)
        
        return result
        
    except Exception as e:
        print(f"[ERROR] Error upserting contact: {e}")
        return {
            "ok": False,
            "error": str(e)
        }

@app.get("/property_context/{phone}")
def get_property_context(phone: str):
    """Get comprehensive property context for frontend AI assistant"""
    # Get tenant context
    tenant_context = Context(
        tenant_name="Tenant",
        unit="Unknown",
        address="Unknown",
        tenant_phone=phone,
        property_name="Property"
    )
    
    # Get maintenance tickets for this tenant
    tenant_tickets = []
    for ticket in maintenance_tickets.values():
        if ticket.tenant_phone == phone:
            tenant_tickets.append(ticket)
    
    # Get SMS history
    sms_history = sms_messages.get(phone, [])
    
    return {
        "context": tenant_context,
        "maintenance_tickets": tenant_tickets,
        "sms_history": sms_history[-10:],  # Last 10 messages
        "total_tickets": len(tenant_tickets),
        "open_tickets": len([t for t in tenant_tickets if t.status == "open"])
    }

# ------------------ Contact Management ------------------
@app.post("/contacts/upsert")
async def upsert_contact(phone: str, context: Context, send_verification: bool = False, property_id: str = None):
    """Register/update contact information"""
    phone = phone.strip()
    if not phone:
        raise HTTPException(400, "phone required")
    
    result = {"ok": True}
    
    # Map phone to property if property_id provided
    if property_id:
        phone_to_property[phone] = property_id
        print(f"[PHONE] Mapped phone {phone} to property {property_id}")
    
    # Send verification SMS if requested
    if send_verification:
        try:
            verification_result = await send_verification_sms(phone, context)
            result["verification_sent"] = verification_result["success"]
            if not verification_result["success"]:
                result["verification_error"] = verification_result.get("error", "Unknown error")
        except Exception as e:
            result["verification_sent"] = False
            result["verification_error"] = str(e)
    
    return result

@app.get("/contacts/{phone}", response_model=Context)
def get_contact(phone: str):
    """Get contact information"""
    # For now, return a default context
    return Context(
        tenant_name="Unknown",
        unit="Unknown",
        address="Unknown",
        tenant_phone=phone,
    )

# ------------------ Thread Management ------------------
@app.get("/threads")
def list_threads():
    """Get all conversation threads"""
    return []

@app.get("/threads/{phone}")
def get_thread(phone: str):
    """Get messages for a specific phone number"""
    return sms_messages.get(phone, [])

@app.get("/chat/{phone}")
def get_chat_history(phone: str):
    """Get AI chat history for a phone number"""
    return sms_messages.get(phone, [])

# ------------------ SMS Management ------------------
@app.post("/sms/send")
async def send_sms(req: SendSmsRequest):
    """Send SMS manually to tenant"""
    try:
        # Use property_id or propertyId (support both formats)
        property_id = req.property_id or req.propertyId
        
        message_sid = await send_sms_via_twilio(req.to, req.message)
        if message_sid:
            log_sms(req.to, "outbound", req.message, req.to, TWILIO_FROM_NUMBER, message_sid)
            
            # Link phone to property if provided
            if property_id:
                phone_to_property[req.to] = property_id
                print(f"[LINK] Linked phone {req.to} to property {property_id}")
            
            return {"success": True, "message_sid": message_sid}
        else:
            return {"success": False, "error": "Failed to send SMS"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending SMS: {str(e)}")

@app.post("/sms/verification/{phone}")
async def send_verification_sms(phone: str, context: Context):
    """Send verification SMS to new tenant introducing Esto"""
    verification_message = (
        f"Hi {context.tenant_name}!\n\n"
        f"This is {context.property_name or 'your property management team'} using Esto. "
        f"You can now text this number for quick assistance with:\n"
        f"- Maintenance requests\n"
        f"- Rent questions\n"
        f"- General inquiries\n\n"
        f"Just send a text and I'll help you right away!"
    )
    
    try:
        message_sid = await send_sms_via_twilio(phone, verification_message)
        if message_sid:
            log_sms(phone, "outbound", verification_message, phone, TWILIO_FROM_NUMBER, message_sid)
            return {"success": True, "message_sid": message_sid}
        else:
            return {"success": False, "error": "Failed to send verification SMS"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending verification SMS: {str(e)}")

# ------------------ Property Settings ------------------
@app.get("/properties/{property_id}/settings")
def get_property_settings(property_id: str):
    """Get property settings"""
    return property_settings.get(property_id, PropertySettings())

@app.post("/properties/{property_id}/settings")
def update_property_settings_post_settings(property_id: str, settings: PropertySettings):
    """Update property settings"""
    property_settings[property_id] = settings
    return {"success": True, "settings": settings}

@app.get("/debug/phone-mappings")
def get_phone_mappings():
    """Debug endpoint to see current phone mappings"""
    return {
        "phone_to_property": phone_to_property,
        "property_settings": {k: {"ai_enabled": v.ai_enabled, "auto_reply": v.auto_reply} for k, v in property_settings.items()}
    }

@app.post("/debug/map-phone")
def map_phone_to_property(phone: str, property_id: str):
    """Debug endpoint to manually map a phone to a property"""
    phone = phone.strip()
    phone_to_property[phone] = property_id
    
    # Set up default property settings
    property_settings[property_id] = PropertySettings(
        ai_enabled=True,
        auto_reply=True,
        verification_sent=False
    )
    
    return {"ok": True, "message": f"Mapped {phone} to property {property_id}"}

# ------------------ Twilio Integration ------------------
@app.api_route("/sms", methods=["GET", "POST"])
async def receive_sms(request: Request):
    """Twilio webhook endpoint for incoming SMS"""
    if request.method == "GET":
        return "SMS webhook endpoint is ready! Twilio should POST here."
    
    try:
        # Parse form data
        form_data = await request.form()
        from_number = form_data.get("From", "Unknown")
        to_number = form_data.get("To", "Unknown")
        message_body = form_data.get("Body", "")
        message_sid = form_data.get("MessageSid", f"SM{uuid.uuid4().hex[:30]}")
        media_count = int(form_data.get("NumMedia", 0))
    except Exception as e:
        print(f"[ERROR] Error parsing form data: {e}")
        # Fallback to JSON parsing
        try:
            json_data = await request.json()
            from_number = json_data.get("From", "Unknown")
            to_number = json_data.get("To", "Unknown")
            message_body = json_data.get("Body", "")
            message_sid = json_data.get("MessageSid", f"SM{uuid.uuid4().hex[:30]}")
            media_count = int(json_data.get("NumMedia", 0))
        except Exception as e2:
            print(f"[ERROR] Error parsing JSON data: {e2}")
            return {"error": "Invalid request format"}
    
    print(f"[PHONE] New SMS received:")
    print(f"   From: {from_number}")
    print(f"   To: {to_number}")
    print(f"   Body: {message_body}")
    print(f"   SID: {message_sid}")
    print(f"   Media: {media_count} files")
    print("-" * 50)
    
    # Log the inbound SMS from tenant
    log_sms(from_number, "inbound", message_body, to_number, from_number, message_sid)
    
    # Process through AI if enabled and send response back to tenant
    ai_reply = None
    try:
        # Get actual property settings for this phone number
        settings = get_property_settings_by_phone(from_number)
        print(f"[SETTINGS] Property settings for {from_number}: AI={settings.ai_enabled}, Auto-reply={settings.auto_reply}")
        
        if settings.ai_enabled and settings.auto_reply:
            # Get tenant context - try to find actual property info
            property_id = phone_to_property.get(from_number)
            print(f"[SEARCH] Looking up property for phone {from_number}: {property_id}")
            print(f"[SEARCH] Available phone mappings: {list(phone_to_property.keys())}")
            
            if property_id:
                # Try to get actual property info from property_settings
                property_info = property_settings.get(property_id, {})
                tenant_context = Context(
                    tenant_name=property_info.get("tenant_name", "Tenant"),
                    unit=property_info.get("unit", "Unknown"),
                    address=property_info.get("address", "Unknown"),
                    tenant_phone=from_number,
                    property_name=property_info.get("property_name", f"Property {property_id}")
                )
                print(f"[HOME] Found property context for {from_number}: {property_id}")
            else:
                # Fallback to generic context
                tenant_context = Context(
                    tenant_name="Tenant",
                    unit="Unknown",
                    address="Unknown",
                    tenant_phone=from_number,
                    property_name="Unknown Property"
                )
                print(f"[WARNING] No property mapping found for {from_number}, using generic context")
            
            # Process media URLs if present
            media_urls = []
            if media_count > 0:
                for i in range(media_count):
                    media_url = form_data.get(f"MediaUrl{i}", "")
                    if media_url:
                        media_urls.append(media_url)
            
            # Create tenant SMS request
            tenant_request = TenantSmsRequest(
                message=message_body,
                context=tenant_context,
                phone=from_number,
                media_urls=media_urls if media_urls else None
            )
            
            # Process through tenant SMS AI
            print(f"[AI] Processing SMS with AI for {from_number}...")
            tenant_response = await process_tenant_sms(tenant_request)
            ai_reply = tenant_response.reply
            print(f"[AI] AI response generated: {ai_reply[:100]}...")
            
            # Send AI response back to tenant
            if ai_reply:
                reply_sid = await send_sms_via_twilio(from_number, ai_reply)
                if reply_sid:
                    log_sms(from_number, "outbound", ai_reply, from_number, to_number, reply_sid)
                    print(f"[AI] AI replied: {ai_reply}")
                    
                    # Log maintenance ticket creation
                    if tenant_response.maintenance_ticket_created:
                        print(f"[TICKET] Maintenance ticket {tenant_response.ticket_id} created for {from_number}")
        else:
            print(f"[PHONE] AI disabled or auto-reply off for {from_number}")
        
    except Exception as e:
        import traceback
        print(f"[ERROR] Error processing SMS with AI: {e}")
        print(f"[ERROR] Full traceback: {traceback.format_exc()}")
        # Send fallback response only if auto-reply is enabled
        if settings.auto_reply:
            fallback_msg = "Thanks for your message. We'll get back to you soon!"
            reply_sid = await send_sms_via_twilio(from_number, fallback_msg)
            if reply_sid:
                log_sms(from_number, "outbound", fallback_msg, from_number, to_number, reply_sid)
    
    # Return TwiML response
    try:
        from twilio.twiml.messaging_response import MessagingResponse
        response = MessagingResponse()
        return str(response)
    except ImportError:
        # Fallback if Twilio library is not available
        return "<?xml version=\"1.0\" encoding=\"UTF-8\"?><Response></Response>"

# ------------------ Data Flow Tracking ------------------
data_flow_events = []
pms_tenants = []  # Tenants synced from PMS
pms_leases = []   # Leases synced from PMS

class DataFlowEvent(BaseModel):
    id: str
    timestamp: str
    direction: str  # "inbound" or "outbound"
    type: str  # "tenant", "lease", "communication", "payment"
    status: str  # "success", "pending", "failed"
    details: Dict[str, Any]

class PMSTenant(BaseModel):
    id: str
    name: str
    unit: str
    property_name: str
    phone: str
    email: str
    synced_at: str
    status: str  # "active", "pending", "inactive"

class PMSLease(BaseModel):
    id: str
    tenant_id: str
    tenant_name: str
    unit: str
    property_name: str
    start_date: str
    end_date: str
    rent_amount: float
    synced_at: str
    status: str  # "active", "pending", "expired"

def generate_mock_data_flow():
    """Generate mock data flow events for demonstration"""
    global data_flow_events, pms_tenants, pms_leases
    
    # Generate mock tenants
    mock_tenant_names = [
        ("John Smith", "101", "Sunset Apartments"),
        ("Sarah Johnson", "202", "Sunset Apartments"),
        ("Michael Brown", "303", "Riverside Complex"),
        ("Emily Davis", "104", "Riverside Complex"),
        ("David Wilson", "205", "Oak Street Residences"),
    ]
    
    pms_tenants = []
    for i, (name, unit, prop) in enumerate(mock_tenant_names):
        tenant = PMSTenant(
            id=f"TNT{1000 + i}",
            name=name,
            unit=unit,
            property_name=prop,
            phone=f"+1555000{1000 + i}",
            email=f"{name.lower().replace(' ', '.')}@email.com",
            synced_at=datetime.now().isoformat(),
            status="active"
        )
        pms_tenants.append(tenant)
        
        data_flow_events.append(DataFlowEvent(
            id=f"EVT{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now().isoformat(),
            direction="inbound",
            type="tenant",
            status="success",
            details={
                "tenant_id": tenant.id,
                "tenant_name": tenant.name,
                "unit": tenant.unit,
                "property": tenant.property_name
            }
        ))
    
    # Generate mock leases
    pms_leases = []
    for i, tenant in enumerate(pms_tenants):
        lease = PMSLease(
            id=f"LSE{2000 + i}",
            tenant_id=tenant.id,
            tenant_name=tenant.name,
            unit=tenant.unit,
            property_name=tenant.property_name,
            start_date="2024-01-01",
            end_date="2025-12-31",
            rent_amount=1200.0 + (i * 100),
            synced_at=datetime.now().isoformat(),
            status="active"
        )
        pms_leases.append(lease)
        
        data_flow_events.append(DataFlowEvent(
            id=f"EVT{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now().isoformat(),
            direction="inbound",
            type="lease",
            status="success",
            details={
                "lease_id": lease.id,
                "tenant_name": lease.tenant_name,
                "unit": lease.unit,
                "rent_amount": lease.rent_amount
            }
        ))
    
    # Generate mock outbound communications
    for i in range(8):
        data_flow_events.append(DataFlowEvent(
            id=f"EVT{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now().isoformat(),
            direction="outbound",
            type="communication",
            status="success",
            details={
                "message_type": "sms" if i % 2 == 0 else "email",
                "recipient": pms_tenants[i % len(pms_tenants)].name,
                "subject": "Maintenance Update" if i % 3 == 0 else "Rent Reminder"
            }
        ))
    
    # Generate mock outbound payments
    for i in range(5):
        data_flow_events.append(DataFlowEvent(
            id=f"EVT{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now().isoformat(),
            direction="outbound",
            type="payment",
            status="success",
            details={
                "payment_id": f"PAY{3000 + i}",
                "tenant_name": pms_tenants[i % len(pms_tenants)].name,
                "amount": 1200.0 + (i * 100),
                "method": "ACH"
            }
        ))

generate_mock_data_flow()

@app.get("/api/data-flow/events")
async def get_data_flow_events():
    """Get all data flow events"""
    return {"events": [e.model_dump() for e in data_flow_events]}

@app.get("/api/data-flow/stats")
async def get_data_flow_stats():
    """Get data flow statistics"""
    inbound_events = [e for e in data_flow_events if e.direction == "inbound"]
    outbound_events = [e for e in data_flow_events if e.direction == "outbound"]
    
    return {
        "total_events": len(data_flow_events),
        "inbound": {
            "total": len(inbound_events),
            "tenants": len([e for e in inbound_events if e.type == "tenant"]),
            "leases": len([e for e in inbound_events if e.type == "lease"])
        },
        "outbound": {
            "total": len(outbound_events),
            "communications": len([e for e in outbound_events if e.type == "communication"]),
            "payments": len([e for e in outbound_events if e.type == "payment"])
        },
        "success_rate": len([e for e in data_flow_events if e.status == "success"]) / len(data_flow_events) * 100 if data_flow_events else 0
    }

# ------------------ Tenant Application Endpoints ------------------
@app.post("/api/tenant-applications/process-documents")
async def process_tenant_documents_endpoint(request: dict):
    """Process tenant application documents (driver's license, pay stubs, credit score)"""
    try:
        from backend_modules.llm_service import process_tenant_documents
        
        application_id = request.get("applicationId", "")
        drivers_license_url = request.get("driversLicenseUrl")
        pay_stub_urls = request.get("payStubUrls", [])
        credit_score_url = request.get("creditScoreUrl")
        
        if not application_id:
            raise HTTPException(status_code=400, detail="applicationId is required")
        
        # Process documents using Gemini Vision
        result = await process_tenant_documents(
            drivers_license_url=drivers_license_url,
            pay_stub_urls=pay_stub_urls,
            credit_score_url=credit_score_url
        )
        
        return {
            "success": True,
            "applicationId": application_id,
            "extractedData": result
        }
        
    except Exception as e:
        print(f"Error processing tenant documents: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing documents: {str(e)}")

@app.post("/api/tenant-applications/{application_id}/calculate-score")
async def calculate_screening_score_endpoint(application_id: str, request: dict):
    """Calculate screening score for a tenant application"""
    try:
        from backend_modules.screening_service import calculate_screening_score
        from datetime import datetime
        
        # Get application data from request (in production, fetch from database)
        credit_score = request.get("creditScore")
        monthly_income = request.get("monthlyIncome")
        monthly_rent = request.get("monthlyRent", 0)
        license_expiration = request.get("licenseExpiration")
        license_name = request.get("licenseName")
        applicant_name = request.get("applicantName", "")
        
        # Get property settings (defaults if not provided)
        min_credit_score = request.get("minCreditScore", 600)
        income_multiplier = request.get("incomeMultiplier", 3.0)
        min_income_multiplier = request.get("minIncomeMultiplier", 2.5)
        
        # Calculate score (based on credit score and income only)
        score, notes = calculate_screening_score(
            credit_score=credit_score,
            monthly_income=monthly_income,
            monthly_rent=monthly_rent,
            min_credit_score=min_credit_score,
            income_multiplier=income_multiplier,
            min_income_multiplier=min_income_multiplier
        )
        
        # Determine status based on score
        if score == "green":
            status = "approved"
            auto_approved = True
        elif score == "yellow":
            status = "under_review"
            auto_approved = False
        else:
            status = "rejected"
            auto_approved = False
        
        return {
            "success": True,
            "applicationId": application_id,
            "score": score,
            "status": status,
            "notes": notes,
            "autoApproved": auto_approved
        }
        
    except Exception as e:
        print(f"Error calculating screening score: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error calculating score: {str(e)}")

@app.post("/api/tenant-applications/{application_id}/background-check")
async def run_background_check_endpoint(application_id: str, request: Request):
    """Run background check for a tenant application"""
    try:
        from backend_modules.screening_service import run_background_check
        from datetime import datetime
        
        # Parse request body
        request_data = await request.json()
        
        # Get application data from request
        applicant_name = request_data.get("applicantName", "")
        applicant_email = request_data.get("applicantEmail", "")
        applicant_phone = request_data.get("applicantPhone")
        license_number = request_data.get("licenseNumber")
        license_dob = request_data.get("licenseDOB")
        employer_name = request_data.get("employerName")
        credit_score = request_data.get("creditScore")
        
        if not applicant_name or not applicant_email:
            raise HTTPException(status_code=400, detail="applicantName and applicantEmail are required")
        
        # Parse DOB if provided
        dob = None
        if license_dob:
            if isinstance(license_dob, str):
                dob = datetime.fromisoformat(license_dob.replace("Z", "+00:00"))
            else:
                dob = license_dob
        
        # Run background check
        bg_check_result = run_background_check(
            applicant_name=applicant_name,
            applicant_email=applicant_email,
            applicant_phone=applicant_phone,
            license_number=license_number,
            dob=dob,
            employer_name=employer_name,
            credit_score=credit_score
        )
        
        return {
            "success": True,
            "applicationId": application_id,
            "backgroundCheck": bg_check_result
        }
        
    except Exception as e:
        print(f"Error running background check: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error running background check: {str(e)}")

# Calendar endpoints removed - system uses database queries to find best tenants

# Scheduling endpoints removed - system uses database queries to find best tenants
# Approved applicants can be contacted directly by property managers

@app.post("/api/tenant-applications/{application_id}/send-rejection-email")
async def send_rejection_email_endpoint(application_id: str, request: dict):
    """Send rejection email to applicant"""
    try:
        from backend_modules.agentmail_service import AgentmailClient, get_rejection_email_template
        
        applicant_name = request.get("applicantName", "")
        applicant_email = request.get("applicantEmail", "")
        property_name = request.get("propertyName", "the property")
        
        if not applicant_email:
            raise HTTPException(status_code=400, detail="applicantEmail is required")
        
        agentmail_client = AgentmailClient()
        subject, body = get_rejection_email_template(applicant_name, property_name)
        
        email_result = await agentmail_client.send_email(
            to=applicant_email,
            subject=subject,
            body=body
        )
        
        return {
            "success": email_result.get("success", False),
            "applicationId": application_id,
            "emailSent": email_result.get("success", False)
        }
        
    except Exception as e:
        print(f"Error sending rejection email: {e}")
        raise HTTPException(status_code=500, detail=f"Error sending email: {str(e)}")

@app.post("/api/properties/{property_id}/best-applicant")
async def find_best_applicant_endpoint(property_id: str, request: dict):
    """
    Find the best applicant for a property by analyzing applications using Gemini AI
    
    Request body:
    {
        "userId": "user_id",
        "propertyRent": 2000.0 (optional),
        "applicationIds": ["id1", "id2", ...] (optional - if provided, analyzes only these)
    }
    """
    try:
        from backend_modules.llm_service import call_gemini, TEXT_MODEL
        
        user_id = request.get("userId")
        property_rent = request.get("propertyRent")
        application_ids = request.get("applicationIds", [])
        
        if not user_id:
            raise HTTPException(status_code=400, detail="userId is required")
        
        # Step 1: Fetch applications from database via frontend API
        frontend_url = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
        service_token = os.getenv("APPLICATION_SERVICE_TOKEN", "")
        
        applicants_data = []
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Fetch all applications for this user
                api_url = f"{frontend_url}/api/applications/internal"
                headers = {
                    "Authorization": f"Bearer {service_token}",
                    "Content-Type": "application/json"
                }
                
                # First, get all applications for the user
                response = await client.get(api_url, headers=headers, params={"userId": user_id})
                response.raise_for_status()
                result = response.json()
                all_applications = result.get("applications", [])
                
                # Filter by property_id and optionally by application_ids
                for app in all_applications:
                    app_property_id = app.get("propertyId")
                    app_id = app.get("id")
                    
                    # Filter by property if specified
                    if property_id and app_property_id != property_id:
                        continue
                    
                    # Filter by application IDs if specified
                    if application_ids and len(application_ids) > 0:
                        if app_id not in application_ids:
                            continue
                    
                    # Calculate income ratio if rent and income provided
                    monthly_income = app.get("monthlyIncome")
                    income_ratio = None
                    if property_rent and monthly_income:
                        income_ratio = monthly_income / property_rent
                    
                    applicants_data.append({
                        "application_id": app_id,
                        "applicant_name": app.get("applicantName", "Unknown"),
                        "applicant_email": app.get("applicantEmail", ""),
                        "applicant_phone": app.get("applicantPhone"),
                        "credit_score": app.get("creditScore"),
                        "monthly_income": monthly_income,
                        "annual_income": app.get("annualIncome"),
                        "income_ratio": income_ratio,
                        "screening_score": app.get("screeningScore"),
                        "status": app.get("status", "pending"),
                        "employer_name": app.get("employerName"),
                        "screening_notes": app.get("screeningNotes"),
                        "background_check": app.get("backgroundCheckResult"),
                        "email_body": app.get("emailBody", "")[:500] if app.get("emailBody") else None,
                        "received_at": app.get("receivedAt")
                    })
                    
        except Exception as e:
            print(f"⚠️ Error fetching applications from database: {e}")
            return {
                "success": False,
                "error": f"Failed to fetch applications from database: {str(e)}",
                "bestApplicant": None
            }
        
        # If no matching applicants found
        if len(applicants_data) == 0:
            return {
                "success": False,
                "error": "No applicants found" + (" for the selected applications" if application_ids else " for this property"),
                "bestApplicant": None
            }
        
        # Step 2: Format applicants data for Gemini analysis
        applicants_text_parts = []
        for idx, app in enumerate(applicants_data):
            monthly_income_str = f"${app.get('monthly_income', 0):,.2f}" if app.get('monthly_income') else "N/A"
            annual_income_str = f"${app.get('annual_income', 0):,.2f}" if app.get('annual_income') else "N/A"
            income_ratio_str = f"{app.get('income_ratio', 0):.2f}x" if app.get('income_ratio') else "N/A"
            
            applicant_text = f"""Applicant {idx + 1} (ID: {app.get('application_id', 'N/A')}):
Name: {app.get('applicant_name', 'N/A')}
Email: {app.get('applicant_email', 'N/A')}
Phone: {app.get('applicant_phone', 'N/A')}
Credit Score: {app.get('credit_score', 'N/A')}
Monthly Income: {monthly_income_str}
Annual Income: {annual_income_str}
Income to Rent Ratio: {income_ratio_str}
Screening Score: {app.get('screening_score', 'N/A')}
Status: {app.get('status', 'N/A')}
Employer: {app.get('employer_name', 'N/A')}
Screening Notes: {app.get('screening_notes', 'N/A')}
Background Check: {app.get('background_check', 'N/A')}
Received At: {app.get('received_at', 'N/A')}
Email Body: {app.get('email_body', 'N/A')}"""
            applicants_text_parts.append(applicant_text)
        
        applicants_text = "\n\n".join(applicants_text_parts)
        
        # Step 3: Use Gemini to analyze and rank applicants
        rent_info = f"Property rent: ${property_rent:,.2f}/month" if property_rent else "Property rent: Not specified"
        
        llm_prompt = f"""You are an expert property manager analyzing tenant applications to select the SINGLE BEST applicant.

Here are the applicants for property {property_id}:

{applicants_text}

{rent_info}

Analyze all applicants and determine the SINGLE BEST applicant based on:
1. Credit score (higher is better, above 680 is ideal, above 700 is excellent)
2. Income to rent ratio (3x or higher is ideal, 4x+ is excellent)
3. Screening score (green > yellow > red)
4. Complete documentation (driver's license, pay stubs, credit report)
5. Employment stability (long-term employer is better)
6. Background check results (no issues is preferred)

You must select ONLY ONE applicant - the one with the best overall qualification profile.

Provide your analysis in this JSON format:
{{
    "bestApplicantId": "application_id",
    "reasoning": "Detailed explanation of why this applicant is the best choice, considering all factors",
    "keyStrengths": ["strength 1", "strength 2"],
    "concerns": ["concern 1 or null if none"],
    "recommendation": "APPROVE", "REVIEW", or "DECLINE",
    "rankedApplicants": [
        {{"applicationId": "id", "rank": 1, "score": "explanation"}},
        {{"applicationId": "id", "rank": 2, "score": "explanation"}}
    ]
}}

Return ONLY valid JSON, no other text. You must select exactly ONE bestApplicantId."""
        
        llm_messages = [
            {"role": "user", "content": llm_prompt}
        ]
        
        llm_response = await call_gemini(llm_messages, TEXT_MODEL)
        llm_content = llm_response.get("content", "")
        
        # Parse LLM response (try to extract JSON)
        import json
        import re
        
        # Try to extract JSON from response
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', llm_content, re.DOTALL)
        if json_match:
            try:
                agent_analysis = json.loads(json_match.group())
            except Exception as parse_error:
                print(f"⚠️ Error parsing LLM JSON response: {parse_error}")
                agent_analysis = {
                    "reasoning": llm_content[:500],
                    "recommendation": "REVIEW"
                }
        else:
            agent_analysis = {
                "reasoning": llm_content[:500] if llm_content else "Analysis completed",
                "recommendation": "REVIEW"
            }
        
        # Find the best applicant from the data
        best_applicant_id = agent_analysis.get("bestApplicantId")
        best_applicant_data = None
        
        if best_applicant_id:
            best_applicant_data = next(
                (app for app in applicants_data if app.get("application_id") == best_applicant_id),
                None
            )
        
        # If no ID provided or not found, select top ranked by credit + income
        if not best_applicant_data:
            # Sort by credit score first, then income ratio
            sorted_apps = sorted(
                applicants_data,
                key=lambda x: (
                    x.get("credit_score") or 0,
                    x.get("income_ratio") or 0
                ),
                reverse=True
            )
            best_applicant_data = sorted_apps[0] if sorted_apps else None
        
        # Add ranking information if available
        ranked_applicants = agent_analysis.get("rankedApplicants", [])
        if ranked_applicants and best_applicant_data:
            # Find the rank of the best applicant
            for ranked in ranked_applicants:
                if ranked.get("applicationId") == best_applicant_data.get("application_id"):
                    best_applicant_data["rank"] = ranked.get("rank", 1)
                    best_applicant_data["rankExplanation"] = ranked.get("score", "")
                    break
        
        return {
            "success": True,
            "bestApplicant": best_applicant_data,
            "agentAnalysis": agent_analysis,
            "allApplicants": applicants_data  # Return all applicants for frontend display
        }
        
    except Exception as e:
        print(f"Error finding best applicant: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error finding best applicant: {str(e)}")

# ------------------ Agentmail Inbox Monitoring ------------------

@app.post("/api/agentmail/check-inbox")
async def check_agentmail_inbox(request: Request, background_tasks: BackgroundTasks):
    """Manually trigger inbox check (also runs as periodic background task)"""
    try:
        from backend_modules.inbox_monitor import monitor_inbox
        
        # Get user_id from request body if provided (from frontend)
        body = await request.json() if request.headers.get("content-type") == "application/json" else {}
        user_id = body.get("userId") or os.getenv("DEFAULT_USER_ID", "default_user")
        
        print(f"📬 Checking inbox for user_id: {user_id}")
        
        # Run in background with user_id
        background_tasks.add_task(monitor_inbox, user_id=user_id)
        
        return {"success": True, "message": "Inbox check initiated", "user_id": user_id}
    except Exception as e:
        print(f"Error checking inbox: {e}")
        raise HTTPException(status_code=500, detail=f"Error checking inbox: {str(e)}")

@app.get("/api/agentmail/inbox-status")
async def get_inbox_status():
    """Check Agentmail inbox status - shows if emails have been received"""
    try:
        from backend_modules.agentmail_service import AgentmailClient
        
        agentmail_client = AgentmailClient()
        
        inbox_id = os.getenv("AGENTMAIL_INBOX_ID", "")
        
        # Get all threads from Agentmail
        threads = await agentmail_client.list_threads(inbox_id=inbox_id)
        
        # Get details for first few threads
        thread_details = []
        for thread in threads[:10]:  # Limit to first 10
            thread_id = thread.get("thread_id") or thread.get("id")
            subject = thread.get("subject", "No subject")
            
            # Get full thread with messages
            full_thread = await agentmail_client.get_thread(thread_id)
            if full_thread:
                messages = full_thread.get("messages", [])
                unread_count = len([m for m in messages if not m.get("read", False)])
                
                # Get first message details
                first_msg = messages[0] if messages else {}
                sender = first_msg.get("from", "") or (first_msg.get("from_", [""])[0] if first_msg.get("from_") else "")
                
                thread_details.append({
                    "thread_id": thread_id,
                    "subject": subject,
                    "message_count": len(messages),
                    "unread_count": unread_count,
                    "sender": sender,
                    "last_updated": first_msg.get("date") or first_msg.get("created_at")
                })
        
        return {
            "success": True,
            "inbox_id": inbox_id,
            "total_threads": len(threads),
            "threads": thread_details,
            "webhook_configured": True  # Assuming it is if they're asking
        }
    except Exception as e:
        print(f"Error checking inbox status: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/api/agentmail/webhook")
async def agentmail_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Webhook endpoint for Agentmail events
    Receives real-time notifications when new emails arrive
    
    This endpoint immediately returns 200 OK to acknowledge receipt,
    then processes the webhook payload in the background.
    """
    try:
        payload = await request.json()
        
        # Log payload structure for debugging
        print(f"📬 Received webhook payload keys: {list(payload.keys())}")
        
        # Validate webhook payload - check for required fields
        event_type = payload.get("event_type")
        message = payload.get("message")
        
        # Some webhooks might have message nested or different structure
        if not message:
            # Try alternative payload structures
            if "data" in payload:
                payload["message"] = payload.get("data", {})
            elif "body" in payload:
                payload["message"] = payload.get("body", {})
        
        # Require either event_type OR message (some webhooks might not have event_type)
        if not event_type and not payload.get("message"):
            # Log full payload for debugging
            print(f"⚠️ Invalid webhook payload structure: {payload}")
            raise HTTPException(status_code=400, detail="Invalid webhook payload: missing event_type or message")
        
        # Ensure event_type is set (default if missing)
        if not event_type:
            payload["event_type"] = "message.received"
        
        event_id = payload.get("event_id", "unknown")
        print(f"📬 Received Agentmail webhook event {event_id} (type: {event_type or payload.get('event_type')})")
        
        # Process webhook in background to avoid timeouts
        from backend_modules.webhook_handler import handle_agentmail_webhook
        
        def process_webhook_sync():
            """Wrapper to run async function in background task"""
            import asyncio
            try:
                # Create new event loop for background task
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(handle_agentmail_webhook(payload))
                if result.get("success"):
                    print(f"✅ Successfully processed webhook event {event_id}")
                else:
                    print(f"❌ Failed to process webhook: {result.get('error')}")
                loop.close()
            except Exception as e:
                print(f"❌ Error in background webhook processing: {e}")
                import traceback
                traceback.print_exc()
        
        # Run processing in background
        background_tasks.add_task(process_webhook_sync)
        
        # Return 200 immediately to acknowledge receipt
        return {"success": True, "message": "Webhook received and processing"}
        
    except Exception as e:
        print(f"Error processing webhook: {e}")
        import traceback
        traceback.print_exc()
        # Still return 200 to prevent Agentmail from retrying on our errors
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Esto Minimal Backend...")
    print(f"📱 Twilio Number: {TWILIO_FROM_NUMBER}")
    print(f"🐘 Database: None (minimal mode)")
    print(f"🤖 Text Model: {TEXT_MODEL}")
    print(f"👁️ Vision Model: {VISION_MODEL}")
    print("🌐 Endpoints available:")
    print("   • AI Chat: http://localhost:8000/pm_chat")
    print("   • SMS Webhook: http://localhost:8000/sms")
    print("   • Threads: http://localhost:8000/threads")
    print("   • Health: http://localhost:8000/health")
    print("   • Tenant Apps: http://localhost:8000/api/tenant-applications/...")
    print("   • Data Flow: http://localhost:8000/api/data-flow/stats")
    print("-" * 50)
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
