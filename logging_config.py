"""
Centralized Logging Configuration for ReSemantic
"""
import logging
import sys
from pathlib import Path

def setup_logging(log_level=logging.INFO):
    """Setup structured logging with file + console output."""
    
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Console handler (user-friendly)
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console_fmt = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S'
    )
    console.setFormatter(console_fmt)
    
    # File handler (detailed for debugging)
    file_handler = logging.FileHandler(log_dir / "resemantic.log")
    file_handler.setLevel(logging.DEBUG)
    file_fmt = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s:%(funcName)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_fmt)
    
    # Add handlers
    root_logger.addHandler(console)
    root_logger.addHandler(file_handler)
    
    return root_logger

# Module-level loggers (import these!)
extraction_logger = logging.getLogger("resemantic.extraction")
storage_logger = logging.getLogger("resemantic.storage")
chat_logger = logging.getLogger("resemantic.chat")
