# 🔧 Fix Vercel DATABASE_URL Error

## Error You're Seeing:
```
Environment variable not found: DATABASE_URL
```

## Solution: Create & Connect Vercel Postgres Database

### Step 1: Create Vercel Postgres Database

1. **Go to Vercel Dashboard**: https://vercel.com/dashboard
2. **Click on "Storage" tab** (top navigation)
3. **Click "Create Database"**
4. **Select "Postgres"**
5. **Configure database**:
   - **Database Name**: `propai-db` (or any name you prefer)
   - **Region**: Select same region as your deployment (e.g., Washington D.C. - iad1)
   - Click **"Create"**

### Step 2: Connect Database to Your Project

1. **After creating the database**, you'll see a prompt to connect it
2. **Select your project**: `prop-2assjk435` (your PropAI project)
3. **Click "Connect"**
4. **Vercel will automatically**:
   - Add `DATABASE_URL` environment variable
   - Add `POSTGRES_URL` environment variable
   - Add `POSTGRES_PRISMA_URL` environment variable
   - Add `POSTGRES_URL_NON_POOLING` environment variable

### Step 3: Redeploy Your Application

**Option A: Automatic Redeploy**
- Vercel should automatically trigger a redeploy after connecting the database

**Option B: Manual Redeploy**
1. Go to your project → Deployments
2. Click the three dots (...) on the latest deployment
3. Click "Redeploy"
4. Click "Redeploy" again to confirm

### Step 4: Run Database Migrations

After the redeploy completes, you need to run Prisma migrations to create the database tables.

**Option A: Using Vercel Dashboard**
1. Go to your project → Settings → Functions
2. Wait for deployment to complete
3. The `postinstall` script should run `prisma generate` automatically

**Option B: Using Vercel CLI (if migrations don't auto-run)**
```bash
# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login

# Link to your project
vercel link

# Pull environment variables (including DATABASE_URL)
vercel env pull .env.local

# Navigate to frontend directory
cd propai-frontend

# Run migrations
npx prisma migrate deploy

# Or if you need to push schema without migrations
npx prisma db push
```

### Step 5: Verify Database Connection

1. **Visit your site**: https://prop-2assjk435-michaelandreyeshchevs-projects.vercel.app/auth
2. **Try to sign up** with a new account
3. **Should work now!** ✅

---

## Alternative: Add DATABASE_URL Manually (If you have existing DB)

If you already have a PostgreSQL database elsewhere:

1. **Go to**: Vercel Dashboard → Your Project → Settings → Environment Variables
2. **Add new variable**:
   - **Name**: `DATABASE_URL`
   - **Value**: Your PostgreSQL connection string
     ```
     postgresql://USER:PASSWORD@HOST:PORT/DATABASE?schema=public
     ```
   - **Environment**: Production, Preview, Development
3. **Click "Save"**
4. **Redeploy** your application

---

## Verify Environment Variables

After connecting the database, verify the variables are set:

1. Go to: **Vercel Dashboard → Your Project → Settings → Environment Variables**
2. You should see:
   - ✅ `DATABASE_URL`
   - ✅ `POSTGRES_URL`
   - ✅ `POSTGRES_PRISMA_URL`
   - ✅ `POSTGRES_URL_NON_POOLING`
   - ✅ `NEXT_PUBLIC_BACKEND_URL` (if you added it)
   - ✅ `NEXT_PUBLIC_API_BASE` (if you added it)
   - ✅ `NEXTAUTH_URL` (if you added it)
   - ✅ `NEXTAUTH_SECRET` (if you added it)

---

## Expected Result

After fixing, you should be able to:
- ✅ Sign up for new accounts
- ✅ Log in successfully
- ✅ Create properties
- ✅ All database operations work

---

## Troubleshooting

### Issue: Database connected but still getting error

**Solution**: Redeploy the application
```bash
# In Vercel Dashboard
Deployments → Latest → Redeploy
```

### Issue: Migrations not running

**Solution**: Manually run migrations
```bash
cd propai-frontend
npx prisma migrate deploy
```

### Issue: "Cannot find module '@prisma/client'"

**Solution**: Regenerate Prisma Client
```bash
cd propai-frontend
npx prisma generate
```

Then redeploy.

---

## Quick Summary

1. ✅ Create Vercel Postgres database
2. ✅ Connect it to your project
3. ✅ Redeploy application
4. ✅ Database tables created automatically via migrations
5. ✅ Test signup/login

**You should be good to go!** 🚀

