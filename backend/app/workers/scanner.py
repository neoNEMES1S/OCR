"""
File system scanner for discovering PDF files.
Idempotent scanning with checksum-based change detection.
"""
import os
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from app.utils.hashing import compute_sha256

logger = logging.getLogger(__name__)


def scan_folder(path: str, include_subfolders: bool = False) -> List[Dict[str, Any]]:
    """
    Scan a folder for PDF files and return metadata.
    
    Args:
        path: Root folder path to scan
        include_subfolders: Whether to recursively scan subdirectories
        
    Returns:
        List of dictionaries containing:
        - path: Full file path
        - filename: Base filename
        - sha256: File checksum
        - last_modified: Last modification datetime
        - file_size: File size in bytes
        
    Raises:
        FileNotFoundError: If path does not exist
        PermissionError: If path is not accessible
    """
    folder_path = Path(path)
    
    if not folder_path.exists():
        raise FileNotFoundError(f"Folder not found: {path}")
    
    if not folder_path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {path}")
    
    discovered_files = []
    
    if include_subfolders:
        # Use os.walk for recursive scanning
        for root, dirs, files in os.walk(folder_path):
            for filename in files:
                if filename.lower().endswith('.pdf'):
                    file_path = Path(root) / filename
                    try:
                        file_info = _get_file_info(file_path)
                        discovered_files.append(file_info)
                        logger.info(f"Discovered: {file_path}")
                    except Exception as e:
                        logger.error(f"Error processing {file_path}: {e}")
    else:
        # Only scan immediate directory
        for item in folder_path.iterdir():
            if item.is_file() and item.name.lower().endswith('.pdf'):
                try:
                    file_info = _get_file_info(item)
                    discovered_files.append(file_info)
                    logger.info(f"Discovered: {item}")
                except Exception as e:
                    logger.error(f"Error processing {item}: {e}")
    
    logger.info(f"Scan complete. Found {len(discovered_files)} PDF files in {path}")
    return discovered_files


def _get_file_info(file_path: Path) -> Dict[str, Any]:
    """
    Extract metadata from a single file.
    
    Args:
        file_path: Path to file
        
    Returns:
        Dictionary with file metadata
    """
    stat = file_path.stat()
    
    return {
        'path': str(file_path.absolute()),
        'filename': file_path.name,
        'sha256': compute_sha256(file_path),
        'last_modified': datetime.fromtimestamp(stat.st_mtime),
        'file_size': stat.st_size
    }


def should_ingest_file(existing_checksum: str | None, 
                       existing_modified: datetime | None,
                       new_checksum: str,
                       new_modified: datetime) -> bool:
    """
    Determine if a file should be (re-)ingested based on checksum and timestamp.
    
    Args:
        existing_checksum: Checksum from database (None if new file)
        existing_modified: Last modified time from database
        new_checksum: Current file checksum
        new_modified: Current file modification time
        
    Returns:
        True if file should be ingested
    """
    # New file
    if existing_checksum is None:
        return True
    
    # Checksum changed - file content modified
    if existing_checksum != new_checksum:
        return True
    
    # File unchanged
    return False
