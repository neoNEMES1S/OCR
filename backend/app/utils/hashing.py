"""
File hashing utilities for checksum computation.
"""
import hashlib
from pathlib import Path


def compute_sha256(file_path: str | Path) -> str:
    """
    Compute SHA256 checksum of a file.
    
    Args:
        file_path: Path to file
        
    Returns:
        Hex string of SHA256 hash
    """
    sha256_hash = hashlib.sha256()
    
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    return sha256_hash.hexdigest()
