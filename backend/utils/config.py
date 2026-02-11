"""
Configuration Management for Industrial Land Monitoring System
Handles environment variables and application settings
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application configuration settings"""
    
    # Application
    APP_NAME: str = "CSIDC Industrial Land Monitoring System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database Configuration
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/csidc_monitoring"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    
    # PostGIS Settings
    POSTGIS_VERSION: str = "3.3"
    SRID: int = 4326  # WGS84
    
    # Google Earth Engine
    GEE_PROJECT_ID: Optional[str] = None
    GEE_SERVICE_ACCOUNT: Optional[str] = None
    GEE_PRIVATE_KEY_PATH: Optional[str] = None
    
    # Machine Learning
    ML_MODEL_PATH: str = "./models/weights"
    UNET_WEIGHTS: str = "unet_builtup_v1.pth"
    SIAMESE_WEIGHTS: str = "siamese_change_v1.pth"
    ML_DEVICE: str = "cuda"  # or "cpu"
    ML_BATCH_SIZE: int = 4
    
    # Sentinel-2 Settings
    SENTINEL_CLOUD_THRESHOLD: int = 20
    SENTINEL_SCALE: int = 10  # 10m resolution
    
    # Landsat Settings
    LANDSAT_SCALE: int = 30  # 30m resolution
    
    # Detection Thresholds
    ENCROACHMENT_THRESHOLD: float = 0.01  # 1% outside boundary
    ILLEGAL_CONSTRUCTION_THRESHOLD: float = 1.10  # 10% over approved
    UNUSED_LAND_HEATMAP_THRESHOLD: float = 0.05
    CHANGE_DETECTION_THRESHOLD: float = 0.70  # 70% change confidence
    
    # File Storage
    TEMP_STORAGE_PATH: str = "./temp"
    EXPORT_STORAGE_PATH: str = "./exports"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"
    LOG_ROTATION: str = "500 MB"
    LOG_RETENTION: str = "30 days"
    
    # Security
    SECRET_KEY: str = "change-this-in-production-use-strong-random-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8080"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Dependency function to get application settings
    
    Returns:
        Settings: Application configuration
    """
    return settings


# Create required directories
def setup_directories():
    """Create required directories if they don't exist"""
    directories = [
        settings.TEMP_STORAGE_PATH,
        settings.EXPORT_STORAGE_PATH,
        settings.ML_MODEL_PATH,
        os.path.dirname(settings.LOG_FILE)
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)


if __name__ == "__main__":
    # Test configuration
    setup_directories()
    print(f"Configuration loaded successfully")
    print(f"App: {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"Database: {settings.DATABASE_URL}")
