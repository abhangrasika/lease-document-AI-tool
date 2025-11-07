# PropAI - Property Management with AI

Our property management platform that handles tenant SMS, maintenance requests, and property management tasks using AI. Built with Next.js + FastAPI + Twilio + Gemini AI.

> **⚠️ Security Note**: All API keys, secrets, and sensitive credentials have been redacted from this codebase. Set environment variables as described in the deployment guides.

> **🚀 Ready to Deploy?** Start here: **[START_HERE.md](START_HERE.md)** - Complete deployment guide (~45 min)

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │  Backend API     │    │   Twilio SMS    │
│   (Next.js)     │◄──►│   (FastAPI)      │◄──►│   Webhooks      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   Database       │
                       │ (PostgreSQL/     │
                       │  SQLite)         │
                       └──────────────────┘
```

## ✨ Features

### 🤖 AI-Powered Features
- **Property Manager AI Assistant** - Context-aware chat for property management tasks
- **Tenant SMS Processing** - Intelligent SMS handling with maintenance ticket creation
- **Lease Document Analysis** - AI-powered lease processing and key term extraction
- **Property Context Collection** - Comprehensive property analysis using AI

### 📱 SMS & Communication
- **Twilio Integration** - Automated SMS handling for tenant communication
- **Message Classification** - Automatic categorization of incoming messages
- **Maintenance Ticket Creation** - AI-driven ticket generation from SMS
- **Emergency Detection** - Automatic escalation of urgent issues

### 🏠 Property Management
- **Property Dashboard** - Manage multiple properties and tenants
- **Lease Management** - Upload and analyze lease documents
- **Maintenance Tracking** - Track and manage maintenance requests
- **Tenant Communication** - Centralized SMS conversation management

### 🔐 Authentication & Security
- **NextAuth.js Integration** - Secure user authentication
- **Role-based Access** - Property manager and admin access levels
- **Beta Application System** - Controlled access management

## 🚀 Production Deployment

**Ready to deploy to production?** We've prepared comprehensive deployment guides:

- **[📋 Quick Start Guide](DEPLOYMENT_QUICK_START.md)** - Fast deployment checklist (~45 minutes)
- **[📖 Detailed Deployment Steps](PRODUCTION_DEPLOYMENT_STEPS.md)** - Complete step-by-step instructions
- **[🗺️ Deployment Plan](production-deployment-guide.plan.md)** - Full deployment strategy

### What You'll Need:
- GitHub account (for connecting to Render & Vercel)
- Render account (backend hosting - free tier available)
- Vercel account (frontend + database hosting - free tier available)
- Twilio account (SMS - free trial with $15 credit)

### Deployment Stack:
- **Backend**: Render (FastAPI + Python)
- **Frontend**: Vercel (Next.js + React)
- **Database**: Vercel Postgres
- **SMS**: Twilio
- **AI**: Gemini 2.0 Flash

---

## 🛠️ Local Development Setup

**Note**: Environment variables are already set up on Vercel (frontend) and Render (backend), so you only need local setup for development.

### Prerequisites
- Node.js 18+ and npm
- Python 3.11+
- Git

### 1. Clone & Setup

```bash
git clone https://github.com/yourusername/propai.git
cd propai
```

### 2. Backend (FastAPI)

```bash
# Install Python deps
pip install -r requirements.txt

# Create local .env (only for local dev)
cp env.production.example .env
```

Edit `.env` for local development:
```env
LLM_API_KEY=your_gemini_api_key
DATABASE_URL=sqlite:///./propai.db
USE_FAKE_TWILIO=1
FRONTEND_ORIGIN=http://localhost:3000
```

### 3. Frontend (Next.js)

```bash
cd propai-frontend

# Install deps
npm install

# Create local .env.local (only for local dev)
cp .env.local.example .env.local
```

Edit `.env.local` for local development:
```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
DATABASE_URL=sqlite:///./propai.db
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your_local_secret
```

### 4. Database Setup

```bash
cd propai-frontend
npm run db:generate
npm run db:migrate
```

### 5. Run Locally

**Terminal 1 - Backend:**
```bash
python start_backend.py
```

**Terminal 2 - Frontend:**
```bash
cd propai-frontend
npm run dev
```

Go to `http://localhost:3000`

## 📁 Project Structure

```
propai/
├── propai-frontend/          # Next.js frontend application
│   ├── app/                  # Next.js 13+ app directory
│   │   ├── api/             # API routes
│   │   ├── auth/            # Authentication pages
│   │   ├── dashboard/       # Main dashboard
│   │   ├── properties/      # Property management
│   │   └── maintenance/     # Maintenance tickets
│   ├── components/          # React components
│   ├── lib/                 # Utilities and API functions
│   ├── prisma/              # Database schema and migrations
│   └── types/               # TypeScript type definitions
├── backend_modules/          # Backend utility modules
├── minimal_backend.py        # Main FastAPI backend
├── start_backend.py          # Backend startup script
├── requirements.txt          # Python dependencies
└── render.yaml              # Render.com deployment config
```

## 🔧 Key Environment Variables

**Production**: Already set up on Vercel/Render
**Local Development**: You need these in your `.env` files

### Backend (.env)
- `LLM_API_KEY` - Gemini API key
- `DATABASE_URL` - Database URL (use SQLite for local)
- `USE_FAKE_TWILIO=1` - Use fake SMS for local dev

### Frontend (.env.local)
- `NEXT_PUBLIC_BACKEND_URL=http://localhost:8000` - Backend URL
- `DATABASE_URL` - Same as backend
- `NEXTAUTH_SECRET` - Random string for auth

## 🚀 Deployment

**Already deployed!** 
- Frontend: Vercel (auto-deploys from main branch)
- Backend: Render (auto-deploys from main branch)

To deploy changes: just push to main branch.

## 📚 Main API Endpoints

### Backend (FastAPI)
- `POST /pm_chat` - Property manager AI chat
- `POST /tenant_sms` - Process tenant SMS (creates maintenance tickets)
- `POST /sms` - Twilio webhook for incoming SMS
- `GET /maintenance_tickets` - Get all maintenance tickets
- `GET /sms/threads` - Get SMS conversations

### Frontend (Next.js API routes)
- `/api/properties` - Property management
- `/api/leases` - Lease document processing
- `/api/maintenance-tickets` - Maintenance ticket management

## 🧪 Quick Test

```bash
# Test AI chat
curl -X POST http://localhost:8000/pm_chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Help with maintenance", "context": {"tenant_name": "John", "unit": "3A"}}'

# Test SMS (fake mode)
curl -X POST http://localhost:8000/sms \
  -d "From=+1234567890" \
  -d "Body=My toilet is broken"
```

## 🔍 Common Issues

1. **Backend won't start** - Check your `.env` file has `LLM_API_KEY`
2. **Frontend can't connect** - Make sure `NEXT_PUBLIC_BACKEND_URL=http://localhost:8000`
3. **Database errors** - Run `npm run db:migrate` in the frontend folder
4. **SMS not working** - Set `USE_FAKE_TWILIO=1` in backend `.env` for local testing

## 🛠️ Tech Stack

- **Frontend**: Next.js + TypeScript + Prisma + Tailwind
- **Backend**: FastAPI + Python + Gemini AI
- **SMS**: Twilio
- **Database**: PostgreSQL (prod) / SQLite (local)
- **Deploy**: Vercel (frontend) + Render (backend)

---
