# LHM Engine - Cloud Deployment Guide

## Current Status
- Engine is running locally with 24/7 auto-restart
- Git repo initialized at `C:\Users\enock\Downloads`
- Deployment configs ready for Railway and Render

## GitHub Authentication Required

### Option A: Complete GitHub CLI Auth (Recommended)
1. Open browser and go to: https://github.com/login/device
2. Enter code: `9E72-0A0B`
3. Click "Authorize github-cli"
4. Run this command after auth: `gh auth status`

### Option B: Manual GitHub Setup
1. Go to https://github.com/new
2. Create a new public repository named `lhm-engine`
3. Run these commands:

```powershell
cd C:\Users\enock\Downloads
git remote add origin https://github.com/YOUR_USERNAME/lhm-engine.git
git branch -M main
git push -u origin main
```

## Railway Deployment (Free 24/7)

### Prerequisites
- GitHub repo created and pushed (see above)
- Railway CLI installed OR use Railway web interface

### Steps
1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your `lhm-engine` repository
5. Railway will auto-detect `railway.json` and deploy
6. Add environment variables in Railway dashboard:
   - `LHM_TELEGRAM_TOKEN` = `8899227512:AAE7dr-MvhyySbSv2KHcGmuzA4hepE8AHHQ`
   - `LHM_TELEGRAM_CHAT_ID` = `7247622315`
   - `DRY_RUN` = `true`
   - `USE_FREE_SCRAPERS` = `true`
7. Deploy - Railway will keep it running 24/7 on free tier

### Using Railway CLI
```powershell
$env:Path += ";C:\Users\enock\Downloads\gh_cli\bin"
railway login
cd C:\Users\enock\Downloads
railway init
railway up
```

## Render Deployment (Free Worker)

### Prerequisites
- GitHub repo created and pushed

### Steps
1. Go to https://render.com
2. Click "New" + "Web Service"
3. Connect your GitHub repository `lhm-engine`
4. Render will auto-detect `render.yaml`
5. Configure:
   - **Type**: Worker
   - **Plan**: Free
   - **Start Command**: `python deepseek_python_20260707_a6bd19.py --dry-run`
   - **Build Command**: `pip install -r requirements_enhanced.txt`
6. Add environment variables:
   - `LHM_TELEGRAM_TOKEN` = `8899227512:AAE7dr-MvhyySbSv2KHcGmuzA4hepE8AHHQ`
   - `LHM_TELEGRAM_CHAT_ID` = `7247622315`
   - `DRY_RUN` = `true`
   - `USE_FREE_SCRAPERS` = `true`
7. Click "Create Web Service"

## Local 24/7 Setup (Already Active)

### What's Already Running
- Background process: `bgp_f6111895d001nQNWSBAMdwCqO4` (PID 14732)
- Auto-restart batch: `C:\Users\enock\Downloads\lhm_autorestart.bat`
- Startup shortcut: `C:\Users\enock\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\LHM Engine.lnk`
- Engine auto-starts on Windows boot and restarts on crash

### Manual Control
```powershell
# Check status
Get-Process -Name python -ErrorAction SilentlyContinue

# Stop engine
Stop-Process -Name python -Force -ErrorAction SilentlyContinue

# Start engine
Start-Process -FilePath "C:\Users\enock\AppData\Local\Programs\Python\Python312\python.exe" -ArgumentList "C:\Users\enock\Downloads\deepseek_python_20260707_a6bd19.py","--dry-run" -WindowStyle Hidden
```

## Important Notes
- Engine is in **DRY RUN MODE** - no real bets placed
- All arbitrage opportunities are logged but not executed
- To enable live betting, set `DRY_RUN=false` in cloud environment variables
- Never commit real betting credentials to GitHub
