# Complete Demo Flow: Agentmail → Hyperspell → Google Calendar

## Overview
Your demo will show a real email application being processed, ranked by Hyperspell against 15 mock applications, and automatically scheduled if it's top-ranked.

---

## Step-by-Step Demo Flow

### 1. 📧 **You Send Email via Agentmail**
```
Send email to: your-agentmail-inbox@...
Subject: "Tenant Application"
Attachments:
  - Driver's license (image/PDF)
  - Pay stubs (image/PDF)  
  - Credit report (image/PDF)
Body: Include name, phone, property interest
```

### 2. 🔍 **System Detects & Processes**
```
Console Output:
📬 NEW APPLICATION FROM AGENTMAIL
   Thread ID: thread_abc123
   Message ID: msg_xyz789
   From: applicant@example.com
   Applicant: John Doe

📄 Processing documents for message msg_xyz789
✅ Extracted: Credit 720, Income $6000/month
📊 Screening Score: green
```

### 3. 🤖 **Agent Makes Decision**
```
Console Output:
🤖 Agent decision: approve - Applicant has excellent credit score of 720 and 
   strong income ratio of 3.0x rent. Compared to other applicants...
```

### 4. 💾 **Indexed in Hyperspell**
```
Console Output:
✅ Indexed application app_123 in Hyperspell for querying
```

### 5. 🔍 **Hyperspell Query (RANKING)**
```
Console Output:
🔍 QUERYING HYPERSPELL to rank this applicant...

📊 Hyperspell Ranking Result:
   Based on credit score (720) and income ratio (3.0x), John Doe ranks 
   #2 among all 16 applicants. This is an excellent candidate in the 
   top 15% of all applications received...
```

### 6. 🎯 **Top 3 Check & Auto-Schedule**
```
Console Output:
🎯 DEMO HIGHLIGHT: John Doe ranked in TOP 3 by Hyperspell!
   ✅ Auto-scheduling property showing...

📅 Getting calendar availability from Hyperspell...
✅ Found available slots

✅ DEMO SUCCESS!
   📅 Scheduled: 2024-11-05 at 14:00
   📅 Google Calendar Event ID: event_abc123xyz
   ✅ Application status: scheduled

📧 Sent confirmation email to applicant@example.com
```

### 7. ✅ **Complete**
- ✅ Application appears on `/applications` page with status "scheduled"
- ✅ Google Calendar event created (visible in your Google Calendar)
- ✅ Confirmation email sent to applicant
- ✅ Application ranked against 15 mock applications

---

## What Makes This Demo Special

1. **Real Email Processing**: Actually receives via Agentmail (not fake)
2. **Hyperspell Ranking**: Queries all 16 applications (1 real + 15 mock) to rank
3. **Intelligent Selection**: Agent uses Hyperspell data to choose top applicant
4. **Auto-Scheduling**: Top-ranked applicants automatically get scheduled
5. **Google Calendar Integration**: Event appears in your actual Google Calendar
6. **End-to-End Automation**: Email → Processing → Ranking → Scheduling → Calendar

---

## Console Output Flow (What You'll See)

```
📬 Checking Agentmail inbox for new threads...
📧 Found 1 new thread(s) with unread messages

📬 NEW APPLICATION FROM AGENTMAIL
   Thread ID: thread_abc123
   Message ID: msg_xyz789
   From: applicant@example.com
   Applicant: John Doe

📄 Processing documents for message msg_xyz789
✅ Extracted: Credit 720, Income $6000/month
📊 Screening Score: green

🤖 Agent decision: approve - [reasoning...]
✅ Application processed: approved (green)
✅ Indexed application app_123 in Hyperspell for querying

🔍 QUERYING HYPERSPELL to rank this applicant...
📊 Hyperspell Ranking Result:
   [ranking analysis...]

🎯 DEMO HIGHLIGHT: John Doe ranked in TOP 3 by Hyperspell!
   ✅ Auto-scheduling property showing...

✅ DEMO SUCCESS!
   📅 Scheduled: 2024-11-05 at 14:00
   📅 Google Calendar Event ID: event_abc123xyz
   ✅ Application status: scheduled

📧 Sent confirmation email to applicant@example.com
```

---

## Required Environment Variables

Make sure these are set:

```bash
# Enable intelligent agent
USE_TENANT_AGENT=true

# Auto-schedule top-ranked applicants (default: true)
AUTO_SCHEDULE_TOP_APPLICANTS=true

# Agentmail
AGENTMAIL_API_KEY=your_key
AGENTMAIL_INBOX_ID=your_inbox_id

# Hyperspell
HYPERSPELL_API_KEY=your_key
HYPERSPELL_API_URL=https://api.hyperspell.com

# Gemini (for agent)
LLM_API_KEY=your_gemini_key

# Frontend API
APPLICATION_SERVICE_TOKEN=your_token
FRONTEND_ORIGIN=https://ten8link.vercel.app
DEFAULT_USER_ID=your_user_id
```

---

## Tips for Demo

1. **Use High-Quality Applicant**: Send email with credit score >700 and income >3x rent to ensure top ranking
2. **Show Console**: Keep backend console visible to show the real-time processing
3. **Show Applications Page**: Refresh `/applications` page to see status update
4. **Show Google Calendar**: Open your Google Calendar to show the event was created
5. **Highlight Ranking**: Point out how Hyperspell compared 16 applications and ranked yours

---

## What Happens Behind the Scenes

1. **Email → Agentmail**: Email received in monitored inbox
2. **Document Extraction**: Gemini AI extracts credit score, income, etc. from attachments
3. **Screening**: Calculates green/yellow/red score
4. **Agent Decision**: Gemini agent decides approve/reject/review
5. **Hyperspell Indexing**: Application stored as searchable "memory"
6. **Hyperspell Query**: Natural language query: "Rank all applicants..."
7. **Top 3 Check**: System checks if this applicant is in top 3
8. **Auto-Schedule**: If top 3, picks first available calendar slot
9. **Google Calendar**: Hyperspell creates event in your calendar
10. **Database Update**: Application status → "scheduled"
11. **Confirmation Email**: Agentmail sends confirmation to applicant

---

**Ready for your demo!** 🚀

Send your test email and watch the magic happen!

