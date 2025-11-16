"""
Query validation and sanitization for SQL-Mongo Query Converter.

Provides validation, sanitization, and security checks for SQL and MongoDB queries.
"""

import re
from typing import Dict, List, Optional, Any
from .exceptions import ValidationError, InvalidQueryError
from .logger import get_logger

logger = get_logger(__name__)


class QueryValidator:
    """Validator for SQL and MongoDB queries."""

    # Truly dangerous SQL keywords that should always be blocked
    DANGEROUS_SQL_KEYWORDS = [
        'DROP', 'TRUNCATE', 'ALTER', 'EXEC', 'EXECUTE',
        'GRANT', 'REVOKE', 'SHUTDOWN', 'xp_', 'sp_'
    ]

    # Write operation keywords - allowed when mutations are enabled
    MUTATION_KEYWORDS = ['INSERT', 'UPDATE', 'DELETE', 'CREATE']

    # Maximum query length to prevent DoS
    MAX_QUERY_LENGTH = 10000

    # Maximum nesting depth for MongoDB queries
    MAX_NESTING_DEPTH = 10

    @staticmethod
    def validate_sql_query(query: str, allow_mutations: bool = False) -> bool:
        """
        Validate a SQL query for safety and correctness.

        Args:
            query: SQL query to validate
            allow_mutations: Whether to allow INSERT/UPDATE/DELETE queries

        Returns:
            True if valid

        Raises:
            ValidationError: If query is invalid or unsafe
        """
        if not query or not isinstance(query, str):
            raise ValidationError("Query must be a non-empty string", query=str(query))

        query_upper = query.upper().strip()

        # Check query length
        if len(query) > QueryValidator.MAX_QUERY_LENGTH:
            raise ValidationError(
                f"Query exceeds maximum length of {QueryValidator.MAX_QUERY_LENGTH} characters",
                query=query[:100] + "..."
            )

        # Check for truly dangerous keywords (always blocked)
        for keyword in QueryValidator.DANGEROUS_SQL_KEYWORDS:
            if keyword in query_upper:
                raise ValidationError(
                    f"Dangerous keyword '{keyword}' detected in query",
                    query=query,
                    details={'keyword': keyword}
                )

        # Check for mutation keywords when mutations are not allowed
        if not allow_mutations:
            for keyword in QueryValidator.MUTATION_KEYWORDS:
                if keyword in query_upper:
                    raise ValidationError(
                        f"Write operation keyword '{keyword}' detected in query. "
                        "Use allow_mutations=True to enable write operations.",
                        query=query,
                        details={'keyword': keyword}
                    )

        # Validate basic SQL structure
        valid_start_keywords = ['SELECT']
        if allow_mutations:
            valid_start_keywords.extend(['INSERT', 'UPDATE', 'DELETE'])

        if not any(query_upper.startswith(kw) for kw in valid_start_keywords):
            if allow_mutations:
                raise ValidationError(
                    "Query must start with SELECT, INSERT, UPDATE, or DELETE",
                    query=query
                )
            else:
                raise ValidationError(
                    "Query must start with SELECT (use allow_mutations=True for write operations)",
                    query=query
                )

        # Check for balanced parentheses
        if query.count('(') != query.count(')'):
            raise ValidationError(
                "Unbalanced parentheses in query",
                query=query,
                details={'open': query.count('('), 'close': query.count(')')}
            )

        # Check for balanced quotes
        single_quotes = query.count("'") - query.count("\\'")
        double_quotes = query.count('"') - query.count('\\"')

        if single_quotes % 2 != 0:
            raise ValidationError("Unbalanced single quotes in query", query=query)

        if double_quotes % 2 != 0:
            raise ValidationError("Unbalanced double quotes in query", query=query)

        logger.debug(f"SQL query validated successfully: {query[:50]}...")
        return True

    @staticmethod
    def validate_mongo_query(query: Dict[str, Any]) -> bool:
        """
        Validate a MongoDB query for safety and correctness.

        Args:
            query: MongoDB query dictionary

        Returns:
            True if valid

        Raises:
            ValidationError: If query is invalid
        """
        if not isinstance(query, dict):
            raise ValidationError(
                "MongoDB query must be a dictionary",
                query=str(query)
            )

        # Check nesting depth
        depth = QueryValidator._get_nesting_depth(query)
        if depth > QueryValidator.MAX_NESTING_DEPTH:
            raise ValidationError(
                f"Query exceeds maximum nesting depth of {QueryValidator.MAX_NESTING_DEPTH}",
                query=str(query),
                details={'depth': depth}
            )

        # Validate required fields
        if 'collection' in query and not isinstance(query['collection'], str):
            raise ValidationError(
                "Collection name must be a string",
                query=str(query)
            )

        # Validate operators
        QueryValidator._validate_mongo_operators(query)

        logger.debug(f"MongoDB query validated successfully: {str(query)[:50]}...")
        return True

    @staticmethod
    def _get_nesting_depth(obj: Any, current_depth: int = 0) -> int:
        """Calculate the nesting depth of a dictionary or list."""
        if not isinstance(obj, (dict, list)):
            return current_depth

        if isinstance(obj, dict):
            if not obj:
                return current_depth
            return max(QueryValidator._get_nesting_depth(v, current_depth + 1) for v in obj.values())

        if isinstance(obj, list):
            if not obj:
                return current_depth
            return max(QueryValidator._get_nesting_depth(item, current_depth + 1) for item in obj)

        return current_depth

    @staticmethod
    def _validate_mongo_operators(query: Dict[str, Any]):
        """Validate MongoDB operators in the query."""
        valid_operators = {
            # Comparison
            '$eq', '$ne', '$gt', '$gte', '$lt', '$lte', '$in', '$nin',
            # Logical
            '$and', '$or', '$not', '$nor',
            # Element
            '$exists', '$type',
            # Evaluation
            '$regex', '$mod', '$text', '$where',
            # Array
            '$all', '$elemMatch', '$size',
            # Update operators
            '$set', '$unset', '$inc', '$mul', '$rename', '$setOnInsert',
            '$push', '$pull', '$addToSet', '$pop', '$pullAll',
            '$currentDate', '$min', '$max',
            # Aggregation
            '$group', '$match', '$project', '$sort', '$limit', '$skip',
            '$unwind', '$lookup', '$sum', '$avg', '$count'
        }

        def check_operators(obj: Any, path: str = ""):
            """Recursively check for invalid operators."""
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key.startswith('$') and key not in valid_operators:
                        raise ValidationError(
                            f"Unknown MongoDB operator: {key}",
                            query=str(query),
                            details={'operator': key, 'path': path}
                        )
                    check_operators(value, f"{path}.{key}" if path else key)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_operators(item, f"{path}[{i}]")

        check_operators(query)

    @staticmethod
    def sanitize_sql_string(value: str) -> str:
        """
        Sanitize a string value for use in SQL queries.

        Args:
            value: String to sanitize

        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            return value

        # Escape single quotes
        value = value.replace("'", "''")

        # Remove null bytes
        value = value.replace('\x00', '')

        return value

    @staticmethod
    def sanitize_identifier(identifier: str) -> str:
        """
        Sanitize a SQL identifier (table name, column name).

        Args:
            identifier: Identifier to sanitize

        Returns:
            Sanitized identifier

        Raises:
            InvalidQueryError: If identifier is invalid
        """
        if not isinstance(identifier, str):
            raise InvalidQueryError(f"Identifier must be a string, got {type(identifier)}")

        # Only allow alphanumeric characters and underscores
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', identifier):
            raise InvalidQueryError(
                f"Invalid identifier: {identifier}. "
                "Identifiers must start with a letter or underscore and contain only "
                "letters, numbers, and underscores."
            )

        return identifier
