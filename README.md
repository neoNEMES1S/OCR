# 🔍 OCR PDF Search System

A full-featured OCR PDF processing and search system with auto-ingestion, background workers, and both keyword and semantic search capabilities.

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 18+](https://img.shields.io/badge/node.js-18+-green.svg)](https://nodejs.org/)

## 🚀 Quick Start

**One-Click Launch (macOS):**
```bash
# Clone and start
git clone https://github.com/neoNEMES1S/OCR.git
cd OCR
./start.command  # Or double-click in Finder
```

Or use the GUI launcher:
```bash
python3 launcher.py
```

See **[START_HERE.md](./START_HERE.md)** for detailed instructions.

## ✨ Key Features

### 📤 Direct File Upload (NEW!)
- **Drag & drop** PDF files directly into the web UI
- Upload multiple files simultaneously
- Real-time processing status with progress tracking
- Instant search availability once processed
- Perfect for testing or adding individual documents
- Automatic duplicate detection via checksums

### 📁 Folder Scanning
- Configure a folder path for batch processing
- Recursive subfolder scanning support
- Manual refresh/rescan with **cancel button**
- Persistent scan status across page refreshes
- Idempotent scanning (skip unchanged files)

### 🔍 Dual Search
- **Keyword Search**: Lightning-fast full-text search (SQLite FTS5)
- **Semantic Search**: AI-powered similarity search (vector embeddings)
- Search by filename or document content
- Results grouped by document with page numbers

### ⚙️ Background Processing
- Asynchronous job queue with Redis & RQ
- Non-blocking PDF processing
- Scalable worker architecture
- Status tracking and error handling

## Overview

This MVP provides:

1. **Direct upload**: Drag & drop PDFs for immediate processing
2. **Auto-ingestion**: Automatically scans and processes PDFs from a configured folder
3. **Manual refresh**: Trigger rescans via API endpoint with cancel option
4. **Settings management**: Configure folder path and scan options
5. **Full-text search**: Keyword search using SQLite FTS5
6. **Semantic search**: Vector similarity search using embeddings
7. **Background processing**: RQ worker queue with Redis for async ingestion
8. **Web UI**: Modern React frontend with Tailwind CSS & shadcn/ui

## Architecture

```
┌─────────────────┐
│  React Frontend │  (Port 3000)
│  TypeScript     │
└────────┬────────┘
         │ HTTP/REST
         ▼
┌─────────────────┐
│  FastAPI        │  (Port 8000)
│  Python 3.11    │
└────────┬────────┘
         │
    ┌────┴────────────────┬──────────────┐
    ▼                     ▼              ▼
┌──────────┐      ┌──────────┐   ┌──────────┐
│ SQLite   │      │  Redis   │   │ SQLite   │
│ Metadata │      │   RQ     │   │  FTS5    │
└──────────┘      └────┬─────┘   └──────────┘
                       │
                       ▼
                  ┌──────────┐
                  │ RQ Worker│
                  │ Ingestion│
                  └──────────┘
```

### Components

**Backend (Python):**
- FastAPI web server with REST API
- SQLAlchemy ORM with SQLite (Postgres-ready)
- RQ (Python-RQ) worker queue with Redis
- File scanner with checksum-based change detection
- OCR stub (pdfminer.six for native PDFs)
- Embeddings stub (random or sentence-transformers)
- Vector DB stub (in-memory, ready for Qdrant/Pinecone)
- FTS5 full-text search index

**Frontend (TypeScript):**
- React 18 with TypeScript
- Vite build tool
- React Router for navigation
- API client with typed interfaces

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Redis server
- Docker (optional, for Redis)

### 1. Start Redis

```bash
docker run -p 6379:6379 redis
```

Or install and run Redis locally.

### 2. Start Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure settings (optional)
# Edit .env or settings.json

# Start FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Start RQ Worker

In a separate terminal:

```bash
cd backend
source venv/bin/activate
rq worker app.workers
```

### 4. Start Frontend

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

### 5. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Usage

### Configure Settings

1. Go to **Settings** page
2. Set folder path (e.g., `/tmp/pdfs`)
3. Enable "Include Subfolders" if needed
4. Enable "Auto-ingest on Startup" for automatic scanning
5. Click "Save Settings"

### Trigger Manual Scan

1. On Settings page, click "Refresh / Rescan"
2. Monitor scan progress (polls automatically)
3. View summary: new files, skipped files, errors

### Search Documents

1. Go to **Search** page
2. Choose search type:
   - **Keyword**: Fast full-text search with exact matches
   - **Semantic**: AI-powered contextual search
3. Enter query and click "Search"
4. View results grouped by document
5. Click "Open" to view specific page (TODO: implement viewer)

## API Examples

### Set Folder

```bash
curl -X POST http://localhost:8000/api/v1/settings/folder \
  -H "Content-Type: application/json" \
  -d '{
    "folder_path": "/tmp/pdfs",
    "include_subfolders": true,
    "auto_ingest": true
  }'
```

### Trigger Scan

```bash
curl -X POST http://localhost:8000/api/v1/scan \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Check Scan Status

```bash
curl http://localhost:8000/api/v1/scan/{job_id}
```

### Full-text Search

```bash
curl "http://localhost:8000/api/v1/search/fulltext?q=invoice&page=1&page_size=20"
```

### Semantic Search

```bash
curl -X POST http://localhost:8000/api/v1/search/semantic \
  -H "Content-Type: application/json" \
  -d '{
    "query": "contract termination clause",
    "top_k": 5
  }'
```

## Implementation Status

### ✅ Completed

- [x] Auto-ingestion on startup
- [x] Manual scan API endpoint
- [x] Settings API (get/set folder config)
- [x] Full-text search with FTS5
- [x] Semantic search API
- [x] Background worker queue (RQ)
- [x] File scanner with checksum tracking
- [x] SQLAlchemy models (Document, Chunk, ScanJob)
- [x] React frontend with search and settings
- [x] API client with TypeScript types
- [x] Unit tests (scanner)
- [x] Integration tests (API endpoints)

### 🔄 Stubs / TODOs

#### OCR (`backend/app/services/ocr_stub.py`)
- Currently uses `pdfminer.six` for native PDFs only
- **TODO**: Integrate Tesseract for scanned documents
- **TODO**: Add AWS Textract or Google Vision API
- **TODO**: Improve bounding box extraction

#### Embeddings (`backend/app/services/embeddings_stub.py`)
- Currently returns random vectors (or basic sentence-transformers)
- **TODO**: Use production embedding service (OpenAI, Cohere, etc.)
- **TODO**: Implement batch processing
- **TODO**: Add embedding caching

#### Vector DB (`backend/app/services/vector_client.py`)
- Currently uses in-memory dictionary
- **TODO**: Integrate Qdrant, Pinecone, or Weaviate
- **TODO**: Add connection pooling and retry logic
- **TODO**: Support advanced filtering

#### Frontend
- **TODO**: Implement PDF viewer route
- **TODO**: Add pagination for search results
- **TODO**: Improve styling (CSS framework)
- **TODO**: Add authentication
- **TODO**: Add document management UI

## Testing

### Backend Tests

```bash
cd backend
pytest
```

Run specific tests:

```bash
pytest app/tests/test_scanner.py
pytest app/tests/test_scan_endpoint.py -v
```

### Frontend Tests

```bash
cd frontend
# TODO: Add test setup
npm test
```

## Development Notes

### Database Schema

**Documents table:**
- Tracks PDF files with checksum for change detection
- Status: queued → processing → done/error

**Chunks table:**
- Per-page text chunks from OCR
- Links to embeddings in vector DB
- Stores bounding box metadata

**ScanJobs table:**
- Tracks background scan job status
- Records summary statistics (new, skipped, errors)

### Idempotent Scanning

The scanner uses SHA256 checksums to detect file changes:
- New files → always ingest
- Changed files (different checksum) → re-ingest
- Unchanged files → skip

This ensures efficient rescanning without re-processing unchanged documents.

### Worker Queue

RQ jobs:
- `scan_and_ingest_job`: Scans folder and enqueues per-file ingestion
- `ingest_document`: Processes single PDF through OCR → embeddings → vector DB → FTS

Jobs are retryable and include error tracking.

## Project Structure

```
OCR/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app
│   │   ├── config.py            # Settings
│   │   ├── db.py                # Database & FTS
│   │   ├── models.py            # ORM models
│   │   ├── api/v1/              # API endpoints
│   │   ├── workers/             # RQ tasks
│   │   ├── services/            # OCR, embeddings, vector
│   │   ├── utils/               # Helpers
│   │   └── tests/               # Unit & integration tests
│   ├── requirements.txt
│   └── README.md
├── frontend/
│   ├── src/
│   │   ├── api.ts               # API client
│   │   ├── App.tsx              # Main app
│   │   ├── components/          # React components
│   │   └── pages/               # Page components
│   ├── package.json
│   ├── vite.config.ts
│   └── README.md
└── README.md (this file)
```

## Deployment

You have two main deployment options:

### Option 1: Separate Hosting (Recommended for Production)

Deploy frontend and backend independently:
- **Frontend**: Static hosting (Netlify, Vercel, S3+CloudFront) - FREE
- **Backend**: Server/container (DigitalOcean, AWS ECS, Cloud Run)
- **Benefits**: Better scalability, CDN performance, independent scaling

### Option 2: Single Server (Simpler, Good for MVPs)

FastAPI serves both the API and React frontend from one server:
- **Setup**: Run `./deploy-single-server.sh` to build and combine
- **Benefits**: Simpler deployment, no CORS, single server
- **Good for**: Internal tools, small scale, development

### Quick Single-Server Setup

```bash
# Build frontend and copy to backend
./deploy-single-server.sh

# Start everything
cd backend
source venv/bin/activate

# Terminal 1: Redis
docker run -p 6379:6379 redis

# Terminal 2: RQ Worker
rq worker app.workers

# Terminal 3: Server (serves both API and frontend)
uvicorn serve_frontend:app --host 0.0.0.0 --port 8000
```

Access at: **http://localhost:8000**

### Full Deployment Guide

See **[DEPLOYMENT.md](./DEPLOYMENT.md)** for:
- Detailed comparison of hosting options
- Production deployment strategies
- Docker configurations
- Security checklist
- Systemd service setup
- Performance optimization

## Troubleshooting

### Redis connection error
- Ensure Redis is running: `redis-cli ping`
- Check REDIS_URL in config

### Worker not processing jobs
- Check RQ worker logs
- Ensure worker is connected to same Redis instance

### PDF processing fails
- Check PDF is valid (not encrypted)
- Current stub only works with native PDFs, not scanned images

### Search returns no results
- Verify documents were ingested successfully
- Check document status in database
- Ensure FTS5 table was populated

## Performance Considerations

- **FTS5**: Fast for keyword search, scales to millions of documents
- **Vector search**: Current stub is O(n); production DB required for large scale
- **Embeddings**: Batch processing recommended for bulk ingestion
- **Worker queue**: Scale horizontally by adding more RQ workers

## Security

**Production checklist:**
- [ ] Add authentication (JWT, OAuth)
- [ ] Configure CORS properly
- [ ] Use environment variables for secrets
- [ ] Enable HTTPS
- [ ] Sanitize user inputs
- [ ] Rate limiting on API endpoints
- [ ] Validate file uploads

## License

MIT

## Contributing

This is an MVP scaffold. Contributions welcome for:
- Production OCR integration
- Vector DB implementation
- Frontend improvements
- Test coverage
- Documentation

## Support

For issues or questions, please refer to:
- Backend README: `backend/README.md`
- Frontend README: `frontend/README.md`
- API Docs: http://localhost:8000/docs

