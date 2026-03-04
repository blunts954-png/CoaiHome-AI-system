# Shopify Token Setup (2026 Update)

## The Reality
Shopify has retired the old "Legacy Custom Apps" where you could just copy a permanent `shpat_` token. New apps (like your "CoaiHome Automation") use the **Developer Dashboard** and a more secure `client_credentials` grant.

**Good News:** I have updated our core system to handle this new flow automatically. You no longer need to find a secret token hidden in the UI.

---

## How to Connect Your Empire (2026 Method)

### Step 1: Get Your API Credentials
You already found them! Looking at your screenshot:
- **Client ID**: `41d4177eb96e6ba9684b42e7388f9987`
- **Secret**: You have this in the "Credentials" tab of your app.

### Step 2: Update Your .env File
Open `dropshipping_ai_system/.env` and update these lines:

```bash
# Enter the Client ID from your screenshot
SHOPIFY_API_KEY=41d4177eb96e6ba9684b42e7388f9987

# Enter the Secret from your screenshot (Click the eye icon to see it)
SHOPIFY_API_SECRET=your_secret_here

# Leave this BLANK - the system will now fetch its own token
SHOPIFY_ACCESS_TOKEN=
```

### Step 3: Launch
Once you've updated the `.env`, run:
```bash
python build_complete_store.py
```

The system will now talk to Shopify using the modern `client_credentials` grant, fetch its own token, and start building your store immediately.

---

## Why didn't the "Reveal" button show up?
Because in 2026, Shopify wants systems like ours to fetch tokens programmatically using the Client ID and Secret. This is safer and more professional. Our system is now fully compatible with this standard.
