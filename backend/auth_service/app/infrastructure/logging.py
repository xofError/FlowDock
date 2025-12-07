"""
Infrastructure Layer: Structured Logging Configuration

Implements JSON logging for better integration with monitoring stacks (ELK, Loki, etc).
All logs are emitted as structured JSON for easier parsing and analysis.
"""

import logging
import sys
from pythonjsonlogger import jsonlogger


def setup_logging(level=logging.INFO):
    """Configure structured JSON logging.
    
    Args:
        level: Logging level (default: INFO)
    
    This sets up a JSON logger that outputs structured logs to stdout,
    making it easy to parse with log aggregation tools like Loki or ELK Stack.
    
    Log format: {"timestamp": "...", "level": "INFO", "logger": "...", "message": "..."}
    """
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create stdout handler
    log_handler = logging.StreamHandler(sys.stdout)
    log_handler.setLevel(level)
    
    # Create JSON formatter
    formatter = jsonlogger.JsonFormatter(
        fmt='%(timestamp)s %(level)s %(name)s %(message)s',
        timestamp=True
    )
    log_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(log_handler)
    
    # Set up loggers for key modules
    logging.getLogger("uvicorn").setLevel(level)
    logging.getLogger("uvicorn.access").setLevel(level)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)  # Reduce SQL noise
