# Quick Deploy to Render (5 Minutes)

## Step 1: Prepare Your Code

1. **Commit all changes to GitHub:**
   ```bash
   git add .
   git commit -m "Prepare for deployment"
   git push
   ```

## Step 2: Create Render Account

1. Go to https://render.com
2. Sign up with GitHub (recommended)
3. Authorize Render to access your repositories

## Step 3: Create PostgreSQL Database

1. In Render Dashboard, click **"New +"** → **"PostgreSQL"**
2. Settings:
   - **Name:** `agriapp-db`
   - **Database:** `agriapp` (auto-filled)
   - **User:** `agriapp_user` (auto-filled)
   - **Region:** Choose closest to you
   - **PostgreSQL Version:** Latest
   - **Plan:** Free
3. Click **"Create Database"**
4. Wait for it to provision (~2 minutes)
5. **Copy the Internal Database URL** (you'll need this)
   postgresql://agriapp_user:0RS8WBUF21eeb9ef4N8iGGy4xh3wsFRh@dpg-d59pqg3e5dus73emb6m0-a/agriapp_6swx

## Step 4: Create Web Service

1. In Render Dashboard, click **"New +"** → **"Web Service"**
2. Connect your GitHub repository
3. Select your repo and branch
4. Settings:
   - **Name:** `agriapp-backend`
   - **Environment:** `Python 3`
   - **Region:** Same as database
   - **Branch:** `main` (or your default branch)
   - **Root Directory:** (leave empty)
   - **Build Command:** `pip install -r requirements.txt && alembic upgrade head`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free
   
   > **💡 Tip:** The build command includes `alembic upgrade head` to automatically run migrations. This works on the free tier and means you can skip Step 5!
5. Click **"Advanced"** and add environment variables:

### Environment Variables:

```
DATABASE_URL=<paste Internal Database URL from Step 3>
TWILIO_SID=<your-twilio-account-sid>
TWILIO_AUTH_TOKEN=<your-twilio-auth-token>
TWILIO_PHONE=<your-twilio-phone-number>
TWILIO_VERIFY_SERVICE_SID=<your-twilio-verify-service-sid>
OPENAI_API_KEY=<your-openai-api-key>
SECRET_KEY=<generate-random-string-here>
ADMIN_PHONES=9999999999,8888888888
ENV=production
DEBUG=false
```

**To generate SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

6. Click **"Create Web Service"**

## Step 5: Run Database Migrations

### ✅ If you used the build command from Step 4:
**You can skip this step!** Migrations will run automatically during deployment. Just wait for the build to complete (~3-5 minutes) and check the logs to confirm migrations ran.

---

### 🔧 Alternative: Manual Migration (If needed)

If you didn't include migrations in the build command, or if you need to run them manually:

1. Wait for first deployment to complete (~3-5 minutes)
2. Go to your web service dashboard
3. Look for **"Shell"** tab (available on free tier - may be in the top menu or sidebar)
4. Click **"Open Shell"** or **"Connect"**
5. Once connected, run:
   ```bash
   alembic upgrade head
   ```
6. You should see: `INFO  [alembic.runtime.migration] Running upgrade ...`

**Note:** 
- The Shell tab is available on Render's free tier
- If you don't see it, try refreshing the page or check the "Settings" → "Shell" section
- Sometimes it takes a moment to appear after the first deployment

## Step 6: Test Your API

1. Get your Render URL: `https://agriapp-backend.onrender.com`
2. Test health endpoint:
   ```
   https://agriapp-backend.onrender.com/health
   ```
3. Should return: `{"status": "ok"}`

## Step 7: Update Frontend

1. Open `AgriApp/src/config.ts`
2. Update:
   ```typescript
   export const API_BASE_URL = "https://agriapp-backend.onrender.com";
   ```
3. Save and rebuild your app

## ✅ Done!

Your backend is now live and accessible from anywhere!

---

## 🔧 Troubleshooting

### Database Connection Error
- Check `DATABASE_URL` is set correctly
- Ensure you used **Internal Database URL** (not Public URL)
- Wait a few minutes after creating database

### Build Fails
- Check `requirements.txt` is correct
- Verify Python version in `runtime.txt` (3.11)
- Check build logs in Render dashboard

### Migrations Fail - "relation already exists"
- **This is fixed!** The migration now checks if tables exist before creating them
- If you still see this error, it means you're using an old migration file
- **Solution:** Pull the latest code with the updated migration, or manually delete the database and recreate it
- The app no longer auto-creates tables in production (only in local dev)

### CORS Errors
- Update `app/main.py` to allow your frontend domain:
  ```python
  allow_origins=["*"]  # Change to your frontend URL in production
  ```

---

## 📝 Notes

- **Free tier spins down** after 15 min inactivity (takes ~30s to wake up)
- **Database persists** even when web service is sleeping
- **Auto-deploys** on every git push to main branch
- **Logs** available in Render dashboard

---

## 🚀 Next Steps

1. Test all API endpoints
2. Update frontend to use new URL
3. Share URL with QA team
4. Monitor logs in Render dashboard

