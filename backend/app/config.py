"""
Configuration management for OCR PDF application.
Loads settings from environment variables and settings.json file.
"""
import json
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment and file."""
    
    # Auto-ingest settings
    AUTO_INGEST: bool = True
    FOLDER_PATH: str = "/tmp/pdfs"
    INCLUDE_SUBFOLDERS: bool = False
    
    # Database
    DATABASE_URL: str = "sqlite:///./ocr_dev.db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Storage
    STORAGE_PATH: str = "./storage"
    
    # Full-text search
    FTS_DB_PATH: str = "./fts_index.db"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
_settings: Optional[Settings] = None
_settings_file = Path("settings.json")


def get_settings() -> Settings:
    """Get or create global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
        # Load from settings.json if it exists
        if _settings_file.exists():
            with open(_settings_file, 'r') as f:
                data = json.load(f)
                for key, value in data.items():
                    if hasattr(_settings, key):
                        setattr(_settings, key, value)
    return _settings


def save_settings(folder_path: Optional[str] = None, 
                  include_subfolders: Optional[bool] = None,
                  auto_ingest: Optional[bool] = None) -> Settings:
    """
    Update and persist settings to settings.json file.
    Returns updated settings instance.
    """
    settings = get_settings()
    
    data = {}
    if _settings_file.exists():
        with open(_settings_file, 'r') as f:
            data = json.load(f)
    
    # Update with new values
    if folder_path is not None:
        settings.FOLDER_PATH = folder_path
        data['FOLDER_PATH'] = folder_path
    
    if include_subfolders is not None:
        settings.INCLUDE_SUBFOLDERS = include_subfolders
        data['INCLUDE_SUBFOLDERS'] = include_subfolders
    
    if auto_ingest is not None:
        settings.AUTO_INGEST = auto_ingest
        data['AUTO_INGEST'] = auto_ingest
    
    # Save to file
    with open(_settings_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    return settings


def reload_settings() -> Settings:
    """Force reload settings from file."""
    global _settings
    _settings = None
    return get_settings()
