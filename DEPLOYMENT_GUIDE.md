# Deployment Guide for QA Testing

This guide covers several hosting options for deploying the backend API for QA testing.

## 🚀 Recommended Options

### 1. **Render** (Recommended - Easiest & Free Tier)
**Best for:** Quick setup, free PostgreSQL, automatic deployments

**Pros:**
- Free tier available
- Built-in PostgreSQL database
- Automatic SSL certificates
- Easy environment variable management
- GitHub auto-deploy

**Cons:**
- Free tier spins down after 15 min inactivity (takes ~30s to wake up)
- Limited resources on free tier

**Setup Steps:**

1. **Create Render Account:**
   - Go to https://render.com
   - Sign up with GitHub

2. **Create PostgreSQL Database:**
   - Dashboard → New → PostgreSQL
   - Name: `agriapp-db`
   - Region: Choose closest to you
   - Plan: Free
   - Copy the **Internal Database URL** (you'll need this)

3. **Create Web Service:**
   - Dashboard → New → Web Service
   - Connect your GitHub repo
   - Settings:
     - **Name:** `agriapp-backend`
     - **Environment:** Python 3
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
     - **Plan:** Free

4. **Environment Variables:**
   Add these in Render dashboard:
   ```
   DATABASE_URL=<from PostgreSQL service>
   TWILIO_SID=<your-twilio-sid>
   TWILIO_AUTH_TOKEN=<your-twilio-token>
   OPENAI_API_KEY=<your-openai-key>
   SECRET_KEY=<generate-random-string>
   ADMIN_PHONES=9999999999,8888888888
   ```

5. **Run Migrations:**
   - After first deploy, go to Shell in Render
   - Run: `alembic upgrade head`

6. **Update Frontend Config:**
   - Get your Render URL (e.g., `https://agriapp-backend.onrender.com`)
   - Update `AgriApp/src/config.ts`:
     ```typescript
     export const API_BASE_URL = "https://agriapp-backend.onrender.com";
     ```

---

### 2. **Railway** (Great Alternative)
**Best for:** Simple deployment, good free tier

**Pros:**
- $5 free credit monthly
- PostgreSQL included
- Simple deployment
- Good documentation

**Setup Steps:**

1. **Create Railway Account:**
   - Go to https://railway.app
   - Sign up with GitHub

2. **Create New Project:**
   - New Project → Deploy from GitHub repo

3. **Add PostgreSQL:**
   - New → Database → PostgreSQL
   - Railway auto-creates `DATABASE_URL` env var

4. **Configure Service:**
   - Settings → Add start command:
     ```
     uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```

5. **Environment Variables:**
   Add in Variables tab:
   ```
   TWILIO_SID=<your-twilio-sid>
   TWILIO_AUTH_TOKEN=<your-twilio-token>
   OPENAI_API_KEY=<your-openai-key>
   SECRET_KEY=<generate-random-string>
   ADMIN_PHONES=9999999999,8888888888
   ```

6. **Run Migrations:**
   - Deployments → View Logs → Open Shell
   - Run: `alembic upgrade head`

---

### 3. **Fly.io** (Container-Based)
**Best for:** More control, Docker support

**Pros:**
- Free tier with 3 shared VMs
- Global edge deployment
- Docker support
- Good performance

**Setup Steps:**

1. **Install Fly CLI:**
   ```bash
   # Windows
   powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
   ```

2. **Login:**
   ```bash
   fly auth login
   ```

3. **Create Fly App:**
   ```bash
   fly launch
   ```

4. **Add PostgreSQL:**
   ```bash
   fly postgres create
   fly postgres attach <postgres-app-name> -a <your-app-name>
   ```

5. **Set Secrets:**
   ```bash
   fly secrets set TWILIO_SID=<your-sid>
   fly secrets set TWILIO_AUTH_TOKEN=<your-token>
   fly secrets set OPENAI_API_KEY=<your-key>
   fly secrets set SECRET_KEY=<random-string>
   fly secrets set ADMIN_PHONES=9999999999,8888888888
   ```

---

### 4. **DigitalOcean App Platform** (Paid but Reliable)
**Best for:** Production-like environment

**Pros:**
- Stable, no spin-down
- Good performance
- Easy scaling

**Cons:**
- $5/month minimum

**Setup:**
- Similar to Render but with paid tier
- Better for production QA

---

## 📝 Pre-Deployment Checklist

Before deploying, ensure:

- [ ] All environment variables are documented
- [ ] Database migrations are tested locally
- [ ] CORS is configured (currently allows all origins - tighten for production)
- [ ] `requirements.txt` is up to date
- [ ] No hardcoded secrets in code
- [ ] Health check endpoint works (`/health`)

---

## 🔧 Quick Setup Script for Render

Create `render.yaml` in your repo root:

```yaml
services:
  - type: web
    name: agriapp-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: agriapp-db
          property: connectionString
      - key: TWILIO_SID
        sync: false
      - key: TWILIO_AUTH_TOKEN
        sync: false
      - key: OPENAI_API_KEY
        sync: false
      - key: SECRET_KEY
        generateValue: true
      - key: ADMIN_PHONES
        value: 9999999999,8888888888

databases:
  - name: agriapp-db
    plan: free
```

---

## 🎯 Recommended for QA: **Render**

**Why Render:**
1. ✅ Free tier perfect for QA
2. ✅ Built-in PostgreSQL (no separate setup)
3. ✅ Automatic HTTPS
4. ✅ Easy environment variable management
5. ✅ GitHub auto-deploy
6. ✅ Simple migration process

**Trade-off:** Free tier spins down after inactivity (30s wake-up time)

---

## 📱 Frontend Configuration

After deploying backend, update frontend:

**File:** `AgriApp/src/config.ts`

```typescript
// For Render
export const API_BASE_URL = "https://your-app.onrender.com";

// For Railway
export const API_BASE_URL = "https://your-app.up.railway.app";

// For Fly.io
export const API_BASE_URL = "https://your-app.fly.dev";
```

---

## 🐛 Troubleshooting

### Database Connection Issues
- Check `DATABASE_URL` is set correctly
- Ensure migrations ran: `alembic upgrade head`
- Check database is accessible from web service

### CORS Errors
- Verify frontend URL is in `allow_origins` (currently `["*"]` for dev)
- For production, update in `app/main.py`:
  ```python
  allow_origins=["https://your-frontend-domain.com"]
  ```

### Environment Variables
- Double-check all required vars are set
- Use Render's environment variable validation

---

## 🚀 Next Steps

1. Choose a platform (recommend Render)
2. Deploy backend
3. Run migrations
4. Test API endpoints
5. Update frontend config
6. Test full flow

