# EASIEST METHOD - No OAuth Needed!

## The Problem
OAuth flow is complicated. Here's the **easier way** to get API access.

---

## METHOD 1: Create Private App (RECOMMENDED - 5 minutes)

### Step 1: Create Private App
1. Go to https://coaihome.myshopify.com/admin
2. Login to your store
3. Go to **Settings** (bottom left)
4. Click **Apps and sales channels**
5. Scroll down and click **Develop apps**

### Step 2: Create New App
1. Click **Create an app**
2. App name: `CoaiHome Automation`
3. Developer: Your name
4. Click **Create**

### Step 3: Configure Permissions
1. Click **Configuration** tab
2. Click **Configure** next to "Admin API access scopes"
3. Enable these permissions:
   - [x] `read_products`
   - [x] `write_products`
   - [x] `read_themes`
   - [x] `write_themes`
   - [x] `read_content`
   - [x] `write_content`
   - [x] `read_script_tags`
   - [x] `write_script_tags`

### Step 4: Install App
1. Click **Install app** button
2. Confirm "I understand, install this app"

### Step 5: Get Token
1. Click **API credentials** tab
2. Click **Reveal token once**
3. Copy the token (starts with `shpat_`)

### Step 6: Add to Your Store
1. Open file: `dropshipping_ai_system/.env`
2. Add this line:
   ```
   SHOPIFY_ACCESS_TOKEN=shpat_XXXXXXXXXXXXXXXXXXXXXXXX
   ```
   (Replace with your actual token)

3. Save the file

### Step 7: Run Auto Builder
```bash
cd dropshipping_ai_system
python auto_build_shopify_store.py
```

**BOOM! Your store will be built automatically!**

---

## METHOD 2: Manual Upload (Even Easier - 10 minutes)

If API is too much trouble, just use the files I already created:

### Step 1: Upload Products
1. Go to https://coaihome.myshopify.com/admin
2. Click **Products** → **Import**
3. Upload file: `DEPLOY_PACKAGE/shopify_import.csv`
4. All 15 products created instantly!

### Step 2: Copy CSS
1. Go to **Online Store** → **Themes** → **Customize**
2. Click **Theme Settings** → **Custom CSS**
3. Open file: `DEPLOY_PACKAGE/css.txt`
4. Copy all contents
5. Paste into Custom CSS box
6. Save

### Step 3: Set Colors
1. Still in Theme Settings, click **Colors**
2. Set:
   - Primary: `#2563EB`
   - Secondary: `#F97316`
   - Success: `#10B981`
3. Save

### Step 4: Add Pages
1. Go to **Online Store** → **Pages**
2. Click **Add Page**
3. For each file in `DEPLOY_PACKAGE/pages/`:
   - Copy the HTML content
   - Paste into page editor
   - Save

### Step 5: Launch!
1. Go to **Online Store** → **Preferences**
2. Remove password protection
3. Your store is LIVE!

---

## Which Method Should You Choose?

| Method | Time | Effort | Result |
|--------|------|--------|--------|
| **Private App** | 5 min | Medium | Fully automated builds |
| **Manual Upload** | 10 min | Low | One-time setup |

**Recommendation:** Try Method 1 (Private App) first. If it's too confusing, use Method 2 (Manual).

Both work! Both get your store live!

---

## After Setup

Once you have API access or manual setup complete:

1. **Test your store:** https://coaihome.myshopify.com
2. **Start TikTok marketing** (scripts in `store_content/tiktok_scripts.json`)
3. **Make money!** 💰

---

## Need Help?

If you get stuck:
1. Shopify Help Center: https://help.shopify.com
2. Shopify Support: Available 24/7 in your admin
3. This guide is saved as: `EASIEST_METHOD.md`

**You've got this!** 
