# 🚀 Deploy Flask Backend to Render (Free)

Complete step-by-step guide to deploy your VidyAI Flask backend to Render for FREE.

---

## 📋 Prerequisites

Before you start, make sure you have:

- ✅ GitHub account
- ✅ Your code pushed to a GitHub repository
- ✅ All API keys ready:
  - Groq API key
  - Gemini API key
  - Supabase URL and key
  - Frontend URL (for CORS)

---

## Step 1: Prepare Your Code (2 minutes)

### 1.1 Create Procfile

Create a file named `Procfile` (no extension) in your `VidyAi_Flask` directory:

```
web: gunicorn app:app
```

This tells Render how to run your Flask app.

### 1.2 Update requirements.txt

Make sure `gunicorn` is in your `requirements.txt`. If not, add it:

```txt
gunicorn>=21.2.0
```

### 1.3 Update app.py (Optional but Recommended)

Update the port handling in `app.py` to work with Render:

```python
if __name__ == '__main__':
    # Get configuration from environment
    # Render uses PORT environment variable
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('PORT', os.getenv('FLASK_PORT', 5000)))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    
    logger.info(f"Starting VidyAI Flask Backend on {host}:{port}")
    logger.info(f"Debug mode: {debug}")
    logger.info(f"CORS origins: {cors_origins}")
    
    app.run(host=host, port=port, debug=debug)
```

**Note:** This is optional because Render uses gunicorn (from Procfile), not `app.run()`.

### 1.4 Commit and Push to GitHub

```bash
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

---

## Step 2: Sign Up for Render (1 minute)

1. Go to [render.com](https://render.com)
2. Click **"Get Started for Free"**
3. Sign up with **GitHub** (recommended - easiest way)
   - Click "Continue with GitHub"
   - Authorize Render to access your repositories
4. Verify your email if prompted

---

## Step 3: Create Web Service (5 minutes)

### 3.1 Start New Service

1. In Render dashboard, click **"New +"** button (top right)
2. Select **"Web Service"**
3. Click **"Connect account"** if you haven't connected GitHub yet
4. Select your GitHub repository
5. Click **"Connect"**

### 3.2 Configure Service

Fill in these settings:

**Basic Settings:**
- **Name:** `vidyai-flask-backend` (or any name you like)
- **Region:** Choose closest to you (e.g., `Oregon (US West)`)
- **Branch:** `main` (or your main branch name)
- **Root Directory:** `VidyAi_Flask` ⚠️ **Important!**
- **Environment:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn app:app`

**Advanced Settings (Optional):**
- **Auto-Deploy:** `Yes` (deploys automatically on git push)
- **Health Check Path:** `/api/health`

### 3.3 Add Environment Variables

Click **"Add Environment Variable"** and add each one:

```
GROQ_API_KEY
```
- Value: Your Groq API key

```
GEMINI_API_KEY
```
- Value: Your Gemini API key

```
SUPABASE_URL
```
- Value: Your Supabase project URL

```
SUPABASE_KEY
```
- Value: Your Supabase anon key

```
CORS_ORIGINS
```
- Value: `https://your-frontend.vercel.app,https://your-frontend.netlify.app`
- Add all your frontend URLs separated by commas
- No spaces, no trailing slashes

```
FLASK_ENV
```
- Value: `production`

```
LOG_LEVEL
```
- Value: `WARNING` (reduces log output)

```
SECRET_KEY
```
- Value: Generate a random secret key
- To generate: Run `python -c "import secrets; print(secrets.token_hex(32))"` in terminal

```
MAX_CONTENT_LENGTH
```
- Value: `104857600` (100MB in bytes)

**Important:** 
- Don't add quotes around values
- Don't add spaces
- Click "Save" after each variable

### 3.4 Create Service

1. Review all settings
2. Scroll down and click **"Create Web Service"**
3. Render will start building your app

---

## Step 4: Wait for Deployment (5-10 minutes)

### 4.1 Monitor Build

You'll see the build logs in real-time:
- Installing dependencies
- Building your app
- Starting the service

**First deployment takes 5-10 minutes.**

### 4.2 Check Status

- **Building** (yellow) = Still deploying
- **Live** (green) = Successfully deployed! ✅
- **Failed** (red) = Check logs for errors

### 4.3 Get Your URL

Once deployed, you'll see:
- **URL:** `https://vidyai-flask-backend.onrender.com`
- Copy this URL - you'll need it!

---

## Step 5: Test Your Deployment (2 minutes)

### 5.1 Test Health Endpoint

Open in browser or use curl:

```bash
curl https://your-app-name.onrender.com/api/health
```

Should return:
```json
{
  "status": "healthy",
  "service": "VidyAI Flask Backend",
  "version": "1.0.0"
}
```

### 5.2 Test from Frontend

Update your frontend's API URL:

```javascript
// In your frontend code
const API_URL = 'https://your-app-name.onrender.com';
```

Test a simple API call from your frontend.

---

## Step 6: Handle Cold Starts (Important!)

### The Problem

Render's free tier spins down your app after **15 minutes of inactivity**.
- First request after spin-down takes **~30 seconds** (cold start)
- Subsequent requests are fast

### The Solution: Keep-Alive Service

Use a free service to ping your app every 10 minutes:

**Option 1: UptimeRobot (Recommended)**

1. Sign up at [uptimerobot.com](https://uptimerobot.com) (free)
2. Click **"Add New Monitor"**
3. Configure:
   - **Monitor Type:** HTTP(s)
   - **Friendly Name:** VidyAI Flask Keep-Alive
   - **URL:** `https://your-app-name.onrender.com/api/health`
   - **Monitoring Interval:** 5 minutes
4. Click **"Create Monitor"**

**Option 2: cron-job.org**

1. Go to [cron-job.org](https://cron-job.org)
2. Create account (free)
3. Create new cron job:
   - **URL:** `https://your-app-name.onrender.com/api/health`
   - **Schedule:** Every 10 minutes
4. Save

This keeps your app "warm" and prevents cold starts.

---

## Step 7: Update Frontend (2 minutes)

### 7.1 Update API URL

In your frontend code, update the API base URL:

**Before:**
```javascript
const API_URL = 'http://localhost:5000';
```

**After:**
```javascript
const API_URL = 'https://your-app-name.onrender.com';
```

### 7.2 Update CORS Origins

Make sure your Render app's `CORS_ORIGINS` includes your frontend URL:
- Go to Render dashboard
- Click on your service
- Go to "Environment" tab
- Update `CORS_ORIGINS` if needed
- Save changes (auto-redeploys)

---

## ✅ Deployment Complete!

Your Flask backend is now live at:
```
https://your-app-name.onrender.com
```

---

## 🔧 Troubleshooting

### Build Fails

**Problem:** Build fails with dependency errors

**Solution:**
1. Check build logs in Render dashboard
2. Verify all packages in `requirements.txt` are correct
3. Test locally: `pip install -r requirements.txt`
4. Check Python version compatibility

### App Crashes on Start

**Problem:** Service shows "Failed" status

**Solution:**
1. Check logs in Render dashboard
2. Verify `Procfile` exists and is correct
3. Verify `gunicorn` is in `requirements.txt`
4. Test locally: `gunicorn app:app`

### CORS Errors

**Problem:** Frontend gets CORS errors

**Solution:**
1. Check `CORS_ORIGINS` environment variable
2. Make sure frontend URL is included (exact match)
3. No trailing slashes in URLs
4. Include `https://` protocol

### 502 Bad Gateway

**Problem:** Getting 502 errors

**Solution:**
1. App might be spinning up (wait 30 seconds)
2. Check if app is running in dashboard
3. Review logs for errors
4. Verify all environment variables are set

### Video Processing Timeout

**Problem:** Video processing takes too long

**Solution:**
1. Free tier has 512MB RAM - may be limited
2. Process smaller videos
3. Consider upgrading to paid plan for more resources
4. Optimize video processing code

### Module Not Found

**Problem:** `ModuleNotFoundError` in logs

**Solution:**
1. Check `requirements.txt` includes all dependencies
2. Verify build completed successfully
3. Check for typos in package names

---

## 📊 Monitoring Your App

### View Logs

1. Go to Render dashboard
2. Click on your service
3. Click **"Logs"** tab
4. See real-time logs

### Check Metrics

1. Click **"Metrics"** tab
2. See CPU, memory, and request metrics
3. Monitor for issues

### View Events

1. Click **"Events"** tab
2. See deployment history
3. Check for errors

---

## 🔄 Updating Your App

### Automatic Updates

If you enabled **Auto-Deploy:**
1. Push changes to GitHub
2. Render automatically detects changes
3. Rebuilds and redeploys automatically

### Manual Updates

1. Go to Render dashboard
2. Click on your service
3. Click **"Manual Deploy"**
4. Select branch and click **"Deploy"**

---

## 💰 Free Tier Limits

**What you get for FREE:**
- ✅ 750 hours/month (enough for 24/7 if single instance)
- ✅ 512MB RAM
- ✅ 0.1 CPU
- ✅ Free SSL certificate
- ✅ Automatic HTTPS
- ✅ GitHub integration

**Limitations:**
- ⚠️ Spins down after 15 minutes inactivity
- ⚠️ Limited RAM for heavy processing
- ⚠️ Slower CPU (0.1 CPU)

**For production with heavy usage, consider paid plans:**
- Starter: $7/month - More RAM, faster CPU
- Professional: $25/month - Even better performance

---

## 🎯 Best Practices

1. **Use Environment Variables**
   - Never commit API keys
   - Use Render's environment variables

2. **Monitor Logs**
   - Check logs regularly
   - Set up alerts if possible

3. **Keep App Warm**
   - Use UptimeRobot or similar
   - Prevents cold starts

4. **Optimize Code**
   - Reduce memory usage
   - Optimize video processing
   - Cache when possible

5. **Test Locally First**
   - Test with gunicorn: `gunicorn app:app`
   - Fix issues before deploying

---

## 📚 Additional Resources

- [Render Documentation](https://render.com/docs)
- [Render Community](https://community.render.com)
- [Gunicorn Documentation](https://gunicorn.org)

---

## 🆘 Need Help?

1. **Check Logs** - Most issues show in logs
2. **Render Docs** - Comprehensive documentation
3. **Community Forum** - Active community
4. **Test Locally** - Reproduce issues locally first

---

## ✅ Quick Checklist

Before deploying:
- [ ] Code pushed to GitHub
- [ ] `Procfile` created
- [ ] `gunicorn` in `requirements.txt`
- [ ] All API keys ready
- [ ] Frontend URL for CORS ready

After deploying:
- [ ] Health endpoint works
- [ ] Frontend can connect
- [ ] No CORS errors
- [ ] Keep-alive service set up
- [ ] Logs look good

---

**That's it! Your Flask backend is now live on Render! 🎉**

If you encounter any issues, check the troubleshooting section or Render's documentation.

