# Railway.app Setup Guide
## Step-by-Step Environment Variables

---

## Step 1: Access Your Railway Project

1. Go to https://railway.app/dashboard
2. Click on your project (e.g., "dropshipping-ai")
3. Click on your service (the one running your app)

---

## Step 2: Add Environment Variables

### Method 1: Railway Dashboard (Easiest)

1. Click on the **"Variables"** tab
2. Click **"New Variable"**
3. Add each variable one by one:

### Method 2: Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to your project
railway link

# Set variables
railway variables set SHOPIFY_ACCESS_TOKEN=shpat_xxxxx
railway variables set AUTODS_API_KEY=xxxxx
# ... add more
```

---

## REQUIRED Variables (Add These First)

### Shopify (Required)
```
SHOPIFY_SHOP_URL=coaihome.myshopify.com
SHOPIFY_ACCESS_TOKEN=shpat_xxxxx_your_token_here
```

### AutoDS (Required)
```
AUTODS_API_KEY=your_autods_api_key_here
AUTODS_BASE_URL=https://api.autods.com
```

### OpenAI (Required)
```
AI_API_KEY=sk-your_openai_api_key_here
AI_PROVIDER=openai
AI_MODEL=gpt-4-turbo-preview
```

---

## Store Configuration (Recommended)

```
STORE_NICHE=home_organization
STORE_BRAND_NAME=CoaiHome
STORE_TARGET_COUNTRY=US
STORE_CURRENCY=USD
STORE_PRIMARY_COLOR=#4A6741
STORE_SECONDARY_COLOR=#FFFFFF
STORE_BASE_MARKUP=2.5
STORE_MIN_PRICE=15.0
STORE_MAX_PRICE=60.0
```

---

## AI Guardrails (Optional but Recommended)

```
AI_MAX_PRICE_CHANGE_PERCENT=10.0
AI_MIN_PROFIT_MARGIN=30.0
AI_MAX_PRODUCTS_PER_DAY=5
AI_MIN_PRODUCT_RATING=4.0
AI_MAX_SHIPPING_DAYS=14
```

---

## Notifications (Optional)

```
NOTIFY_EMAIL_ENABLED=false
NOTIFY_DAILY_SUMMARY_ENABLED=true
```

(Change to true and add email settings if you want notifications)

---

## System Settings (Optional)

```
SYSTEM_DEBUG=false
SYSTEM_LOG_LEVEL=INFO
```

---

## FULL List to Copy/Paste

Copy this entire block and add each line as a separate variable in Railway:

```bash
# REQUIRED - Shopify
SHOPIFY_SHOP_URL=coaihome.myshopify.com
SHOPIFY_ACCESS_TOKEN=REPLACE_WITH_YOUR_TOKEN

# REQUIRED - AutoDS
AUTODS_API_KEY=REPLACE_WITH_AUTODS_KEY
AUTODS_BASE_URL=https://api.autods.com
AUTODS_AUTO_FULFILLMENT_ENABLED=true
AUTODS_AUTO_PRICING_ENABLED=true
AUTODS_AUTO_IMPORT_ENABLED=true

# REQUIRED - OpenAI
AI_API_KEY=REPLACE_WITH_OPENAI_KEY
AI_PROVIDER=openai
AI_MODEL=gpt-4-turbo-preview
AI_TEMPERATURE=0.3
AI_MAX_PRICE_CHANGE_PERCENT=10.0
AI_MIN_PROFIT_MARGIN=30.0
AI_MAX_PRODUCTS_PER_DAY=5
AI_MIN_PRODUCT_RATING=4.0
AI_MAX_SHIPPING_DAYS=14

# Store Settings
STORE_NICHE=home_organization
STORE_BRAND_NAME=CoaiHome
STORE_TARGET_COUNTRY=US
STORE_CURRENCY=USD
STORE_PRIMARY_COLOR=#4A6741
STORE_SECONDARY_COLOR=#FFFFFF
STORE_BRAND_TONE=modern
STORE_BASE_MARKUP=2.5
STORE_MIN_PRICE=15.0
STORE_MAX_PRICE=60.0
STORE_PRICE_ROUNDING=0.99

# System
SYSTEM_DEBUG=false
SYSTEM_LOG_LEVEL=INFO
SYSTEM_DATABASE_URL=sqlite:///app/data/dropshipping_ai.db
SYSTEM_REQUIRE_APPROVAL_FOR_IMPORT=false
SYSTEM_REQUIRE_APPROVAL_FOR_PRICE_CHANGES=false

# Notifications (optional)
NOTIFY_DAILY_SUMMARY_ENABLED=true
NOTIFY_EMAIL_ENABLED=false
```

---

## Where to Get Each Value

| Variable | Where to Get It |
|----------|-----------------|
| `SHOPIFY_ACCESS_TOKEN` | Shopify Admin → Apps → Develop apps → Your app → Admin API access token |
| `AUTODS_API_KEY` | AutoDS.com → Settings → API |
| `AI_API_KEY` | OpenAI.com → API keys → Create new secret key |

---

## After Adding Variables

1. **Redeploy your app:**
   - Go to "Deployments" tab
   - Click "Redeploy" 
   - OR push a new commit to trigger redeploy

2. **Check logs:**
   - Click "Deployments" 
   - Click on latest deployment
   - Check "Logs" tab to see if app started successfully

3. **Test your app:**
   - Go to your Railway URL (shown in dashboard)
   - Should see your landing page

---

## Troubleshooting

**"App failed to start" in logs:**
→ Check that all REQUIRED variables are set
→ Check for typos in variable names

**"Invalid API token" errors:**
→ Shopify token should start with `shpat_`
→ OpenAI key should start with `sk-`
→ Make sure no extra spaces

**Can't find Variables tab:**
→ Make sure you clicked on your SERVICE (not just the project)
→ Look for tabs: Deployments, Variables, Settings, Logs

**Variables not saving:**
→ Click "Add" or press Enter after each variable
→ Make sure to redeploy after adding all variables

---

## Quick Check

After adding variables, you should see in Railway Variables tab:

```
SHOPIFY_SHOP_URL = coaihome.myshopify.com
SHOPIFY_ACCESS_TOKEN = shpat_xxxxxxxx
AUTODS_API_KEY = xxxxxxxx
AI_API_KEY = sk-xxxxxxxx
[plus all the other settings]
```

Then redeploy and you're live! 🚀
