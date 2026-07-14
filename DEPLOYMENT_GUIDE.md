# LHM Engine - Deployment Status & Options

## What's Already Running (Local)
- **Engine**: Active in background with 24/7 auto-restart
- **GitHub Actions**: Scheduled workflow pushes to `main` branch
- **GitHub Repo**: https://github.com/enockjosee0-netizen/lhm-engine

## Honest Truth About "Free Forever"

| Option | Cost | Credit Card? | 24/7? | Notes |
|--------|------|--------------|-------|-------|
| **GitHub Actions** | $0 | No | Scheduled | Runs every 5 min on public repo |
| **Railway** | $0/mo | Yes for free tier | Yes | 500 hrs/month, requires card |
| **Render** | $0/mo | Yes for free tier | Yes | Free worker, requires card |
| **Fly.io** | $0/mo | Yes for free tier | Yes | 3 shared VMs, requires card |

### Only GitHub Actions is truly free forever without a credit card.

## GitHub Actions (Already Configured - TRULY FREE FOREVER)

Your repo already has `.github/workflows/lhm-engine.yml` which:
- Runs every 5 minutes
- Uses free GitHub-hosted runners
- No credit card required
- Unlimited runs for public repos

### To enable GitHub Actions secrets:
1. Go to https://github.com/enockjosee0-netizen/lhm-engine/settings/secrets/actions
2. Add these secrets:
   - `LHM_TELEGRAM_TOKEN` = `8899227512:AAE7dr-MvhyySbSv2KHcGmuzA4hepE8AHHQ`
   - `LHM_TELEGRAM_CHAT_ID` = `7247622315`
   - `LHM_SECRET_KEY` = `89f80a2f39ff5f4a9393d96a3f3a87022fb6e3729fa313bd75572cd2501ea509`
   - `LHM_ENCRYPTION_KEY` = `87ea687d13559bf725b38a7092af9247`

### To trigger a manual run:
- Go to https://github.com/enockjosee0-netizen/lhm-engine/actions
- Click "LHM Engine Scheduled Run" → "Run workflow"

## Railway (Free tier - requires credit card)

### Prerequisites
- Railway account at https://railway.app
- Credit card for free tier verification

### Steps
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

### Using Railway CLI
```powershell
$env:Path += ";C:\Users\enock\Downloads\gh_cli\bin"
railway login
cd C:\Users\enock\Downloads
railway init
railway up
```

## Render (Free worker - requires credit card)

### Prerequisites
- Render account at https://render.com
- Credit card for free tier verification

### Steps
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

## Recommendation

**For truly free forever**: Use **GitHub Actions** only. It requires no credit card and runs on schedule.

**For true 24/7**: Use **Railway** or **Render**, but you must provide a credit card for verification. Free tiers are not lifetime guarantees - they can change terms at any time.

## Current Status
- ✅ GitHub repo pushed: https://github.com/enockjosee0-netizen/lhm-engine
- ✅ GitHub Actions workflow configured (runs every 5 min)
- ✅ Local engine running with auto-restart
- ⏳ Railway/Render: awaiting your account setup and credit card verification
