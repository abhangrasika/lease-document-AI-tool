# Agentmail Webhook Setup Guide

This guide explains how to set up the Agentmail webhook for real-time email processing.

## Overview

The webhook implementation allows Agentmail to instantly notify your backend when new emails arrive, eliminating the need for polling. This is more efficient and provides faster response times.

## Backend Webhook Endpoint

Your backend already has a webhook endpoint ready at:
```
POST /api/agentmail/webhook
```

**URL:** `https://your-backend-url.onrender.com/api/agentmail/webhook`

## Setup Steps

### 1. Get Your Webhook URL

For production (Render deployment):
```
https://prop-ai.onrender.com/api/agentmail/webhook
```

For local development (using ngrok):
```bash
# Install ngrok: https://ngrok.com/
ngrok http 8000

# Use the HTTPS URL ngrok provides, e.g.:
https://abc123.ngrok-free.app/api/agentmail/webhook
```

### 2. Register Webhook with Agentmail

Use the Agentmail API to register your webhook:

```python
from agentmail import AgentmailClient

client = AgentmailClient(api_key="your_agentmail_api_key")

# Register webhook
webhook = client.webhooks.create(
    url="https://prop-ai.onrender.com/api/agentmail/webhook"
)

print(f"Webhook registered: {webhook.webhook_id}")
```

Or using the Agentmail dashboard/CLI if available.

### 3. Verify Webhook Works

1. Send a test email to your Agentmail inbox
2. Check your backend logs - you should see:
   ```
   📬 Received Agentmail webhook event evt_...
   📬 Received webhook event evt_... for message msg_...
      Thread: thd_..., From: sender@example.com, Subject: ...
   ```

### 4. Webhook Payload Structure

The webhook receives payloads with this structure:

```json
{
  "event_type": "message.received",
  "event_id": "evt_123abc...",
  "message": {
    "from_": ["sender@example.com"],
    "organization_id": "org_abc123...",
    "inbox_id": "inbox_def456...",
    "thread_id": "thd_ghi789...",
    "message_id": "msg_jkl012...",
    "labels": ["received"],
    "subject": "Email Subject",
    "text": "The full text body of the email.",
    "html": "<html>...</html>",
    "attachments": [
      {
        "attachment_id": "att_pqr678...",
        "filename": "document.pdf",
        "content_type": "application/pdf",
        "size": 123456
      }
    ]
  }
}
```

## How It Works

1. **Email Arrives**: When a new email arrives in your Agentmail inbox
2. **Webhook Triggered**: Agentmail immediately sends a POST request to your webhook URL
3. **Immediate Acknowledgment**: Your backend returns 200 OK immediately
4. **Background Processing**: The webhook payload is processed in the background:
   - Extracts contact information
   - Downloads and categorizes attachments
   - Processes documents (driver's license, pay stubs, credit score)
   - Calculates screening score
   - Saves application to database
   - Sends appropriate emails (scheduling, rejection, etc.)
5. **Result**: New application appears in your frontend dashboard

## Webhook Endpoint Behavior

- **Returns 200 OK immediately** to acknowledge receipt
- **Processes payload in background** to avoid timeouts
- **Handles errors gracefully** - still returns 200 to prevent retries
- **Logs all events** for debugging

## Troubleshooting

### Webhook Not Receiving Events

1. **Check webhook registration**: Verify the webhook is registered with Agentmail
2. **Check URL accessibility**: Ensure your backend URL is publicly accessible
3. **Check logs**: Look for webhook POST requests in your backend logs
4. **Test manually**: Send a test email to your Agentmail inbox

### Webhook Processing Errors

1. **Check backend logs**: Look for error messages with stack traces
2. **Verify environment variables**: 
   - `AGENTMAIL_API_KEY`
   - `AGENTMAIL_INBOX_ID`
   - `FRONTEND_ORIGIN`
   - `APPLICATION_SERVICE_TOKEN`
   - `DEFAULT_USER_ID`
3. **Test endpoint manually**: Use curl or Postman to send a test webhook payload

### Testing Webhook Locally

```bash
# Start ngrok
ngrok http 8000

# Register the ngrok URL with Agentmail
# Then send a test email to your inbox

# Or test manually with curl:
curl -X POST http://localhost:8000/api/agentmail/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "message.received",
    "event_id": "evt_test123",
    "message": {
      "from_": ["test@example.com"],
      "thread_id": "thd_test",
      "message_id": "msg_test",
      "subject": "Test Email",
      "text": "Test body",
      "attachments": []
    }
  }'
```

## Benefits Over Polling

- **Real-time**: Instant notification when emails arrive
- **Efficient**: No constant API calls checking for new emails
- **Scalable**: Works well even with high email volume
- **Reliable**: Agentmail handles retries if your endpoint is temporarily down

## Next Steps

1. Register your webhook URL with Agentmail
2. Test by sending an email to your inbox
3. Verify applications appear in the frontend
4. Monitor backend logs for any issues

For more details, see the [Agentmail Webhooks Documentation](https://docs.agentmail.to/overview).

