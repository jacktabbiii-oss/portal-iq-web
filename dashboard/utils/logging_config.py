"""Centralized logging configuration for Portal IQ Dashboard.

Provides structured logging with file rotation and context tracking.
"""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional
import functools
import time


# Log directory - create if doesn't exist
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Log format with timestamp, level, module, and message
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Default log level from environment
DEFAULT_LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


def setup_logger(
    name: str,
    level: str = None,
    log_to_file: bool = True,
    log_to_console: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """Set up a logger with file and console handlers.

    Args:
        name: Logger name (usually __name__ of the module)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to log to rotating file
        log_to_console: Whether to log to console (stderr)
        max_bytes: Max size per log file before rotation
        backup_count: Number of backup files to keep

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Only configure if not already configured
    if logger.handlers:
        return logger

    level = level or DEFAULT_LOG_LEVEL
    logger.setLevel(getattr(logging, level, logging.INFO))

    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)

    # File handler with rotation
    if log_to_file:
        log_file = LOG_DIR / f"portal_iq_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)  # File gets all logs
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Console handler (only errors by default in production)
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_level = logging.DEBUG if os.getenv("DEBUG") else logging.WARNING
        console_handler.setLevel(console_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


def get_logger(name: str = "portal_iq") -> logging.Logger:
    """Get or create a logger for the given name.

    Convenience function that ensures logger is configured.

    Args:
        name: Logger name

    Returns:
        Configured logger
    """
    return setup_logger(name)


def log_execution_time(logger: Optional[logging.Logger] = None):
    """Decorator to log function execution time.

    Args:
        logger: Logger to use (defaults to portal_iq logger)

    Example:
        @log_execution_time()
        def slow_function():
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            _logger = logger or get_logger("portal_iq.performance")
            start = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start
                _logger.info(f"{func.__name__} completed in {elapsed:.2f}s")
                return result
            except Exception as e:
                elapsed = time.time() - start
                _logger.error(f"{func.__name__} failed after {elapsed:.2f}s: {e}")
                raise
        return wrapper
    return decorator


def log_data_operation(operation: str, details: str = ""):
    """Log a data operation with context.

    Args:
        operation: Type of operation (load, save, merge, etc.)
        details: Additional details about the operation
    """
    logger = get_logger("portal_iq.data")
    logger.info(f"DATA_OP | {operation} | {details}")


def log_user_action(action: str, user_id: str = "anonymous", details: str = ""):
    """Log a user action for analytics/debugging.

    Args:
        action: Type of action (search, compare, view, etc.)
        user_id: User identifier
        details: Additional details
    """
    logger = get_logger("portal_iq.user")
    logger.info(f"USER_ACTION | {action} | user={user_id} | {details}")


def log_error(error: Exception, context: str = "", notify: bool = False):
    """Log an error with context and optional notification.

    Args:
        error: The exception that occurred
        context: Where/why the error occurred
        notify: Whether to send notification (future: Sentry, email, etc.)
    """
    logger = get_logger("portal_iq.errors")
    logger.error(f"ERROR | {context} | {type(error).__name__}: {error}", exc_info=True)

    # Future: Add Sentry/notification integration here
    if notify:
        pass  # TODO: Integrate with error tracking service


def log_api_call(endpoint: str, method: str = "GET", status: int = 200, duration_ms: float = 0):
    """Log an API call for monitoring.

    Args:
        endpoint: API endpoint called
        method: HTTP method
        status: Response status code
        duration_ms: Request duration in milliseconds
    """
    logger = get_logger("portal_iq.api")
    level = logging.INFO if status < 400 else logging.WARNING if status < 500 else logging.ERROR
    logger.log(level, f"API | {method} {endpoint} | {status} | {duration_ms:.0f}ms")


# Create default logger on import
default_logger = setup_logger("portal_iq")
