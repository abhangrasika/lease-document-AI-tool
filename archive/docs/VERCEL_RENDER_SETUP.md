# Vercel + Render Setup: Automatic Email Indexing

## Important: Where Your Code Runs

- **Vercel** = Frontend (Next.js) - Can't run Python or long-running tasks
- **Render** = Backend (Python/FastAPI) - Runs background tasks and webhooks

Your backend is already running on Render at: `https://prop-ai.onrender.com`

---

## Automatic Email Indexing Setup

### Option 1: Webhook (Automatic - Recommended)

**How it works:**
1. Email arrives in Agentmail
2. Agentmail sends webhook to your Render backend
3. Backend automatically processes and indexes in Hyperspell

**Setup:**
1. Register webhook with Agentmail pointing to:
   ```
   https://prop-ai.onrender.com/api/agentmail/webhook
   ```

2. When emails arrive, they'll automatically:
   - ✅ Get processed as applications (if tenant applications)
   - ✅ Get indexed in Hyperspell (ALL emails)
   - ✅ Be queryable via Hyperspell

**No Vercel code needed** - this runs on Render backend automatically!

---

### Option 2: Scheduled Task on Render

If webhooks aren't working, set up a cron job on Render:

**In Render Dashboard:**
1. Go to your backend service
2. Add a **Cron Job**:
   - **Command:** `curl -X POST https://prop-ai.onrender.com/api/agentmail/check-inbox`
   - **Schedule:** Every 5 minutes: `*/5 * * * *`

This will automatically check for new emails every 5 minutes.

---

### Option 3: Manual Trigger (For Testing)

You can manually trigger email indexing:

```bash
curl -X POST https://prop-ai.onrender.com/api/agentmail/index-all
```

Or from your frontend (Vercel):
```typescript
fetch('https://prop-ai.onrender.com/api/agentmail/index-all', {
  method: 'POST'
})
```

---

## What Happens Automatically

When an email arrives via Agentmail webhook:

1. **Webhook received** → `POST /api/agentmail/webhook`
2. **Processed as application** → If it's a tenant application
3. **Indexed in Hyperspell** → ALL emails are indexed automatically
4. **Collection**: `"agentmail_emails"` (separate from `"tenant_applications"`)

---

## Query All Your Emails

After emails are indexed, query them:

```python
# From your backend (Render)
from backend_modules.hyperspell_service import HyperspellClient

client = HyperspellClient()
result = await client.query(
    user_id=user_id,
    query="Show me all emails about tenant applications",
    collections=["agentmail_emails"],
    answer=True
)
```

---

## Verifying It Works

1. **Send a test email** to your Agentmail inbox
2. **Check Render logs** - you should see:
   ```
   📬 Received Agentmail webhook event evt_...
   💾 Indexed email thread thd_... in Hyperspell
   ```
3. **Query Hyperspell** to confirm email is indexed

---

## Troubleshooting

### Emails Not Being Indexed

1. **Check webhook is registered** with Agentmail
2. **Check Render logs** for webhook events
3. **Verify HYPERSPELL_API_KEY** is set in Render environment variables
4. **Check AGENTMAIL_API_KEY** is set

### Webhook Not Receiving Events

1. **Verify webhook URL** is accessible: `https://prop-ai.onrender.com/api/agentmail/webhook`
2. **Check Agentmail dashboard** to see if webhook is registered
3. **Test manually**: Send a test email to trigger webhook

---

**Summary:** Your backend on Render handles all email processing and indexing automatically via webhooks. Vercel (frontend) doesn't need to do anything - it just displays the results!

