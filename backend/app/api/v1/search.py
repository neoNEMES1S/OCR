"""
Search API endpoints for full-text and semantic search.
"""
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db_dependency, search_fts
from app.models import Document, Chunk
from app.services.embeddings_stub import generate_embedding
from app.services.vector_client import query_vectors

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/search", tags=["search"])


class SearchResult(BaseModel):
    """Search result for a single chunk."""
    document_id: int
    filename: str
    page_no: int
    snippet: str
    score: float
    chunk_id: Optional[int] = None
    bbox: Optional[Dict[str, Any]] = None


class FullTextSearchResponse(BaseModel):
    """Response model for full-text search."""
    query: str
    total_results: int
    page: int
    page_size: int
    results: List[SearchResult]


class SemanticSearchRequest(BaseModel):
    """Request model for semantic search."""
    query: str
    top_k: int = 10
    filters: Optional[Dict[str, Any]] = None


class SemanticSearchResponse(BaseModel):
    """Response model for semantic search."""
    query: str
    results: List[SearchResult]


@router.get("/fulltext", response_model=FullTextSearchResponse)
async def fulltext_search(
    q: str = Query(..., description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page"),
    db: Session = Depends(get_db_dependency)
):
    """
    Perform full-text search using SQLite FTS5.
    
    Searches through all indexed document chunks and returns matching results
    with highlighted snippets.
    
    Args:
        q: Search query (supports FTS5 query syntax)
        page: Page number (1-indexed)
        page_size: Number of results per page
        db: Database session
        
    Returns:
        Paginated search results with snippets
        
    Raises:
        HTTPException: If search fails
    """
    try:
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Search FTS5 index
        fts_results = search_fts(q, limit=page_size, offset=offset)
        
        if not fts_results:
            return FullTextSearchResponse(
                query=q,
                total_results=0,
                page=page,
                page_size=page_size,
                results=[]
            )
        
        # Fetch document details
        doc_ids = [r['doc_id'] for r in fts_results]
        documents = db.query(Document).filter(Document.id.in_(doc_ids)).all()
        doc_map = {doc.id: doc for doc in documents}
        
        # Fetch chunk details for bbox
        chunk_ids = [r['chunk_id'] for r in fts_results]
        chunks = db.query(Chunk).filter(Chunk.chunk_id.in_(chunk_ids)).all()
        chunk_map = {chunk.chunk_id: chunk for chunk in chunks}
        
        # Build results
        results = []
        for fts_result in fts_results:
            doc = doc_map.get(fts_result['doc_id'])
            chunk = chunk_map.get(fts_result['chunk_id'])
            
            if doc:
                results.append(SearchResult(
                    document_id=doc.id,
                    filename=doc.filename,
                    page_no=fts_result['page_no'],
                    snippet=fts_result['snippet'],
                    score=abs(fts_result['rank']),  # FTS5 rank is negative
                    chunk_id=fts_result['chunk_id'],
                    bbox=chunk.bbox_range if chunk else None
                ))
        
        # TODO: Get accurate total count (FTS5 doesn't provide it directly)
        total_results = len(results)
        
        logger.info(f"Full-text search for '{q}' returned {len(results)} results")
        
        return FullTextSearchResponse(
            query=q,
            total_results=total_results,
            page=page,
            page_size=page_size,
            results=results
        )
        
    except Exception as e:
        logger.error(f"Full-text search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/semantic", response_model=SemanticSearchResponse)
async def semantic_search(
    request: SemanticSearchRequest,
    db: Session = Depends(get_db_dependency)
):
    """
    Perform semantic search using vector similarity.
    
    Converts the query to an embedding and finds similar document chunks
    using vector search.
    
    Args:
        request: Search request with query and parameters
        db: Database session
        
    Returns:
        Semantically similar search results
        
    Raises:
        HTTPException: If search fails
    """
    try:
        # Generate embedding for query
        query_embedding = generate_embedding(request.query)
        
        # Query vector database
        vector_results = query_vectors(
            vector=query_embedding,
            top_k=request.top_k,
            filters=request.filters
        )
        
        if not vector_results:
            return SemanticSearchResponse(
                query=request.query,
                results=[]
            )
        
        # Fetch document and chunk details
        chunk_ids = [r['metadata']['chunk_id'] for r in vector_results]
        chunks = db.query(Chunk).filter(Chunk.chunk_id.in_(chunk_ids)).all()
        chunk_map = {chunk.chunk_id: chunk for chunk in chunks}
        
        doc_ids = [chunk.document_id for chunk in chunks]
        documents = db.query(Document).filter(Document.id.in_(doc_ids)).all()
        doc_map = {doc.id: doc for doc in documents}
        
        # Build results
        results = []
        for vec_result in vector_results:
            chunk_id = vec_result['metadata']['chunk_id']
            chunk = chunk_map.get(chunk_id)
            
            if chunk:
                doc = doc_map.get(chunk.document_id)
                if doc:
                    # Create snippet from chunk text
                    snippet = chunk.text[:200] + "..." if len(chunk.text) > 200 else chunk.text
                    
                    results.append(SearchResult(
                        document_id=doc.id,
                        filename=doc.filename,
                        page_no=chunk.page_no,
                        snippet=snippet,
                        score=vec_result['score'],
                        chunk_id=chunk.chunk_id,
                        bbox=chunk.bbox_range
                    ))
        
        logger.info(f"Semantic search for '{request.query}' returned {len(results)} results")
        
        return SemanticSearchResponse(
            query=request.query,
            results=results
        )
        
    except Exception as e:
        logger.error(f"Semantic search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
