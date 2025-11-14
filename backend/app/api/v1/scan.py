"""
Scan API endpoints for triggering manual folder rescans.
"""
import logging
import uuid
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from redis import Redis
from rq import Queue

from app.config import get_settings
from app.db import get_db_dependency
from app.models import ScanJob

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/scan", tags=["scan"])


class ScanRequest(BaseModel):
    """Request model for triggering a scan."""
    path: Optional[str] = None  # If None, use config default
    include_subfolders: Optional[bool] = None  # If None, use config default


class ScanResponse(BaseModel):
    """Response model for scan trigger."""
    job_id: str
    scan_path: str
    include_subfolders: bool
    message: str


class ScanJobStatus(BaseModel):
    """Response model for scan job status."""
    job_id: str
    scan_path: str
    include_subfolders: bool
    started_at: datetime
    completed_at: Optional[datetime]
    status: str  # running, completed, failed
    new_files: Optional[int]
    skipped_files: Optional[int]
    error_count: Optional[int]
    errors: Optional[List[str]]


def get_queue():
    """Get RQ queue instance."""
    settings = get_settings()
    redis_conn = Redis.from_url(settings.REDIS_URL)
    return Queue('default', connection=redis_conn)


@router.post("", response_model=ScanResponse)
async def trigger_scan(
    request: ScanRequest = ScanRequest(),
    db: Session = Depends(get_db_dependency)
):
    """
    Trigger a background scan job to ingest PDFs from a folder.
    
    The scan job will:
    1. Discover PDF files in the specified folder
    2. Check for new or modified files (using checksums)
    3. Enqueue ingestion jobs for changed files
    4. Update scan job status with summary
    
    Args:
        request: Scan parameters (path and include_subfolders)
        db: Database session
        
    Returns:
        Job ID and scan parameters
        
    Raises:
        HTTPException: If scan trigger fails
    """
    try:
        settings = get_settings()
        
        # Use provided values or fall back to config
        scan_path = request.path if request.path else settings.FOLDER_PATH
        include_subfolders = (
            request.include_subfolders 
            if request.include_subfolders is not None 
            else settings.INCLUDE_SUBFOLDERS
        )
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Create scan job record
        scan_job = ScanJob(
            job_id=job_id,
            scan_path=scan_path,
            include_subfolders=include_subfolders,
            status='running'
        )
        db.add(scan_job)
        db.commit()
        
        # Enqueue background job
        queue = get_queue()
        rq_job = queue.enqueue(
            'app.workers.ingest_worker.scan_and_ingest_job',
            scan_path,
            include_subfolders,
            job_id,
            job_timeout='30m'
        )
        
        logger.info(f"Triggered scan job {job_id} for path: {scan_path} (RQ job: {rq_job.id})")
        
        return ScanResponse(
            job_id=job_id,
            scan_path=scan_path,
            include_subfolders=include_subfolders,
            message=f"Scan job started. Track progress at /api/v1/scan/{job_id}"
        )
        
    except Exception as e:
        logger.error(f"Failed to trigger scan: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to trigger scan: {str(e)}")


@router.get("/{job_id}", response_model=ScanJobStatus)
async def get_scan_status(job_id: str, db: Session = Depends(get_db_dependency)):
    """
    Get status and results of a scan job.
    
    Args:
        job_id: Scan job identifier
        db: Database session
        
    Returns:
        Scan job status and summary
        
    Raises:
        HTTPException: If job not found
    """
    scan_job = db.query(ScanJob).filter(ScanJob.job_id == job_id).first()
    
    if not scan_job:
        raise HTTPException(status_code=404, detail=f"Scan job {job_id} not found")
    
    return ScanJobStatus(
        job_id=scan_job.job_id,
        scan_path=scan_job.scan_path,
        include_subfolders=scan_job.include_subfolders,
        started_at=scan_job.started_at,
        completed_at=scan_job.completed_at,
        status=scan_job.status,
        new_files=scan_job.new_files,
        skipped_files=scan_job.skipped_files,
        error_count=scan_job.error_count,
        errors=scan_job.errors
    )
