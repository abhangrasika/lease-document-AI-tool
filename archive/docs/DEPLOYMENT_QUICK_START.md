# 🚀 PropAI Deployment Quick Start

## ✅ Pre-Deployment Checklist (DONE)
- ✅ Code bugs fixed
- ✅ Prisma schema updated to PostgreSQL
- ✅ Ready to deploy!

---

## 📝 Quick Deployment Checklist

### 1️⃣ Render Backend (10 minutes)
- [ ] Sign up at https://render.com
- [ ] Create new Web Service
- [ ] Connect GitHub repo
- [ ] Set environment variables (see below)
- [ ] Deploy and save URL

### 2️⃣ Vercel Frontend (15 minutes)
- [ ] Sign up at https://vercel.com
- [ ] Create Postgres database
- [ ] Import project (root: `propai-frontend`)
- [ ] Connect database
- [ ] Set environment variables (see below)
- [ ] Deploy and save URL

### 3️⃣ Update CORS (2 minutes)
- [ ] Update `FRONTEND_ORIGIN` in Render
- [ ] Use your Vercel URL
- [ ] Redeploy backend

### 4️⃣ Twilio Setup (10 minutes)
- [ ] Sign up at https://www.twilio.com/try-twilio
- [ ] Get phone number
- [ ] Get Account SID and Auth Token
- [ ] Configure webhook: `https://your-backend.onrender.com/sms`
- [ ] Add credentials to Render
- [ ] Set `USE_FAKE_TWILIO=0`

### 5️⃣ Test Everything (10 minutes)
- [ ] Test backend health endpoint
- [ ] Create account on frontend
- [ ] Add test property
- [ ] Send test SMS
- [ ] Verify SMS response

---

## 🔑 Environment Variables Copy-Paste

### Render (Backend)
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

**After Twilio Setup, Add:**
```
TWILIO_ACCOUNT_SID=ACxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxx
TWILIO_FROM_NUMBER=+15551234567
USE_FAKE_TWILIO=0
```

### Vercel (Frontend)
```
NEXT_PUBLIC_BACKEND_URL=https://your-backend.onrender.com
NEXT_PUBLIC_API_BASE=https://your-backend.onrender.com
NEXTAUTH_URL=https://your-app.vercel.app
NEXTAUTH_SECRET=<generate-random-32-char-string>
```

**Generate NEXTAUTH_SECRET:**
```bash
openssl rand -base64 32
```

---

## 🎯 Critical URLs to Save

**During Deployment:**
1. **Backend URL**: `https://______________.onrender.com`
2. **Frontend URL**: `https://______________.vercel.app`
3. **Twilio Number**: `+1______________`

**Test Endpoints:**
- Backend Health: `https://your-backend.onrender.com/health`
- Frontend Home: `https://your-app.vercel.app`
- Backend Stats: `https://your-backend.onrender.com/api/data-flow/stats`

---

## ⚡ Quick Test Commands

```bash
# Test backend is alive
curl https://your-backend.onrender.com/health

# Test AI endpoint
curl -X POST https://your-backend.onrender.com/pm_chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "context": {"tenant_name": "Test", "unit": "1A", "address": "123 St", "property_name": "Test"}}'

# Test SMS webhook (replace with your Twilio number)
curl -X POST https://your-backend.onrender.com/sms \
  -d "From=+1234567890" \
  -d "To=+your-twilio-number" \
  -d "Body=Test message"
```

---

## 🆘 Troubleshooting

**Backend not starting?**
→ Check Render logs, verify environment variables

**Frontend build failed?**
→ Ensure database is connected, check build logs

**CORS errors?**
→ Update `FRONTEND_ORIGIN` in Render to match Vercel URL exactly

**SMS not working?**
→ Check Twilio webhook URL, verify credentials, ensure `USE_FAKE_TWILIO=0`

---

## 📚 Full Documentation

For detailed step-by-step instructions, see:
- `PRODUCTION_DEPLOYMENT_STEPS.md` - Complete deployment guide
- `production-deployment-guide.plan.md` - Original deployment plan

---

## ⏱️ Total Time Estimate

- Backend deployment: **10 minutes**
- Frontend deployment: **15 minutes**
- Twilio setup: **10 minutes**
- Testing: **10 minutes**

**Total: ~45 minutes** 🎉

---

## 💡 Pro Tips

1. **Deploy backend first** - You need the URL for frontend config
2. **Use strong NEXTAUTH_SECRET** - Generate with openssl
3. **Save all URLs immediately** - You'll need them for configuration
4. **Test incrementally** - Test each phase before moving to next
5. **Check logs frequently** - Render and Vercel have great logging
6. **Start with fake Twilio** - Test without SMS first, then add Twilio
7. **Free tiers are enough** - Perfect for testing and small deployments

---

## 🎉 When You're Done

You'll have:
- ✅ Production backend on Render
- ✅ Production frontend on Vercel
- ✅ PostgreSQL database
- ✅ AI-powered SMS responses
- ✅ Property management system
- ✅ Maintenance ticket tracking

**Share your frontend URL and start managing properties!** 🏠

