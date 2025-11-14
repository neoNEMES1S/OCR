"""
Embeddings generation service stub.

TODO: Replace with production embedding service or optimize model selection
TODO: Consider batch processing for better throughput
TODO: Add embedding caching layer
TODO: Support multiple embedding models (OpenAI, Cohere, etc.)
"""
import logging
import numpy as np
from typing import List

logger = logging.getLogger(__name__)

# Global model instance (lazy loaded)
_model = None
_use_real_model = False  # Set to True to use sentence-transformers


def get_model():
    """
    Lazy load the embedding model.
    
    TODO: Make model selection configurable
    TODO: Add model warmup on startup
    TODO: Support GPU acceleration if available
    """
    global _model
    
    if _model is None and _use_real_model:
        logger.info("Loading sentence-transformers model (this may take a moment)...")
        from sentence_transformers import SentenceTransformer
        # Using a lightweight model for development
        # TODO: Choose production model based on use case (e.g., 'all-mpnet-base-v2')
        _model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("Embedding model loaded")
    
    return _model


def generate_embedding(text: str, model_name: str = "stub") -> List[float]:
    """
    Generate embedding vector for text.
    
    This is a STUB implementation that returns either:
    - Random vectors (if _use_real_model=False)
    - Real embeddings from sentence-transformers (if _use_real_model=True)
    
    Args:
        text: Input text to embed
        model_name: Model identifier (unused in stub)
        
    Returns:
        List of floats representing the embedding vector
        
    TODO: Replace with production embedding service
    TODO: Handle text truncation for max token limits
    TODO: Add error handling and retries
    TODO: Implement batch embedding for efficiency
    """
    if not text or not text.strip():
        logger.warning("Empty text provided for embedding")
        return [0.0] * 384  # Return zero vector
    
    if _use_real_model:
        model = get_model()
        if model:
            # Generate real embedding
            embedding = model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
    
    # STUB: Return random vector for development
    # Dimension 384 matches all-MiniLM-L6-v2 for consistency
    logger.debug(f"Generating stub embedding for text (length: {len(text)})")
    
    # Use hash of text as seed for reproducibility in testing
    seed = hash(text) % (2**32)
    rng = np.random.RandomState(seed)
    vector = rng.randn(384).astype(np.float32)
    
    # Normalize to unit length (common practice for embeddings)
    vector = vector / np.linalg.norm(vector)
    
    return vector.tolist()


def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for multiple texts efficiently.
    
    TODO: Implement true batch processing for better performance
    TODO: Add progress tracking for large batches
    TODO: Handle batch size limits
    
    Args:
        texts: List of text strings
        
    Returns:
        List of embedding vectors
    """
    if _use_real_model:
        model = get_model()
        if model:
            embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
            return [emb.tolist() for emb in embeddings]
    
    # STUB: Generate individually
    return [generate_embedding(text) for text in texts]


def get_embedding_dimension() -> int:
    """
    Return the dimension of embedding vectors.
    
    Returns:
        Embedding dimension size
    """
    if _use_real_model:
        model = get_model()
        if model:
            return model.get_sentence_embedding_dimension()
    
    # Stub dimension (matches all-MiniLM-L6-v2)
    return 384


# Configuration helper
def enable_real_embeddings(enabled: bool = True):
    """
    Enable or disable real embedding generation.
    
    Args:
        enabled: True to use sentence-transformers, False for stub
    """
    global _use_real_model
    _use_real_model = enabled
    logger.info(f"Real embeddings {'enabled' if enabled else 'disabled'}")
