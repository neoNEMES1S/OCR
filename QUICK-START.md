# Quick Start Guide

Get the OCR PDF application running locally in 5 minutes.

## Prerequisites

- Python 3.11+
- Node.js 18+
- Docker (for Redis)

## Option A: Automated Start (Easiest)

Run the test script which sets up and starts everything:

```bash
./test-local.sh
```

The script will:
1. ✅ Check if Redis is running (offer to start it)
2. ✅ Install backend dependencies
3. ✅ Install frontend dependencies  
4. ✅ Start all services
5. ✅ Open browser to http://localhost:3000

**To stop everything:**

```bash
./stop-services.sh
```

---

## Option B: Manual Start (Step by Step)

### Step 1: Start Redis

```bash
docker run -d -p 6379:6379 --name ocr-redis redis:7-alpine
```

Verify it's running:
```bash
redis-cli ping
# Should return: PONG
```

### Step 2: Setup Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 3: Setup Frontend

```bash
cd frontend
npm install
```

### Step 4: Start Services (in 3 separate terminals)

**Terminal 1 - Backend API:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - RQ Worker:**
```bash
cd backend
source venv/bin/activate
rq worker app.workers
```

**Terminal 3 - Frontend:**
```bash
cd frontend
npm run dev
```

### Step 5: Access Application

Open http://localhost:3000 in your browser.

---

## Testing the Application

### 1. Configure Folder Settings

1. Go to **Settings** page (top navigation)
2. Set folder path: `/tmp/pdfs` (or any folder with PDFs)
3. Enable "Include Subfolders" if needed
4. Enable "Auto-ingest on Startup"
5. Click **Save Settings**

### 2. Prepare Test PDFs

Create a test folder with some PDFs:

```bash
# Create test folder
mkdir -p /tmp/pdfs

# Download a sample PDF (or copy your own)
curl -o /tmp/pdfs/sample.pdf https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf
```

Or copy any PDF files you have.

### 3. Trigger a Scan

1. On Settings page, click **"Refresh / Rescan"**
2. Watch the progress (auto-updates every 2 seconds)
3. See summary: new files, skipped files

### 4. Search Documents

1. Go to **Search** page
2. Try **Keyword search**:
   - Enter a word you know is in your PDFs
   - Click Search
   - See highlighted snippets

3. Try **Semantic search**:
   - Select "Semantic (AI)" radio button
   - Enter a natural language query
   - Click Search
   - See contextually similar results

---

## Verify It's Working

### Check Backend

```bash
# Health check
curl http://localhost:8000/health

# API docs
open http://localhost:8000/docs
```

### Check Frontend

```bash
# Should load React app
open http://localhost:3000
```

### Check Worker

```bash
# In backend directory
rq info

# Should show:
# - default queue
# - Worker count
# - Jobs processed
```

### Check Database

```bash
# In backend directory
python3 << EOF
from app.db import get_db
from app.models import Document

with get_db() as db:
    docs = db.query(Document).all()
    print(f"Documents in DB: {len(docs)}")
    for doc in docs:
        print(f"  - {doc.filename}: {doc.ingestion_status}")
EOF
```

---

## Troubleshooting

### "Redis connection refused"

Start Redis:
```bash
docker run -d -p 6379:6379 --name ocr-redis redis:7-alpine
```

### "Port 3000 already in use"

Kill the process:
```bash
lsof -ti:3000 | xargs kill
```

### "Port 8000 already in use"

Kill the process:
```bash
lsof -ti:8000 | xargs kill
```

### Worker not processing jobs

Check RQ worker is running:
```bash
rq info
```

Restart worker if needed.

### Frontend shows "Network Error"

1. Check backend is running on port 8000
2. Check browser console for errors
3. Verify proxy in `frontend/vite.config.ts`

### No PDFs found during scan

1. Check folder path in settings
2. Verify PDFs exist: `ls /tmp/pdfs`
3. Check folder permissions

### Search returns no results

1. Wait for ingestion to complete (check Settings page status)
2. Verify documents status: `queued` → `processing` → `done`
3. Check worker logs for errors

---

## What's Running?

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** | http://localhost:3000 | React UI |
| **Backend API** | http://localhost:8000 | FastAPI REST API |
| **API Docs** | http://localhost:8000/docs | Interactive API documentation |
| **Redis** | localhost:6379 | Task queue |
| **RQ Worker** | (background) | Processes ingestion jobs |

---

## Stop Everything

**Automated:**
```bash
./stop-services.sh
```

**Manual:**
```bash
# Stop services (Ctrl+C in each terminal)

# Stop Redis
docker stop ocr-redis
docker rm ocr-redis
```

---

## Next Steps

Once you've verified it works locally:

1. **Deploy Frontend to Vercel:**
   - See [DEPLOYMENT.md](./DEPLOYMENT.md) → "Option 1: Separate Hosting"
   - Configure `VITE_API_URL` environment variable

2. **Deploy Backend to Supabase:**
   - Or any server (DigitalOcean, Fly.io, Railway)
   - Update CORS settings with your frontend URL
   - Set environment variables

3. **Test Production Setup:**
   - Verify API calls work
   - Check CORS configuration
   - Test search functionality

---

## Quick Reference

```bash
# Start everything
./test-local.sh

# Stop everything  
./stop-services.sh

# View logs
tail -f logs/backend.log
tail -f logs/worker.log
tail -f logs/frontend.log

# Check Redis
redis-cli ping

# Check RQ
cd backend && source venv/bin/activate && rq info

# Rebuild frontend only
cd frontend && npm run build
```

---

## Getting Help

- Check [README.md](./README.md) for overview
- See [DEPLOYMENT.md](./DEPLOYMENT.md) for deployment guides
- See [HOSTING-COMPARISON.md](./HOSTING-COMPARISON.md) for hosting options

If you encounter issues, check:
1. All services are running
2. Redis is accessible
3. Ports 3000, 6379, 8000 are available
4. Python and Node versions are correct

