# Ask Gemini for Best Applicant

This script fetches all tenant applications from the database and asks Gemini AI to identify the best applicant.

## How Applications Are Stored

Applications are stored in the **PostgreSQL database** via Prisma:
- Model: `TenantApplication` 
- They're created through:
  - Email processing (via Agentmail webhooks)
  - Manual creation through the UI
  - Seeding scripts (`seed-apps.js`, `seed_mock_applications.py`)

## Usage

### Option 1: Using the API (Recommended)

**Requirements:**
1. Frontend server must be running on `http://localhost:3000`
2. Set `APPLICATION_SERVICE_TOKEN` environment variable (or it will use default: `your-service-token-here`)

```bash
# Make sure frontend is running first
cd propai-frontend
npm run dev

# In another terminal, run the script
cd /Users/michael/prop_ai
python3 ask_gemini_best_applicant.py

# Or with a specific user ID
python3 ask_gemini_best_applicant.py cmgk8d5yz0000l104mkwr8j0w
```

### Option 2: Direct Database Access (If API doesn't work)

If you have `DATABASE_URL` set, you can modify the script to use direct database access via Prisma from Node.js:

```bash
cd propai-frontend
# Make sure DATABASE_URL is set in .env.local
export DATABASE_URL="your-postgres-connection-string"
node ask_gemini_best_applicant.js
```

## Environment Variables

You can set these in your shell or `.env` file:

```bash
# For API access
export APPLICATION_SERVICE_TOKEN="your-service-token-here"  # or actual token
export FRONTEND_ORIGIN="http://localhost:3000"  # Default
export USER_ID="cmgk8d5yz0000l104mkwr8j0w"  # Optional, has default

# Gemini API key is hardcoded in the script
# Key: AIzaSyB19XVVUEizOwjiR4OdgdQD_UPvQMHnnC4
```

## What the Script Does

1. **Fetches all applications** from the database (via API or direct DB)
2. **Displays a summary** of all applications
3. **Sends all application data to Gemini AI** with a prompt to find the best applicant
4. **Displays Gemini's analysis** including:
   - Best applicant name and email
   - Explanation of why they're the best choice
   - Any concerns or red flags

## Example Output

```
📊 Fetching applications from API...

🔗 Using API endpoint: http://localhost:3000/api/applications/internal
👤 User ID: cmgk8d5yz0000l104mkwr8j0w

✅ Found 15 applications

📋 Applications Summary:
------------------------------------------------------------
1. Sarah Johnson - Credit: 780, Score: green, Status: approved
2. Michael Chen - Credit: 720, Score: green, Status: awaiting_tenant
3. Emily Rodriguez - Credit: 695, Score: green, Status: scheduled
...
------------------------------------------------------------

🤖 Sending applications to Gemini AI...

🎯 GEMINI AI ANALYSIS:
============================================================
Best Applicant: Sarah Johnson
Email: sarah.johnson@example.com

Sarah Johnson is the best applicant based on:
- Excellent credit score of 780
- High monthly income of $7,500
- Green screening score
- Complete application with all required documents

No concerns identified.
============================================================
```

## Troubleshooting

**Error: "Unauthorized"**
- Set `APPLICATION_SERVICE_TOKEN` environment variable
- Or check that the default token matches in `propai-frontend/app/api/applications/internal/route.ts`

**Error: "Connection refused" or "500 Internal Server Error"**
- Make sure the frontend is running: `cd propai-frontend && npm run dev`
- Check that the API endpoint is accessible

**Error: "No applications found"**
- Make sure applications exist in the database
- Try running `seed-apps.js` to create mock applications:
  ```bash
  cd propai-frontend
  node seed-apps.js
  ```

**Error: "DATABASE_URL not found" (for Node.js version)**
- Set `DATABASE_URL` environment variable
- Or create `.env.local` in `propai-frontend/` with:
  ```
  DATABASE_URL="your-postgres-connection-string"
  ```

