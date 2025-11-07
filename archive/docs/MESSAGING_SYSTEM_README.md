# PropAI Messaging System

A comprehensive messaging system with two distinct AI-powered communication channels using Groq Llama 4.

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │  Unified Backend │    │   Twilio SMS    │
│   (Next.js)     │◄──►│   (FastAPI)      │◄──►│   Webhooks      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   Groq Llama 4   │
                       │   (Two Models)   │
                       └──────────────────┘
```

## Two Distinct AI Systems

### 1. Tenant SMS Processing 🤖📱

**Purpose**: Process incoming SMS messages from tenants with maintenance ticket creation

**Features**:
- **Prompt Engineering**: Optimized for tenant communication with empathy and solution-oriented responses
- **Maintenance Detection**: Automatically identifies maintenance-related messages using keyword analysis
- **Ticket Creation**: Creates maintenance tickets with priority classification (low, normal, high, critical)
- **Multimodal Support**: Processes images and media when necessary (limited to conserve API calls)
- **Troubleshooting**: Provides helpful troubleshooting steps for common issues

**API Endpoint**: `POST /tenant_sms`

**Example Request**:
```json
{
  "message": "My toilet is overflowing and water is leaking everywhere!",
  "context": {
    "tenant_name": "John Doe",
    "unit": "3A",
    "address": "123 Main St, Apartment 3A",
    "property_name": "Sunset Apartments",
    "tenant_phone": "+1234567890"
  },
  "phone": "+1234567890",
  "media_urls": ["data:image/jpeg;base64,..."]
}
```

**Example Response**:
```json
{
  "reply": "I understand this is urgent! First, try turning off the water supply valve behind the toilet. If that doesn't work, turn off the main water supply. I've created a maintenance ticket for this issue.\n\n🎫 Maintenance ticket #MT12345678 has been created for this issue.",
  "maintenance_ticket_created": true,
  "ticket_id": "MT12345678"
}
```

### 2. Frontend AI Assistant 🤖💼

**Purpose**: AI assistant and secretary for property managers with comprehensive property context

**Features**:
- **Prompt Engineering**: Acts as a professional assistant/secretary for property managers
- **Comprehensive Context**: Provides all available property and tenant information
- **Maintenance Tracking**: References existing maintenance tickets and provides status updates
- **Multimodal Support**: Processes images and documents when necessary
- **Professional Responses**: Detailed, formatted responses for property management tasks

**API Endpoint**: `POST /pm_chat`

**Example Request**:
```json
{
  "message": "Can you give me a summary of this property and any maintenance issues?",
  "context": {
    "tenant_name": "John Doe",
    "unit": "3A",
    "address": "123 Main St, Apartment 3A",
    "property_name": "Sunset Apartments",
    "tenant_phone": "+1234567890",
    "hotline": "+1-555-MAINT",
    "portal_url": "https://tenant-portal.example.com"
  },
  "phone": "+1234567890",
  "image_url": "data:image/jpeg;base64,..."
}
```

**Example Response**:
```
Property Summary for Sunset Apartments - Unit 3A

Tenant Information:
- Name: John Doe
- Phone: +1234567890
- Hotline: +1-555-MAINT
- Portal: https://tenant-portal.example.com

Maintenance Tickets for this tenant:
- #MT12345678 (CRITICAL) - My toilet is overflowing and water is leaking everywhere! - Status: open
- #MT12345679 (HIGH) - Kitchen faucet not working properly - Status: in_progress

Recent Activity:
- 3 SMS messages in the last 24 hours
- 2 open maintenance tickets requiring attention

Recommendations:
1. Address the critical toilet issue immediately
2. Follow up on the kitchen faucet repair
3. Consider scheduling a property inspection
```

## Maintenance Ticket System

### Automatic Ticket Creation

Tickets are automatically created when tenant messages contain maintenance-related keywords:

**Critical Priority Keywords**:
- fire, flood, gas leak, electrical, emergency, urgent, overflowing, leaking water

**High Priority Keywords**:
- broken, not working, damaged, repair, fix

**Common Maintenance Keywords**:
- toilet, sink, faucet, heating, cooling, electrical, plumbing, appliance, door, window, lock, key

### Ticket Structure

```json
{
  "id": "MT12345678",
  "tenant_phone": "+1234567890",
  "tenant_name": "John Doe",
  "unit": "3A",
  "property_name": "Sunset Apartments",
  "issue_description": "Toilet overflowing with water leaking",
  "priority": "critical",
  "status": "open",
  "created_at": "2024-01-15T10:30:00Z",
  "media_urls": ["data:image/jpeg;base64,..."]
}
```

## Multimodal Support

Both systems support multimodal processing when necessary:

- **Images**: Processed when tenants send photos of issues
- **Documents**: Handled for property managers reviewing documents
- **Efficient Usage**: Only uses vision model when media is present to conserve API calls

## API Endpoints

### Core Messaging
- `POST /tenant_sms` - Process tenant SMS with maintenance ticket creation
- `POST /pm_chat` - Frontend AI assistant for property managers
- `POST /sms` - Twilio webhook for incoming SMS

### Maintenance Tickets
- `GET /maintenance_tickets` - Get all maintenance tickets
- `GET /maintenance_tickets/{ticket_id}` - Get specific ticket
- `GET /property_context/{phone}` - Get comprehensive property context

### Property Management
- `GET /properties/{property_id}/settings` - Get property settings
- `POST /properties/{property_id}/settings` - Update property settings
- `POST /contacts/upsert` - Register/update contact information

## Frontend Integration

### New Components

1. **MaintenanceTickets.tsx**: Displays all maintenance tickets with filtering and status management
2. **Enhanced PropertyDetail.tsx**: Added maintenance tickets tab
3. **Updated AIChat.tsx**: Now uses the enhanced PM chat with comprehensive context

### API Functions

```typescript
// New API functions in lib/api.ts
export async function getMaintenanceTickets(): Promise<{ tickets: any[] }>
export async function getMaintenanceTicket(ticketId: string): Promise<any>
export async function getPropertyContext(phone: string): Promise<PropertyContext>
export async function processTenantSms(message: string, context: Context, phone: string, mediaUrls?: string[]): Promise<TenantSmsResponse>
```

## Environment Configuration

```env
# Groq Configuration
LLM_API_KEY=your_groq_api_key
LLM_MODEL=llama-3.1-8b-instant
LLM_VISION_MODEL=meta-llama/llama-4-maverick-17b-128e-instruct
LLM_URL=https://api.groq.com/openai/v1/chat/completions

# Twilio Configuration
TWILIO_FROM_NUMBER=+1234567890
USE_FAKE_TWILIO=0

# Frontend Configuration
NEXT_PUBLIC_BACKEND_URL=https://prop-ai.onrender.com
```

## Testing

Run the test script to verify both messaging systems:

```bash
python test_messaging_system.py
```

This will test:
- Tenant SMS processing with maintenance ticket creation
- Property manager AI assistant
- Maintenance ticket retrieval
- Property context retrieval

## Deployment

The system is designed to work with your existing deployment setup:
- **Backend**: Deployed on Render [[memory:8250268]]
- **Frontend**: Deployed on Vercel [[memory:8250268]]

## Key Benefits

1. **Dual AI Systems**: Separate, optimized prompts for tenants vs property managers
2. **Automatic Maintenance Tracking**: No manual ticket creation needed
3. **Comprehensive Context**: Property managers get full property and tenant information
4. **Efficient API Usage**: Multimodal support only when necessary
5. **Professional Communication**: Appropriate tone and detail level for each audience
6. **Scalable Architecture**: Easy to extend with additional features

## Future Enhancements

- Ticket status updates and workflow management
- Integration with external maintenance services
- Advanced analytics and reporting
- Automated scheduling and notifications
- Multi-property management support
