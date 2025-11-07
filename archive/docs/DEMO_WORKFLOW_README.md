# Demo Workflow: Agentmail → Hyperspell Intelligent Tenant Screening

This guide shows you how to run the complete demo workflow where an email comes in via Agentmail, gets processed by an intelligent agent, and indexed in Hyperspell for querying/ranking.

## Prerequisites

1. **Environment Variables Set:**
   ```bash
   # Agentmail
   AGENTMAIL_API_KEY=your_key
   AGENTMAIL_INBOX_ID=your_inbox_id
   
   # Hyperspell
   HYPERSPELL_API_KEY=your_key
   HYPERSPELL_API_URL=https://api.hyperspell.com
   
   # Gemini (for intelligent agent)
   LLM_API_KEY=your_gemini_key
   
   # Default user ID
   DEFAULT_USER_ID=your_user_id
   
   # Optional: Enable intelligent agent
   USE_TENANT_AGENT=true  # Set to "true" to use Gemini agent
   ```

## Step 1: Seed Mock Applications (Optional but Recommended)

Before the demo, seed 15 mock applications into Hyperspell so you have data to query:

```bash
cd /Users/michael/prop_ai
python seed_mock_applications.py [your_user_id]
```

This will:
- Create 15 varied mock applications (different credit scores, incomes, statuses)
- Index them all in Hyperspell as searchable "memories"
- Distribute them over the past 2 weeks

**Expected Output:**
```
🌱 Seeding 15 mock applications to Hyperspell...
✅ [1/15] Indexed: Sarah Johnson (Credit: 780, Score: green, Status: approved)
✅ [2/15] Indexed: Michael Chen (Credit: 720, Score: green, Status: awaiting_tenant)
...
📊 Summary:
   ✅ Successfully indexed: 15
   ❌ Failed: 0
```

## Step 2: Start Backend (if not already running)

```bash
# From project root
python minimal_backend.py
# Or
python start_backend.py
```

The backend will:
- Monitor Agentmail inbox every 5-10 minutes (or via webhook)
- Process incoming emails automatically
- Use intelligent agent if `USE_TENANT_AGENT=true`

## Step 3: Send Test Email to Agentmail Inbox

Send an email to your Agentmail inbox with:
- **Subject:** "Tenant Application for [Property Address]"
- **Body:** Include name, phone, property interest
- **Attachments:**
  - Driver's license (image or PDF)
  - Pay stub(s) (image or PDF)
  - Credit score report (image or PDF)

**Example Email:**
```
Subject: Tenant Application for 123 Main Street

Hi,

I'm interested in applying for the property at 123 Main Street.

Name: John Doe
Phone: 555-1234
Email: john.doe@example.com

I've attached my driver's license, recent pay stubs, and credit report.

Thank you!
John Doe
```

## Step 4: Watch the Workflow

### Automatic Processing Flow:

```
1. 📧 Email arrives → Agentmail inbox
2. 🔍 Backend detects new email (via webhook or polling)
3. 📄 Extracts contact info and downloads attachments
4. 🤖 Processes documents with Gemini AI:
   - Extracts data from driver's license
   - Extracts income from pay stubs
   - Extracts credit score
5. 📊 Calculates screening score:
   - Green (credit ≥680, income ≥3x rent)
   - Yellow (credit ≥600, income ≥2.5x rent)
   - Red (below thresholds)
6. 🤖 Intelligent Agent (if enabled):
   - Queries Hyperspell: "How does this applicant rank?"
   - Makes decision using Gemini AI reasoning
   - Considers comparison with other applicants
7. 💾 Stores in Hyperspell:
   - Indexes application as searchable "memory"
   - Includes all metadata (credit, income, status, etc.)
8. 💾 Saves to database via frontend API
9. 📧 Sends response email:
   - Approved → Scheduling email with available times
   - Rejected → Professional decline email
   - Missing docs → Request missing documents
10. 📅 If approved and tenant replies → Creates calendar event
```

### Console Output Example:

```
📬 Checking Agentmail inbox for new threads...
📧 Found 1 new thread(s) with unread messages
📄 Processing documents for message msg_123
✅ Extracted: Credit 720, Income $6000/month
📊 Screening Score: green
🤖 Agent decision: approve - Applicant has excellent credit score of 720 and strong income ratio of 3.0x rent. Compared to other applicants, this ranks in the top 30%...
✅ Application processed: approved (green)
✅ Indexed application app_abc123 in Hyperspell for querying
✅ Application saved to database: app_abc123
📧 Sent scheduling email to john.doe@example.com
✅ Updated application app_abc123 status to 'awaiting_tenant'
```

## Step 5: Query Hyperspell (See Results)

Once applications are indexed, you can query Hyperspell to see rankings:

### Example Queries:

```python
from backend_modules.hyperspell_service import HyperspellClient

client = HyperspellClient()
user_id = "your_user_id"

# Query 1: Find top applicants
result = await client.query(
    user_id=user_id,
    query="Show me top 5 applicants with credit scores above 700",
    collections=["tenant_applications"],
    limit=5
)

# Query 2: Get AI summary
result = await client.query(
    user_id=user_id,
    query="What's the average credit score of approved applicants?",
    collections=["tenant_applications"],
    answer=True  # Get AI-generated answer
)

# Query 3: Rank by property
result = await client.query(
    user_id=user_id,
    query="Rank all applicants for property_123 by credit score and income ratio",
    collections=["tenant_applications"],
    answer=True
)
```

## Step 6: View in Dashboard

Check your frontend dashboard at `/applications`:
- See the new application appear in real-time
- View status, credit score, income ratio
- See activity feed updates
- Check if scheduling email was sent

## Agent Behavior

### With `USE_TENANT_AGENT=true`:

The intelligent agent will:
1. **Query Hyperspell** to see how the new applicant compares
2. **Use Gemini AI** to make a reasoned decision
3. **Consider context** from other applicants
4. **Provide reasoning** for its decision

**Example Agent Reasoning:**
```
"Applicant has credit score of 720 and income ratio of 3.0x rent. 
Compared to 15 existing applications, this ranks in the top 30%.
The applicant has complete documentation and a green screening score.
Decision: APPROVE - Strong candidate with excellent financial qualifications."
```

### Without Agent (`USE_TENANT_AGENT=false`):

Uses simple rule-based screening:
- Green → Approve
- Yellow → Review
- Red → Reject

## Testing the Complete Flow

### 1. Test with High-Quality Applicant:

Send email with:
- Credit score: 750
- Income: $7000/month (3.5x $2000 rent)
- All documents provided

**Expected:** Auto-approved, scheduling email sent, indexed in Hyperspell

### 2. Test with Medium-Quality Applicant:

Send email with:
- Credit score: 650
- Income: $5500/month (2.75x rent)
- All documents provided

**Expected:** Under review, agent queries Hyperspell for comparison

### 3. Test with Low-Quality Applicant:

Send email with:
- Credit score: 580
- Income: $4500/month (2.25x rent)
- All documents provided

**Expected:** Rejected, decline email sent

### 4. Test Missing Documents:

Send email with only 1-2 documents

**Expected:** Email requesting missing documents

## Troubleshooting

### Applications not appearing in Hyperspell:

1. Check `HYPERSPELL_API_KEY` is set
2. Check Hyperspell API is accessible
3. Look for error messages in console: `⚠️ Could not index application in Hyperspell`

### Agent not making decisions:

1. Check `USE_TENANT_AGENT=true` is set
2. Check `LLM_API_KEY` (Gemini) is set
3. Look for agent errors in console

### No email processing:

1. Check `AGENTMAIL_API_KEY` and `AGENTMAIL_INBOX_ID`
2. Verify backend is monitoring inbox (check console for polling messages)
3. Check Agentmail webhook is configured (if using webhooks)

## Demo Tips

1. **Pre-seed data:** Run `seed_mock_applications.py` first so Hyperspell has comparison data
2. **Show querying:** After applications come in, demonstrate Hyperspell queries
3. **Compare with/without agent:** Show difference between rule-based and agent-based decisions
4. **Show ranking:** Query Hyperspell to show how applicants rank against each other

## Next Steps

After the demo works, you can:
- Add more sophisticated agent reasoning
- Create dashboard views of Hyperspell rankings
- Add property-specific ranking criteria
- Integrate with calendar scheduling more deeply

---

**Ready for demo!** 🚀

Send an email to your Agentmail inbox and watch the magic happen!

