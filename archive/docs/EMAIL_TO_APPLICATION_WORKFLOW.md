# Email to Application Workflow

## How It Works

When a prospective tenant sends an email to your Agentmail inbox with attachments, the system automatically:

1. **Receives Email** → Agentmail inbox receives the email
2. **Monitors Inbox** → Backend checks inbox every 5-10 minutes (or via webhook)
3. **Extracts Data** → Parses contact info (name, email, phone) from email body
4. **Downloads Attachments** → Downloads and categorizes:
   - Driver's license
   - Pay stubs
   - Credit score reports
5. **Processes Documents** → Uses Gemini AI to extract:
   - License: name, DOB, expiration, number
   - Income: employer, monthly/annual income, pay frequency
   - Credit: score, date pulled
6. **Calculates Screening Score** → Determines:
   - Green (approved)
   - Yellow (under review)
   - Red (rejected)
7. **Saves to Database** → Creates `TenantApplication` record in PostgreSQL
8. **Appears in UI** → Shows up on `/applications` page immediately
9. **Sends Response Email**:
   - **Approved** → Sends scheduling email with available times
   - **Rejected** → Sends professional decline email
   - **Missing Docs** → Requests missing documents

## Setup Required

### 1. Environment Variables

**Backend (Render):**
```env
# Agentmail
AGENTMAIL_API_KEY=your_agentmail_api_key
AGENTMAIL_INBOX_ID=your_inbox_id
AGENTMAIL_API_URL=https://api.agentmail.com

# Frontend URL for saving applications
FRONTEND_ORIGIN=https://ten8link.vercel.app

# Service token for internal API calls
APPLICATION_SERVICE_TOKEN=your-secret-service-token

# Default user ID (for applications)
DEFAULT_USER_ID=your-user-id
```

**Frontend (Vercel):**
```env
# Service token (must match backend)
APPLICATION_SERVICE_TOKEN=your-secret-service-token

# Database (already set)
DATABASE_URL=your_postgres_url
```

### 2. Agentmail Configuration

1. **Set up Agentmail inbox**:
   - Create inbox in Agentmail dashboard
   - Get `AGENTMAIL_API_KEY` and `AGENTMAIL_INBOX_ID`
   - Configure inbox to receive tenant applications

2. **Configure webhook (optional but recommended)**:
   - Point Agentmail webhook to: `https://your-backend.onrender.com/api/agentmail/webhook`
   - This triggers immediate processing instead of polling

### 3. Periodic Inbox Checking

**Option A: Webhook (Recommended)**
- Configure Agentmail webhook → Instant processing
- No additional setup needed

**Option B: Scheduled Task**
- Set up cron job or scheduled task to call:
  ```
  POST https://your-backend.onrender.com/api/agentmail/check-inbox
  ```
- Run every 5-10 minutes

**Option C: Render Cron Job**
```yaml
# Add to render.yaml
services:
  - type: cron
    name: check-agentmail-inbox
    schedule: "*/10 * * * *"  # Every 10 minutes
    command: curl -X POST https://your-backend.onrender.com/api/agentmail/check-inbox
```

## Testing the Workflow

### 1. Send Test Email

Send an email to your Agentmail inbox:
- **To**: Your Agentmail inbox email
- **Subject**: "Application for Property"
- **Body**: 
  ```
  Hi, I'm John Doe (john.doe@email.com, phone: +1234567890).
  I'm interested in applying for your property.
  Please find my documents attached.
  ```
- **Attachments**:
  - Driver's license (image or PDF)
  - Pay stub (image or PDF)
  - Credit score report (image or PDF)

### 2. Trigger Processing

**Option A: Webhook** (if configured)
- Email is automatically processed when received

**Option B: Manual trigger**
```bash
curl -X POST https://your-backend.onrender.com/api/agentmail/check-inbox
```

### 3. Verify in UI

1. Go to: `https://ten8link.vercel.app/applications`
2. Login as property manager
3. You should see the new application
4. Click "View Email Thread" to see the original email

## What Gets Extracted

From the email:
- ✅ Applicant name (parsed from body or email address)
- ✅ Email address
- ✅ Phone number (if mentioned)
- ✅ Email subject
- ✅ Full email body (stored for thread view)

From documents (via AI):
- ✅ Driver's license: name, DOB, expiration, license number
- ✅ Pay stubs: employer, monthly/annual income, pay frequency
- ✅ Credit score: score value, date pulled

## Email Thread Display

The Applications page shows:
- Original email subject
- Full email body
- Expandable/collapsible view
- Preserves formatting

## Current Status

✅ **Implemented:**
- Email inbox monitoring
- Document processing
- Data extraction
- Screening score calculation
- Database save via internal API
- Email thread display in UI

⚠️ **To Complete:**
- Set `APPLICATION_SERVICE_TOKEN` in both backend and frontend
- Set `DEFAULT_USER_ID` in backend (or determine user ID from email)
- Configure Agentmail webhook OR set up periodic checking
- Test with real email

## Troubleshooting

**Applications not appearing:**
1. Check backend logs for errors
2. Verify `APPLICATION_SERVICE_TOKEN` matches in both places
3. Verify `FRONTEND_ORIGIN` is correct in backend
4. Check if email was processed (backend logs)
5. Verify user ID is correct

**Email not processing:**
1. Check Agentmail credentials
2. Verify inbox ID is correct
3. Check webhook URL if using webhooks
4. Review backend logs for errors

**Documents not extracting:**
1. Verify Gemini API key is set
2. Check document URLs are accessible
3. Review extraction logs in backend

