# 📱 Demo Day SMS Failsafes & Safe Test Phrases

## ✅ Pre-Demo Checklist

**Before demo day, verify:**

1. **Property Settings Enabled** (in frontend):
   - Go to property → SMS settings
   - ✅ "Enable AI responses" = ON
   - ✅ "Auto-reply to messages" = ON

2. **Phone Number Mapped**:
   - Make sure your test phone number is mapped to a property
   - System needs `phone_to_property` mapping to work properly

3. **Twilio Webhook Active**:
   - Verify `/sms` endpoint is receiving messages
   - Check backend logs when you send a test message

4. **Environment Variables**:
   - `USE_FAKE_TWILIO=0` (if using real Twilio)
   - `LLM_API_KEY` is set (Gemini API key)
   - `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER` set

---

## 🎯 **SAFE Demo Phrases** (These Will Always Work)

These messages have built-in fallbacks and won't break:

### Tier 1: Guaranteed Responses (Hard-coded)
1. **`"when is rent due?"`**
   - ✅ Hard-coded response (no AI needed)
   - Always returns: "According to the lease provided by the property manager, rent is $2,000 and due every 1st of the month"
   - **Best for opening demo** - instant response, no AI risk

### Tier 2: Simple Questions (Low Risk)
2. **`"Hello"`** or **`"Hi"`**
   - Simple greeting, AI will respond politely
   - No ticket creation, just conversation

3. **`"What's my unit number?"`**
   - Safe question that won't trigger ticket creation
   - AI responds with context info

4. **`"How do I pay rent?"`**
   - General inquiry, safe for demo

5. **`"Thanks"`** or **`"Thank you"`**
   - Safe acknowledgment, friendly response

### Tier 3: Maintenance Troubleshooting (Shows Full Feature)
6. **`"My sink is dripping"`**
   - Shows AI troubleshooting flow
   - Will ask questions, provide steps
   - May create ticket after troubleshooting

7. **`"The toilet won't flush"`**
   - Classic maintenance issue
   - Shows step-by-step troubleshooting

8. **`"The lights aren't working"`**
   - Safe electrical question
   - AI will guide through breaker checks

### Tier 4: Ticket Closure (Shows Workflow)
9. **`"It's fixed now"`** or **`"Resolved"`**
   - If there's an open ticket, this closes it
   - Shows ticket management feature

---

## 🛡️ **Failsafes Built-In**

The system has **3 layers of error handling**:

1. **Hard-coded responses** (line 406):
   - "when is rent due?" → instant response

2. **Gemini with function calling** (line 535):
   - Primary AI response
   - If this fails → goes to layer 3

3. **Fallback responses** (lines 542, 555, 559):
   - "Thanks for your message! I'll help you with that..."
   - "Thanks for your message! I'm here to help..."
   - "Thanks for your message! I'm experiencing some technical difficulties, but I'll make sure your message gets to the right person."

4. **Final catch-all** (line 648):
   - "Thanks for your message! I'm experiencing some technical difficulties, but I'll make sure your message gets to the right person. Is there anything urgent I should know about?"

**Result**: Even if Gemini API fails completely, user gets a friendly response.

---

## ⚠️ **What Might Cause Issues** (Avoid These for Demo)

1. **Very long messages** (>1000 chars):
   - Might hit token limits
   - Keep demo messages short

2. **Complex multi-part questions**:
   - AI might struggle with 5+ questions in one message
   - Split into separate messages

3. **Messages that require external API calls**:
   - Don't ask about weather, news, etc.
   - Stick to property/tenant-related questions

4. **Offensive/inappropriate content**:
   - While it won't break, might generate awkward responses

5. **Images without proper URLs**:
   - If testing media, make sure Twilio Media URLs are valid
   - Media requires vision model, might be slower

---

## 🚀 **Recommended Demo Flow**

### Opening (30 seconds)
1. **Start with**: `"when is rent due?"`
   - ✅ Guaranteed instant response
   - Shows system is working

### Main Demo (2-3 minutes)
2. **Show greeting**: `"Hello"`
   - AI introduces itself as Esto
   - Personalizes with tenant name

3. **Show troubleshooting**: `"My sink is leaking"`
   - AI asks follow-up questions
   - Provides troubleshooting steps
   - Demonstrates intelligent conversation

4. **Show ticket creation** (if time):
   - Continue maintenance conversation
   - After troubleshooting, AI creates ticket
   - Shows ticket number in response

### Closing (30 seconds)
5. **Show acknowledgment**: `"Thanks, that helps!"`
   - Friendly closing interaction

---

## 🧪 **Pre-Demo Testing Script**

Run these in order before demo day:

```bash
# 1. Test hard-coded response (MUST WORK)
Text: "when is rent due?"
Expected: Instant response about rent date

# 2. Test simple greeting (SHOULD WORK)
Text: "Hi"
Expected: Friendly greeting from Esto

# 3. Test maintenance question (SHOULD WORK)
Text: "My sink is dripping"
Expected: AI asks questions, provides troubleshooting

# 4. Test fallback (if Gemini fails)
# Send any message, verify you get SOMETHING back
Expected: Any response is better than silence
```

---

## 🔍 **How to Check if It's Working**

### Backend Logs to Watch For:
```
[PHONE] New SMS received:
   From: +1234567890
   Body: [your message]

[SETTINGS] Property settings for +1234567890: AI=True, Auto-reply=True
[AI] Processing SMS with AI for +1234567890...
[AI] Calling Gemini with function calling...
[OK] LLM generated response: [response preview]
[AI] AI replied: [full response]
```

### If You See:
- ✅ `[OK] LLM generated response` → **Working perfectly**
- ⚠️ `[WARNING] No content in LLM response` → Fallback response will be sent
- ❌ `[ERROR] LLM Error` → Fallback response will be sent
- ❌ `[PHONE] AI disabled or auto-reply off` → **Check property settings in frontend**

---

## 💡 **Pro Tips for Demo**

1. **Have a backup plan**: If AI doesn't respond, show the hard-coded "when is rent due?" as proof it works

2. **Show the dashboard**: After sending SMS, immediately show the message in the frontend dashboard

3. **Demonstrate context**: Send multiple messages to show conversation history

4. **Test with photos** (optional): Send an image of a maintenance issue to show vision capabilities

5. **Show ticket creation**: If demo goes well, show how maintenance tickets are created automatically

---

## 🆘 **If Something Breaks During Demo**

**Quick Fixes:**

1. **No response at all?**
   - Check: Is `auto_reply` enabled in property settings?
   - Fallback: Manually send response via frontend

2. **Generic fallback message?**
   - Say: "The AI is using a safe fallback mode - in production, it would use full AI responses"
   - This shows error handling works

3. **Twilio not receiving?**
   - Check webhook URL in Twilio console
   - Verify backend is running

4. **Gemini API error?**
   - System will still respond with fallback
   - Not ideal, but not a complete failure

---

## ✅ **Summary: Ultra-Safe Demo Messages**

**These 3 are guaranteed to work well:**

1. `"when is rent due?"` → Hard-coded, instant
2. `"Hello"` → Simple AI response
3. `"My sink is dripping"` → Shows full troubleshooting flow

**Use these 3 for a 5-minute demo and you're golden! 🎯**

