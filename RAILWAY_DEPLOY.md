# Deploy to Railway - Step by Step

## Method 1: Deploy from GitHub (Recommended - Easiest)

### Step 1: Push Code to GitHub

Open terminal/command prompt in your `dropshipping_ai_system` folder:

```bash
# 1. Initialize git (if not done)
git init

# 2. Add all files
git add .

# 3. Commit
git commit -m "Initial commit - CoaiHome AI system"

# 4. Create GitHub repo (go to github.com/new)
#    Name: coaihome-ai
#    Public or Private
#    DON'T initialize with README

# 5. Connect to GitHub (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/coaihome-ai.git

# 6. Push
git branch -M main
git push -u origin main
```

### Step 2: Deploy on Railway

1. Go to https://railway.app
2. Click **"Start a New Project"**
3. Click **"Deploy from GitHub repo"**
4. Connect your GitHub account (if not already)
5. Select your repo: **coaihome-ai**
6. Click **"Add Variables"**
7. Add your environment variables (see below)
8. Click **"Deploy"**
9. Done! Railway will give you a URL

---

## Method 2: Deploy with Railway CLI

### Install Railway CLI

**Windows (PowerShell):**
```powershell
npm install -g @railway/cli
```

**Mac/Linux:**
```bash
npm install -g @railway/cli
```

### Login and Deploy

```bash
# Login to Railway
railway login

# Go to your project folder
cd dropshipping_ai_system

# Initialize Railway project
railway init

# Set all environment variables
railway variables set SHOPIFY_SHOP_URL=coaihome.myshopify.com
railway variables set SHOPIFY_ACCESS_TOKEN=shpat_xxxxx
railway variables set AUTODS_API_KEY=xxxxx
railway variables set AI_API_KEY=sk-xxxxx
railway variables set STORE_BRAND_NAME=CoaiHome
railway variables set STORE_NICHE=home_organization

# Deploy
railway up

# Open in browser
railway open
```

---

## Environment Variables to Add

After creating project, click **"Variables"** tab and add:

### Required:
```
SHOPIFY_SHOP_URL = coaihome.myshopify.com
SHOPIFY_ACCESS_TOKEN = shpat_xxxxx (your actual token)
AUTODS_API_KEY = your_autods_key
AI_API_KEY = sk-your_openai_key
```

### Recommended:
```
STORE_BRAND_NAME = CoaiHome
STORE_NICHE = home_organization
STORE_TARGET_COUNTRY = US
SYSTEM_DEBUG = false
```

---

## Verify Deployment

### Check Logs:
1. In Railway dashboard, click your project
2. Click **"Deployments"** tab
3. Click on the latest deployment
4. Check **"Logs"** - should see "Application startup complete"

### Test Your App:
1. Railway gives you a URL like:
   ```
   https://coaihome-ai-production.up.railway.app
   ```
2. Visit that URL in browser
3. Should see your landing page

---

## Common Issues

### "Build failed"
→ Check Python version is set to 3.11 in railway.json

### "App crashed"
→ Check all environment variables are set
→ Check logs for specific error

### "Can't find variables"
→ Click on your SERVICE (not the project overview)
→ Then click Variables tab

### "Domain not working"
→ Wait 2-3 minutes for DNS to propagate
→ Or click "Settings" → "Domains" to add custom domain

---

## Your Railway URL

Once deployed, your URL will be something like:
```
https://coaihome-ai-production.up.railway.app
```

Use this URL for:
- Shopify App URL field
- Sharing your dashboard
- Connecting to your store

---

## Need to Redeploy?

### After code changes:
```bash
# Push to GitHub
git add .
git commit -m "Update"
git push

# Railway auto-deploys!
```

### Or manual redeploy:
1. Railway dashboard → Deployments
2. Click **"Redeploy"**

---

## Summary

| Method | Best For | Time |
|--------|----------|------|
| GitHub deploy | Everyone | 5 min |
| CLI deploy | Developers | 3 min |

**Easiest way:** Push to GitHub → Connect in Railway dashboard → Add variables → Deploy!

---

Let's GO! 🚀
