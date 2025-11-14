# 🚀 One-Click Start Guide

## Quick Start (Easiest!)

### On macOS:
**Double-click:** `start.command`

OR

**Run:** `python3 launcher.py`

### On Windows:
**Double-click:** `start.bat` (coming soon)

OR

**Run:** `python launcher.py`

---

## What Happens?

The launcher will:
1. ✅ Check and install dependencies (automatic)
2. ✅ Start Redis (automatic)
3. ✅ Start Backend API
4. ✅ Start RQ Worker
5. ✅ Start Frontend
6. ✅ Open browser automatically

**Everything in one window with visual feedback!**

---

## Using the Launcher

### Main Window

```
🔍 OCR PDF Application
━━━━━━━━━━━━━━━━━━━━━━━━
Status: 🟢 Running

[▶ Start All]  [⏹ Stop All]  [🌐 Open Browser]

Service Status:
  Redis:        🟢 Running
  Backend API:  🟢 Running
  RQ Worker:    🟢 Running
  Frontend:     🟢 Running

Logs:
  [12:34:56] Starting OCR PDF Application...
  [12:34:57] Redis started successfully
  [12:34:59] Backend API started on http://localhost:8000
  [12:35:01] Frontend started on http://localhost:3000
  [12:35:03] All services started successfully!
```

### Buttons

**▶ Start All Services**
- Installs dependencies if needed
- Starts Redis, Backend, Worker, Frontend
- Opens browser automatically

**⏹ Stop All Services**
- Stops all running services
- Clean shutdown

**🌐 Open in Browser**
- Opens http://localhost:3000
- Available after services start

---

## First Time Setup

### Prerequisites

You need:
- ✅ Python 3.11+ (check: `python3 --version`)
- ✅ Node.js 18+ (check: `node --version`)
- ✅ Redis (installer will help with this)

### Install Redis (One Time)

**macOS (Homebrew):**
```bash
# Fix permissions if needed
sudo chown -R $(whoami) /opt/homebrew/Cellar

# Install Redis
brew install redis
```

**macOS (Manual - No Installation):**
The launcher will attempt to start Redis automatically if installed via Homebrew.

If Redis is not installed, you'll see an error message with instructions.

---

## Troubleshooting

### "Redis is NOT running"

**Fix:**
```bash
# Install Redis
brew install redis

# Or run manually
redis-server
```

Then click "Start All Services" again.

### "Port already in use"

Another instance is running. Either:
- Click "Stop All Services" first
- Or kill processes manually:
  ```bash
  lsof -ti:3000 | xargs kill  # Frontend
  lsof -ti:8000 | xargs kill  # Backend
  ```

### "Command not found: python3"

Your system doesn't have Python 3. Install from:
https://www.python.org/downloads/

### Launcher won't open (Mac)

**Right-click** `start.command` → **Open** (first time only)

This bypasses macOS security for unidentified developers.

### "Permission denied"

Make executable:
```bash
chmod +x start.command
chmod +x launcher.py
```

---

## Manual Control (Alternative)

If you prefer manual control, see:
- [QUICK-START.md](./QUICK-START.md) - Step-by-step manual start
- [test-local.sh](./test-local.sh) - Automated script

---

## What's Running?

| Service | URL | Log Location |
|---------|-----|--------------|
| Frontend | http://localhost:3000 | In launcher window |
| Backend API | http://localhost:8000 | In launcher window |
| API Docs | http://localhost:8000/docs | - |
| Redis | localhost:6379 | - |

---

## Stopping

**Option 1:** Click "⏹ Stop All Services" in launcher

**Option 2:** Close launcher window (will ask to stop services)

**Option 3:** Press Ctrl+C in terminal

---

## Next Steps

1. **Click "Start All Services"**
2. Wait for browser to open
3. Go to **Settings** page
4. Set folder path (click 💡 for suggestions)
5. Click **Refresh / Rescan**
6. Go to **Search** page
7. Try searching!

---

## Tips

💡 **Keep launcher window open** to see logs and control services

💡 **Logs scroll automatically** - latest messages at bottom

💡 **Green status** = everything working

💡 **Red status** = check logs for errors

💡 **First start takes longer** (installing dependencies)

---

## Deployment

Once you've tested locally, deploy to production:

See [DEPLOYMENT.md](./DEPLOYMENT.md) for:
- Deploying frontend to Vercel
- Deploying backend to Supabase
- Production configuration

---

## Questions?

- Check logs in launcher window
- See [README.md](./README.md)
- See [QUICK-START.md](./QUICK-START.md)
- See [FOLDER-ACCESS-GUIDE.md](./FOLDER-ACCESS-GUIDE.md)

---

**Ready? Double-click `start.command` and let's go! 🚀**

