# Backend Deployment Guide

## Issue: Property Context Collection Failing

The property context collection feature is currently failing because the backend needs to be redeployed with the new Gemini integration and property context API endpoint.

## Current Status

- ✅ Frontend API endpoint created (`/api/property-context`)
- ✅ Database schema updated with PropertyContext model
- ✅ Backend API endpoint created (`/api/ai/collect-property-context`)
- ✅ Gemini integration implemented
- ❌ Backend not deployed with new changes

## Solution

### 1. Deploy Backend to Render

The backend needs to be redeployed to Render with the updated code that includes:

- Gemini 2.0 Flash integration
- Property context collection API endpoint
- Updated LLM service

### 2. Steps to Deploy

1. **Commit and push changes to your repository:**
   ```bash
   git add .
   git commit -m "Add Gemini integration and property context collection"
   git push origin main
   ```

2. **Render will automatically deploy** if you have auto-deploy enabled, or manually trigger deployment in the Render dashboard.

3. **Verify deployment** by checking:
   - Health endpoint: `https://prop-ai.onrender.com/health`
   - Should show `"text_model": "gemini-2.0-flash"` instead of `"llama-3.1-8b-instant"`

### 3. Enable Real AI Functionality

Once the backend is deployed, update the frontend API to use real AI:

1. Open `propai-frontend/app/api/property-context/route.ts`
2. Comment out the mock data section (lines 43-74)
3. Uncomment the backend call code (lines 76-103)
4. Deploy the frontend to Vercel

### 4. Test the Integration

After deployment, test the property context collection:

1. Go to a property detail page
2. Click on the "Property Context" tab
3. Click "Collect Property Context"
4. Verify that real AI-generated data is collected

## Current Workaround

The frontend is currently using mock data to demonstrate the UI functionality. The property context collection will work with sample data until the backend is properly deployed.

## Files Modified

### Backend Files:
- `minimal_backend.py` - Added Gemini integration and property context API
- `backend_modules/llm_service.py` - Updated to use Gemini
- `backend_modules/config.py` - Updated model configuration
- `render.yaml` - Updated environment variables

### Frontend Files:
- `propai-frontend/app/api/property-context/route.ts` - Property context API
- `propai-frontend/components/PropertyContext.tsx` - UI component
- `propai-frontend/components/PropertyDetail.tsx` - Integration
- `propai-frontend/prisma/schema.prisma` - Database schema

## Environment Variables

Make sure these are set in Render:

- `LLM_API_KEY`: `AIzaSyBG2RIEPLO_d37g4X9TWMRxJoG74jWO-g0`
- `LLM_MODEL`: `gemini-2.0-flash`
- `LLM_VISION_MODEL`: `gemini-2.0-flash`
- `LLM_URL`: `https://generativelanguage.googleapis.com/v1beta/models`
- `DATABASE_URL`: (from your ten8Link database)

## Expected Behavior After Deployment

1. Property context collection will use real Gemini AI
2. AI will analyze property addresses and provide comprehensive information
3. Data will be stored in the database
4. UI will display real property insights for prospective tenants
