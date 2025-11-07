# Tenant Screening System - Complete Setup Guide

This guide will walk you through setting up and completing the automated tenant screening and property showing workflow.

## ✅ What's Already Implemented

All core functionality has been implemented:

### Database Schema
- ✅ `TenantApplication` model in Prisma schema
- ✅ `PropertySettings` model for screening criteria
- ✅ All relations and indexes configured

### Backend Services
- ✅ Document processing service (`backend_modules/llm_service.py`)
- ✅ Screening score calculation (`backend_modules/screening_service.py`)
- ✅ Agentmail email service (`backend_modules/agentmail_service.py`)
- ✅ Hyperspell calendar service (`backend_modules/hyperspell_service.py`)
- ✅ All API endpoints in `minimal_backend.py`

### Frontend API Routes
- ✅ `/api/applications` - GET, POST
- ✅ `/api/applications/[id]` - GET, PATCH, DELETE
- ✅ `/api/applications/[id]/process` - Document processing
- ✅ `/api/applications/[id]/calculate-score` - Screening score
- ✅ `/api/applications/[id]/approve` - Approve and send email
- ✅ `/api/applications/[id]/reject` - Reject and send email
- ✅ `/api/applications/[id]/schedule` - Schedule showing
- ✅ `/api/calendar/availability` - Get available slots
- ✅ Navigation link added to Topbar

### Frontend UI Components
- ⏳ **Still need to create:** UI components and pages (see below)

---

## 🔧 Step-by-Step Setup Instructions

### Step 1: Configure Database

1. **Ensure DATABASE_URL is set:**
   ```bash
   # In propai-frontend/.env.local or .env
   DATABASE_URL="your_postgresql_connection_string"
   ```

2. **Run Prisma migration:**
   ```bash
   cd propai-frontend
   npx prisma migrate dev --name add_tenant_applications
   npx prisma generate
   ```

   This will:
   - Create the `TenantApplication` table
   - Create the `PropertySettings` table
   - Add all necessary indexes and relations

### Step 2: Configure Environment Variables

Add these to your backend `.env` file (root directory):

```bash
# Agentmail Configuration (for email receiving and sending)
AGENTMAIL_API_KEY=your_agentmail_api_key_here
AGENTMAIL_INBOX_ID=your_agentmail_inbox_id_here
AGENTMAIL_API_URL=https://api.agentmail.com  # Update with actual Agentmail API URL

# Hyperspell Configuration (for Google Calendar operations)
HYPERSPELL_API_KEY=your_hyperspell_api_key_here
HYPERSPELL_API_URL=https://api.hyperspell.com  # Update with actual Hyperspell API URL

# Backend URL (for frontend)
NEXT_PUBLIC_BACKEND_URL=https://your-backend-url.com  # or http://localhost:8000 for local
```

**How to get these credentials:**
- **Agentmail**: Sign up at Agentmail, create an inbox, get API key from dashboard
- **Hyperspell**: Sign up at Hyperspell, connect Google Calendar, get API key

### Step 3: Install Dependencies (if needed)

Check if you need to install any packages:

```bash
# Backend dependencies should already be in requirements.txt
pip install -r requirements.txt

# Frontend dependencies
cd propai-frontend
npm install
```

### Step 4: Set Up Agentmail

1. **Create an Agentmail account and inbox:**
   - Sign up at Agentmail (or your email service provider)
   - Create an inbox for receiving tenant applications
   - Note the inbox ID and API key

2. **Configure the inbox:**
   - Set up email forwarding or webhook to receive applications
   - Configure reply-to settings for email threading

3. **Test the connection:**
   - Send a test email to your inbox
   - Check backend logs to see if it's being received

### Step 5: Set Up Hyperspell (Google Calendar)

1. **Create a Hyperspell account:**
   - Sign up at Hyperspell
   - Connect your Google Calendar account
   - Get your API key from the dashboard

2. **Link property managers:**
   - Each property manager needs to connect their Google Calendar through Hyperspell
   - Store the Hyperspell user ID for each property manager (can be their email)

3. **Test calendar availability:**
   ```bash
   # Test endpoint
   curl "http://localhost:8000/api/calendar/availability?userId=YOUR_USER_ID&days=14"
   ```

### Step 6: Create Frontend UI Components

The frontend API routes are complete, but you need to create the UI. Create these files:

#### 6.1: Main Applications Page
Create `/propai-frontend/app/applications/page.tsx`:

```tsx
"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function ApplicationsPage() {
  const { data: session } = useSession();
  const router = useRouter();
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    if (session) {
      fetchApplications();
    }
  }, [session, filter]);

  const fetchApplications = async () => {
    try {
      const url = `/api/applications${filter !== "all" ? `?status=${filter}` : ""}`;
      const res = await fetch(url);
      const data = await res.json();
      setApplications(data.applications || []);
    } catch (error) {
      console.error("Error fetching applications:", error);
    } finally {
      setLoading(false);
    }
  };

  if (!session) {
    return <div>Please sign in</div>;
  }

  return (
    <div className="max-w-6xl mx-auto px-6 py-8">
      <h1 className="text-3xl font-bold mb-6">Tenant Applications</h1>
      
      {/* Filters */}
      <div className="flex gap-2 mb-6">
        {["all", "pending", "under_review", "approved", "scheduled", "rejected"].map((status) => (
          <button
            key={status}
            onClick={() => setFilter(status)}
            className={`px-4 py-2 rounded-lg ${
              filter === status ? "bg-blue-600 text-white" : "bg-gray-200"
            }`}
          >
            {status.replace("_", " ")}
          </button>
        ))}
      </div>

      {/* Applications List */}
      {loading ? (
        <div>Loading...</div>
      ) : applications.length === 0 ? (
        <div>No applications found</div>
      ) : (
        <div className="space-y-4">
          {applications.map((app: any) => (
            <Link
              key={app.id}
              href={`/applications/${app.id}`}
              className="block bg-white rounded-lg p-6 border hover:shadow-md transition"
            >
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-semibold text-lg">{app.applicantName}</h3>
                  <p className="text-gray-600">{app.applicantEmail}</p>
                  <p className="text-sm text-gray-500 mt-2">
                    Property: {app.property?.name || "Unknown"}
                  </p>
                </div>
                <div className="text-right">
                  <span className={`px-3 py-1 rounded-full text-sm ${
                    app.status === "approved" ? "bg-green-100 text-green-700" :
                    app.status === "rejected" ? "bg-red-100 text-red-700" :
                    app.status === "under_review" ? "bg-yellow-100 text-yellow-700" :
                    "bg-gray-100 text-gray-700"
                  }`}>
                    {app.status}
                  </span>
                  {app.screeningScore && (
                    <span className={`ml-2 px-2 py-1 rounded text-xs ${
                      app.screeningScore === "green" ? "bg-green-500 text-white" :
                      app.screeningScore === "yellow" ? "bg-yellow-500 text-white" :
                      "bg-red-500 text-white"
                    }`}>
                      {app.screeningScore}
                    </span>
                  )}
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
```

#### 6.2: Application Detail Page
Create `/propai-frontend/app/applications/[id]/page.tsx`:

```tsx
"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { useParams, useRouter } from "next/navigation";

export default function ApplicationDetailPage() {
  const { id } = useParams();
  const { data: session } = useSession();
  const router = useRouter();
  const [application, setApplication] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (session && id) {
      fetchApplication();
    }
  }, [session, id]);

  const fetchApplication = async () => {
    try {
      const res = await fetch(`/api/applications/${id}`);
      const data = await res.json();
      setApplication(data.application);
    } catch (error) {
      console.error("Error fetching application:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleProcessDocuments = async () => {
    try {
      const res = await fetch(`/api/applications/${id}/process`, { method: "POST" });
      const data = await res.json();
      if (data.success) {
        fetchApplication();
      }
    } catch (error) {
      console.error("Error processing documents:", error);
    }
  };

  const handleCalculateScore = async () => {
    try {
      const res = await fetch(`/api/applications/${id}/calculate-score`, { method: "POST" });
      const data = await res.json();
      if (data.success) {
        fetchApplication();
      }
    } catch (error) {
      console.error("Error calculating score:", error);
    }
  };

  const handleApprove = async () => {
    try {
      const res = await fetch(`/api/applications/${id}/approve`, { method: "POST" });
      const data = await res.json();
      if (data.success) {
        fetchApplication();
      }
    } catch (error) {
      console.error("Error approving:", error);
    }
  };

  const handleReject = async () => {
    try {
      const res = await fetch(`/api/applications/${id}/reject`, { method: "POST" });
      const data = await res.json();
      if (data.success) {
        fetchApplication();
      }
    } catch (error) {
      console.error("Error rejecting:", error);
    }
  };

  if (!session || loading) {
    return <div>Loading...</div>;
  }

  if (!application) {
    return <div>Application not found</div>;
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      <h1 className="text-3xl font-bold mb-6">{application.applicantName}</h1>
      
      {/* Contact Info */}
      <section className="bg-white rounded-lg p-6 border mb-6">
        <h2 className="text-xl font-semibold mb-4">Contact Information</h2>
        <p>Email: {application.applicantEmail}</p>
        <p>Phone: {application.applicantPhone || "N/A"}</p>
        <p>Property: {application.property?.name || "Unknown"}</p>
      </section>

      {/* Extracted Data */}
      <section className="bg-white rounded-lg p-6 border mb-6">
        <h2 className="text-xl font-semibold mb-4">Extracted Information</h2>
        {application.creditScore && (
          <p>Credit Score: {application.creditScore}</p>
        )}
        {application.monthlyIncome && (
          <p>Monthly Income: ${application.monthlyIncome.toLocaleString()}</p>
        )}
        {application.licenseName && (
          <p>License Name: {application.licenseName}</p>
        )}
      </section>

      {/* Screening Results */}
      {application.screeningScore && (
        <section className="bg-white rounded-lg p-6 border mb-6">
          <h2 className="text-xl font-semibold mb-4">Screening Results</h2>
          <div className={`inline-block px-4 py-2 rounded-lg ${
            application.screeningScore === "green" ? "bg-green-100 text-green-700" :
            application.screeningScore === "yellow" ? "bg-yellow-100 text-yellow-700" :
            "bg-red-100 text-red-700"
          }`}>
            {application.screeningScore.toUpperCase()}
          </div>
          {application.screeningNotes && (
            <p className="mt-2">{application.screeningNotes}</p>
          )}
        </section>
      )}

      {/* Actions */}
      <div className="flex gap-4">
        <button
          onClick={handleProcessDocuments}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Process Documents
        </button>
        <button
          onClick={handleCalculateScore}
          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
        >
          Calculate Score
        </button>
        <button
          onClick={handleApprove}
          className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
        >
          Approve
        </button>
        <button
          onClick={handleReject}
          className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
        >
          Reject
        </button>
      </div>
    </div>
  );
}
```

### Step 7: Set Up Background Worker for Agentmail Monitoring

The Agentmail inbox monitoring needs to run as a background task. Add this to `minimal_backend.py` or create a separate worker file:

```python
# Add to minimal_backend.py startup or create background_worker.py
import asyncio
from backend_modules.agentmail_service import AgentmailClient

async def monitor_agentmail_inbox():
    """Poll Agentmail inbox every 5-10 minutes for new emails"""
    client = AgentmailClient()
    
    while True:
        try:
            emails = await client.check_inbox()
            for email in emails:
                # Process email and create TenantApplication
                # Extract attachments, create application in database
                print(f"📧 New email from {email.get('from')}")
                # TODO: Implement email processing logic
        except Exception as e:
            print(f"❌ Error monitoring inbox: {e}")
        
        await asyncio.sleep(300)  # Wait 5 minutes

# Start background task when backend starts
# Add to main() or startup event
```

### Step 8: Test the System

1. **Test Document Processing:**
   ```bash
   curl -X POST http://localhost:8000/api/tenant-applications/process-documents \
     -H "Content-Type: application/json" \
     -d '{
       "applicationId": "test-123",
       "driversLicenseUrl": "https://example.com/license.jpg",
       "payStubUrls": ["https://example.com/paystub1.jpg"],
       "creditScoreUrl": "https://example.com/credit.jpg"
     }'
   ```

2. **Test Screening Score:**
   ```bash
   curl -X POST http://localhost:8000/api/tenant-applications/test-123/calculate-score \
     -H "Content-Type: application/json" \
     -d '{
       "creditScore": 720,
       "monthlyIncome": 5000,
       "monthlyRent": 1500,
       "licenseExpiration": "2026-12-31",
       "licenseName": "John Doe",
       "applicantName": "John Doe"
     }'
   ```

3. **Test Calendar Availability:**
   ```bash
   curl "http://localhost:8000/api/calendar/availability?userId=YOUR_USER_ID&days=14"
   ```

### Step 9: Deploy

1. **Backend Deployment:**
   - Deploy to Render, Railway, or your hosting provider
   - Ensure environment variables are set
   - Start the background worker for Agentmail monitoring

2. **Frontend Deployment:**
   - Deploy to Vercel or your hosting provider
   - Set `NEXT_PUBLIC_BACKEND_URL` environment variable
   - Run Prisma migrations on production database

---

## 📝 Remaining Manual Steps

1. **Get API Credentials:**
   - Sign up for Agentmail account
   - Sign up for Hyperspell account
   - Get API keys and configure

2. **Create UI Components:**
   - The basic pages above are templates - enhance them with full functionality
   - Add document viewers, email thread displays, timeline components
   - Style according to your design system

3. **Set Up Email Processing:**
   - Implement email parsing logic in background worker
   - Handle attachments and file storage (S3/Cloudinary)
   - Extract phone numbers from email signatures

4. **Configure Property Settings:**
   - Set screening criteria per property
   - Configure business hours and parking instructions
   - Link property managers to their Hyperspell accounts

---

## 🐛 Troubleshooting

### Database Migration Fails
- Check `DATABASE_URL` is correct
- Ensure PostgreSQL is running
- Try `npx prisma db push` instead of migrate

### Agentmail Not Receiving Emails
- Verify inbox ID and API key
- Check API URL is correct
- Ensure background worker is running

### Hyperspell Calendar Issues
- Verify Google Calendar is connected in Hyperspell
- Check user ID mapping is correct
- Test API endpoint directly

### Document Processing Fails
- Verify Gemini API key is set
- Check image URLs are accessible
- Review backend logs for errors

---

## ✅ Completion Checklist

- [ ] Database migration run successfully
- [ ] Environment variables configured
- [ ] Agentmail account set up and tested
- [ ] Hyperspell account set up and tested
- [ ] Frontend UI pages created
- [ ] Background worker running
- [ ] Document processing tested
- [ ] Screening score calculation tested
- [ ] Email sending tested
- [ ] Calendar integration tested
- [ ] End-to-end flow tested

---

## 📚 Additional Resources

- Full specification: `TENANT_SCREENING_PROMPT.md`
- Implementation status: `TENANT_SCREENING_IMPLEMENTATION_STATUS.md`
- Prisma schema: `propai-frontend/prisma/schema.prisma`
- Backend endpoints: `minimal_backend.py`

---

**Need Help?** Check the implementation status document or review the code comments in the service files.

