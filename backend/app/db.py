"""
Database connection management and session factory.
"""
import sqlite3
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import get_settings
from app.models import Base


# SQLAlchemy engine
_engine = None
_SessionLocal = None


def get_engine():
    """Get or create database engine."""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(
            settings.DATABASE_URL,
            connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
            echo=False
        )
    return _engine


def get_session_factory():
    """Get or create session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _SessionLocal


def create_tables():
    """Create all database tables."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Database session context manager.
    Use in with statement or as dependency.
    """
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db_dependency():
    """FastAPI dependency for database session."""
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()


# Full-text search (FTS5) helpers

def get_fts_connection():
    """Get connection to FTS5 database."""
    settings = get_settings()
    return sqlite3.connect(settings.FTS_DB_PATH)


def init_fts_table():
    """Initialize FTS5 table for full-text search."""
    conn = get_fts_connection()
    try:
        cursor = conn.cursor()
        # Create FTS5 virtual table
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS fts_chunks USING fts5(
                content,
                doc_id UNINDEXED,
                chunk_id UNINDEXED,
                page_no UNINDEXED,
                tokenize='porter unicode61'
            )
        """)
        conn.commit()
    finally:
        conn.close()


def index_chunk_fts(chunk_id: int, doc_id: int, page_no: int, content: str):
    """Add or update a chunk in the FTS index."""
    conn = get_fts_connection()
    try:
        cursor = conn.cursor()
        # Delete existing if any
        cursor.execute("DELETE FROM fts_chunks WHERE chunk_id = ?", (chunk_id,))
        # Insert new
        cursor.execute(
            "INSERT INTO fts_chunks (content, doc_id, chunk_id, page_no) VALUES (?, ?, ?, ?)",
            (content, doc_id, chunk_id, page_no)
        )
        conn.commit()
    finally:
        conn.close()


def search_fts(query: str, limit: int = 20, offset: int = 0):
    """
    Search FTS5 index and return matching chunks.
    Returns list of dicts with chunk_id, doc_id, page_no, snippet, rank.
    """
    conn = get_fts_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                chunk_id,
                doc_id,
                page_no,
                snippet(fts_chunks, 0, '<mark>', '</mark>', '...', 32) as snippet,
                rank
            FROM fts_chunks
            WHERE fts_chunks MATCH ?
            ORDER BY rank
            LIMIT ? OFFSET ?
        """, (query, limit, offset))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'chunk_id': row[0],
                'doc_id': row[1],
                'page_no': row[2],
                'snippet': row[3],
                'rank': row[4]
            })
        return results
    finally:
        conn.close()
