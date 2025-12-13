# ⚡ Quick Start: Deploy to Render in 5 Minutes

## Prerequisites
- ✅ Code pushed to GitHub
- ✅ API keys ready

---

## Step 1: Prepare Files (Already Done!)

I've created:
- ✅ `Procfile` - Tells Render how to run your app
- ✅ `requirements.txt` - Updated with gunicorn
- ✅ `app.py` - Updated to handle PORT variable

**Just commit and push:**
```bash
git add .
git commit -m "Ready for Render"
git push
```

---

## Step 2: Deploy on Render

### 2.1 Sign Up
1. Go to [render.com](https://render.com)
2. Click **"Get Started for Free"**
3. Sign up with **GitHub**

### 2.2 Create Web Service
1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repo
3. Select your repository

### 2.3 Configure

**Settings:**
- **Name:** `vidyai-flask-backend`
- **Root Directory:** `VidyAi_Flask` ⚠️
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn app:app`

**Environment Variables:**
Add these (click "Add Environment Variable" for each):

```
GROQ_API_KEY = your_key
GEMINI_API_KEY = your_key
SUPABASE_URL = your_url
SUPABASE_KEY = your_key
CORS_ORIGINS = https://your-frontend.vercel.app
FLASK_ENV = production
LOG_LEVEL = WARNING
SECRET_KEY = (generate with: python -c "import secrets; print(secrets.token_hex(32))")
```

### 2.4 Deploy
1. Click **"Create Web Service"**
2. Wait 5-10 minutes
3. Your app will be live!

---

## Step 3: Test

```bash
curl https://your-app-name.onrender.com/api/health
```

Should return: `{"status": "healthy", ...}`

---

## Step 4: Keep It Warm (Prevent Cold Starts)

Use [UptimeRobot](https://uptimerobot.com) (free):
1. Sign up
2. Add monitor:
   - URL: `https://your-app-name.onrender.com/api/health`
   - Interval: 5 minutes
3. Done! App stays warm

---

## Step 5: Update Frontend

Change API URL in your frontend:
```javascript
const API_URL = 'https://your-app-name.onrender.com';
```

---

## ✅ Done!

Your backend is live! 🎉

**Full guide:** See [RENDER_DEPLOYMENT.md](./RENDER_DEPLOYMENT.md) for detailed instructions.

