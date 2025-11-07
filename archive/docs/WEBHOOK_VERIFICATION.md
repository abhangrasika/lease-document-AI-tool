# Webhook Verification & Automatic Email Indexing

## Your Webhook is Set Up ✅

If you have the Agentmail webhook configured, here's what happens automatically:

### Automatic Flow (No Manual Steps Needed)

1. **Email arrives** → Agentmail inbox
2. **Agentmail sends webhook** → `POST https://prop-ai.onrender.com/api/agentmail/webhook`
3. **Backend processes**:
   - ✅ Extracts data from email
   - ✅ Processes as application (if tenant application)
   - ✅ **Automatically indexes in Hyperspell** (ALL emails)
4. **Result**: Email is searchable in Hyperspell immediately

---

## Webhook Endpoint

Your backend webhook endpoint is ready at:
```
POST https://prop-ai.onrender.com/api/agentmail/webhook
```

When Agentmail sends events to this URL, your backend will:
- Process tenant applications
- Index ALL emails in Hyperspell (collection: `"agentmail_emails"`)
- Make them queryable

---

## What Gets Indexed

Every email that comes through the webhook is automatically:
- Stored in Hyperspell as a searchable "memory"
- Queryable via natural language
- Includes metadata (from, subject, date, thread_id)

---

## Query Your Emails

After emails are indexed (automatically via webhook), query them:

```python
# Find all emails about applications
result = await client.query(
    user_id=user_id,
    query="Show me all emails about tenant applications",
    collections=["agentmail_emails"],
    answer=True
)

# Find emails from specific person
result = await client.query(
    user_id=user_id,
    query="What did john.smith@example.com say in their emails?",
    collections=["agentmail_emails"]
)
```

---

## Verify It's Working

### Test 1: Send a Test Email
1. Send email to your Agentmail inbox
2. Check Render backend logs - should see:
   ```
   📬 Received Agentmail webhook event evt_...
   💾 Indexed email thread thd_... in Hyperspell
   ```

### Test 2: Query Hyperspell
```python
# Query to see if emails are indexed
result = await client.query(
    user_id=user_id,
    query="List all emails I've received",
    collections=["agentmail_emails"],
    limit=10
)
print(f"Found {len(result.get('documents', []))} emails")
```

---

## If Webhook Isn't Working

### Option 1: Manually Index All Emails
```bash
curl -X POST https://prop-ai.onrender.com/api/agentmail/index-all
```

This will read ALL emails from Agentmail and index them in Hyperspell.

### Option 2: Manual Inbox Check
```bash
curl -X POST https://prop-ai.onrender.com/api/agentmail/check-inbox
```

This reads all emails and processes/indexes them.

---

## Summary

✅ **With webhook set up**: Emails automatically indexed when they arrive
✅ **All emails**: Go to Hyperspell collection `"agentmail_emails"`
✅ **Tenant applications**: Also processed and indexed in `"tenant_applications"`
✅ **No manual steps needed**: Everything happens automatically

Your emails are being indexed automatically! 🎉

