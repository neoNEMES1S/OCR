"""
Upload API endpoints for direct PDF file uploads.
"""
import logging
import shutil
from pathlib import Path
from datetime import datetime
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from redis import Redis
from rq import Queue

from app.config import get_settings
from app.db import get_db_dependency
from app.models import Document
from app.utils.hashing import compute_sha256

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/upload", tags=["upload"])


class UploadResponse(BaseModel):
    """Response model for file upload."""
    success: bool
    filename: str
    document_id: int
    message: str
    job_id: str


class UploadSummary(BaseModel):
    """Summary of uploaded files."""
    total_files: int
    successful: int
    failed: int
    files: List[dict]


@router.post("", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db_dependency)
):
    """
    Upload a single PDF file for processing.
    
    The file will be:
    1. Saved to storage
    2. Added to database
    3. Enqueued for OCR processing
    
    Args:
        file: PDF file to upload
        db: Database session
        
    Returns:
        Upload status and document ID
        
    Raises:
        HTTPException: If upload fails or file is not a PDF
    """
    # Validate file type
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )
    
    try:
        settings = get_settings()
        storage_dir = Path(settings.STORAGE_PATH)
        storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Create temporary file to compute checksum
        temp_path = storage_dir / f"temp_{file.filename}"
        
        # Save uploaded file temporarily
        with open(temp_path, 'wb') as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Compute checksum
        checksum = compute_sha256(temp_path)
        file_size = temp_path.stat().st_size
        
        # Check if file already exists (by checksum)
        existing = db.query(Document).filter(
            Document.checksum == checksum
        ).first()
        
        if existing:
            # File already exists, remove temp file
            temp_path.unlink()
            logger.info(f"File {file.filename} already exists (checksum match)")
            
            # Re-enqueue if previous ingestion failed
            if existing.ingestion_status == 'error':
                logger.info(f"Re-enqueueing failed document {existing.id}")
                existing.ingestion_status = 'queued'
                db.commit()
                
                # Enqueue ingestion
                redis_conn = Redis.from_url(settings.REDIS_URL)
                queue = Queue('default', connection=redis_conn)
                job = queue.enqueue(
                    'app.workers.ingest_worker.ingest_document',
                    existing.storage_path,
                    existing.id,
                    job_timeout='10m'
                )
                
                return UploadResponse(
                    success=True,
                    filename=file.filename,
                    document_id=existing.id,
                    message=f"File already exists. Re-queued for processing.",
                    job_id=job.id
                )
            
            return UploadResponse(
                success=True,
                filename=file.filename,
                document_id=existing.id,
                message=f"File already exists with status: {existing.ingestion_status}",
                job_id=""
            )
        
        # Create new document record
        doc = Document(
            filename=file.filename,
            source_path=f"upload:{file.filename}",
            checksum=checksum,
            last_modified=datetime.utcnow(),
            file_size=file_size,
            ingestion_status='queued'
        )
        db.add(doc)
        db.flush()  # Get document ID
        
        # Move temp file to permanent storage with document ID
        final_path = storage_dir / f"{doc.id}_{file.filename}"
        temp_path.rename(final_path)
        
        doc.storage_path = str(final_path)
        db.commit()
        
        logger.info(f"File uploaded: {file.filename} (ID: {doc.id})")
        
        # Enqueue ingestion job
        redis_conn = Redis.from_url(settings.REDIS_URL)
        queue = Queue('default', connection=redis_conn)
        
        job = queue.enqueue(
            'app.workers.ingest_worker.ingest_document',
            str(final_path),
            doc.id,
            job_timeout='10m'
        )
        
        logger.info(f"Enqueued ingestion job {job.id} for document {doc.id}")
        
        return UploadResponse(
            success=True,
            filename=file.filename,
            document_id=doc.id,
            message=f"File uploaded successfully. Processing started.",
            job_id=job.id
        )
        
    except Exception as e:
        logger.error(f"Upload failed: {e}", exc_info=True)
        # Cleanup temp file if it exists
        if temp_path.exists():
            temp_path.unlink()
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )


@router.post("/multiple", response_model=UploadSummary)
async def upload_multiple_pdfs(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db_dependency)
):
    """
    Upload multiple PDF files at once.
    
    Args:
        files: List of PDF files
        db: Database session
        
    Returns:
        Summary of upload results
    """
    results = []
    successful = 0
    failed = 0
    
    for file in files:
        try:
            # Reuse single upload endpoint
            result = await upload_pdf(file, db)
            results.append({
                'filename': result.filename,
                'success': True,
                'document_id': result.document_id,
                'message': result.message
            })
            successful += 1
        except Exception as e:
            results.append({
                'filename': file.filename,
                'success': False,
                'document_id': None,
                'message': str(e)
            })
            failed += 1
    
    return UploadSummary(
        total_files=len(files),
        successful=successful,
        failed=failed,
        files=results
    )


@router.get("/status/{document_id}")
async def get_document_status(
    document_id: int,
    db: Session = Depends(get_db_dependency)
):
    """
    Check the processing status of an uploaded document.
    
    Args:
        document_id: Document ID
        db: Database session
        
    Returns:
        Document processing status
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
        'document_id': doc.id,
        'filename': doc.filename,
        'status': doc.ingestion_status,
        'page_count': doc.page_count,
        'error_message': doc.error_msg,
        'ingested_at': doc.ingested_at.isoformat() if doc.ingested_at else None
    }

