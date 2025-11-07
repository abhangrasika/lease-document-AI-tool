# How Agentmail is Called - Webhook vs Polling

## Overview

There are **two ways** your system detects and processes new tenant applications from Agentmail:

1. **Webhook (Real-time)** - Automatic when emails arrive
2. **Polling (Manual refresh)** - When you click refresh or manually trigger

---

## Method 1: Webhook (Real-time Processing) ⚡

### How It Works

1. **Agentmail sends webhook** → When a new email arrives in your Agentmail inbox, Agentmail automatically sends a POST request to your backend
2. **Backend receives webhook** → `/api/agentmail/webhook` endpoint receives the payload
3. **Immediate processing** → Email is processed in the background and application is created

### Webhook Endpoint

```
POST https://your-backend-url/api/agentmail/webhook
```

### Webhook Payload Structure

```json
{
  "event_type": "message.received",
  "event_id": "evt_123abc...",
  "message": {
    "message_id": "msg_456def...",
    "thread_id": "thd_789ghi...",
    "inbox_id": "inbox_xyz...",
    "from_": ["applicant@email.com"],
    "subject": "Application for Property",
    "text": "Email body text...",
    "html": "<html>...</html>",
    "attachments": [...],
    "labels": []
  }
}
```

### Setup Required

⚠️ **You must register the webhook with Agentmail** for this to work:

1. Get your webhook URL:
   - Production: `https://prop-ai.onrender.com/api/agentmail/webhook`
   - Local (with ngrok): `https://abc123.ngrok-free.app/api/agentmail/webhook`

2. Register webhook via Agentmail API or dashboard:
   ```python
   # Example registration (check Agentmail docs for exact API)
   webhook = agentmail_client.webhooks.create(
       url="https://prop-ai.onrender.com/api/agentmail/webhook",
       events=["message.received"]
   )
   ```

### Why Webhooks Might Not Work

- ❌ Webhook not registered with Agentmail
- ❌ Backend URL not publicly accessible
- ❌ Agentmail can't reach your webhook URL (firewall, network issues)
- ❌ Webhook endpoint returning errors (check backend logs)

---

## Method 2: Polling (Manual Check) 🔄

### How It Works

1. **User clicks refresh** → Frontend calls `/api/applications/check-inbox`
2. **Frontend API calls backend** → `POST /api/agentmail/check-inbox`
3. **Backend polls Agentmail** → Calls `AgentmailClient.check_inbox()`
4. **Backend processes threads** → For each thread with unread messages, processes the application

### Code Flow

```
Frontend: /api/applications/check-inbox
    ↓
Backend: /api/agentmail/check-inbox
    ↓
monitor_inbox()
    ↓
AgentmailClient.check_inbox()
    ↓
AgentmailClient.list_threads(inbox_id)  → Get all threads
    ↓
For each thread:
    AgentmailClient.get_thread(thread_id)  → Get full thread with messages
    ↓
    Check for unread messages
    ↓
    process_incoming_email_from_thread()  → Process if unread found
```

### What Was Fixed

**Previous Issue**: The `check_inbox()` method only checked threads that already had messages in the list response. But Agentmail's `list_threads()` API doesn't include messages - you need to call `get_thread()` for each thread.

**Fix Applied**: Now `check_inbox()`:
1. Gets all threads via `list_threads()`
2. **Fetches full details for each thread** via `get_thread()`
3. Checks each thread for unread messages
4. Returns only threads with unread messages

### Why Polling Might Not Detect New Applications

**Before the fix:**
- ❌ Threads returned by `list_threads()` don't include messages
- ❌ Code only checked threads that already had messages in the response
- ❌ Result: No threads with messages found → No applications processed

**After the fix:**
- ✅ Now fetches full thread details for all threads
- ✅ Checks for unread messages in each thread
- ✅ Processes any threads with unread messages

---

## How Agentmail API is Called

### AgentmailClient Methods

```python
from backend_modules.agentmail_service import AgentmailClient

client = AgentmailClient()

# 1. List threads for an inbox
threads = await client.list_threads(inbox_id="inbox_123")
# Returns: List of thread summaries (no messages included)

# 2. Get full thread details (includes messages)
thread = await client.get_thread(thread_id="thd_456")
# Returns: Full thread object with messages array

# 3. Check inbox (new fixed method)
unread_threads = await client.check_inbox()
# Returns: List of threads that have unread messages
# Internally: list_threads() → get_thread() for each → filter unread
```

### API Endpoints Used

```python
# List threads
GET {AGENTMAIL_API_URL}/inboxes/{inbox_id}/threads

# Get thread with messages
GET {AGENTMAIL_API_URL}/threads/{thread_id}

# Send email
POST {AGENTMAIL_API_URL}/inboxes/{inbox_id}/send
POST {AGENTMAIL_API_URL}/threads/{thread_id}/reply

# Download attachment
GET {AGENTMAIL_API_URL}/attachments/{attachment_id}/download
```

---

## Troubleshooting: "Why isn't my webhook detecting new applications when I refresh?"

### The Confusion

When you "refresh" (click refresh button), you're using **polling**, not webhooks:
- Refresh button → Calls `/api/applications/check-inbox` → Uses **polling** method
- Webhooks → Automatic when emails arrive → Uses **webhook** method

These are **separate methods**. The refresh button doesn't use webhooks!

### To Fix Refresh/Manual Check

✅ **Already fixed!** The polling method (`check_inbox()`) now:
- Fetches full thread details for all threads
- Properly detects unread messages
- Processes new applications

Check backend logs when you refresh - you should see:
```
📬 Checking Agentmail inbox for new threads...
📬 Found X thread(s) in inbox, checking for unread messages...
📧 Thread thd_123 has Y unread message(s)
✅ Found Z thread(s) with unread messages
📬 Processing message msg_456 from thread thd_123
✅ Successfully processed message msg_456
```

### To Fix Webhooks

1. **Verify webhook is registered** with Agentmail (check Agentmail dashboard/API)
2. **Test webhook URL** is publicly accessible:
   ```bash
   curl -X POST https://prop-ai.onrender.com/api/agentmail/webhook \
     -H "Content-Type: application/json" \
     -d '{"event_type":"message.received","event_id":"test","message":{"message_id":"test"}}'
   ```
3. **Check backend logs** for webhook POST requests:
   ```
   📬 Received Agentmail webhook event evt_...
   ```
4. **Send test email** to your Agentmail inbox and watch logs

---

## Summary

- **Webhook**: Real-time, automatic - requires registration with Agentmail
- **Polling**: Manual/on-demand - fixed to properly check all threads for unread messages
- **Refresh button**: Uses polling method (not webhooks)
- **Both methods** call the same processing code (`process_incoming_email_from_thread()`)

The polling method is now fixed and should detect new applications when you refresh!

