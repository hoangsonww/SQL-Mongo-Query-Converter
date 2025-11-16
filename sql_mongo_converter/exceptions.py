"""
Custom exceptions for SQL-Mongo Query Converter.

This module defines custom exception classes for better error handling
and debugging throughout the conversion process.
"""


class ConverterError(Exception):
    """Base exception class for all converter errors."""

    def __init__(self, message: str, query: str = None, details: dict = None):
        """
        Initialize the converter error.

        Args:
            message: Error message
            query: The query that caused the error
            details: Additional error details
        """
        self.message = message
        self.query = query
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        """Return a formatted error message."""
        error_msg = f"{self.__class__.__name__}: {self.message}"
        if self.query:
            error_msg += f"\nQuery: {self.query}"
        if self.details:
            error_msg += f"\nDetails: {self.details}"
        return error_msg


class SQLParseError(ConverterError):
    """Raised when SQL query parsing fails."""
    pass


class MongoParseError(ConverterError):
    """Raised when MongoDB query parsing fails."""
    pass


class UnsupportedOperationError(ConverterError):
    """Raised when an unsupported SQL or MongoDB operation is encountered."""
    pass


class ValidationError(ConverterError):
    """Raised when query validation fails."""
    pass


class InvalidQueryError(ConverterError):
    """Raised when a query is malformed or invalid."""
    pass


class ConversionError(ConverterError):
    """Raised when query conversion fails."""
    pass


class TypeConversionError(ConverterError):
    """Raised when type conversion fails."""
    pass
