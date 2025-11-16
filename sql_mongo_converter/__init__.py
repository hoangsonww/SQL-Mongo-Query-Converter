"""
SQL-Mongo Query Converter

A production-ready library for converting SQL queries to MongoDB queries and vice versa.
Includes validation, logging, benchmarking, and CLI tools.
"""

from .converter import sql_to_mongo, mongo_to_sql
from .exceptions import (
    ConverterError,
    SQLParseError,
    MongoParseError,
    UnsupportedOperationError,
    ValidationError,
    InvalidQueryError,
    ConversionError,
    TypeConversionError,
)
from .validator import QueryValidator
from .logger import get_logger, ConverterLogger
from .benchmark import ConverterBenchmark, BenchmarkResult

__version__ = "2.0.0"

__all__ = [
    # Core conversion functions
    "sql_to_mongo",
    "mongo_to_sql",
    # Exceptions
    "ConverterError",
    "SQLParseError",
    "MongoParseError",
    "UnsupportedOperationError",
    "ValidationError",
    "InvalidQueryError",
    "ConversionError",
    "TypeConversionError",
    # Validation
    "QueryValidator",
    # Logging
    "get_logger",
    "ConverterLogger",
    # Benchmarking
    "ConverterBenchmark",
    "BenchmarkResult",
    # Version
    "__version__",
]
