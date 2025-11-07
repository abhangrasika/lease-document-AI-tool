# Environment Variables Setup Guide

Based on your architecture:
- **Backend**: Deployed on **Render** (Python/FastAPI)
- **Frontend**: Deployed on **Vercel** (Next.js)

You need to set environment variables in **BOTH** places.

---

## 🔵 Render (Backend) Environment Variables

Go to: **Render Dashboard** → Your `propai-backend` service → **Environment** tab

### Required Variables for Tenant Screening:

```bash
# Agentmail (Email receiving and sending)
AGENTMAIL_API_KEY=your_agentmail_api_key
AGENTMAIL_INBOX_ID=your_agentmail_inbox_id
AGENTMAIL_API_URL=https://api.agentmail.com  # Update with actual Agentmail API URL

# Hyperspell (Google Calendar operations)
HYPERSPELL_API_KEY=your_hyperspell_api_key
HYPERSPELL_API_URL=https://api.hyperspell.com  # Update with actual Hyperspell API URL
```

### Already Set in render.yaml (don't need to add again):
- `HOST`, `PORT`, `RELOAD`
- `DATABASE_URL` (from database connection)
- `LLM_API_KEY`, `LLM_MODEL`, `LLM_VISION_MODEL`, `LLM_URL`
- `TWILIO_FROM_NUMBER`, `USE_FAKE_TWILIO`
- `FRONTEND_ORIGIN`

### How to Add in Render:
1. Go to https://dashboard.render.com
2. Click on your `propai-backend` service
3. Go to **Environment** tab
4. Click **Add Environment Variable**
5. Add each variable above
6. Click **Save Changes**
7. Render will automatically redeploy

**Note:** You can also add these to `render.yaml` if you prefer, but using the dashboard is easier for sensitive keys.

---

## 🟢 Vercel (Frontend) Environment Variables

Go to: **Vercel Dashboard** → Your project → **Settings** → **Environment Variables**

### Required Variables for Tenant Screening:

```bash
# Backend URL (already should exist, but verify it's correct)
NEXT_PUBLIC_BACKEND_URL=https://prop-ai.onrender.com  # or your Render backend URL

# Database (already should exist)
DATABASE_URL=your_postgresql_connection_string
```

### Already Required (from existing setup):
- `NEXTAUTH_URL`
- `NEXTAUTH_SECRET`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`

### How to Add in Vercel:
1. Go to https://vercel.com/dashboard
2. Select your project (likely `prop-ai-three` or similar)
3. Go to **Settings** → **Environment Variables**
4. Click **Add New**
5. Add each variable above
6. Select which environments to apply to (Production, Preview, Development)
7. Click **Save**
8. **Redeploy** your application (Vercel won't auto-redeploy)

---

## 📝 Quick Checklist

### Render (Backend):
- [ ] `AGENTMAIL_API_KEY`
- [ ] `AGENTMAIL_INBOX_ID`
- [ ] `AGENTMAIL_API_URL`
- [ ] `HYPERSPELL_API_KEY`
- [ ] `HYPERSPELL_API_URL`

### Vercel (Frontend):
- [ ] `NEXT_PUBLIC_BACKEND_URL` (verify it points to your Render backend)
- [ ] `DATABASE_URL` (should already exist)

---

## 🔍 How to Verify

### Check Backend Variables (Render):
```bash
# After deployment, test endpoint
curl https://prop-ai.onrender.com/health
```

### Check Frontend Variables (Vercel):
- Check browser console for any API connection errors
- Verify `/api/applications` routes work
- Check Network tab to see if backend URL is correct

---

## 🚨 Important Notes

1. **Never commit `.env` files to git** - These are set in the deployment platforms
2. **NEXT_PUBLIC_*** prefix** - Only variables prefixed with `NEXT_PUBLIC_` are exposed to the browser in Next.js
3. **Backend secrets** - Keep Agentmail and Hyperspell keys secure (only in Render)
4. **Redeploy after changes** - Both platforms may need redeployment after adding variables

---

## 🔄 After Adding Variables

### Render:
- Automatically redeploys when you save environment variables
- Check deployment logs to verify

### Vercel:
- **Manual redeployment required**
- Go to **Deployments** tab → Click **⋯** → **Redeploy**

---

## 📚 Reference

- Render docs: https://render.com/docs/environment-variables
- Vercel docs: https://vercel.com/docs/concepts/projects/environment-variables
- Your backend: `render.yaml`
- Your frontend: `VERCEL_ENV_SETUP.md`

---

## 🆘 Troubleshooting

**Backend not connecting to Agentmail/Hyperspell?**
- Check Render logs: Dashboard → Service → **Logs** tab
- Verify API keys are correct
- Check API URLs are correct

**Frontend can't reach backend?**
- Verify `NEXT_PUBLIC_BACKEND_URL` in Vercel matches your Render backend URL
- Check CORS settings in backend
- Check Render service is running

**Database connection issues?**
- Verify `DATABASE_URL` in both Render and Vercel (they use the same database)
- Check database is accessible from both platforms

