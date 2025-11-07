# Automated Tenant Screening & Property Showing Workflow

Build an automated tenant screening and property showing workflow integrated with your existing PropAI codebase.

## YOUR EXISTING TECH STACK (USE THESE)

**Backend:**
- FastAPI (Python) - `/Users/michael/prop_ai/minimal_backend.py`
- Google Gemini 2.0 Flash - Already integrated for AI/document processing
- Pydantic models - Follow existing patterns in `backend_modules/models.py`
- Twilio (SMS) - Already configured in `backend_modules/config.py`

**Frontend:**
- Next.js 14+ (TypeScript) - `/Users/michael/prop_ai/propai-frontend/`
- Prisma ORM with PostgreSQL
- NextAuth.js (Google OAuth + Credentials)

**Database:**
- PostgreSQL via Prisma
- Existing models: `User`, `Property`, `Lease`, `PropertyContext`

**Existing Patterns to Follow:**
- Document processing: Similar to `/propai-frontend/app/api/leases/route.ts` (PDF extraction, AI processing)
- Backend API: Extend `/Users/michael/prop_ai/minimal_backend.py` with new endpoints
- AI processing: Use existing Gemini integration like `process_lease_document()` function

**IMPORTANT: Communication Channel Separation:**
- **SMS (Twilio)**: EXISTING functionality for CURRENT tenants only (maintenance requests, tenant communication)
- **Email (Agentmail)**: NEW functionality for PROSPECTIVE tenants (applications, screening, scheduling)
  - Use Agentmail API for BOTH receiving (monitoring inbox) AND sending (automated emails to applicants)
- Do NOT mix these channels - keep SMS system unchanged, build new email system using Agentmail

---

## 1. MONITOR AGENTMAIL INBOX (RECEIVING)

**Implementation:**
- Create a background worker/periodic task (use `asyncio` or `celery` if needed)
- Use `agentmail` Python package (already installed) to connect to Agentmail API
- Poll inbox every 5-10 minutes for new emails with attachments
- Extract email metadata: sender name, email, phone number (parse from email body/signature)
- Store email thread/conversation history for each application

**Agentmail Setup:**
- Configure Agentmail inbox for receiving tenant applications
- Store Agentmail API credentials in environment variables
- Each property manager can have their own Agentmail inbox or shared inbox with filtering

**Data Extraction:**
- Download all attachments from emails
- Store attachment metadata (filename, mimeType, fileSize) - similar to `Lease` model
- Use existing file storage pattern (currently base64 in `documentService.ts`, but should migrate to S3/Cloudinary)

**Database Schema:**
```prisma
model TenantApplication {
  id              String   @id @default(cuid())
  userId          String   // Property manager who owns this application
  propertyId      String?  // Link to Property model (optional, may not know property yet)
  property        Property? @relation(fields: [propertyId], references: [id])
  
  // Contact Info (from email)
  applicantName   String
  applicantEmail  String
  applicantPhone  String?
  
  // Email Metadata
  emailSubject    String?
  emailBody       String?  // Full email text for context
  receivedAt      DateTime @default(now())
  
  // Document Attachments (store file URLs like Lease model)
  driversLicenseUrl    String?
  driversLicenseText   String?  // OCR extracted text
  payStubUrls          String[] // Array of pay stub file URLs
  payStubTexts         String[] // OCR extracted text for each
  creditScoreUrl       String?
  creditScoreText      String?  // OCR extracted text
  
  // Extracted Data (from document processing)
  licenseName          String?
  licenseDOB           DateTime?
  licenseExpiration    DateTime?
  licenseNumber        String?
  
  employerName         String?
  monthlyIncome        Float?
  annualIncome         Float?
  payFrequency         String?  // "weekly", "bi-weekly", "monthly"
  
  creditScore          Int?
  creditScoreDate      DateTime?
  
  // Screening Status
  status               String   @default("pending") // "pending", "under_review", "approved", "rejected", "scheduled"
  screeningScore       String?  // "green", "yellow", "red"
  screeningNotes       String?
  
  // Scheduling
  calendarEventId      String?  // Google Calendar event ID
  scheduledDate        DateTime?
  scheduledTime        String?
  showingConfirmed     Boolean  @default(false)
  
  // Metadata
  createdAt            DateTime @default(now())
  updatedAt            DateTime @updatedAt
  
  // Relations
  user                 User     @relation(fields: [userId], references: [id], onDelete: Cascade)
  
  @@index([userId])
  @@index([propertyId])
  @@index([status])
}
```

---

## 2. EXTRACT & VALIDATE APPLICATION DOCUMENTS

**Backend Endpoint:**
- Add to `minimal_backend.py`: `POST /api/tenant-applications/process-documents`
- Reuse existing Gemini vision model integration (same as lease processing)

**Document Processing:**
- **Driver's License**: Use Gemini 2.0 Flash vision model (already configured)
  - Extract: Full name, DOB, expiration date, license number
  - Validate: Check expiration date (flag if expired or expiring within 30 days)
  - Pattern matching: Look for state abbreviation, license format

- **Pay Stubs**: OCR + AI extraction
  - Extract: Employer name, gross income, pay period (weekly/bi-weekly/monthly)
  - Calculate: Monthly/annual income based on frequency
  - Handle multiple pay stubs (take average or most recent)
  - Follow similar pattern to `process_lease_document()` in `backend_modules/llm_service.py`

- **Credit Score Documents**: OCR + AI extraction
  - Extract: Credit score number, date pulled, credit bureau
  - Validate: Ensure score is numeric and within valid range (300-850)

**Validation Logic:**
```python
# In minimal_backend.py - similar to process_lease_document()
async def process_tenant_documents(application_id: str, document_urls: dict):
    # Use existing Gemini integration
    # Similar to how lease documents are processed
    # Return extracted data as Pydantic model
```

**Missing Document Handling:**
- If any of the 3 required documents are missing:
  - Update application status to "pending"
  - Send automated email (see section 7) requesting missing documents
  - Set reminder to check back in 24 hours

---

## 3. BACKGROUND & INCOME VERIFICATION

**Screening Criteria (Configurable):**
- Store in `Property` model or new `PropertySettings`:
  ```prisma
  model PropertySettings {
    // ... existing fields
    minCreditScore     Int      @default(600)
    incomeMultiplier   Float    @default(3.0)  // Rent must be <= income / multiplier
    minIncomeMultiplier Float   @default(2.5)  // Yellow flag threshold
  }
  ```

**Scoring System:**
```python
def calculate_screening_score(credit_score: int, monthly_income: float, monthly_rent: float, 
                              license_valid: bool, document_match: bool) -> str:
    if credit_score >= 650 and monthly_income >= (monthly_rent * 3) and license_valid and document_match:
        return "green"
    elif credit_score >= 600 and monthly_income >= (monthly_rent * 2.5) and license_valid:
        return "yellow"
    else:
        return "red"
```

**Status Updates:**
- **Green**: Auto-approve → status = "approved", send scheduling email
- **Yellow**: status = "under_review", flag for manual review within 48 hours
- **Red**: status = "rejected", send decline email

**Email Notifications (PROSPECTIVE TENANTS ONLY):**
- Use Agentmail API for sending automated emails to applicants
- Agentmail handles both inbound (monitoring) and outbound (sending) email
- Store email templates in backend (similar to system prompts)
- Keep SMS (Twilio) system separate - that's for current tenant communication only
- All applicant communication must be via Agentmail email, not SMS

**Agentmail Email Sending:**
- Use Agentmail's send email API endpoint
- Send from the same Agentmail inbox/address that receives applications
- Maintain email thread continuity (reply-to threading)
- Track email delivery status and opens (if Agentmail supports it)

---

## 4. PULL GOOGLE CALENDAR AVAILABILITY via Hyperspell

**IMPORTANT: Use Hyperspell for ALL Google Calendar Operations**
- Use Hyperspell API/SDK for ALL Google Calendar interactions
- Do NOT use Google Calendar API directly
- Hyperspell handles authentication, API calls, and calendar management

**Integration Setup:**
- Install Hyperspell Python SDK or use their REST API
- Authenticate through Hyperspell (Hyperspell handles Google Calendar OAuth internally)
- Store Hyperspell API credentials and any necessary tokens
- Each property manager connects their Google Calendar through Hyperspell

**Backend Endpoint:**
- `GET /api/calendar/availability?days=14&userId={userId}`
- Query Google Calendar availability via Hyperspell API
- Hyperspell will query the property manager's connected Google Calendar
- Filter available slots:
  - Exclude busy/blocked times (Hyperspell handles this)
  - Business hours only (9am-6pm configurable per property)
  - Minimum 1 hour buffer between showings
  - Exclude weekends (optional, configurable)

**Hyperspell API Usage:**
```python
# Example: Get calendar availability via Hyperspell
import hyperspell

# Initialize Hyperspell client
client = hyperspell.Client(api_key=HYPERSPELL_API_KEY)

# Get availability for connected Google Calendar
availability = client.calendar.get_availability(
    user_id=property_manager_id,
    days=14,
    start_time="09:00",
    end_time="18:00"
)
```

**Response Format:**
```json
{
  "available_slots": [
    {"date": "2025-01-15", "time": "10:00", "duration": 60},
    {"date": "2025-01-15", "time": "14:00", "duration": 60},
    ...
  ]
}
```

---

## 5. OFFER SCHEDULING TO QUALIFIED LEADS

**Automated Email via Agentmail:**
- Triggered when application status changes to "approved"
- Send email using Agentmail API (not SendGrid/Mailgun)
- Email template:
  ```
  Subject: Approved! Schedule Your Property Showing
  
  Hi [Applicant Name],
  
  Thank you for your application! We're pleased to approve you to schedule a property showing.
  
  Here are available times I can show you the property:
  
  [LIST OF AVAILABLE SLOTS FROM GOOGLE CALENDAR via Hyperspell]
  
  Please reply to this email with your preferred date and time:
  "I'd like to schedule for [DATE] at [TIME]"
  
  Best regards,
  [Your Name]
  ```
- Use Agentmail's reply-to threading so responses come back to monitored inbox

**Email Parsing:**
- Monitor Agentmail inbox for tenant replies (same inbox that receives applications)
- Use Gemini to parse natural language responses (e.g., "Tuesday at 2pm", "January 15th at 3:00")
- Extract date/time and match to available slot
- If slot is still available, proceed to calendar creation
- Update application's email thread history

---

## 6. CREATE CALENDAR EVENT & CONFIRMATIONS

**Calendar Event Creation via Hyperspell:**
- Use Hyperspell API to create Google Calendar event (NOT direct Google Calendar API)
- Hyperspell handles creating the event in the property manager's connected Google Calendar
- Event details:
  ```python
  # Create calendar event via Hyperspell
  import hyperspell
  
  client = hyperspell.Client(api_key=HYPERSPELL_API_KEY)
  
  event = client.calendar.create_event(
      user_id=property_manager_id,
      summary=f"{applicant_name} - Property Showing",
      description=f"""
      Tenant: {applicant_name}
      Email: {applicant_email}
      Phone: {applicant_phone}
      Income: ${monthly_income:,.2f}/month
      Credit Score: {credit_score}
      Property: {property_address}
      Unit: {property_unit}
      
      Parking: [CONFIGURABLE PER PROPERTY]
      """,
      start_time=scheduled_datetime.isoformat(),
      end_time=(scheduled_datetime + timedelta(hours=1)).isoformat(),
      location=property_address
  )
  
  # Hyperspell returns event ID
  calendar_event_id = event.id
  ```

**Store Event ID:**
- Save Google Calendar event ID (from Hyperspell response) to `TenantApplication.calendarEventId`
- Use Hyperspell API for updating/canceling events if tenant reschedules
- Hyperspell handles all Google Calendar event modifications

**Confirmation Emails via Agentmail:**
- **To Applicant (Agentmail Email)**: 
  - Send confirmation using Agentmail API
  - Include: date/time, address, parking instructions
  - What to bring (ID, proof of income if needed)
  - Contact info for reschedules
  - Maintain email thread for continuity

- **To Property Manager**: 
  - Send notification via Agentmail to property manager's email (or use Agentmail API to send to property manager)
  - Include applicant summary, showing time, property address
  - (Note: Do NOT use SMS/Twilio for this - SMS is only for current tenant communication)

---

## 7. REJECTION & FOLLOW-UP

**Rejection Email via Agentmail:**
```python
# Automated professional decline using Agentmail API
if screening_score == "red":
    send_email_via_agentmail(
        to=applicant_email,
        subject="Application Update - [Property Name]",
        body="""
        Thank you for your interest in [Property Name].
        
        After reviewing your application, we are unable to move forward at this time.
        
        We encourage you to apply again in the future.
        """
    )
    # Use Agentmail API to send email, not SendGrid/Mailgun
```

**Follow-up Automation:**
- **Under Review**: Set cron job to check applications with status "under_review" older than 48 hours
- **No Response to Scheduling**: If tenant doesn't reply within 24 hours, send gentle reminder
- **Reminders**: Use existing backend scheduling or add `celery` for delayed tasks

---

## 8. DATABASE INTEGRATION

**Prisma Migration:**
- Add `TenantApplication` model to `propai-frontend/prisma/schema.prisma`
- Add optional relation to `Property` model
- Run migration: `npx prisma migrate dev --name add_tenant_applications`

**Backend Models:**
- Create Pydantic models in `backend_modules/models.py`:
  ```python
  class TenantApplication(BaseModel):
      id: str
      userId: str
      propertyId: Optional[str]
      applicantName: str
      applicantEmail: str
      applicantPhone: Optional[str]
      status: str
      screeningScore: Optional[str]
      # ... etc
  ```

---

## 9. FRONTEND UI - APPLICATIONS SECTION

**Navigation Integration:**
- Add "Applications" link to main navigation (similar to "Properties", "Messages", "Maintenance")
- Route: `/app/applications` - main applications dashboard
- Show badge/count of pending applications in nav if > 0

**Main Applications Page: `/app/applications/page.tsx`**
- List view of all tenant applications for the logged-in property manager
- Filterable by status: "All", "Pending", "Under Review", "Approved", "Scheduled", "Rejected"
- Sortable by: Date received, Status, Applicant name
- Search by applicant name or email
- Cards display:
  - Applicant name and email
  - Status badge (color-coded: green/yellow/red)
  - Property (if linked) or "Unknown Property"
  - Date received
  - Quick view of key metrics (credit score, income, screening score)

**Application Cards (`TenantApplicationCard.tsx`):**
```
┌─────────────────────────────────────────────┐
│ [Status Badge] Applicant Name                │
│ applicant@email.com                          │
│ Property: 123 Main St, Unit 4B              │
│                                              │
│ 📊 Credit: 720  💰 Income: $5,200/mo       │
│ 📅 Received: Jan 10, 2025                   │
│                                              │
│ [View Details] [Approve] [Reject]           │
└─────────────────────────────────────────────┘
```

**Application Detail Page: `/app/applications/[id]/page.tsx`**
Display comprehensive application details:

**Header Section:**
- Applicant name (large, prominent)
- Status badge with color (green/yellow/red)
- Quick actions: Approve, Reject, Request More Info, Schedule Showing

**Contact Information:**
- Email: applicant@example.com
- Phone: (555) 123-4567
- Property Applied For: [Property Name] (if linked)

**Extracted Context (from Documents):**
- **Driver's License:**
  - Full Name: John Doe
  - Date of Birth: 01/15/1990
  - License Number: D12345678
  - Expiration: 01/15/2028
  - Status: Valid / Expiring Soon / Expired

- **Credit Score:**
  - Score: 720
  - Date Pulled: 01/08/2025
  - Bureau: Experian / Equifax / TransUnion

- **Income Information:**
  - Employer: ABC Company
  - Monthly Income: $5,200
  - Annual Income: $62,400
  - Pay Frequency: Bi-weekly
  - Income vs Rent Ratio: 3.2x (if property rent is known)

**Screening Results:**
- Screening Score: Green / Yellow / Red
- Automated Notes: "Credit score above threshold, income sufficient..."
- Manual Notes: (Editable textarea for property manager)

**Scheduled Showing (if approved and scheduled):**
- **Date:** January 20, 2025
- **Time:** 2:00 PM - 3:00 PM
- **Status:** Confirmed / Pending Confirmation
    - **Calendar Event:** [View in Google Calendar] (link via Hyperspell)
- **Property Address:** 123 Main St, Unit 4B
- **Parking Instructions:** [From Property settings]

**Document Viewer:**
- Tabs or sections for:
  - Driver's License (preview image + extracted text)
  - Pay Stubs (all uploaded stubs, preview + extracted data)
  - Credit Score Document (preview + extracted data)
- Download buttons for all documents
- OCR confidence indicator if available

**Email Thread:**
- Show original application email
- Show all sent/received emails in thread
- Timestamp each message
- Ability to send follow-up email from UI

**Timeline/Activity Log:**
- "Application received: Jan 10, 2025"
- "Documents processed: Jan 10, 2025"
- "Status changed to Approved: Jan 11, 2025"
- "Scheduling email sent: Jan 11, 2025"
- "Showing scheduled: Jan 12, 2025"
- etc.

**Components to Build:**
1. `TenantApplicationCard.tsx` - Card component for list view
2. `ApplicationDetail.tsx` - Full detail view component
3. `ScreeningStatusBadge.tsx` - Visual status indicator (green/yellow/red)
4. `DocumentViewer.tsx` - Display uploaded documents with preview
5. `ApplicantContext.tsx` - Display extracted DL, credit, income info
6. `ScheduledShowing.tsx` - Display showing details if scheduled
7. `EmailThread.tsx` - Display email conversation history
8. `ApplicationTimeline.tsx` - Activity log component
9. `ApplicationFilters.tsx` - Filter/search component

**API Routes:**
- `/app/api/applications/route.ts` - GET (list), POST (create manually)
- `/app/api/applications/[id]/route.ts` - GET (detail), PATCH (update), DELETE
- `/app/api/applications/[id]/process/route.ts` - POST (trigger document processing)
- `/app/api/applications/[id]/approve/route.ts` - POST (approve and send scheduling email)
- `/app/api/applications/[id]/reject/route.ts` - POST (reject and send decline email)
- `/app/api/applications/[id]/schedule/route.ts` - POST (manually schedule showing)
- `/app/api/calendar/availability/route.ts` - GET (get available slots)

---

## 10. ERROR HANDling & Monitoring

**Error Scenarios:**
1. **Document extraction fails**: 
   - Flag application for manual review
   - Log error with application ID
   - Send notification to property manager

2. **Hyperspell/Google Calendar connection fails**:
   - Alert property manager via email (NOT SMS - SMS is for current tenants only)
   - Fall back to manual scheduling option in UI
   - Retry Hyperspell API connection every 5 minutes
   - Check Hyperspell API status and Google Calendar connection through Hyperspell

3. **Agentmail inbox monitoring fails**:
   - Log error and retry with exponential backoff
   - Alert if offline for >30 minutes

4. **Tenant doesn't respond**:
   - Auto-reminder after 24 hours
   - Second reminder after 48 hours
   - Archive application after 7 days of no response

**Logging:**
- Use existing Python logging patterns
- Store errors in database or log file
- Include application ID, error type, timestamp

---

## 11. ENVIRONMENT VARIABLES

Add to `.env` files:
```bash
# Agentmail (for both receiving and sending emails)
AGENTMAIL_API_KEY=your_agentmail_api_key
AGENTMAIL_INBOX_ID=your_inbox_id
AGENTMAIL_API_URL=https://api.agentmail.com  # or whatever Agentmail API endpoint is

# Hyperspell (handles all Google Calendar operations)
HYPERSPELL_API_KEY=your_hyperspell_key
HYPERSPELL_API_URL=https://api.hyperspell.com  # or whatever Hyperspell API endpoint is
# Note: Hyperspell handles Google Calendar OAuth internally, so you may not need direct Google Calendar credentials

# OCR Service (if not using Gemini Vision)
TESSERACT_PATH=/usr/local/bin/tesseract  # Optional, for local OCR
```

**Note:** All email sending/receiving uses Agentmail - no SendGrid/Mailgun needed.

---

## 12. IMPLEMENTATION ORDER

1. **Database Schema**: Add `TenantApplication` model to Prisma
2. **Agentmail Integration**: Set up inbox monitoring (receiving) AND email sending service
3. **Document Processing**: Extend Gemini integration for tenant documents
4. **Screening Logic**: Build scoring system and validation
5. **Calendar Integration**: Set up Hyperspell API integration for Google Calendar
   - Connect property manager's Google Calendar through Hyperspell
   - Use Hyperspell for ALL calendar operations (availability, creating events, updates)
6. **Email System**: Configure Agentmail API for automated email sending (already handling receiving)
7. **Frontend UI**: Build application management dashboard
8. **Automation**: Connect all pieces with background workers

---

## NOTES

- **Reuse Existing Code**: Follow patterns from `process_lease_document()`, SMS workflows, and property management
- **Extend Don't Replace**: Add new endpoints to `minimal_backend.py`, don't rewrite existing functionality
- **Database Consistency**: Use Prisma migrations, follow existing schema patterns
- **Error Handling**: Use existing FastAPI error handling patterns
- **AI Processing**: Leverage existing Gemini 2.0 Flash integration for all document/text processing
- **Email via Agentmail**: Use Agentmail API for ALL email operations (receiving applications + sending responses/confirmations) - no SendGrid/Mailgun needed
- **Calendar via Hyperspell**: Use Hyperspell API for ALL Google Calendar operations (availability, creating events, updates) - do NOT use Google Calendar API directly

