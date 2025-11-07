# Tenant Screening Implementation Status

This document tracks the implementation progress of the automated tenant screening and property showing workflow as specified in `TENANT_SCREENING_PROMPT.md`.

## ✅ Completed

### 1. Database Schema (Foundation)
- ✅ Added `TenantApplication` model to Prisma schema with all required fields:
  - Contact information (name, email, phone)
  - Email metadata (subject, body, receivedAt)
  - Document URLs (driver's license, pay stubs, credit score)
  - Extracted data fields (license info, income, credit score)
  - Screening status and scores
  - Scheduling information (calendar event ID, scheduled date/time)
  - Proper indexes and relations

- ✅ Added `PropertySettings` model for screening criteria:
  - `minCreditScore` (default: 600)
  - `incomeMultiplier` (default: 3.0)
  - `minIncomeMultiplier` (default: 2.5) 
  - Business hours configuration
  - Parking instructions

- ✅ Updated `User` and `Property` models with proper relations

**Next Step:** Run Prisma migration when `DATABASE_URL` is configured:
```bash
cd propai-frontend
npx prisma migrate dev --name add_tenant_applications
```

### 2. Backend Models (Pydantic)
- ✅ Added `TenantApplication` Pydantic model
- ✅ Added `PropertyScreeningSettings` Pydantic model
- ✅ Added `ProcessDocumentsRequest` model
- ✅ Added `DocumentExtractionResult` model
- ✅ Added `ScreeningScoreRequest` and `ScreeningScoreResponse` models

### 3. Document Processing (AI/LLM)
- ✅ Fixed bug in `call_gemini` function (payload definition)
- ✅ Added `process_tenant_documents()` function in `llm_service.py`
- ✅ Implemented `_extract_drivers_license()` for driver's license processing
- ✅ Implemented `_extract_pay_stubs()` for pay stub processing (supports multiple)
- ✅ Implemented `_extract_credit_score()` for credit score document processing
- ✅ All use Gemini 2.0 Flash Vision model (already configured)
- ✅ Proper error handling and extraction error tracking

## 🚧 In Progress / Next Steps

### 4. Backend API Endpoints (FastAPI)
**Priority: HIGH**

Need to add to `minimal_backend.py`:

1. `POST /api/tenant-applications/process-documents`
   - Accept document URLs
   - Call `process_tenant_documents()` from `llm_service.py`
   - Update application in database with extracted data

2. `POST /api/tenant-applications/{id}/calculate-score`
   - Calculate screening score (green/yellow/red)
   - Implement scoring logic from spec:
     - Green: credit >= 650, income >= rent * 3, valid license
     - Yellow: credit >= 600, income >= rent * 2.5, valid license
     - Red: otherwise
   - Auto-approve if green, set to under_review if yellow, reject if red

3. `GET /api/calendar/availability?days=14&userId={userId}`
   - Integrate with Hyperspell API
   - Return available time slots

4. `POST /api/tenant-applications/{id}/schedule`
   - Create calendar event via Hyperspell
   - Send confirmation emails via Agentmail

### 5. Agentmail Integration
**Priority: HIGH**

- ⏳ Install/configure `agentmail` Python package (check if already installed)
- ⏳ Create background worker for inbox monitoring (poll every 5-10 minutes)
- ⏳ Implement email sending service for:
  - Application approval emails with scheduling options
  - Rejection emails
  - Confirmation emails after scheduling
  - Reminder emails (24h, 48h follow-ups)

**Implementation Approach:**
- Use `asyncio` background task or `celery` if needed
- Add to `minimal_backend.py` startup or separate worker process

### 6. Hyperspell Integration
**Priority: MEDIUM**

- ⏳ Install Hyperspell Python SDK or use REST API
- ⏳ Set up authentication/API key configuration
- ⏳ Implement:
  - Calendar availability querying
  - Calendar event creation
  - Calendar event updates/cancellations

### 7. Frontend API Routes (Next.js)
**Priority: HIGH**

Need to create in `propai-frontend/app/api/applications/`:

- ⏳ `route.ts` - GET (list), POST (create manually)
- ⏳ `[id]/route.ts` - GET (detail), PATCH (update), DELETE
- ⏳ `[id]/process/route.ts` - POST (trigger document processing)
- ⏳ `[id]/approve/route.ts` - POST (approve and send scheduling email)
- ⏳ `[id]/reject/route.ts` - POST (reject and send decline email)
- ⏳ `[id]/schedule/route.ts` - POST (manually schedule showing)
- ⏳ `calendar/availability/route.ts` - GET (get available slots)

### 8. Frontend UI Components
**Priority: MEDIUM**

Need to create in `propai-frontend/components/`:

- ⏳ `TenantApplicationCard.tsx` - Card component for list view
- ⏳ `ApplicationDetail.tsx` - Full detail view component
- ⏳ `ScreeningStatusBadge.tsx` - Visual status indicator (green/yellow/red)
- ⏳ `DocumentViewer.tsx` - Display uploaded documents with preview
- ⏳ `ApplicantContext.tsx` - Display extracted DL, credit, income info
- ⏳ `ScheduledShowing.tsx` - Display showing details if scheduled
- ⏳ `EmailThread.tsx` - Display email conversation history
- ⏳ `ApplicationTimeline.tsx` - Activity log component
- ⏳ `ApplicationFilters.tsx` - Filter/search component

### 9. Frontend Pages
**Priority: MEDIUM**

- ⏳ `/app/applications/page.tsx` - Main applications dashboard
  - List view with filters
  - Search functionality
  - Status badges
  - Sortable columns

- ⏳ `/app/applications/[id]/page.tsx` - Application detail page
  - All sections from spec (contact info, extracted context, screening results, etc.)

### 10. Navigation Integration
**Priority: LOW**

- ⏳ Add "Applications" link to main navigation
- ⏳ Show badge/count of pending applications if > 0

## 📋 Environment Variables Needed

Add these to `.env` files (backend and frontend):

```bash
# Agentmail (for both receiving and sending emails)
AGENTMAIL_API_KEY=your_agentmail_api_key
AGENTMAIL_INBOX_ID=your_inbox_id
AGENTMAIL_API_URL=https://api.agentmail.com  # or whatever Agentmail API endpoint is

# Hyperspell (handles all Google Calendar operations)
HYPERSPELL_API_KEY=your_hyperspell_key
HYPERSPELL_API_URL=https://api.hyperspell.com  # or whatever Hyperspell API endpoint is
```

## 🔧 Implementation Notes

### Current Architecture
- **Backend**: FastAPI (Python) in `minimal_backend.py`
- **Frontend**: Next.js 14+ (TypeScript) in `propai-frontend/`
- **Database**: PostgreSQL via Prisma (when DATABASE_URL configured)
- **AI**: Gemini 2.0 Flash (already integrated)

### Key Design Decisions
1. **Communication Channels**: 
   - SMS (Twilio) = CURRENT tenants only (maintenance, communication)
   - Email (Agentmail) = PROSPECTIVE tenants only (applications, screening, scheduling)
   - These must remain separate!

2. **Calendar Integration**: 
   - Use Hyperspell for ALL Google Calendar operations
   - Do NOT use Google Calendar API directly
   - Hyperspell handles OAuth internally

3. **Document Processing**:
   - Reuse existing Gemini Vision model integration
   - Follow pattern from `process_lease_document()`
   - All extraction uses function calling for structured output

### Testing Strategy
1. Test document extraction with sample documents
2. Test scoring logic with various scenarios
3. Test email sending/receiving via Agentmail
4. Test calendar integration via Hyperspell
5. Test end-to-end flow: email → extraction → scoring → scheduling

## 📚 Reference

- Full specification: `TENANT_SCREENING_PROMPT.md`
- Existing lease processing pattern: `propai-frontend/app/api/leases/route.ts`
- Existing LLM service: `backend_modules/llm_service.py`
- Existing backend: `minimal_backend.py`

---

**Last Updated:** Initial implementation foundation completed
**Next Priority:** Backend API endpoints and Agentmail integration

