"""
Integration tests for SQL-Mongo Query Converter.
Tests actual behavior and real-world scenarios.
"""

import pytest
from sql_mongo_converter import sql_to_mongo, mongo_to_sql


class TestRealWorldSQLToMongo:
    """Test real-world SQL to MongoDB conversions."""

    def test_basic_select(self):
        """Test basic SELECT query."""
        result = sql_to_mongo("SELECT * FROM users")
        assert result['collection'] == 'users'
        assert result['find'] == {}

    def test_select_with_where(self):
        """Test SELECT with WHERE clause."""
        result = sql_to_mongo("SELECT * FROM users WHERE age > 25")
        assert result['collection'] == 'users'
        assert 'age' in result['find']
        assert result['find']['age']['$gt'] == 25

    def test_select_with_multiple_conditions(self):
        """Test SELECT with multiple WHERE conditions."""
        result = sql_to_mongo("SELECT * FROM users WHERE age > 25 AND status = 'active'")
        assert result['collection'] == 'users'
        assert 'age' in result['find']
        assert 'status' in result['find']

    def test_select_with_specific_columns(self):
        """Test SELECT with specific columns."""
        result = sql_to_mongo("SELECT name, email FROM users")
        assert result['collection'] == 'users'
        assert 'name' in result['projection']
        assert 'email' in result['projection']

    def test_select_with_limit(self):
        """Test SELECT with LIMIT."""
        result = sql_to_mongo("SELECT * FROM users LIMIT 10")
        assert result['limit'] == 10

    def test_comparison_operators(self):
        """Test various comparison operators."""
        # Greater than
        result = sql_to_mongo("SELECT * FROM users WHERE age > 25")
        assert result['find']['age']['$gt'] == 25

        # Less than
        result = sql_to_mongo("SELECT * FROM users WHERE age < 65")
        assert result['find']['age']['$lt'] == 65

        # Greater than or equal
        result = sql_to_mongo("SELECT * FROM users WHERE age >= 18")
        assert result['find']['age']['$gte'] == 18

        # Less than or equal
        result = sql_to_mongo("SELECT * FROM users WHERE age <= 100")
        assert result['find']['age']['$lte'] == 100

        # Equality
        result = sql_to_mongo("SELECT * FROM users WHERE status = 'active'")
        assert result['find']['status'] == 'active'


class TestRealWorldMongoToSQL:
    """Test real-world MongoDB to SQL conversions."""

    def test_basic_find(self):
        """Test basic MongoDB find."""
        result = mongo_to_sql({'collection': 'users', 'find': {}})
        assert 'SELECT * FROM users' in result

    def test_find_with_filter(self):
        """Test MongoDB find with filter."""
        result = mongo_to_sql({
            'collection': 'users',
            'find': {'age': {'$gt': 25}}
        })
        assert 'users' in result
        assert 'age > 25' in result

    def test_find_with_projection(self):
        """Test MongoDB find with projection."""
        result = mongo_to_sql({
            'collection': 'users',
            'find': {},
            'projection': {'name': 1, 'email': 1}
        })
        assert 'name' in result
        assert 'email' in result

    def test_find_with_limit(self):
        """Test MongoDB find with limit."""
        result = mongo_to_sql({
            'collection': 'users',
            'find': {},
            'limit': 10
        })
        assert 'LIMIT 10' in result

    def test_mongodb_operators(self):
        """Test various MongoDB operators."""
        # $gt
        result = mongo_to_sql({'collection': 'users', 'find': {'age': {'$gt': 25}}})
        assert 'age > 25' in result

        # $gte
        result = mongo_to_sql({'collection': 'users', 'find': {'age': {'$gte': 18}}})
        assert 'age >= 18' in result

        # $lt
        result = mongo_to_sql({'collection': 'users', 'find': {'age': {'$lt': 65}}})
        assert 'age < 65' in result

        # $lte
        result = mongo_to_sql({'collection': 'users', 'find': {'age': {'$lte': 100}}})
        assert 'age <= 100' in result


class TestRoundTrip:
    """Test round-trip conversions."""

    def test_simple_round_trip(self):
        """Test simple SQL -> Mongo -> SQL conversion."""
        original_sql = "SELECT * FROM users WHERE age > 25"
        mongo_query = sql_to_mongo(original_sql)
        back_to_sql = mongo_to_sql(mongo_query)

        # Should contain key elements
        assert 'users' in back_to_sql
        assert 'age' in back_to_sql
        assert '25' in back_to_sql

    def test_with_projection_round_trip(self):
        """Test round-trip with projection."""
        original_sql = "SELECT name, email FROM users WHERE age > 25"
        mongo_query = sql_to_mongo(original_sql)
        back_to_sql = mongo_to_sql(mongo_query)

        assert 'name' in back_to_sql
        assert 'email' in back_to_sql
        assert 'users' in back_to_sql


class TestEdgeCases:
    """Test edge cases."""

    def test_case_insensitive_sql(self):
        """Test case-insensitive SQL."""
        result1 = sql_to_mongo("SELECT * FROM users")
        result2 = sql_to_mongo("select * from users")
        result3 = sql_to_mongo("SeLeCt * FrOm users")

        assert result1['collection'] == result2['collection'] == result3['collection']

    def test_extra_whitespace(self):
        """Test handling of extra whitespace."""
        result = sql_to_mongo("SELECT  *  FROM  users  WHERE  age  >  25")
        assert result['collection'] == 'users'
        assert 'age' in result['find']

    def test_newlines_in_query(self):
        """Test handling of newlines."""
        result = sql_to_mongo("""
            SELECT *
            FROM users
            WHERE age > 25
        """)
        assert result['collection'] == 'users'
        assert 'age' in result['find']


class TestProductionReadiness:
    """Test production-ready features."""

    def test_returns_dict(self):
        """Ensure all conversions return dictionaries."""
        result = sql_to_mongo("SELECT * FROM users")
        assert isinstance(result, dict)

    def test_consistent_structure(self):
        """Ensure consistent result structure."""
        result = sql_to_mongo("SELECT * FROM users")
        assert 'collection' in result
        assert 'find' in result

    def test_handles_various_data_types(self):
        """Test handling of different data types."""
        # Integer
        result = sql_to_mongo("SELECT * FROM users WHERE age > 25")
        assert isinstance(result['find']['age']['$gt'], int)

        # Float
        result = sql_to_mongo("SELECT * FROM products WHERE price > 99.99")
        assert isinstance(result['find']['price']['$gt'], float)

        # String
        result = sql_to_mongo("SELECT * FROM users WHERE name = 'John'")
        assert isinstance(result['find']['name'], str)
