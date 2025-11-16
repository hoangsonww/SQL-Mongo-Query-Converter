"""
Logging configuration for SQL-Mongo Query Converter.

Provides a centralized logging system with configurable levels and formats.
"""

import logging
import sys
from typing import Optional
from pathlib import Path


# Default log format
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DETAILED_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"


class ConverterLogger:
    """Logger wrapper for the SQL-Mongo converter."""

    _instances = {}

    def __init__(self, name: str = "sql_mongo_converter", level: int = logging.INFO):
        """
        Initialize the logger.

        Args:
            name: Logger name
            level: Logging level
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.propagate = False

        # Remove existing handlers to avoid duplicates
        self.logger.handlers = []

        # Add console handler
        self._add_console_handler(level)

    def _add_console_handler(self, level: int):
        """Add a console handler to the logger."""
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter(DEFAULT_FORMAT)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def add_file_handler(self, log_file: str, level: int = logging.DEBUG):
        """
        Add a file handler to the logger.

        Args:
            log_file: Path to log file
            level: Logging level for file handler
        """
        # Create log directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        handler = logging.FileHandler(log_file)
        handler.setLevel(level)
        formatter = logging.Formatter(DETAILED_FORMAT)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def set_level(self, level: int):
        """Set the logging level."""
        self.logger.setLevel(level)
        for handler in self.logger.handlers:
            handler.setLevel(level)

    def debug(self, message: str, **kwargs):
        """Log a debug message."""
        self.logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log an info message."""
        self.logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log a warning message."""
        self.logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log an error message."""
        self.logger.error(message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log a critical message."""
        self.logger.critical(message, **kwargs)

    @classmethod
    def get_logger(cls, name: str = "sql_mongo_converter", level: int = logging.INFO) -> "ConverterLogger":
        """
        Get or create a logger instance.

        Args:
            name: Logger name
            level: Logging level

        Returns:
            ConverterLogger instance
        """
        if name not in cls._instances:
            cls._instances[name] = cls(name, level)
        return cls._instances[name]


# Default logger instance
logger = ConverterLogger.get_logger()


def get_logger(name: Optional[str] = None, level: int = logging.INFO) -> ConverterLogger:
    """
    Get a logger instance.

    Args:
        name: Logger name (defaults to sql_mongo_converter)
        level: Logging level

    Returns:
        ConverterLogger instance
    """
    if name is None:
        name = "sql_mongo_converter"
    return ConverterLogger.get_logger(name, level)
