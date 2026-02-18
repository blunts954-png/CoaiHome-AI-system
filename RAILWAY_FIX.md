# Railway Deploy Fix

## Problem
Your code is in a **subfolder** (`dropshipping_ai_system/`) but Railway is looking at the **root** folder.

Railpack sees:
```
./
└── dropshipping_ai_system/   <-- Your code is HERE
    ├── main.py
    ├── requirements.txt
    └── ...
```

But it needs to see:
```
./
├── main.py                    <-- Files should be HERE
├── requirements.txt
└── ...
```

---

## Solution 1: Move Files to Root (Recommended)

### Step 1: Go up one folder
```bash
cd ..
```

### Step 2: Move all files up
**Windows (PowerShell):**
```powershell
# Move all files from subfolder to current folder
Move-Item -Path "dropshipping_ai_system\*" -Destination "."
Move-Item -Path "dropshipping_ai_system\api_clients" -Destination "."
Move-Item -Path "dropshipping_ai_system\automation" -Destination "."
Move-Item -Path "dropshipping_ai_system\config" -Destination "."
Move-Item -Path "dropshipping_ai_system\models" -Destination "."
Move-Item -Path "dropshipping_ai_system\scripts" -Destination "."
Move-Item -Path "dropshipping_ai_system\services" -Destination "."
Move-Item -Path "dropshipping_ai_system\web" -Destination "."

# Remove empty folder
Remove-Item -Recurse -Force "dropshipping_ai_system"
```

**Mac/Linux:**
```bash
# Move all files up
mv dropshipping_ai_system/* .
mv dropshipping_ai_system/.* . 2>/dev/null

# Remove empty folder
rmdir dropshipping_ai_system
```

### Step 3: Verify structure
```bash
ls
```

Should show:
```
README.md
requirements.txt
main.py
api_clients/
automation/
config/
models/
web/
...
```

### Step 4: Commit and push
```bash
git add .
git commit -m "Move files to root for Railway"
git push
```

### Step 5: Redeploy on Railway
Railway will auto-detect Python and deploy!

---

## Solution 2: Create a Start Script (Quick Fix)

In your **root folder** (where `dropshipping_ai_system/` is), create:

**`start.sh`** file:
```bash
#!/bin/bash
cd dropshipping_ai_system
python main.py
```

**Or `Procfile`** (no extension):
```
web: cd dropshipping_ai_system && python main.py
```

**Or `railway.json`** in root:
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "cd dropshipping_ai_system && python main.py",
    "restartPolicyType": "ON_FAILURE"
  }
}
```

Then commit and push:
```bash
git add start.sh
git commit -m "Add start script"
git push
```

---

## Solution 3: Change Railway Root Directory

In Railway dashboard:
1. Go to your project
2. Click **Settings** tab
3. Find **Root Directory** setting
4. Change from `/` to `/dropshipping_ai_system`
5. Redeploy

---

## Recommended: Use Solution 1

Moving files to root is cleanest and easiest long-term.

### After moving files, your repo should look like:

```
CoaiHome-AI-system/
├── README.md
├── requirements.txt
├── main.py
├── Dockerfile
├── railway.json
├── api_clients/
│   ├── shopify_client.py
│   └── autods_client.py
├── automation/
│   ├── store_builder.py
│   ├── product_research.py
│   ├── pricing_engine.py
│   ├── fulfillment_monitor.py
│   └── scheduler.py
├── config/
│   └── settings.py
├── models/
│   └── database.py
├── services/
│   ├── ai_service.py
│   └── notification_service.py
├── web/
│   └── templates/
└── ...
```

**NOT** like this:
```
CoaiHome-AI-system/
└── dropshipping_ai_system/     <- This extra folder causes the problem
    ├── README.md
    ├── requirements.txt
    └── ...
```

---

## Quick Commands (Copy & Paste)

**Windows PowerShell:**
```powershell
cd dropshipping_ai_system
cd ..
Move-Item -Path "dropshipping_ai_system\*" -Destination "." -Force
Move-Item -Path "dropshipping_ai_system\api_clients" -Destination "." -Force
Move-Item -Path "dropshipping_ai_system\automation" -Destination "." -Force
Move-Item -Path "dropshipping_ai_system\config" -Destination "." -Force
Move-Item -Path "dropshipping_ai_system\models" -Destination "." -Force
Move-Item -Path "dropshipping_ai_system\scripts" -Destination "." -Force
Move-Item -Path "dropshipping_ai_system\services" -Destination "." -Force
Move-Item -Path "dropshipping_ai_system\web" -Destination "." -Force
Remove-Item -Recurse -Force "dropshipping_ai_system"
git add .
git commit -m "Restructure for Railway deploy"
git push origin main --force
```

Then redeploy on Railway!

---

## Verify It Works

After pushing, Railway should show:
```
✓ Detected Python app
✓ Installing requirements.txt
✓ Starting application
```

Instead of:
```
✖ Could not determine how to build the app
```

---

Which solution do you want to try? I recommend **Solution 1**! 🚀
