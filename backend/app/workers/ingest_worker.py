"""
RQ worker tasks for document ingestion pipeline.
Coordinates OCR, embedding generation, and vector DB indexing.
"""
import logging
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional
from rq import get_current_job
from rq.job import Job

from app.config import get_settings
from app.db import get_db, index_chunk_fts
from app.models import Document, Chunk, ScanJob
from app.services.ocr_stub import process_pdf
from app.services.embeddings_stub import generate_embedding
from app.services.vector_client import upsert_vector
from app.workers.scanner import scan_folder, should_ingest_file

logger = logging.getLogger(__name__)


def enqueue_ingest(queue, file_path: str, document_id: int) -> Job:
    """
    Enqueue an ingestion job for a document.
    
    Args:
        queue: RQ queue instance
        file_path: Path to PDF file
        document_id: Database ID of document record
        
    Returns:
        RQ Job instance
    """
    job = queue.enqueue(
        'app.workers.ingest_worker.ingest_document',
        file_path,
        document_id,
        job_timeout='10m',
        result_ttl=86400  # Keep results for 24 hours
    )
    logger.info(f"Enqueued ingestion job {job.id} for document {document_id}")
    return job


def ingest_document(file_path: str, document_id: int):
    """
    RQ task: Process a single PDF document through the ingestion pipeline.
    
    Steps:
    1. Copy file to storage
    2. Run OCR to extract text and layout
    3. Create chunk records
    4. Generate embeddings for each chunk
    5. Store embeddings in vector DB
    6. Index chunks in FTS5
    
    Args:
        file_path: Path to source PDF file
        document_id: Database ID of document
        
    TODO: Add retry logic with exponential backoff
    TODO: Handle partial failures (e.g., OCR succeeds but embedding fails)
    """
    job = get_current_job()
    logger.info(f"Starting ingestion for document {document_id} (job {job.id})")
    
    with get_db() as db:
        # Get document record
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            logger.error(f"Document {document_id} not found")
            return
        
        try:
            # Update status
            doc.ingestion_status = 'processing'
            db.commit()
            
            # Step 1: Copy file to storage
            settings = get_settings()
            storage_dir = Path(settings.STORAGE_PATH)
            storage_dir.mkdir(parents=True, exist_ok=True)
            
            storage_path = storage_dir / f"{document_id}_{Path(file_path).name}"
            shutil.copy2(file_path, storage_path)
            doc.storage_path = str(storage_path)
            db.commit()
            
            logger.info(f"Copied file to storage: {storage_path}")
            
            # Step 2: Run OCR
            ocr_results = process_pdf(str(storage_path))
            doc.page_count = len(ocr_results['pages'])
            db.commit()
            
            logger.info(f"OCR extracted {len(ocr_results['pages'])} pages")
            
            # Step 3-6: Process each page
            for page_data in ocr_results['pages']:
                page_no = page_data['page_no']
                text = page_data['text']
                bbox = page_data.get('bbox')
                confidence = page_data.get('confidence')
                
                if not text.strip():
                    logger.warning(f"Page {page_no} has no text, skipping")
                    continue
                
                # Create chunk record
                chunk = Chunk(
                    document_id=document_id,
                    page_no=page_no,
                    text=text,
                    bbox_range=bbox,
                    ocr_confidence=confidence
                )
                db.add(chunk)
                db.flush()  # Get chunk_id
                
                # Generate embedding
                try:
                    embedding = generate_embedding(text)
                    
                    # Store in vector DB
                    vector_id = upsert_vector(
                        vector=embedding,
                        metadata={
                            'document_id': document_id,
                            'chunk_id': chunk.chunk_id,
                            'page_no': page_no,
                            'filename': doc.filename
                        }
                    )
                    chunk.embedding_id = vector_id
                    
                    logger.info(f"Generated embedding for chunk {chunk.chunk_id}")
                except Exception as e:
                    logger.error(f"Embedding generation failed for chunk {chunk.chunk_id}: {e}")
                    # Continue with other chunks
                
                # Index in FTS5
                try:
                    index_chunk_fts(chunk.chunk_id, document_id, page_no, text)
                    logger.info(f"Indexed chunk {chunk.chunk_id} in FTS")
                except Exception as e:
                    logger.error(f"FTS indexing failed for chunk {chunk.chunk_id}: {e}")
                
                db.commit()
            
            # Mark as complete
            doc.ingestion_status = 'done'
            doc.ingested_at = datetime.utcnow()
            doc.error_msg = None
            db.commit()
            
            logger.info(f"Ingestion complete for document {document_id}")
            
        except Exception as e:
            logger.error(f"Ingestion failed for document {document_id}: {e}", exc_info=True)
            doc.ingestion_status = 'error'
            doc.error_msg = str(e)
            db.commit()
            raise


def scan_and_ingest_job(scan_path: str, include_subfolders: bool, job_id: str):
    """
    RQ task: Scan a folder and enqueue ingestion jobs for new/changed files.
    Updates ScanJob record with progress.
    
    Args:
        scan_path: Folder path to scan
        include_subfolders: Whether to scan recursively
        job_id: ScanJob database record ID
    """
    logger.info(f"Starting scan job {job_id} for path: {scan_path}")
    
    from rq import Queue
    from redis import Redis
    from app.config import get_settings
    
    settings = get_settings()
    redis_conn = Redis.from_url(settings.REDIS_URL)
    queue = Queue('default', connection=redis_conn)
    
    new_count = 0
    skipped_count = 0
    errors = []
    
    with get_db() as db:
        scan_job = db.query(ScanJob).filter(ScanJob.job_id == job_id).first()
        
        try:
            # Discover files
            files = scan_folder(scan_path, include_subfolders)
            
            for file_info in files:
                try:
                    # Check if file exists in DB
                    existing = db.query(Document).filter(
                        Document.source_path == file_info['path']
                    ).first()
                    
                    if existing:
                        # Check if changed
                        if should_ingest_file(
                            existing.checksum,
                            existing.last_modified,
                            file_info['sha256'],
                            file_info['last_modified']
                        ):
                            # Update and re-ingest
                            existing.checksum = file_info['sha256']
                            existing.last_modified = file_info['last_modified']
                            existing.file_size = file_info['file_size']
                            existing.ingestion_status = 'queued'
                            db.commit()
                            
                            enqueue_ingest(queue, file_info['path'], existing.id)
                            new_count += 1
                            logger.info(f"Re-ingesting changed file: {file_info['filename']}")
                        else:
                            skipped_count += 1
                            logger.info(f"Skipping unchanged file: {file_info['filename']}")
                    else:
                        # Create new document record
                        doc = Document(
                            filename=file_info['filename'],
                            source_path=file_info['path'],
                            checksum=file_info['sha256'],
                            last_modified=file_info['last_modified'],
                            file_size=file_info['file_size'],
                            ingestion_status='queued'
                        )
                        db.add(doc)
                        db.flush()
                        
                        enqueue_ingest(queue, file_info['path'], doc.id)
                        new_count += 1
                        logger.info(f"Ingesting new file: {file_info['filename']}")
                        
                        db.commit()
                        
                except Exception as e:
                    error_msg = f"Error processing {file_info.get('filename', 'unknown')}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            # Update scan job
            if scan_job:
                scan_job.new_files = new_count
                scan_job.skipped_files = skipped_count
                scan_job.error_count = len(errors)
                scan_job.errors = errors if errors else None
                scan_job.status = 'completed'
                scan_job.completed_at = datetime.utcnow()
                db.commit()
            
            logger.info(f"Scan job {job_id} complete: {new_count} new, {skipped_count} skipped")
            
        except Exception as e:
            logger.error(f"Scan job {job_id} failed: {e}", exc_info=True)
            if scan_job:
                scan_job.status = 'failed'
                scan_job.error_count = len(errors) + 1
                errors.append(f"Scan failed: {str(e)}")
                scan_job.errors = errors
                scan_job.completed_at = datetime.utcnow()
                db.commit()
            raise
