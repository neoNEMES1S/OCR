"""
Settings API endpoints for configuring auto-ingest folder and scan options.
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.config import get_settings, save_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


class FolderSettingsResponse(BaseModel):
    """Response model for folder settings."""
    folder_path: str
    include_subfolders: bool
    auto_ingest: bool


class FolderSettingsUpdate(BaseModel):
    """Request model for updating folder settings."""
    folder_path: Optional[str] = None
    include_subfolders: Optional[bool] = None
    auto_ingest: Optional[bool] = None


@router.get("/folder", response_model=FolderSettingsResponse)
async def get_folder_settings():
    """
    Get current folder ingestion settings.
    
    Returns:
        Current folder path, include_subfolders flag, and auto_ingest flag
    """
    settings = get_settings()
    
    return FolderSettingsResponse(
        folder_path=settings.FOLDER_PATH,
        include_subfolders=settings.INCLUDE_SUBFOLDERS,
        auto_ingest=settings.AUTO_INGEST
    )


@router.post("/folder", response_model=FolderSettingsResponse)
async def update_folder_settings(update: FolderSettingsUpdate):
    """
    Update folder ingestion settings.
    
    Settings are persisted to settings.json and will be used for future auto-ingests.
    
    Args:
        update: Settings to update (only provided fields will be changed)
        
    Returns:
        Updated settings
        
    Raises:
        HTTPException: If settings update fails
    """
    try:
        settings = save_settings(
            folder_path=update.folder_path,
            include_subfolders=update.include_subfolders,
            auto_ingest=update.auto_ingest
        )
        
        logger.info(f"Updated folder settings: {update.model_dump(exclude_none=True)}")
        
        return FolderSettingsResponse(
            folder_path=settings.FOLDER_PATH,
            include_subfolders=settings.INCLUDE_SUBFOLDERS,
            auto_ingest=settings.AUTO_INGEST
        )
    except Exception as e:
        logger.error(f"Failed to update settings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")
