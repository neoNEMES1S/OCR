# OCR PDF Backend

Python backend for OCR PDF processing with FastAPI, RQ workers, and SQLite.

## Features

- **Auto-ingestion**: Automatically scans configured folder on startup
- **Manual scan**: Trigger scans via API
- **Full-text search**: SQLite FTS5 for keyword search
- **Semantic search**: Vector similarity search (stub)
- **Worker queue**: RQ with Redis for background processing
- **Configurable**: Settings API for runtime configuration

## Prerequisites

- Python 3.11+
- Redis server
- pip or virtualenv

## Setup

### 1. Create virtual environment

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

Copy `.env.example` to `.env` and adjust settings:

```bash
AUTO_INGEST=true
FOLDER_PATH=/tmp/pdfs
INCLUDE_SUBFOLDERS=true
DATABASE_URL=sqlite:///./ocr_dev.db
REDIS_URL=redis://localhost:6379/0
STORAGE_PATH=./storage
FTS_DB_PATH=./fts_index.db
```

### 4. Start Redis

Using Docker:

```bash
docker run -p 6379:6379 redis
```

Or install Redis locally and start:

```bash
redis-server
```

### 5. Start RQ worker

In a separate terminal (with venv activated):

```bash
cd backend
rq worker app.workers
```

### 6. Start FastAPI server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: http://localhost:8000

API documentation: http://localhost:8000/docs

## API Usage

### Set folder settings

```bash
curl -X POST http://localhost:8000/api/v1/settings/folder \
  -H "Content-Type: application/json" \
  -d '{
    "folder_path": "/tmp/pdfs",
    "include_subfolders": true,
    "auto_ingest": true
  }'
```

### Get folder settings

```bash
curl http://localhost:8000/api/v1/settings/folder
```

### Trigger manual scan

```bash
curl -X POST http://localhost:8000/api/v1/scan \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/tmp/pdfs",
    "include_subfolders": true
  }'
```

Response includes `job_id` for tracking.

### Check scan status

```bash
curl http://localhost:8000/api/v1/scan/{job_id}
```

### Full-text search

```bash
curl "http://localhost:8000/api/v1/search/fulltext?q=invoice&page=1&page_size=20"
```

### Semantic search

```bash
curl -X POST http://localhost:8000/api/v1/search/semantic \
  -H "Content-Type: application/json" \
  -d '{
    "query": "contract termination clause",
    "top_k": 5
  }'
```

## Testing

Run tests with pytest:

```bash
pytest
```

Run specific test file:

```bash
pytest app/tests/test_scanner.py
```

Run with coverage:

```bash
pytest --cov=app --cov-report=html
```

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app factory
│   ├── config.py            # Configuration management
│   ├── db.py                # Database setup and FTS helpers
│   ├── models.py            # SQLAlchemy models
│   ├── api/
│   │   └── v1/
│   │       ├── settings.py  # Settings endpoints
│   │       ├── scan.py      # Scan endpoints
│   │       └── search.py    # Search endpoints
│   ├── workers/
│   │   ├── scanner.py       # File scanner
│   │   └── ingest_worker.py # RQ ingestion tasks
│   ├── services/
│   │   ├── ocr_stub.py      # OCR stub (pdfminer)
│   │   ├── embeddings_stub.py # Embedding stub
│   │   └── vector_client.py # Vector DB stub
│   ├── utils/
│   │   └── hashing.py       # File hashing utilities
│   └── tests/
│       ├── test_scanner.py  # Scanner tests
│       └── test_scan_endpoint.py # API tests
├── requirements.txt
└── README.md
```

## Architecture

### Auto-Ingest Flow

1. On startup, if `AUTO_INGEST=true`, app calls `scan_on_start()`
2. Scanner discovers PDFs in configured folder
3. For each file, compute SHA256 checksum
4. If new or changed, create Document record and enqueue ingestion job
5. RQ worker processes job: OCR → embeddings → vector DB → FTS index

### Manual Scan Flow

1. Client POSTs to `/api/v1/scan`
2. API creates ScanJob record
3. Background RQ task runs scanner and enqueues ingestion
4. Client polls `/api/v1/scan/{job_id}` for status

### Search Flow

**Full-text:**
1. Query FTS5 index with SQLite
2. Fetch document metadata
3. Return grouped results with snippets

**Semantic:**
1. Generate query embedding
2. Query vector DB for similar chunks
3. Fetch document metadata
4. Return ranked results

## Stubs and TODOs

The current implementation uses stubs for:

- **OCR**: `pdfminer.six` for native PDFs only (no scanned document OCR)
  - TODO: Integrate Tesseract or AWS Textract
- **Embeddings**: Random vectors (or sentence-transformers if enabled)
  - TODO: Use production embedding service (OpenAI, Cohere, etc.)
- **Vector DB**: In-memory dictionary
  - TODO: Integrate Qdrant, Pinecone, or Weaviate

See `TODO` comments in source files for detailed implementation notes.

## Development

### Enable real embeddings

To use sentence-transformers instead of random vectors:

```python
from app.services.embeddings_stub import enable_real_embeddings
enable_real_embeddings(True)
```

### Database migrations

For schema changes, consider using Alembic:

```bash
pip install alembic
alembic init alembic
# Create migrations and apply
```

## Troubleshooting

### Redis connection error

Ensure Redis is running:

```bash
redis-cli ping
# Should return: PONG
```

### Worker not processing jobs

Check RQ worker logs and ensure it's connected to the same Redis instance.

### PDF processing fails

Check that PDFs are valid and not encrypted. Current stub only supports native (digital) PDFs, not scanned images.

## License

MIT
