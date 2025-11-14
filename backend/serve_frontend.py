"""
Alternative main.py that serves the React frontend alongside the API.

This is useful for single-server deployments where you want FastAPI
to serve both the API and the built React application.

Usage:
1. Build the frontend: cd frontend && npm run build
2. Copy frontend/dist to backend/static
3. Run: uvicorn serve_frontend:app --host 0.0.0.0 --port 8000

For production with separate hosting, use app.main:app instead.
"""
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from redis import Redis
from rq import Queue

from app.config import get_settings
from app.db import create_tables, init_fts_table, get_db
from app.models import ScanJob
from app.api.v1 import settings, scan, search

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def scan_on_start():
    """Trigger initial scan on application startup if AUTO_INGEST is enabled."""
    settings_obj = get_settings()
    
    if not settings_obj.AUTO_INGEST:
        logger.info("AUTO_INGEST is disabled, skipping startup scan")
        return
    
    logger.info(f"AUTO_INGEST enabled, scanning folder: {settings_obj.FOLDER_PATH}")
    
    try:
        import uuid
        from datetime import datetime
        
        job_id = f"startup-{uuid.uuid4()}"
        
        with get_db() as db:
            scan_job = ScanJob(
                job_id=job_id,
                scan_path=settings_obj.FOLDER_PATH,
                include_subfolders=settings_obj.INCLUDE_SUBFOLDERS,
                status='running',
                started_at=datetime.utcnow()
            )
            db.add(scan_job)
            db.commit()
        
        redis_conn = Redis.from_url(settings_obj.REDIS_URL)
        queue = Queue('default', connection=redis_conn)
        
        rq_job = queue.enqueue(
            'app.workers.ingest_worker.scan_and_ingest_job',
            settings_obj.FOLDER_PATH,
            settings_obj.INCLUDE_SUBFOLDERS,
            job_id,
            job_timeout='30m'
        )
        
        logger.info(f"Startup scan job enqueued: {job_id} (RQ job: {rq_job.id})")
        
    except Exception as e:
        logger.error(f"Failed to trigger startup scan: {e}", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    logger.info("Starting OCR PDF application...")
    
    create_tables()
    init_fts_table()
    scan_on_start()
    
    logger.info("Application startup complete")
    
    yield
    
    logger.info("Shutting down OCR PDF application...")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application with frontend serving.
    
    Returns:
        Configured FastAPI app instance that serves both API and React frontend
    """
    app = FastAPI(
        title="OCR PDF API",
        description="API for ingesting, processing, and searching PDF documents with OCR",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/api/docs",  # Move docs to /api/docs
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json"
    )
    
    # CORS middleware (less restrictive since frontend is served from same origin)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routers
    app.include_router(settings.router)
    app.include_router(scan.router)
    app.include_router(search.router)
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Basic health check endpoint."""
        return {"status": "healthy", "service": "ocr-pdf-api"}
    
    # Check if frontend static files exist
    static_dir = Path(__file__).parent / "static"
    
    if static_dir.exists():
        # Mount static files (JS, CSS, images)
        app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="assets")
        
        # Serve index.html for all non-API routes (SPA routing)
        @app.get("/{full_path:path}")
        async def serve_frontend(full_path: str):
            """
            Serve the React SPA for all routes not handled by API.
            This enables client-side routing to work properly.
            """
            # Don't serve frontend for API routes
            if full_path.startswith("api/") or full_path.startswith("health"):
                return {"error": "Not found"}
            
            index_file = static_dir / "index.html"
            if index_file.exists():
                return FileResponse(index_file)
            else:
                return {"error": "Frontend not built. Run: cd frontend && npm run build"}
    else:
        logger.warning(f"Static directory not found: {static_dir}")
        logger.warning("Frontend will not be served. Build frontend and copy to backend/static/")
        
        @app.get("/")
        async def root():
            """Root endpoint with setup instructions."""
            return {
                "message": "OCR PDF API",
                "version": "0.1.0",
                "note": "Frontend not available. To enable:",
                "steps": [
                    "1. cd frontend && npm run build",
                    "2. mkdir -p backend/static",
                    "3. cp -r frontend/dist/* backend/static/",
                    "4. Restart server"
                ],
                "api_docs": "/api/docs"
            }
    
    return app


# Create app instance
app = create_app()

