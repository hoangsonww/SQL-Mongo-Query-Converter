"""
Pytest configuration and fixtures for SQL-Mongo Query Converter tests.
"""

import pytest
from sql_mongo_converter import sql_to_mongo, mongo_to_sql


@pytest.fixture
def sample_sql_queries():
    """Sample SQL queries for testing."""
    return {
        'basic_select': "SELECT * FROM users",
        'with_where': "SELECT name, email FROM users WHERE age > 25",
        'with_and': "SELECT * FROM users WHERE age > 25 AND status = 'active'",
        'with_order': "SELECT name, age FROM users ORDER BY age DESC",
        'with_limit': "SELECT * FROM users LIMIT 10",
        'complex': "SELECT name, age FROM users WHERE age >= 18 AND status = 'active' ORDER BY age DESC LIMIT 100",
        'with_group': "SELECT department FROM employees GROUP BY department",
        'multiple_conditions': "SELECT * FROM products WHERE price > 100 AND price < 500 AND category = 'electronics'",
        'with_string': "SELECT * FROM users WHERE name = 'John Doe'",
        'with_numbers': "SELECT * FROM orders WHERE total >= 50.5 AND quantity < 10",
    }


@pytest.fixture
def sample_mongo_queries():
    """Sample MongoDB queries for testing."""
    return {
        'basic_find': {
            'collection': 'users',
            'find': {}
        },
        'with_filter': {
            'collection': 'users',
            'find': {'age': {'$gt': 25}},
            'projection': {'name': 1, 'email': 1}
        },
        'with_and': {
            'collection': 'users',
            'find': {'age': {'$gt': 25}, 'status': 'active'}
        },
        'with_sort': {
            'collection': 'users',
            'find': {},
            'projection': {'name': 1, 'age': 1},
            'sort': [('age', -1)]
        },
        'with_limit': {
            'collection': 'users',
            'find': {},
            'limit': 10
        },
        'complex': {
            'collection': 'users',
            'find': {'age': {'$gte': 18}, 'status': 'active'},
            'projection': {'name': 1, 'age': 1},
            'sort': [('age', -1)],
            'limit': 100
        },
        'with_operators': {
            'collection': 'products',
            'find': {
                'price': {'$gt': 100, '$lt': 500},
                'category': 'electronics'
            }
        },
        'with_in': {
            'collection': 'users',
            'find': {'status': {'$in': ['active', 'pending']}}
        },
        'with_ne': {
            'collection': 'users',
            'find': {'status': {'$ne': 'deleted'}}
        },
    }


@pytest.fixture
def invalid_sql_queries():
    """Invalid SQL queries for error testing."""
    return {
        'unbalanced_parens': "SELECT * FROM users WHERE (age > 25",
        'unbalanced_quotes': "SELECT * FROM users WHERE name = 'John",
        'dangerous_keyword': "DROP TABLE users",
        'empty': "",
        'non_select': "UPDATE users SET age = 30",
    }


@pytest.fixture
def invalid_mongo_queries():
    """Invalid MongoDB queries for error testing."""
    return {
        'not_dict': "not a dictionary",
        'invalid_operator': {'collection': 'users', 'find': {'age': {'$invalid': 25}}},
        'missing_collection': {'find': {'age': {'$gt': 25}}},
    }


@pytest.fixture
def edge_case_queries():
    """Edge case queries for testing."""
    return {
        'sql_with_newlines': """SELECT name, email
                                FROM users
                                WHERE age > 25
                                ORDER BY name""",
        'sql_with_tabs': "SELECT\tname\tFROM\tusers",
        'sql_lowercase': "select * from users where age > 25",
        'sql_mixed_case': "SeLeCt * FrOm users WhErE age > 25",
        'sql_extra_spaces': "SELECT  *  FROM  users  WHERE  age  >  25",
    }
