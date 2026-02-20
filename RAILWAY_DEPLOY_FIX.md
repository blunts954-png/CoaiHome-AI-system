# 🚂 Railway Deployment Fix

## Problem
Your Railway deployment is failing because:
1. ❌ Environment variables not set
2. ❌ Database not initialized
3. ❌ Error handling missing

## Solution

### Step 1: Set Environment Variables on Railway

Go to your Railway dashboard:
https://railway.com/project/a61c5425-9ee6-40e5-b8f2-bc84c03ee90b

Click on **Variables** tab, then add these:

```
SHOPIFY_SHOP_URL=coaihome.myshopify.com
SHOPIFY_ACCESS_TOKEN=shpat_your_actual_token_here
AI_API_KEY=sk-proj_your_actual_key_here
STORE_NICHE=home organization
STORE_BRAND_NAME=CoaiHome
```

**Get your tokens:**
- **SHOPIFY_ACCESS_TOKEN**: Shopify Admin → Settings → Apps → Develop apps → Create app → Install → Reveal token
- **AI_API_KEY**: openai.com → API keys → Create new key

### Step 2: Push Latest Code to GitHub

```bash
cd "c:sers\blunt\Desktop\programs\dropshipping one\dropshipping_ai_system"

git add .
git commit -m "Fix Railway deployment: database, error handling, env vars"
git push origin main
```

### Step 3: Redeploy on Railway

1. Railway will auto-deploy when you push to GitHub
2. Or click **Deploy** in the Railway dashboard
3. Check the **Deploy Logs** for errors

### Step 4: Check Health

Visit:
```
https://your-app-url.railway.app/health
```

Should return:
```json
{
  "status": "healthy",
  "database": "ok",
  "shopify_configured": true
}
```

---

## Testing the Buttons

Once deployed, test these endpoints:

### 1. Health Check
```
GET https://your-app-url.railway.app/health
```

### 2. System Status
```
GET https://your-app-url.railway.app/api/system/status
```

### 3. Research Products (No API needed!)
```
POST https://your-app-url.railway.app/api/research/no-api?niche=home%20organization
```

### 4. Generate TikTok Content
```
POST https://your-app-url.railway.app/api/tiktok/generate-content
```

---

## Fixing "Internal Server Error"

If you still see errors, check Railway logs:

1. Go to Railway dashboard
2. Click your service
3. Click **Logs** tab
4. Look for red error messages

Common fixes:

### Error: "No module named 'xxx'"
Add to `requirements.txt` and redeploy

### Error: "database locked" or "table doesn't exist"
The database should auto-initialize now with `init_and_run.py`

### Error: "SHOPIFY_SHOP_URL not set"
Add the environment variable in Railway dashboard

---

## Quick Fix Script

Run this to push everything:

```bash
cd "c:sers\blunt\Desktop\programs\dropshipping one\dropshipping_ai_system"

echo "Adding files..."
git add -A

echo "Committing..."
git commit -m "Fix Railway deployment with proper error handling and DB init"

echo "Pushing to GitHub..."
git push origin main

echo "Done! Check Railway dashboard for deployment."
```

---

## Making Shopify OAuth Work on Railway

For the "Connect Shopify" button to work on Railway:

1. Add to Railway Variables:
```
SHOPIFY_API_KEY=b2b850c00fb1ce070799b227e8549aa7
SHOPIFY_API_SECRET=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
SHOPIFY_APP_URL=https://your-app-url.railway.app
```

2. In Shopify Partner Dashboard:
   - Go to your app
   - Click **App setup**
   - Add allowed redirect URL:
   ```
   https://your-app-url.railway.app/auth/shopify/callback
   ```

3. Now users can click "Connect Shopify" and OAuth will work!

---

## Need Help?

Check these URLs on your deployed app:

| URL | What It Shows |
|-----|---------------|
| `/health` | System health status |
| `/api/system/status` | Configuration status |
| `/api/stats` | Dashboard statistics |
| `/` | Your control dashboard |

If `/health` shows `"status": "healthy"`, you're good to go! 🎉
