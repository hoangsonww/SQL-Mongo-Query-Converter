"""
Tests for query validation and sanitization.
"""

import pytest
from sql_mongo_converter.validator import QueryValidator
from sql_mongo_converter.exceptions import ValidationError, InvalidQueryError


class TestSQLValidation:
    """Test SQL query validation."""

    def test_valid_select_query(self):
        """Test valid SELECT query."""
        assert QueryValidator.validate_sql_query("SELECT * FROM users") is True

    def test_empty_query(self):
        """Test empty query rejection."""
        with pytest.raises(ValidationError):
            QueryValidator.validate_sql_query("")

    def test_none_query(self):
        """Test None query rejection."""
        with pytest.raises(ValidationError):
            QueryValidator.validate_sql_query(None)

    def test_dangerous_keyword_drop(self):
        """Test dangerous DROP keyword detection."""
        with pytest.raises(ValidationError, match="Dangerous keyword"):
            QueryValidator.validate_sql_query("DROP TABLE users")

    def test_dangerous_keyword_delete(self):
        """Test DELETE keyword detection (now treated as write operation)."""
        with pytest.raises(ValidationError, match="Write operation keyword"):
            QueryValidator.validate_sql_query("DELETE FROM users WHERE id = 1")

    def test_dangerous_keyword_truncate(self):
        """Test dangerous TRUNCATE keyword detection."""
        with pytest.raises(ValidationError, match="Dangerous keyword"):
            QueryValidator.validate_sql_query("TRUNCATE TABLE users")

    def test_allow_mutations(self):
        """Test allowing mutations when specified."""
        # Should not raise error when mutations are allowed
        QueryValidator.validate_sql_query("DELETE FROM users WHERE id = 1", allow_mutations=True)

    def test_unbalanced_parentheses_open(self):
        """Test unbalanced parentheses (too many open)."""
        with pytest.raises(ValidationError, match="Unbalanced parentheses"):
            QueryValidator.validate_sql_query("SELECT * FROM users WHERE (age > 25")

    def test_unbalanced_parentheses_close(self):
        """Test unbalanced parentheses (too many close)."""
        with pytest.raises(ValidationError, match="Unbalanced parentheses"):
            QueryValidator.validate_sql_query("SELECT * FROM users WHERE age > 25)")

    def test_unbalanced_single_quotes(self):
        """Test unbalanced single quotes."""
        with pytest.raises(ValidationError, match="Unbalanced single quotes"):
            QueryValidator.validate_sql_query("SELECT * FROM users WHERE name = 'John")

    def test_unbalanced_double_quotes(self):
        """Test unbalanced double quotes."""
        with pytest.raises(ValidationError, match="Unbalanced double quotes"):
            QueryValidator.validate_sql_query('SELECT * FROM users WHERE name = "John')

    def test_max_query_length(self):
        """Test maximum query length enforcement."""
        long_query = "SELECT * FROM users WHERE " + " AND ".join([f"field{i} = {i}" for i in range(1000)])
        with pytest.raises(ValidationError, match="exceeds maximum length"):
            QueryValidator.validate_sql_query(long_query)

    def test_balanced_quotes(self):
        """Test properly balanced quotes."""
        query = "SELECT * FROM users WHERE name = 'John' AND email = 'john@example.com'"
        assert QueryValidator.validate_sql_query(query) is True

    def test_balanced_parentheses(self):
        """Test properly balanced parentheses."""
        query = "SELECT * FROM users WHERE (age > 25 AND (status = 'active'))"
        assert QueryValidator.validate_sql_query(query) is True


class TestMongoValidation:
    """Test MongoDB query validation."""

    def test_valid_mongo_query(self):
        """Test valid MongoDB query."""
        query = {'collection': 'users', 'find': {'age': {'$gt': 25}}}
        assert QueryValidator.validate_mongo_query(query) is True

    def test_invalid_query_type(self):
        """Test invalid query type (not a dict)."""
        with pytest.raises(ValidationError, match="must be a dictionary"):
            QueryValidator.validate_mongo_query("not a dict")

    def test_invalid_collection_type(self):
        """Test invalid collection type."""
        with pytest.raises(ValidationError, match="Collection name must be a string"):
            QueryValidator.validate_mongo_query({'collection': 123, 'find': {}})

    def test_unknown_operator(self):
        """Test unknown MongoDB operator."""
        query = {'collection': 'users', 'find': {'age': {'$unknown': 25}}}
        with pytest.raises(ValidationError, match="Unknown MongoDB operator"):
            QueryValidator.validate_mongo_query(query)

    def test_valid_operators(self):
        """Test all valid operators."""
        valid_operators = ['$gt', '$gte', '$lt', '$lte', '$eq', '$ne', '$in', '$nin']
        for op in valid_operators:
            query = {'collection': 'users', 'find': {'age': {op: 25}}}
            assert QueryValidator.validate_mongo_query(query) is True

    def test_max_nesting_depth(self):
        """Test maximum nesting depth enforcement."""
        # Create deeply nested query
        deep_query = {'collection': 'users', 'find': {}}
        current = deep_query['find']
        for i in range(15):  # Exceed max depth
            current['nested'] = {}
            current = current['nested']

        with pytest.raises(ValidationError, match="exceeds maximum nesting depth"):
            QueryValidator.validate_mongo_query(deep_query)

    def test_logical_operators(self):
        """Test logical operators validation."""
        query = {
            'collection': 'users',
            'find': {
                '$and': [
                    {'age': {'$gt': 25}},
                    {'status': 'active'}
                ]
            }
        }
        assert QueryValidator.validate_mongo_query(query) is True

    def test_empty_query(self):
        """Test empty MongoDB query."""
        query = {'collection': 'users', 'find': {}}
        assert QueryValidator.validate_mongo_query(query) is True


class TestSanitization:
    """Test string and identifier sanitization."""

    def test_sanitize_sql_string_quotes(self):
        """Test SQL string sanitization with quotes."""
        result = QueryValidator.sanitize_sql_string("O'Reilly")
        assert result == "O''Reilly"

    def test_sanitize_sql_string_null_bytes(self):
        """Test SQL string sanitization with null bytes."""
        result = QueryValidator.sanitize_sql_string("test\x00value")
        assert '\x00' not in result

    def test_sanitize_identifier_valid(self):
        """Test valid identifier sanitization."""
        assert QueryValidator.sanitize_identifier("valid_name") == "valid_name"
        assert QueryValidator.sanitize_identifier("_name") == "_name"
        assert QueryValidator.sanitize_identifier("name123") == "name123"

    def test_sanitize_identifier_invalid_start(self):
        """Test invalid identifier (starts with number)."""
        with pytest.raises(InvalidQueryError, match="Invalid identifier"):
            QueryValidator.sanitize_identifier("123name")

    def test_sanitize_identifier_invalid_chars(self):
        """Test invalid identifier (special characters)."""
        with pytest.raises(InvalidQueryError, match="Invalid identifier"):
            QueryValidator.sanitize_identifier("name-with-dashes")

    def test_sanitize_identifier_sql_injection(self):
        """Test identifier sanitization prevents SQL injection."""
        with pytest.raises(InvalidQueryError):
            QueryValidator.sanitize_identifier("users; DROP TABLE users--")

    def test_sanitize_identifier_non_string(self):
        """Test identifier sanitization with non-string."""
        with pytest.raises(InvalidQueryError, match="must be a string"):
            QueryValidator.sanitize_identifier(123)


class TestNestingDepth:
    """Test nesting depth calculation."""

    def test_simple_dict_depth(self):
        """Test simple dictionary depth."""
        obj = {'a': 1}
        assert QueryValidator._get_nesting_depth(obj) == 1

    def test_nested_dict_depth(self):
        """Test nested dictionary depth."""
        obj = {'a': {'b': {'c': 1}}}
        assert QueryValidator._get_nesting_depth(obj) == 3

    def test_list_depth(self):
        """Test list depth."""
        obj = [1, 2, [3, 4]]
        assert QueryValidator._get_nesting_depth(obj) == 2

    def test_mixed_depth(self):
        """Test mixed dict and list depth."""
        obj = {'a': [{'b': [1, 2]}]}
        assert QueryValidator._get_nesting_depth(obj) == 4

    def test_empty_dict_depth(self):
        """Test empty dict depth."""
        obj = {}
        assert QueryValidator._get_nesting_depth(obj) == 0

    def test_primitive_depth(self):
        """Test primitive value depth."""
        assert QueryValidator._get_nesting_depth(1) == 0
        assert QueryValidator._get_nesting_depth("string") == 0
        assert QueryValidator._get_nesting_depth(None) == 0
