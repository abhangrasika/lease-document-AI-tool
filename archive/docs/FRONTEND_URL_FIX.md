# Frontend URL Connection Fix

## Issue
Backend is trying to connect to `http://localhost:3000` but the frontend is deployed at `https://ten8link.vercel.app`.

Error message:
```
⚠️ Error saving application to database: Connection failed to http://localhost:3000
   Check if frontend is running and FRONTEND_ORIGIN is correct
```

## Solution

### If Backend is Running on Render (Production)

The `render.yaml` file has been updated with the correct URL. You need to:

1. **Update Render Dashboard** (if the yaml hasn't been deployed yet):
   - Go to https://dashboard.render.com
   - Select your `propai-backend` service
   - Go to **Environment** tab
   - Find `FRONTEND_ORIGIN` variable
   - Update it to: `https://ten8link.vercel.app`
   - Click **Save Changes**
   - Render will automatically redeploy

2. **OR push the updated render.yaml**:
   ```bash
   git add render.yaml
   git commit -m "Update FRONTEND_ORIGIN to ten8link.vercel.app"
   git push
   ```
   This will trigger a new deployment with the correct URL.

### If Backend is Running Locally (Development)

Set the environment variable before starting the backend:

**Option 1: Export in your shell**
```bash
export FRONTEND_ORIGIN=https://ten8link.vercel.app
python start_backend.py
```

**Option 2: Create a `.env` file in the root directory**
```bash
# .env (in root directory)
FRONTEND_ORIGIN=https://ten8link.vercel.app
APPLICATION_SERVICE_TOKEN=your_service_token_here
```

Then make sure your backend loads the `.env` file. You may need to install `python-dotenv`:
```bash
pip install python-dotenv
```

And add to your `start_backend.py` or `minimal_backend.py`:
```python
from dotenv import load_dotenv
load_dotenv()
```

**Option 3: Inline with command**
```bash
FRONTEND_ORIGIN=https://ten8link.vercel.app python start_backend.py
```

## Verify the Fix

After setting the environment variable, restart your backend and check the logs. You should see:
- ✅ Application saved to database: [application_id]
- No more connection errors to localhost:3000

## Additional Configuration

Also make sure `APPLICATION_SERVICE_TOKEN` is set correctly, as the backend needs this to authenticate with the frontend's internal API endpoint (`/api/applications/internal`).

To find or set this token, check:
- Vercel Dashboard → Your Project → Environment Variables → `APPLICATION_SERVICE_TOKEN`
- Make sure the same token is set in Render Dashboard as well

