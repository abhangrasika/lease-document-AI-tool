# 🔧 Fix Vercel Deployment with Supabase Database

## ✅ You're Using Supabase - Great Choice!

You have all the connection details. Now let's configure Vercel to use your Supabase database.

---

## 🚀 Quick Fix: Add Environment Variables to Vercel

### Step 1: Go to Vercel Environment Variables

1. **Visit**: https://vercel.com/dashboard
2. **Select your project**: `prop-2assjk435`
3. **Click**: Settings → Environment Variables

### Step 2: Add Database URL

**CRITICAL**: Prisma needs `DATABASE_URL` to connect to the database.

Add this variable:

**Name**: `DATABASE_URL`  
**Value**: 
```
postgres://postgres.yuqjgruqrhavdzevkeka:IQGQfRNotRQHS4ak@aws-1-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require&pgbouncer=true
```

**Environment**: Check all three:
- ✅ Production
- ✅ Preview  
- ✅ Development

Click **"Save"**

### Step 3: Add All Other Environment Variables (Optional but Recommended)

Add these additional variables for completeness:

1. **POSTGRES_URL**
   ```
   postgres://postgres.yuqjgruqrhavdzevkeka:IQGQfRNotRQHS4ak@aws-1-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require&supa=base-pooler.x
   ```

2. **POSTGRES_PRISMA_URL**
   ```
   postgres://postgres.yuqjgruqrhavdzevkeka:IQGQfRNotRQHS4ak@aws-1-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require&pgbouncer=true
   ```

3. **POSTGRES_USER**
   ```
   postgres
   ```

4. **POSTGRES_PASSWORD**
   ```
   IQGQfRNotRQHS4ak
   ```

5. **POSTGRES_HOST**
   ```
   db.yuqjgruqrhavdzevkeka.supabase.co
   ```

6. **POSTGRES_DATABASE**
   ```
   postgres
   ```

7. **NEXT_PUBLIC_SUPABASE_ANON_KEY**
   ```
   YOUR_SUPABASE_JWT_SECRET_HERE
   ```

8. **SUPABASE_JWT_SECRET**
   ```
   VJDwd5iTfnw3EXLKKnSGVXP0V3mOl3+mxrvs2ruNQBstU1aFmcI55tLukWCCdaarYmRmCgWWXZM8XywHqe4lLg==
   ```

**For each variable**:
- Name: (variable name)
- Value: (the value)
- Environment: Check all three (Production, Preview, Development)
- Click "Save"

### Step 4: Add Backend & Auth Environment Variables

If you haven't already, add these as well:

9. **NEXT_PUBLIC_BACKEND_URL**
   ```
   https://your-backend.onrender.com
   ```
   (Replace with your actual Render backend URL when you deploy it)

10. **NEXT_PUBLIC_API_BASE**
   ```
   https://your-backend.onrender.com
   ```
   (Same as above)

11. **NEXTAUTH_URL**
   ```
   https://prop-2assjk435-michaelandreyeshchevs-projects.vercel.app
   ```

12. **NEXTAUTH_SECRET**
   ```
   Generate a random 32-character string
   ```
   
   **Generate it with**:
   ```bash
   # Mac/Linux
   openssl rand -base64 32
   
   # Windows PowerShell
   [Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Minimum 0 -Maximum 256 }))
   ```

### Step 5: Redeploy Your Application

After adding all environment variables:

1. **Go to**: Deployments tab
2. **Click** the three dots (...) on the latest deployment
3. **Click**: "Redeploy"
4. **Click**: "Redeploy" again to confirm

---

## 🗄️ Step 6: Run Database Migrations

After redeployment, you need to create the database tables in Supabase.

### Option A: Using Vercel CLI (Recommended)

```bash
# Install Vercel CLI (if not installed)
npm i -g vercel

# Login to Vercel
vercel login

# Link to your project (in your project root)
vercel link

# Pull environment variables
vercel env pull .env.local

# Navigate to frontend directory
cd propai-frontend

# Run migrations to create tables
npx prisma migrate deploy

# Or if migrations folder doesn't exist, push schema directly
npx prisma db push
```

### Option B: Create Migration Manually

If you want to create proper migrations:

```bash
# In propai-frontend directory
cd propai-frontend

# Create a new migration
npx prisma migrate dev --name init

# This will:
# 1. Create migration files
# 2. Apply them to your database
# 3. Generate Prisma Client

# Then deploy to production
npx prisma migrate deploy
```

---

## ✅ Verify Setup

### 1. Check Vercel Environment Variables

Go to: **Settings → Environment Variables**

You should see:
- ✅ `DATABASE_URL` 
- ✅ `POSTGRES_PRISMA_URL`
- ✅ `NEXTAUTH_URL`
- ✅ `NEXTAUTH_SECRET`
- ✅ (Optional) Other POSTGRES_* variables

### 2. Check Supabase Tables

1. Go to: https://supabase.com/dashboard
2. Open your project: `yuqjgruqrhavdzevkeka`
3. Go to: **Table Editor**
4. You should see tables:
   - `User`
   - `Account`
   - `Session`
   - `VerificationToken`
   - `BetaApplication`
   - `Property`
   - `Lease`
   - `PropertyContext`

### 3. Test Your Application

1. Visit: https://prop-2assjk435-michaelandreyeshchevs-projects.vercel.app/auth
2. Try to **sign up** with:
   - Email: test@example.com
   - Password: SecurePassword123!
3. Should work now! ✅

---

## 🔍 Troubleshooting

### Issue: Still getting "DATABASE_URL not found"

**Solution**: 
1. Verify `DATABASE_URL` is set in Vercel
2. Redeploy the application
3. Check deployment logs

### Issue: "Can't reach database server"

**Solution**: 
1. Check your Supabase project is running
2. Verify the connection string is correct
3. Make sure `sslmode=require` is in the URL

### Issue: "Table does not exist"

**Solution**: Run migrations
```bash
cd propai-frontend
npx prisma migrate deploy
# or
npx prisma db push
```

### Issue: Build fails with Prisma error

**Solution**: Ensure `postinstall` script in `package.json`:
```json
{
  "scripts": {
    "postinstall": "prisma generate"
  }
}
```

---

## 📋 Complete Environment Variables Checklist

Your Vercel project should have these environment variables:

### Database (Supabase):
- ✅ `DATABASE_URL` ← **MOST IMPORTANT**
- ✅ `POSTGRES_URL`
- ✅ `POSTGRES_PRISMA_URL`
- ✅ `POSTGRES_USER`
- ✅ `POSTGRES_PASSWORD`
- ✅ `POSTGRES_HOST`
- ✅ `POSTGRES_DATABASE`
- ✅ `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- ✅ `SUPABASE_JWT_SECRET`

### Authentication:
- ✅ `NEXTAUTH_URL`
- ✅ `NEXTAUTH_SECRET`

### Backend (when you deploy to Render):
- ⏳ `NEXT_PUBLIC_BACKEND_URL` (add after deploying backend)
- ⏳ `NEXT_PUBLIC_API_BASE` (add after deploying backend)

---

## 🎯 Next Steps

After fixing the database connection:

1. ✅ Test signup/login
2. ✅ Deploy backend to Render (follow DEPLOYMENT_QUICK_START.md)
3. ✅ Add backend URL to Vercel environment variables
4. ✅ Test full system (frontend + backend + Supabase)

---

## 🔐 Security Note

⚠️ **IMPORTANT**: The database credentials you shared are now public. After setting up:

1. **Rotate your Supabase password**:
   - Go to: Supabase Dashboard → Settings → Database
   - Click "Reset database password"
   - Update `DATABASE_URL` in Vercel with new password

2. **Rotate JWT Secret** (if concerned):
   - Go to: Supabase Dashboard → Settings → API
   - Generate new JWT secret
   - Update in Vercel

---

## ✅ Summary

1. Add `DATABASE_URL` to Vercel environment variables
2. Add all other Supabase variables
3. Redeploy application
4. Run `npx prisma migrate deploy` or `npx prisma db push`
5. Test signup/login
6. Rotate credentials for security

**You should be live in 5-10 minutes!** 🚀

