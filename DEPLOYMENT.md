# Deployment Guide

## ❌ Why NOT Vercel

Vercel is **serverless** - your app sleeps between requests. This system needs:
- Continuous background jobs (inventory sync every 30 min)
- Persistent database (SQLite file must persist)
- Always-running scheduler

## ✅ Recommended Platforms

### 1. Render.com (Easiest - Free $7/month)

```bash
# 1. Push to GitHub
git init
git add .
git commit -m "Initial commit"
git push origin main

# 2. Go to https://render.com
# 3. Click "New Web Service"
# 4. Connect your GitHub repo
# 5. Select Python environment
# 6. Add environment variables in dashboard
# 7. Deploy!
```

**Why Render:**
- Native Python support
- Persistent disk (for SQLite)
- Background workers
- Free custom domain

---

### 2. Railway.app (Easiest - $5/month)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up

# Add environment variables
railway variables set SHOPIFY_ACCESS_TOKEN=xxx
railway variables set AUTODS_API_KEY=xxx
# ... etc
```

**Why Railway:**
- Zero-config deployment
- Automatic HTTPS
- Persistent volumes
- Great for Python apps

---

### 3. Fly.io (Best Performance - $2-5/month)

```bash
# Install Fly CLI
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"

# Login and launch
fly auth login
fly launch

# Create persistent volume for database
fly volumes create dropshipping_data --size 1

# Set secrets
fly secrets set SHOPIFY_ACCESS_TOKEN=xxx
fly secrets set AUTODS_API_KEY=xxx
fly secrets set AI_API_KEY=xxx

# Deploy
fly deploy
```

**Why Fly:**
- Edge deployment (fast globally)
- Persistent volumes
- Great for long-running processes
- Scale to zero option

---

### 4. DigitalOcean Droplet ($6/month)

```bash
# SSH into your droplet
# Install dependencies
sudo apt update
sudo apt install python3-pip python3-venv nginx

# Clone repo
git clone <your-repo>
cd dropshipping_ai_system

# Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -c "from models.database import init_db; init_db()"

# Create systemd service
sudo nano /etc/systemd/system/dropshipping-ai.service
```

```ini
[Unit]
Description=AI Dropshipping Automation
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/dropshipping_ai_system
Environment=PATH=/root/dropshipping_ai_system/venv/bin
ExecStart=/root/dropshipping_ai_system/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable dropshipping-ai
sudo systemctl start dropshipping-ai

# Setup Nginx reverse proxy
sudo nano /etc/nginx/sites-available/dropshipping-ai
```

---

## Environment Variables to Set

### Required
```bash
SHOPIFY_SHOP_URL=your-store.myshopify.com
SHOPIFY_ACCESS_TOKEN=shpat_xxx
AUTODS_API_KEY=xxx
AI_API_KEY=sk-xxx
```

### Optional (but recommended)
```bash
SYSTEM_DATABASE_URL=sqlite:///data/dropshipping_ai.db
NOTIFY_EMAIL_ENABLED=true
NOTIFY_SMTP_USER=your-email@gmail.com
NOTIFY_SMTP_PASSWORD=app-password
NOTIFY_ALERT_EMAIL=alerts@yourdomain.com
```

---

## Post-Deployment Checklist

- [ ] App is accessible via HTTPS
- [ ] Database is persisting (check after restart)
- [ ] Scheduler jobs are running (check logs)
- [ ] Environment variables are set correctly
- [ ] AutoDS API connection is working
- [ ] Shopify API connection is working
- [ ] AI content generation is working
- [ ] Email/Slack notifications are configured

---

## Quick Start Recommendation

**For beginners:** Use **Railway.app** - fastest setup

**For production:** Use **Fly.io** - best performance/price

**For full control:** Use **DigitalOcean** - full server access
