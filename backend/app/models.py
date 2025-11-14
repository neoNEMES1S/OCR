"""
SQLAlchemy ORM models for OCR PDF application.
Postgres-ready schema with SQLite fallback.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Document(Base):
    """
    Represents a PDF document in the system.
    Tracks ingestion status and metadata.
    """
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False, index=True)
    source_path = Column(String(512), nullable=False)
    storage_path = Column(String(512), nullable=True)  # Where we stored the file
    checksum = Column(String(64), nullable=False, index=True)  # SHA256
    last_modified = Column(DateTime, nullable=False)
    
    # Ingestion tracking
    ingested_at = Column(DateTime, nullable=True)
    ingestion_status = Column(
        String(20), 
        nullable=False, 
        default='queued',
        index=True
    )  # queued, processing, done, error
    error_msg = Column(Text, nullable=True)
    
    # Metadata
    page_count = Column(Integer, nullable=True)
    file_size = Column(Integer, nullable=True)  # bytes
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")


class Chunk(Base):
    """
    Represents a chunk of text from a document page.
    Links to embeddings stored in vector DB.
    """
    __tablename__ = "chunks"
    
    chunk_id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    page_no = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    
    # OCR metadata
    bbox_range = Column(JSON, nullable=True)  # Bounding box coordinates as JSON
    ocr_confidence = Column(Float, nullable=True)  # Average confidence score
    
    # Vector DB reference
    embedding_id = Column(String(128), nullable=True)  # ID in vector store
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document", back_populates="chunks")


class ScanJob(Base):
    """
    Tracks background scan jobs triggered by API or startup.
    """
    __tablename__ = "scan_jobs"
    
    job_id = Column(String(64), primary_key=True)  # RQ job ID
    scan_path = Column(String(512), nullable=False)
    include_subfolders = Column(Boolean, nullable=False, default=False)
    
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Summary stats
    new_files = Column(Integer, nullable=True, default=0)
    skipped_files = Column(Integer, nullable=True, default=0)
    error_count = Column(Integer, nullable=True, default=0)
    errors = Column(JSON, nullable=True)  # List of error messages
    
    status = Column(String(20), nullable=False, default='running')  # running, completed, failed
