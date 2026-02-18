# Shopify App Setup - Exact Fields to Fill

## Here's what to enter in each field:

### ✅ App Name (Already filled)
```
CoaiHome Automation
```

### ✅ App URL
**Enter your deployed Railway/Render URL:**
```
https://your-app.railway.app
```

**OR** if you don't have the URL yet, use:
```
https://coaihome-automation.herokuapp.com
```

*(This isn't critical - it's just a reference URL)*

### ✅ Embed app in Shopify admin
**UNCHECK this box** ❌

Your app is a backend automation service, not something that needs to be embedded in Shopify's admin panel.

### ✅ Preferences URL (Optional)
**Leave EMPTY**

### ✅ Webhooks API Version
**Keep as:** `2026-01` (or latest available)

### ✅ Scopes (IMPORTANT!)
Click "Select scopes" and check these:

**Required scopes:**
- ✅ `read_products`
- ✅ `write_products`
- ✅ `read_orders`
- ✅ `write_orders`
- ✅ `read_inventory`
- ✅ `write_inventory`

**Recommended scopes:**
- ✅ `read_customers`
- ✅ `read_content` (for blog/pages)
- ✅ `read_analytics`

**Full list to select:**
```
read_products, write_products, read_orders, write_orders, 
read_inventory, write_inventory, read_customers, read_content
```

### ✅ Optional scopes
**Leave EMPTY** (or add any extras you want)

### ✅ Use legacy install flow
**UNCHECK** ❌

### ✅ Redirect URLs
**Leave EMPTY**

Your app doesn't use OAuth redirects - it's a backend service.

---

## After Filling Everything:

1. Click **"Save"** at top right
2. Click **"Install app"**
3. You'll see a screen with:
   - **Admin API access token** (starts with `shpat_`)
   - **API key**
   - **API secret key**

4. **COPY the Admin API access token immediately!**
   - It only shows ONCE
   - Save it in a secure place
   - You'll add it to your Railway/Render environment variables

---

## Where to Add the Token

Go to your deployment dashboard (Railway or Render):

**Add environment variable:**
```
SHOPIFY_ACCESS_TOKEN=shpat_xxxxxxxxxxxxxxxx
```

---

## Quick Reference

| Field | What to Enter |
|-------|---------------|
| App name | CoaiHome Automation ✅ |
| App URL | Your Railway URL or placeholder |
| Embed in admin | UNCHECK ❌ |
| Preferences URL | Leave empty |
| Scopes | Click "Select scopes", check all product/order/inventory permissions |
| Redirect URLs | Leave empty |
| Legacy install | UNCHECK ❌ |

---

## Screenshots of What to Select

### Scopes to Enable:
```
☑ read_products
☑ write_products
☑ read_orders
☑ write_orders
☑ read_inventory
☑ write_inventory
☑ read_customers
☑ read_content
```

---

## Troubleshooting

**"You do not have permission to create apps"**
→ You need to be the store owner or have staff permissions

**"Invalid URL" in App URL**
→ Make sure it starts with https://

**Can't find scopes**
→ Click the "Select scopes" button, don't type in the box

**Token not showing**
→ You must install the app first (click "Install app" button)

---

## Next Step After This:

Once you have the token (shpat_xxxx), add it to your Railway/Render environment variables and restart your deployment!
