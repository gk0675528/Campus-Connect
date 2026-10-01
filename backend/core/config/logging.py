"""Logging Configuration"""

import logging
import sys
from loguru import logger
from core.config.settings import settings

# Remove default logger
logger.remove()

# Add file handler
logger.add(
    "logs/campusconnect.log",
    rotation="500 MB",
    retention="10 days",
    level="INFO" if not settings.DEBUG else "DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
)

# Add console handler
logger.add(
    sys.stdout,
    level="DEBUG" if settings.DEBUG else "INFO",
    format="<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    colorize=True,
)

# Get logger for other modules
def get_logger(name: str) -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(name)
