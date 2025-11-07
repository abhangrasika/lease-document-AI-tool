# How to Check if Agentmail Read Your Email

There are **3 ways** to verify if Agentmail received and processed your email:

---

## Method 1: Check Inbox Status API (Easiest) ✅

### Quick Check
```bash
curl https://prop-ai.onrender.com/api/agentmail/inbox-status
```

### What You'll See
```json
{
  "success": true,
  "inbox_id": "inbox_xxx",
  "total_threads": 5,
  "threads": [
    {
      "thread_id": "thd_xxx",
      "subject": "Tenant Application",
      "message_count": 2,
      "unread_count": 0,
      "sender": "john@example.com",
      "last_updated": "2024-01-15T10:30:00Z"
    }
  ],
  "indexed_in_hyperspell": 5,
  "webhook_configured": true
}
```

### What It Means
- ✅ **`total_threads > 0`** → Agentmail received your email
- ✅ **`indexed_in_hyperspell > 0`** → Email was indexed in Hyperspell
- ⚠️ **`unread_count > 0`** → Email received but not processed yet

---

## Method 2: Check Render Backend Logs 📋

### If Webhook is Working
When an email arrives, you'll see in Render logs:
```
📬 Received Agentmail webhook event evt_xxx
   Thread: thd_xxx, From: john@example.com, Subject: Tenant Application
💾 Indexed email thread thd_xxx in Hyperspell
```

### If Webhook is NOT Working
You won't see any webhook logs when emails arrive.

---

## Method 3: Run Local Check Script 🖥️

### Option A: Run Python Script
```bash
python check_inbox_status.py
```

### Option B: Use API Endpoint
```bash
# Check inbox
curl https://prop-ai.onrender.com/api/agentmail/inbox-status | jq

# Check indexing status
curl https://prop-ai.onrender.com/api/agentmail/index-status | jq

# Manually trigger inbox check
curl -X POST https://prop-ai.onrender.com/api/agentmail/check-inbox

# Manually index all emails
curl -X POST https://prop-ai.onrender.com/api/agentmail/index-all
```

---

## Troubleshooting

### ❌ "No threads found in inbox"
**Problem**: Agentmail hasn't received the email yet.

**Solutions**:
1. **Check email address** - Make sure you're sending to the correct Agentmail inbox email
2. **Check spam folder** - Email might be in spam
3. **Wait a few minutes** - Agentmail may take 1-2 minutes to process
4. **Check Agentmail dashboard** - Log into Agentmail directly to see if email appears

### ❌ "Webhook not firing"
**Problem**: Webhook isn't being called when emails arrive.

**Solutions**:
1. **Verify webhook URL** in Agentmail dashboard:
   - Should be: `https://prop-ai.onrender.com/api/agentmail/webhook`
2. **Check Render logs** for webhook errors
3. **Test webhook manually** (if Agentmail supports it)
4. **Use polling instead**: Call `/api/agentmail/check-inbox` periodically

### ❌ "Emails received but not indexed"
**Problem**: Agentmail has emails, but they're not in Hyperspell.

**Solutions**:
1. **Manually index**:
   ```bash
   curl -X POST https://prop-ai.onrender.com/api/agentmail/index-all
   ```
2. **Check Render logs** for indexing errors
3. **Verify Hyperspell API key** is set in Render environment variables

---

## Quick Verification Checklist

- [ ] Email sent to correct Agentmail inbox address
- [ ] `total_threads > 0` in inbox status
- [ ] Webhook logs appear in Render (if using webhook)
- [ ] `indexed_in_hyperspell > 0` (emails are searchable)
- [ ] No errors in Render backend logs

---

## Example: Full Verification Flow

```bash
# 1. Send test email to Agentmail inbox

# 2. Wait 1-2 minutes

# 3. Check inbox status
curl https://prop-ai.onrender.com/api/agentmail/inbox-status

# 4. Check Render logs (Dashboard → Logs)
# Look for: "📬 Received Agentmail webhook"

# 5. Verify indexing
curl https://prop-ai.onrender.com/api/agentmail/index-status

# 6. Query Hyperspell to confirm email is searchable
# (Use Hyperspell query API or your frontend)
```

---

## Summary

**Easiest way**: Use the inbox status API:
```bash
curl https://prop-ai.onrender.com/api/agentmail/inbox-status
```

If `total_threads > 0`, Agentmail received your email! ✅

