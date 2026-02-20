# 🚀 Quick Start - Run Your Business NOW

## What This System Does

This is YOUR **personal AI dropshipping assistant** that:
- Finds winning products automatically
- Creates TikTok content for marketing
- Optimizes pricing for max profit
- Monitors inventory 24/7
- Works WITHOUT AutoDS API!

---

## Step 1: Add Your Credentials

1. Open the file `.env` in Notepad
2. Replace the placeholder text with your real info:

```
SHOPIFY_SHOP_URL=your-store.myshopify.com
SHOPIFY_ACCESS_TOKEN=shpat_xxxxxxxxxxxxx
AI_API_KEY=sk-proj-xxxxxxxxxxxxx
```

**How to get these:**
- **Shopify URL**: It's in your Shopify admin (like `coaihome.myshopify.com`)
- **Access Token**: Shopify Admin → Settings → Apps → Private apps → Create
- **AI Key**: Go to openai.com → Sign up → API keys → Create new key

---

## Step 2: Start Your Business

Double-click this file:
```
start_my_business.py
```

Or in PowerShell:
```bash
python start_my_business.py
```

Wait 3 seconds... your browser will open automatically!

---

## Step 3: Use Your Dashboard

Once you see the dashboard, click these buttons:

### 🎬 Generate TikTok Content
- Creates 30 days of video scripts
- Exports to `content_calendar.csv`
- Open that file, film the videos, post 2-3x daily

### 🔍 Research Products (No AutoDS API)
- Finds trending products automatically
- Shows profit margins, shipping times
- Click to see top products

### ⚡ Start 24/7 Automation
- Runs everything automatically
- Research daily at 9am
- Import products at 10am
- Optimize prices at 2pm
- Generate content at 8pm

---

## What Happens Next?

### Every Day:
1. **Morning**: System finds new products
2. **Midday**: Adjusts prices for profit
3. **Evening**: Creates TikTok scripts

### Your Job:
1. **Film TikToks** using the generated scripts
2. **Post 2-3x daily** at optimal times
3. **Check dashboard** for any alerts

### The System Handles:
- ✅ Product research
- ✅ Pricing optimization
- ✅ Inventory monitoring
- ✅ Order tracking
- ✅ Content creation

---

## Need Help?

**Server won't start?**
- Check your `.env` file has real values
- Make sure Python is installed

**No products showing?**
- Click "Research (No AutoDS API)" button
- Check the system log on the dashboard

**TikTok content not generating?**
- Make sure AI_API_KEY is valid
- Check system log for errors

---

## Quick Commands

If you prefer command line:

```bash
# Research products
curl -X POST http://localhost:8000/api/research/no-api

# Generate TikTok content
curl -X POST http://localhost:8000/api/tiktok/generate-content

# Start full automation
curl -X POST http://localhost:8000/api/full-automation/start

# Check status
curl http://localhost:8000/api/system/status
```

---

## You're Ready! 🎉

1. Start the server
2. Generate TikTok content
3. Research products
4. Start automation
5. Film and post content daily
6. Make money! 💰

**Questions?** Check the system log on your dashboard!
