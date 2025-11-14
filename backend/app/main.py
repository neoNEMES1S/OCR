"""
FastAPI application factory and startup configuration.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis import Redis
from rq import Queue

from app.config import get_settings
from app.db import create_tables, init_fts_table, get_db
from app.models import ScanJob
from app.api.v1 import settings, scan, search, upload

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def scan_on_start():
    """
    Trigger initial scan on application startup if AUTO_INGEST is enabled.
    
    This function is called during FastAPI startup event.
    It discovers PDFs in the configured folder and enqueues ingestion jobs.
    """
    settings = get_settings()
    
    if not settings.AUTO_INGEST:
        logger.info("AUTO_INGEST is disabled, skipping startup scan")
        return
    
    logger.info(f"AUTO_INGEST enabled, scanning folder: {settings.FOLDER_PATH}")
    
    try:
        import uuid
        from datetime import datetime
        
        # Create scan job record
        job_id = f"startup-{uuid.uuid4()}"
        
        with get_db() as db:
            scan_job = ScanJob(
                job_id=job_id,
                scan_path=settings.FOLDER_PATH,
                include_subfolders=settings.INCLUDE_SUBFOLDERS,
                status='running',
                started_at=datetime.utcnow()
            )
            db.add(scan_job)
            db.commit()
        
        # Enqueue background scan job
        redis_conn = Redis.from_url(settings.REDIS_URL)
        queue = Queue('default', connection=redis_conn)
        
        rq_job = queue.enqueue(
            'app.workers.ingest_worker.scan_and_ingest_job',
            settings.FOLDER_PATH,
            settings.INCLUDE_SUBFOLDERS,
            job_id,
            job_timeout='30m'
        )
        
        logger.info(f"Startup scan job enqueued: {job_id} (RQ job: {rq_job.id})")
        
    except Exception as e:
        logger.error(f"Failed to trigger startup scan: {e}", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting OCR PDF application...")
    
    # Initialize database tables
    logger.info("Initializing database tables...")
    create_tables()
    
    # Initialize FTS5 table
    logger.info("Initializing FTS5 index...")
    init_fts_table()
    
    # Trigger startup scan if configured
    scan_on_start()
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down OCR PDF application...")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        Configured FastAPI app instance
    """
    app = FastAPI(
        title="OCR PDF API",
        description="API for ingesting, processing, and searching PDF documents with OCR",
        version="0.1.0",
        lifespan=lifespan
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # TODO: Configure for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(settings.router)
    app.include_router(scan.router)
    app.include_router(search.router)
    app.include_router(upload.router)
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Basic health check endpoint."""
        return {"status": "healthy", "service": "ocr-pdf-api"}
    
    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        return {
            "message": "OCR PDF API",
            "version": "0.1.0",
            "docs": "/docs",
            "endpoints": {
                "settings": "/api/v1/settings/folder",
                "scan": "/api/v1/scan",
                "search": {
                    "fulltext": "/api/v1/search/fulltext",
                    "semantic": "/api/v1/search/semantic"
                }
            }
        }
    
    return app


# Create app instance
app = create_app()
