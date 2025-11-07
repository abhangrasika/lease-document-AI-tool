# Fix: Agentmail API URL Missing Protocol

## Error Message
```
❌ Error sending email via Agentmail: Request URL is missing an 'http://' or 'https://' protocol.
❌ Error getting Agentmail thread: Request URL is missing an 'http://' or 'https://' protocol.
```

## Problem
The `AGENTMAIL_API_URL` environment variable is either:
1. Not set at all
2. Set without the `https://` protocol prefix (e.g., `api.agentmail.com` instead of `https://api.agentmail.com`)

## Solution

### Option 1: Fix in Render (Recommended)

1. Go to **Render Dashboard** → Your `prop-ai` backend service
2. Click **Environment** tab
3. Find `AGENTMAIL_API_URL` variable
4. Make sure it's set to:
   ```
   https://api.agentmail.com
   ```
   (with `https://` prefix)
5. If it's missing or incorrect, add/update it
6. Click **Save Changes**
7. Render will automatically redeploy

### Option 2: Fix in Code (Already Done)

I've updated `backend_modules/agentmail_service.py` to automatically add `https://` if the protocol is missing.

**However**, you still need to set `AGENTMAIL_API_URL` in Render with a valid value.

---

## Verify Configuration

After updating, check your Render environment variables:

```bash
# Should be set to (with actual Agentmail API URL):
AGENTMAIL_API_URL=https://api.agentmail.com
```

**Note**: Replace `https://api.agentmail.com` with the **actual** Agentmail API URL if it's different.

---

## Quick Test

After fixing, send a test email and check logs:
- ✅ Should see: `📬 Received Agentmail webhook event...`
- ✅ Should NOT see: `Request URL is missing an 'http://' or 'https://' protocol`

---

## Current Status

✅ Code fix applied: Will auto-add `https://` if missing
⚠️ **Action Required**: Set `AGENTMAIL_API_URL` in Render environment variables

