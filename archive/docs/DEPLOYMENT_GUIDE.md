# 🚀 PropAI Production Deployment Guide

## Backend Deployment (Render)

### 1. **Prepare Repository**
Make sure your repository has these files:
- `unified_backend.py` - Main backend application
- `start_backend.py` - Startup script
- `migrate_database.py` - Database migration script
- `requirements.txt` - Python dependencies
- `render.yaml` - Render configuration
- `Procfile` - Process definition
- `runtime.txt` - Python version

### 2. **Deploy to Render**

1. **Connect Repository**:
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository

2. **Configure Service**:
   - **Name**: `propai-backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt && python migrate_database.py`
   - **Start Command**: `python start_backend.py`

3. **Set Environment Variables**:
   ```
   HOST=0.0.0.0
   PORT=8000
   RELOAD=false
   LLM_API_KEY=your_groq_api_key_here
   LLM_MODEL=llama-3.1-8b-instant
   LLM_VISION_MODEL=meta-llama/llama-4-maverick-17b-128e-instruct
   LLM_URL=https://api.groq.com/openai/v1/chat/completions
   TWILIO_FROM_NUMBER=+1234567890
   USE_FAKE_TWILIO=0
   FRONTEND_ORIGIN=https://prop-ai-three.vercel.app
   ```

4. **Add Database**:
   - Go to "New +" → "PostgreSQL"
   - Name: `propai-db`
   - Plan: Free
   - Copy the connection string to `DATABASE_URL`

5. **Deploy**:
   - Click "Create Web Service"
   - Wait for deployment to complete
   - Note your service URL (e.g., `https://propai-backend.onrender.com`)

### 3. **Test Backend**
```bash
# Health check
curl https://your-backend-url.onrender.com/health

# Test AI chat
curl -X POST https://your-backend-url.onrender.com/pm_chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, test message",
    "context": {
      "tenant_name": "Test User",
      "unit": "1A",
      "address": "123 Test St"
    }
  }'
```

## Frontend Deployment (Vercel)

### 1. **Update Frontend Configuration**

Update `propai-frontend/.env.local`:
```env
NEXT_PUBLIC_BACKEND_URL=https://your-backend-url.onrender.com
NEXT_PUBLIC_API_BASE=https://your-backend-url.onrender.com
```

### 2. **Deploy to Vercel**

1. **Connect Repository**:
   - Go to [Vercel Dashboard](https://vercel.com/dashboard)
   - Click "New Project"
   - Import your GitHub repository
   - Select the `propai-frontend` folder

2. **Configure Build**:
   - **Framework Preset**: Next.js
   - **Root Directory**: `propai-frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`

3. **Set Environment Variables**:
   ```
   NEXT_PUBLIC_BACKEND_URL=https://your-backend-url.onrender.com
   NEXT_PUBLIC_API_BASE=https://your-backend-url.onrender.com
   ```

4. **Deploy**:
   - Click "Deploy"
   - Wait for deployment to complete
   - Note your frontend URL (e.g., `https://prop-ai-three.vercel.app`)

### 3. **Update Backend CORS**

After getting your Vercel URL, update the backend CORS settings:

1. Go to Render Dashboard → Your Service → Environment
2. Update `FRONTEND_ORIGIN` to your Vercel URL
3. Redeploy the service

## Twilio Configuration

### 1. **Set Up Twilio Webhook**

1. Go to [Twilio Console](https://console.twilio.com)
2. Navigate to Phone Numbers → Manage → Active Numbers
3. Click on your Twilio number
4. Set Webhook URL to: `https://your-backend-url.onrender.com/sms`
5. Set HTTP method to: `POST`
6. Save configuration

### 2. **Test SMS Integration**

Send a test SMS to your Twilio number:
```
Hello, my sink is leaking in unit 3A
```

Check the backend logs to see if the message was received and classified.

## Environment Variables Summary

### Backend (Render)
```env
# Server Configuration
HOST=0.0.0.0
PORT=8000
RELOAD=false

# Database
DATABASE_URL=postgresql://user:pass@host:port/dbname

# LLM Configuration
LLM_API_KEY=your_groq_api_key
LLM_MODEL=llama-3.1-8b-instant
LLM_VISION_MODEL=meta-llama/llama-4-maverick-17b-128e-instruct
LLM_URL=https://api.groq.com/openai/v1/chat/completions

# Twilio Configuration
TWILIO_FROM_NUMBER=+1234567890
USE_FAKE_TWILIO=0

# CORS Configuration
FRONTEND_ORIGIN=https://your-frontend-url.vercel.app
```

### Frontend (Vercel)
```env
NEXT_PUBLIC_BACKEND_URL=https://your-backend-url.onrender.com
NEXT_PUBLIC_API_BASE=https://your-backend-url.onrender.com
```

## Testing Production Deployment

### 1. **Backend Health Check**
```bash
curl https://your-backend-url.onrender.com/health
```

### 2. **Test AI Chat**
```bash
curl -X POST https://your-backend-url.onrender.com/pm_chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What should I do about a leaky faucet?",
    "context": {
      "tenant_name": "John Doe",
      "unit": "3A",
      "address": "123 Main St",
      "hotline": "+1-555-0100"
    }
  }'
```

### 3. **Test SMS Webhook**
```bash
curl -X POST https://your-backend-url.onrender.com/sms \
  -d "From=+1234567890" \
  -d "To=+0987654321" \
  -d "Body=Hello, this is a test message"
```

### 4. **Test Frontend**
- Visit your Vercel URL
- Try the AI chat interface
- Check if messages are being stored

## Monitoring & Maintenance

### 1. **Backend Logs**
- Go to Render Dashboard → Your Service → Logs
- Monitor for errors and performance

### 2. **Database Monitoring**
- Go to Render Dashboard → Your Database
- Monitor connection count and performance

### 3. **Frontend Analytics**
- Use Vercel Analytics to monitor frontend performance
- Check for build errors in Vercel Dashboard

## Troubleshooting

### Common Issues

1. **Backend Won't Start**
   - Check environment variables
   - Verify database connection
   - Check build logs

2. **Database Connection Error**
   - Verify `DATABASE_URL` format
   - Check database is running
   - Run migration script manually

3. **CORS Errors**
   - Update `FRONTEND_ORIGIN` in backend
   - Check frontend `NEXT_PUBLIC_BACKEND_URL`

4. **Twilio Webhook Not Working**
   - Verify webhook URL is accessible
   - Check Twilio configuration
   - Test with curl first

### Support
- Render: [Render Support](https://render.com/docs)
- Vercel: [Vercel Support](https://vercel.com/docs)
- Twilio: [Twilio Support](https://support.twilio.com)

## Security Considerations

1. **Environment Variables**: Never commit API keys to repository
2. **CORS**: Only allow your frontend domain
3. **Database**: Use strong passwords and SSL connections
4. **API Keys**: Rotate regularly and monitor usage

## Cost Optimization

1. **Render Free Tier**: 750 hours/month
2. **Vercel Free Tier**: Unlimited static sites
3. **Database**: Monitor usage to avoid overages
4. **LLM API**: Monitor usage and set limits

Your PropAI system is now ready for production! 🎉
