# Demo Workflow Steps

## How Your Demo Will Work

### 1. Send Real Email via Agentmail
Send an email to your Agentmail inbox with:
- Subject: "Tenant Application"
- Body: Include name, phone, property interest
- Attachments:
  - Driver's license
  - Pay stubs
  - Credit report

### 2. System Processes Email
```
📧 Email arrives → Agentmail inbox
    ↓
🤖 Backend detects new email (monitor_inbox or webhook)
    ↓
📄 Extracts data from documents (Gemini AI)
    ↓
📊 Calculates screening score
    ↓
💾 Indexes in Hyperspell (searchable memory)
```

### 3. Agent Queries Hyperspell
```
🤖 Intelligent Agent:
    ↓
    Queries Hyperspell: "Rank all applicants by credit score and income ratio"
    ↓
    Compares new applicant against 15 mock applications
    ↓
    Determines if applicant is in top 3
```

### 4. If Top-Ranked, Auto-Schedules
```
🎯 If ranked in top 3:
    ↓
    Gets calendar availability from Hyperspell
    ↓
    Picks first available slot
    ↓
    Creates Google Calendar event via Hyperspell
    ↓
    Updates application status to "scheduled"
    ↓
    Sends confirmation email via Agentmail
```

### 5. If Not Top-Ranked
```
📧 Sends scheduling email with available slots
    ↓
    Waits for tenant to reply
    ↓
    Parses reply and schedules manually
```

## Environment Variables Needed

```bash
# Enable agent
USE_TENANT_AGENT=true

# Auto-schedule top applicants (default: true)
AUTO_SCHEDULE_TOP_APPLICANTS=true  # Will auto-schedule if top 3

# Agentmail
AGENTMAIL_API_KEY=your_key
AGENTMAIL_INBOX_ID=your_inbox_id

# Hyperspell
HYPERSPELL_API_KEY=your_key
HYPERSPELL_API_URL=https://api.hyperspell.com

# Gemini
LLM_API_KEY=your_gemini_key

# Frontend
APPLICATION_SERVICE_TOKEN=your_token
FRONTEND_ORIGIN=https://ten8link.vercel.app
DEFAULT_USER_ID=your_user_id
```

## What You'll See

1. **Email arrives** → Console: "📧 Found 1 new thread"
2. **Processing** → Console: "📄 Processing documents..."
3. **Indexed** → Console: "✅ Indexed application in Hyperspell"
4. **Agent queries** → Console: "🤖 Agent decision: approve"
5. **Hyperspell ranking** → Console: "🎯 Agent identified as top-ranked applicant"
6. **Auto-scheduled** → Console: "✅ Auto-scheduled application"
7. **Calendar created** → Console: "📅 Google Calendar event created"
8. **Email sent** → Console: "📧 Sent confirmation email"

## Application Status Flow

- `pending` → Email received
- `under_review` → Documents processing
- `approved` → Agent approved, ranking checked
- `awaiting_tenant` → Scheduling email sent (if not auto-scheduled)
- `scheduled` → ✅ Google Calendar event created (AUTO if top-ranked)

## Notes

- The system will automatically identify your real application vs the 15 mock ones
- If your application is ranked in top 3 by Hyperspell, it auto-schedules
- Google Calendar event is created via Hyperspell API
- Confirmation email sent via Agentmail

