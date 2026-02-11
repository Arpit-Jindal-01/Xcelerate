"""
Logging Configuration for Industrial Land Monitoring System
Uses loguru for structured logging
"""

import sys
from loguru import logger
from pathlib import Path
from .config import settings


def setup_logger():
    """
    Configure application-wide logging with loguru
    
    Features:
    - Console logging with color
    - File rotation
    - Structured logging
    - Different levels for different environments
    """
    
    # Remove default handler
    logger.remove()
    
    # Console handler with custom format
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    logger.add(
        sys.stdout,
        format=console_format,
        level=settings.LOG_LEVEL,
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # File handler with rotation
    log_path = Path(settings.LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
        "{name}:{function}:{line} | {message}"
    )
    
    logger.add(
        settings.LOG_FILE,
        format=file_format,
        level=settings.LOG_LEVEL,
        rotation=settings.LOG_ROTATION,
        retention=settings.LOG_RETENTION,
        compression="zip",
        backtrace=True,
        diagnose=True,
        enqueue=True  # Thread-safe
    )
    
    logger.info(f"Logger initialized - Level: {settings.LOG_LEVEL}")
    
    return logger


# Create configured logger instance
app_logger = setup_logger()


def get_logger(name: str):
    """
    Get a contextual logger for a specific module
    
    Args:
        name: Module name for context
        
    Returns:
        Configured logger instance
    """
    return logger.bind(module=name)


# Utility functions for common logging patterns
def log_api_request(endpoint: str, method: str, params: dict = None):
    """Log API request"""
    logger.info(f"API Request: {method} {endpoint}", extra={"params": params})


def log_api_response(endpoint: str, status: int, duration: float):
    """Log API response"""
    logger.info(
        f"API Response: {endpoint} | Status: {status} | Duration: {duration:.3f}s"
    )


def log_error(error: Exception, context: str = ""):
    """Log error with context"""
    logger.error(f"Error in {context}: {str(error)}", exc_info=True)


def log_gee_operation(operation: str, geometry: dict = None):
    """Log Google Earth Engine operation"""
    logger.info(f"GEE Operation: {operation}", extra={"geometry": geometry})


def log_ml_inference(model: str, input_shape: tuple, duration: float):
    """Log ML inference"""
    logger.info(
        f"ML Inference: {model} | Input: {input_shape} | Duration: {duration:.3f}s"
    )


def log_database_query(query: str, execution_time: float):
    """Log database query"""
    logger.debug(f"DB Query: {query[:100]}... | Time: {execution_time:.3f}s")


def log_violation_detected(violation_type: str, plot_id: str, confidence: float):
    """Log violation detection"""
    logger.warning(
        f"VIOLATION DETECTED: {violation_type} | Plot: {plot_id} | "
        f"Confidence: {confidence:.2%}"
    )


if __name__ == "__main__":
    # Test logging
    test_logger = get_logger("test_module")
    test_logger.info("Test info message")
    test_logger.warning("Test warning message")
    test_logger.error("Test error message")
    log_violation_detected("Encroachment", "PLOT_001", 0.95)
