# Railway Deployment Fix

## Problem
Railway is running old code with SQLAlchemy 2.0 bug.

## Solution 1: Trigger Manual Deploy

1. Go to https://railway.app
2. Select your project: `coaihome-ai-system-production`
3. Click "Deploy" button (or three dots → "Redeploy")

## Solution 2: Railway CLI Redeploy

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to project
railway link

# Redeploy
railway up
```

## Verify After Deploy

```bash
curl https://coaihome-ai-system-production.up.railway.app/health
```

Should show: `"status":"healthy"` (not "degraded")

---

## OAuth "Music" Error - Common Causes

If you see an error page when visiting:
```
https://coaihome-ai-system-production.up.railway.app/auth/shopify/install?shop=coaihome.myshopify.com
```

### Fix 1: Update Shopify App URLs

Go to https://partners.shopify.com → Your App → Configuration

| Setting | Value |
|---------|-------|
| **App URL** | `https://coaihome-ai-system-production.up.railway.app` |
| **Allowed redirect URLs** | `https://coaihome-ai-system-production.up.railway.app/auth/shopify/callback` |

### Fix 2: Check API Credentials

Make sure these match in Railway Variables:
- `SHOPIFY_API_KEY` = App Client ID from Shopify Partners
- `SHOPIFY_API_SECRET` = App Secret from Shopify Partners

### Fix 3: Verify OAuth Scopes

In your Shopify App configuration, these scopes must be allowed:
```
read_products,write_products,read_orders,write_orders,read_inventory,write_inventory,read_customers
```

---

## Test OAuth Flow

1. Visit: `https://coaihome-ai-system-production.up.railway.app/auth/shopify/install?shop=coaihome.myshopify.com`
2. You should be redirected to Shopify login
3. After login, approve the app
4. You should redirect back to: `https://coaihome-ai-system-production.up.railway.app/dashboard?shop=coaihome.myshopify.com&installed=1`

---

## If Still Broken

Check Railway logs:
1. Go to https://railway.app
2. Click your project
3. Click "Deployments" tab
4. Click latest deployment
5. Check "Logs" for errors
