# Production Deployment - Step-by-Step Guide

## ✅ Phase 0: Pre-Deployment Bug Fixes (COMPLETED)

All code fixes have been applied:
- ✅ Fixed Unicode encoding error (removed emoji from SMS)
- ✅ Fixed Pydantic deprecation warnings (.dict() → .model_dump())
- ✅ Updated Prisma schema from SQLite to PostgreSQL

---

## 📋 Phase 1: Backend Deployment (Render)

### Step 1.1: Create Render Account & Deploy Backend

1. **Go to Render**: https://render.com
   - Sign up or log in
   - Click "New +" → "Web Service"
   - Connect your GitHub account if not already connected
   - Select repository: `prop_ai` (or your repository name)

2. **Configure Service**:
   ```
   Name: propai-backend
   Environment: Python
   Region: Oregon (US West) or closest to your users
   Branch: pms-integration (or main)
   Root Directory: (leave empty)
   Build Command: pip install -r requirements.txt
   Start Command: python start_backend.py
   ```

3. **Environment Variables** - Add these in Render:
   ```
   HOST=0.0.0.0
   PORT=8000
   RELOAD=false
   LLM_API_KEY=AIzaSyBG2RIEPLO_d37g4X9TWMRxJoG74jWO-g0
   LLM_MODEL=gemini-2.0-flash
   LLM_VISION_MODEL=gemini-2.0-flash
   LLM_URL=https://generativelanguage.googleapis.com/v1beta/models
   USE_FAKE_TWILIO=1
   FRONTEND_ORIGIN=https://prop-ai-three.vercel.app
   ```

4. **Deploy**:
   - Click "Create Web Service"
   - Wait 3-5 minutes for deployment
   - **SAVE YOUR BACKEND URL**: Example: `https://propai-backend.onrender.com`

5. **Test Backend**:
   ```bash
   curl https://your-backend-url.onrender.com/health
   ```
   Expected response: `{"status": "healthy", ...}`

---

## 📋 Phase 2: Frontend Deployment (Vercel)

### Step 2.1: Create Vercel Postgres Database

1. **Go to Vercel**: https://vercel.com/dashboard
   - Sign up or log in
   - Go to Storage tab
   - Click "Create Database"
   - Select "Postgres"
   - Name: `propai-db`
   - Region: Same as backend (US West) or closest
   - Click "Create"
   - **Database will auto-connect to your project**

### Step 2.2: Deploy Frontend to Vercel

1. **Import Project**:
   - Click "Add New..." → "Project"
   - Import your `prop_ai` repository
   - Configure:
     ```
     Framework Preset: Next.js
     Root Directory: propai-frontend
     Build Command: npm run build (auto-detected)
     Output Directory: .next (auto-detected)
     Install Command: npm install (auto-detected)
     ```

2. **Connect Database**:
   - In project settings → Storage
   - Connect `propai-db` database
   - This auto-adds `POSTGRES_*` and `DATABASE_URL` environment variables

3. **Add Environment Variables**:
   In Vercel Project Settings → Environment Variables, add:
   
   ```
   NEXT_PUBLIC_BACKEND_URL=https://your-backend-url.onrender.com
   NEXT_PUBLIC_API_BASE=https://your-backend-url.onrender.com
   NEXTAUTH_URL=https://your-app.vercel.app
   NEXTAUTH_SECRET=<generate-this-below>
   ```

   **Generate NEXTAUTH_SECRET**:
   ```bash
   # On Mac/Linux:
   openssl rand -base64 32
   
   # On Windows PowerShell:
   [Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Minimum 0 -Maximum 256 }))
   ```

4. **Deploy**:
   - Click "Deploy"
   - Vercel will automatically:
     - Install dependencies
     - Run `prisma generate` (via postinstall script)
     - Build the Next.js app
     - Deploy to production
   - **SAVE YOUR FRONTEND URL**: Example: `https://your-app.vercel.app`

5. **Verify Database Migration**:
   - Go to Vercel project → Deployments
   - Click latest deployment → View Function Logs
   - Check for Prisma migration success
   - If migrations didn't run, manually trigger:
     ```bash
     # Install Vercel CLI
     npm i -g vercel
     
     # Login
     vercel login
     
     # Pull environment variables
     vercel env pull .env.local
     
     # Run migrations
     cd propai-frontend
     npx prisma migrate deploy
     ```

---

## 📋 Phase 3: Update CORS Configuration

### Step 3.1: Update Backend CORS

1. **Go to Render Dashboard**:
   - Navigate to your `propai-backend` service
   - Click "Environment" tab

2. **Update FRONTEND_ORIGIN**:
   - Find `FRONTEND_ORIGIN` variable
   - Change value to your actual Vercel URL:
     ```
     FRONTEND_ORIGIN=https://your-app.vercel.app
     ```
   - Click "Save Changes"

3. **Redeploy**:
   - Render will automatically redeploy
   - Wait for deployment to complete (~2 minutes)

---

## 📋 Phase 4: Twilio SMS Integration

### Step 4.1: Create Twilio Account

1. **Sign Up for Twilio**:
   - Go to: https://www.twilio.com/try-twilio
   - Create free trial account
   - Verify your email and phone number

2. **Get Trial Phone Number**:
   - After signup, Twilio will prompt you to get a phone number
   - OR go to: Console → Phone Numbers → Manage → Buy a number
   - Select a number with SMS capability
   - **SAVE THIS NUMBER**: Format like `+15551234567`

3. **Get Account Credentials**:
   - Go to: Console → Account → API keys & tokens
   - **SAVE**:
     - Account SID: `ACxxxxxxxxx` (visible on dashboard)
     - Auth Token: Click "View" to reveal, then copy

### Step 4.2: Configure Twilio Webhook

1. **Set Up SMS Webhook**:
   - Go to: Phone Numbers → Manage → Active Numbers
   - Click your phone number
   - Scroll to "Messaging Configuration"
   - Under "A MESSAGE COMES IN":
     - Select: "Webhook"
     - URL: `https://your-backend-url.onrender.com/sms`
     - HTTP Method: "POST"
   - Click "Save"

2. **Test Webhook** (Optional):
   ```bash
   curl -X POST https://your-backend-url.onrender.com/sms \
     -d "From=+1234567890" \
     -d "To=+your-twilio-number" \
     -d "Body=Test message"
   ```

### Step 4.3: Add Twilio Credentials to Backend

1. **Update Render Environment Variables**:
   - Go to Render Dashboard → Your Service → Environment
   - Add/Update these variables:
     ```
     TWILIO_ACCOUNT_SID=ACxxxxxxxxx
     TWILIO_AUTH_TOKEN=xxxxxxxxxxxxx
     TWILIO_FROM_NUMBER=+15551234567
     USE_FAKE_TWILIO=0
     ```

2. **Save and Redeploy**:
   - Click "Save Changes"
   - Service will auto-redeploy
   - Check logs to confirm Twilio initialization

---

## 📋 Phase 5: Testing & Verification

### Step 5.1: Test Backend Endpoints

```bash
# Health check
curl https://your-backend-url.onrender.com/health

# Test AI chat endpoint
curl -X POST https://your-backend-url.onrender.com/pm_chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What should I do about a leaky faucet?",
    "context": {
      "tenant_name": "John Doe",
      "unit": "3A",
      "address": "123 Main St",
      "hotline": "+1-555-0100",
      "property_name": "Test Property"
    }
  }'

# Expected: JSON response with AI-generated advice

# Test data flow stats
curl https://your-backend-url.onrender.com/api/data-flow/stats

# Expected: JSON with event statistics
```

### Step 5.2: Test Frontend

1. **Visit Frontend**: `https://your-app.vercel.app`

2. **Create Account**:
   - Click "Sign Up"
   - Enter email and password
   - Verify account creation

3. **Add a Test Property**:
   - Go to "Properties" page
   - Click "Add Property"
   - Fill in property details:
     - Property Name: Test Property
     - Tenant Name: Your Name
     - Unit: 101
     - Address: 123 Test St, City, State
     - Phone: Your phone number (for SMS testing)
     - Hotline: +1-555-0100
     - Portal URL: https://example.com
   - Click "Add Property"

4. **Test Features**:
   - ✅ View property details
   - ✅ Upload a lease document (if available)
   - ✅ Test property context collection
   - ✅ Check maintenance tickets page
   - ✅ Test messaging interface

### Step 5.3: Test End-to-End SMS Integration

1. **Send Test SMS from Your Phone**:
   - Text your Twilio number with: "My sink is leaking"

2. **Verify**:
   - ✅ Check Render logs for incoming SMS
   - ✅ Check for AI processing logs
   - ✅ Verify you receive SMS response on your phone
   - ✅ Check frontend Messages page for conversation

3. **Check Maintenance Ticket Creation**:
   - If issue is escalated, check Maintenance page
   - Verify ticket appears with correct details

---

## 🎯 Final Checklist

### Pre-Production Security

- [ ] Rotate Gemini API key if it was ever committed to git
- [ ] Verify `NEXTAUTH_SECRET` is strong and random
- [ ] Review CORS settings (only allow your frontend domain)
- [ ] Check all environment variables are set correctly
- [ ] Verify no sensitive data in git history

### Performance & Monitoring

- [ ] Verify frontend build is optimized (check Vercel deployment logs)
- [ ] Set up Render email alerts for errors
- [ ] Enable Vercel Analytics (already included)
- [ ] Test on mobile devices
- [ ] Check page load times

### Twilio Configuration

- [ ] Verify Twilio webhook URL is correct
- [ ] Test SMS sending and receiving
- [ ] Add trial phone numbers (if using trial account)
- [ ] Check Twilio usage/credits

---

## 🚨 Common Issues & Solutions

### Backend won't start on Render
- Check Render logs for specific error
- Verify Python version matches `runtime.txt` (3.11.9)
- Ensure all environment variables are set
- Check `requirements.txt` for dependency issues

### Frontend build fails on Vercel
- Check Vercel build logs for errors
- Verify `DATABASE_URL` is set (auto-set when database connected)
- Ensure Prisma schema is correct
- Try clearing build cache: Settings → General → Clear Build Cache

### Database connection errors
- Verify Vercel Postgres database is connected to project
- Check `DATABASE_URL` in Vercel environment variables
- Ensure Prisma schema has `provider = "postgresql"`
- Try redeploying frontend

### CORS errors
- Verify `FRONTEND_ORIGIN` in Render matches your Vercel URL exactly
- No trailing slashes in URLs
- Check browser console for specific CORS error
- Redeploy backend after changing CORS settings

### Twilio webhook not working
- Verify webhook URL is publicly accessible (test with curl)
- Check Render logs when sending test SMS
- Verify Twilio credentials are correct
- Ensure `USE_FAKE_TWILIO=0` for production

### SMS not sending
- Check Twilio account has credits/balance
- Trial accounts can only SMS verified numbers
- Check backend logs for Twilio errors
- Verify phone number format: `+1XXXXXXXXXX` (E.164 format)

---

## 💰 Cost Summary

**Monthly Costs (Free Tier)**:
- Render: FREE (750 hours/month, spins down after 15min inactivity)
- Vercel: FREE (unlimited deployments, 100GB bandwidth)
- Vercel Postgres: FREE (256MB storage, 60 hours compute/month)
- Twilio Trial: FREE $15 credit (limited to verified numbers)
- Gemini API: FREE tier available

**Recommended Production Upgrades**:
- Render Starter: $7/month (no spin-down, better performance)
- Vercel Pro: $20/month (more bandwidth, better analytics)
- Twilio Pay-as-go: ~$1/month + $0.0075 per SMS

---

## 🎉 You're Live!

Once all phases are complete, your PropAI system is production-ready!

**Your Live URLs**:
- Frontend: `https://your-app.vercel.app`
- Backend API: `https://your-backend-url.onrender.com`
- Twilio SMS: `+1XXXXXXXXXX`

**Next Steps**:
1. Set up custom domain on Vercel
2. Configure email notifications
3. Set up database backups
4. Add more properties
5. Invite users to beta test
6. Monitor usage and optimize

**Support Resources**:
- Render Docs: https://render.com/docs
- Vercel Docs: https://vercel.com/docs
- Twilio Docs: https://www.twilio.com/docs
- Prisma Docs: https://www.prisma.io/docs

---

## 📝 Environment Variables Summary

### Backend (Render)
```env
HOST=0.0.0.0
PORT=8000
RELOAD=false
LLM_API_KEY=AIzaSyBG2RIEPLO_d37g4X9TWMRxJoG74jWO-g0
LLM_MODEL=gemini-2.0-flash
LLM_VISION_MODEL=gemini-2.0-flash
LLM_URL=https://generativelanguage.googleapis.com/v1beta/models
TWILIO_ACCOUNT_SID=ACxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxx
TWILIO_FROM_NUMBER=+15551234567
USE_FAKE_TWILIO=0
FRONTEND_ORIGIN=https://your-app.vercel.app
```

### Frontend (Vercel)
```env
# Database (auto-set when Postgres connected)
DATABASE_URL=postgresql://...

# Backend
NEXT_PUBLIC_BACKEND_URL=https://your-backend-url.onrender.com
NEXT_PUBLIC_API_BASE=https://your-backend-url.onrender.com

# Auth
NEXTAUTH_URL=https://your-app.vercel.app
NEXTAUTH_SECRET=<your-generated-secret>
```

