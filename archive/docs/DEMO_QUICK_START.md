# Quick Start: Demo Setup

## 1. Seed Mock Applications

```bash
python seed_mock_applications.py [your_user_id]
```

This creates 15 mock applications in Hyperspell for demo queries.

## 2. Set Environment Variables

```bash
export HYPERSPELL_API_KEY=your_key
export AGENTMAIL_API_KEY=your_key
export AGENTMAIL_INBOX_ID=your_inbox_id
export LLM_API_KEY=your_gemini_key
export DEFAULT_USER_ID=your_user_id
export USE_TENANT_AGENT=true  # Enable intelligent agent
```

## 3. Start Backend

```bash
python minimal_backend.py
```

## 4. Send Test Email

Send email to Agentmail inbox with:
- Subject: "Tenant Application"
- Attachments: Driver's license, pay stubs, credit report
- Body: Include name, phone, property interest

## 5. Watch It Work

The system will:
1. ✅ Receive email via Agentmail
2. ✅ Extract data from documents
3. ✅ Query Hyperspell to compare applicant
4. ✅ Make intelligent decision (if agent enabled)
5. ✅ Index in Hyperspell for future queries
6. ✅ Send response email

## Test Hyperspell Queries

```python
from backend_modules.hyperspell_service import HyperspellClient

client = HyperspellClient()
result = await client.query(
    user_id="your_user_id",
    query="Show me top 5 applicants with credit above 700",
    collections=["tenant_applications"],
    answer=True
)
print(result["answer"])
```

Done! 🚀

