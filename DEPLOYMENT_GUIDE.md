# LHM Engine - Cloud Deployment Guide

## Current Status
- Engine is running locally with 24/7 auto-restart
- Git repo initialized at `C:\Users\enock\Downloads`
- Deployment configs ready for Railway and Render

## GitHub Repository
- **Repo URL**: https://github.com/enockjosee0-netizen/lhm-engine
- **Status**: Code pushed and ready for deployment
- **Branch**: main

## Railway Deployment (Free 24/7)
1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose `lhm-engine` repository
5. Railway auto-detects `railway.json` and deploys
6. Add environment variables in Railway dashboard:
   - `LHM_TELEGRAM_TOKEN` = `8899227512:AAE7dr-MvhyySbSv2KHcGmuzA4hepE8AHHQ`
   - `LHM_TELEGRAM_CHAT_ID` = `7247622315`
   - `DRY_RUN` = `true`
   - `USE_FREE_SCRAPERS` = `true`
7. Deploy - Railway keeps it running 24/7 on free tier

## Render Deployment (Free Worker)
1. Go to https://render.com
2. Click "New" + "Web Service"
3. Connect GitHub repository `lhm-engine`
4. Render auto-detects `render.yaml`
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
