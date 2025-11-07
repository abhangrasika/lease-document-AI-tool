# Tenant Screening & Showing Scheduler - Hackathon Edition ✅

## 🎯 What Was Built

A complete real-time dashboard system that automates tenant screening and property showing scheduling via email.

### Features Implemented

#### 1. **Real-Time Dashboard** (`/applications`)
- 📊 **Stats Bar**: Shows Submitted | Approved | Rejected | Scheduled counts
- 📋 **Application Table**: Beautiful cards with status badges, credit scores, income ratios
- ⚡ **Real-Time Updates**: Polls every 3 seconds for instant status updates
- 📱 **Activity Feed**: Live feed showing all events as they happen
- 🎨 **Color-Coded Statuses**:
  - 🔄 REVIEWING (blue)
  - ✅ APPROVED (green)
  - ⏳ AWAITING TENANT (indigo)
  - 📅 SCHEDULED (green)
  - ❌ REJECTED (red)

#### 2. **Automated Approval Workflow**
When a tenant sends an email with application:
1. ✅ Backend receives email via Agentmail webhook
2. ✅ Extracts data (credit score, income, property)
3. ✅ Runs approval logic (credit score + income check)
4. ✅ Auto-approves if criteria met
5. ✅ Queries Hyperspell for available calendar slots
6. ✅ Sends scheduling email with available times
7. ✅ Updates status to "awaiting_tenant"

#### 3. **Tenant Reply Processing**
When tenant replies with time selection:
1. ✅ Webhook detects reply email
2. ✅ Finds application by tenant email
3. ✅ Parses natural language for date/time
4. ✅ Creates Google Calendar event via Hyperspell
5. ✅ Updates status to "scheduled"
6. ✅ Sends confirmation email

#### 4. **Activity Feed Component**
Shows live events:
- 🔔 New application received
- ✅ Application approved
- 📧 Approval email sent
- 📅 Showing scheduled
- ❌ Application rejected

---

## 🔧 Technical Implementation

### Frontend Changes

#### New Components
- `components/ActivityFeed.tsx` - Real-time activity feed
- Enhanced `app/applications/page.tsx` with:
  - Real-time polling (3-second intervals)
  - Activity feed integration
  - Better stats display
  - Credit score highlighting
  - Income-to-rent ratio display

#### New API Routes
- `app/api/applications/[id]/update-status/route.ts` - Update status (service token auth)
- `app/api/applications/find-by-email/route.ts` - Find application by email
- Updated `app/api/applications/[id]/schedule/route.ts` - Support service token auth

### Backend Changes

#### Updated Files
- `backend_modules/inbox_monitor.py`:
  - Auto-updates status to "awaiting_tenant" after sending scheduling email
  
- `backend_modules/webhook_handler.py`:
  - Detects tenant replies
  - Parses date/time from email
  - Creates calendar events via Hyperspell
  - Updates application status to "scheduled"

---

## 📊 Database Schema

The `TenantApplication` model supports these statuses:
- `pending` - Just received
- `under_review` - Being reviewed
- `approved` - Approved, waiting for scheduling
- `awaiting_tenant` - Scheduling email sent, waiting for tenant reply
- `scheduled` - Tenant selected time, calendar event created
- `rejected` - Did not meet criteria

---

## 🚀 Workflow Flow

### Complete Email → Scheduled Flow

```
1. Tenant sends email
   └─> Agentmail webhook triggers
       └─> Backend processes email
           └─> Extracts credit score + income
               └─> Runs approval check
                   ├─> ✅ APPROVED
                   │   └─> Query Hyperspell for slots
                   │       └─> Send scheduling email
                   │           └─> Status: "awaiting_tenant"
                   │
                   └─> ❌ REJECTED
                       └─> Send rejection email
                           └─> Status: "rejected"

2. Tenant replies "Tuesday at 2pm"
   └─> Webhook detects reply
       └─> Parse date/time
           └─> Create calendar event (Hyperspell)
               └─> Update status: "scheduled"
                   └─> Send confirmation email
```

---

## 🎨 UI Highlights

### Dashboard Features
- **Real-time indicator**: Shows last refresh time with pulsing dot
- **Status badges**: Color-coded with icons
- **Credit score highlighting**: 
  - Green (≥680)
  - Yellow (≥620)
  - Red (<620)
- **Income ratio display**: Shows "3.2x rent" with threshold comparison
- **Activity feed**: Auto-updates with latest events
- **Smooth animations**: Status changes animate smoothly

---

## 🔐 Authentication

### Service Token for Internal API Calls
Backend-to-frontend API calls use `APPLICATION_SERVICE_TOKEN`:
- `POST /api/applications/[id]/update-status` - Service token only
- `POST /api/applications/find-by-email` - Service token only
- `POST /api/applications/[id]/schedule` - Supports both user session and service token

---

## 📝 Environment Variables Required

**Frontend:**
```env
APPLICATION_SERVICE_TOKEN=your-secret-token
DATABASE_URL=your_postgres_url
```

**Backend:**
```env
APPLICATION_SERVICE_TOKEN=your-secret-token  # Must match frontend
FRONTEND_ORIGIN=https://your-frontend.vercel.app
DEFAULT_USER_ID=your-user-id
AGENTMAIL_API_KEY=your_agentmail_key
HYPERSPELL_API_KEY=your_hyperspell_key
```

---

## 🎯 Hackathon Demo Tips

1. **Pre-populate test data**: Add 3-4 applications to database with different statuses
2. **Mock Hyperspell**: If Hyperspell is slow, hardcode available slots in backend
3. **Show one perfect flow**: Demonstrate email → approved → scheduled end-to-end
4. **Real-time magic**: The dashboard polling every 3 seconds creates a "real-time" feel
5. **Activity feed**: Shows all events happening live - very impressive for judges

---

## ✅ Status: Complete

All features from the hackathon spec have been implemented:
- ✅ Real-time dashboard with stats
- ✅ Automated approval workflow
- ✅ Hyperspell calendar integration
- ✅ Tenant reply parsing
- ✅ Calendar event creation
- ✅ Activity feed
- ✅ Status tracking (awaiting_tenant, scheduled, etc.)
- ✅ Beautiful UI with color coding

---

**Ready for hackathon demo!** 🚀

