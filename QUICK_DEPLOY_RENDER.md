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
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free
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

1. Wait for first deployment to complete (~3-5 minutes)
2. Go to your web service → **"Shell"** tab
3. Run:
   ```bash
   alembic upgrade head
   ```
4. You should see: `INFO  [alembic.runtime.migration] Running upgrade ...`

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

### Migrations Fail
- Ensure database is fully provisioned (green status)
- Check `DATABASE_URL` format is correct
- Try running migrations again in Shell

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

