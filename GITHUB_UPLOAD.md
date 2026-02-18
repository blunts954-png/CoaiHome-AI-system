# Upload to GitHub (Step-by-Step)

## Option 1: Command Line (Recommended)

Open terminal/command prompt in your `dropshipping_ai_system` folder:

```bash
# 1. Initialize git
git init

# 2. Add all files
git add .

# 3. Commit
git commit -m "Initial commit - AI Dropshipping Automation System"

# 4. Create GitHub repo (go to github.com/new)
#    - Name: ai-dropshipping-automation
#    - Public or Private
#    - DON'T initialize with README

# 5. Connect to GitHub (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/ai-dropshipping-automation.git

# 6. Push
git branch -M main
git push -u origin main
```

## Option 2: GitHub Desktop (Easiest)

1. Download GitHub Desktop: https://desktop.github.com
2. Click "File" → "Add local repository"
3. Select your `dropshipping_ai_system` folder
4. Click "Publish repository"
5. Name it: `ai-dropshipping-automation`
6. Click "Publish"

## Option 3: VS Code (If you use it)

1. Open folder in VS Code
2. Click Source Control icon (left sidebar)
3. Click "Initialize Repository"
4. Stage all changes (+ icon)
5. Type message: "Initial commit"
6. Click checkmark to commit
7. Click "..." → "Remote" → "Add Remote"
8. Add your GitHub repo URL
9. Push

---

## After Uploading

Your repo URL will be:
```
https://github.com/YOUR_USERNAME/ai-dropshipping-automation
```

Then you can deploy from GitHub on Railway/Render!
