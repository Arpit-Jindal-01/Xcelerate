"""
Database Connection Manager
Handles PostgreSQL + PostGIS connections using SQLAlchemy
"""

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from geoalchemy2 import Geometry
from typing import Generator
import logging

from ..utils.config import settings
from ..utils.logger import get_logger

logger = get_logger(__name__)

# SQLAlchemy Base
Base = declarative_base()

# Database engine
engine = None
SessionLocal = None


def init_db_engine():
    """
    Initialize database engine with connection pooling
    
    Returns:
        SQLAlchemy engine
    """
    global engine, SessionLocal
    
    if engine is not None:
        return engine
    
    try:
        # Create engine with connection pooling
        engine = create_engine(
            settings.DATABASE_URL,
            poolclass=QueuePool,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_pre_ping=True,  # Verify connections before using
            echo=settings.DEBUG,  # Log SQL queries in debug mode
        )
        
        # Enable PostGIS extension
        @event.listens_for(engine, "connect")
        def connect(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
            cursor.close()
        
        # Create session factory
        SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )
        
        logger.info("✓ Database engine initialized successfully")
        logger.info(f"Connection pool: size={settings.DB_POOL_SIZE}, max_overflow={settings.DB_MAX_OVERFLOW}")
        
        return engine
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session
    
    Yields:
        Database session
        
    Usage:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            ...
    """
    if SessionLocal is None:
        init_db_engine()
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    Create all tables in the database
    Should be called during application startup
    """
    try:
        if engine is None:
            init_db_engine()
        
        # Import models to register them
        from . import models
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("✓ Database tables created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create tables: {str(e)}")
        raise


def drop_tables():
    """
    Drop all tables (use with caution!)
    Only for development/testing
    """
    if engine is None:
        init_db_engine()
    
    Base.metadata.drop_all(bind=engine)
    logger.warning("⚠ All tables dropped")


def check_db_connection() -> bool:
    """
    Check if database connection is healthy
    
    Returns:
        True if connection is successful
    """
    try:
        if engine is None:
            init_db_engine()
        
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            logger.info("✓ Database connection healthy")
            return True
            
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False


def check_postgis_installed() -> bool:
    """
    Verify PostGIS extension is installed
    
    Returns:
        True if PostGIS is available
    """
    try:
        if engine is None:
            init_db_engine()
        
        with engine.connect() as conn:
            result = conn.execute(
                "SELECT PostGIS_Version();"
            ).fetchone()
            
            version = result[0] if result else "Unknown"
            logger.info(f"✓ PostGIS installed: {version}")
            return True
            
    except Exception as e:
        logger.error(f"PostGIS check failed: {str(e)}")
        return False


if __name__ == "__main__":
    # Test database connection
    print("Testing database connection...")
    init_db_engine()
    
    if check_db_connection():
        print("✓ Database connection successful")
    else:
        print("✗ Database connection failed")
    
    if check_postgis_installed():
        print("✓ PostGIS is installed")
    else:
        print("✗ PostGIS is not installed")
