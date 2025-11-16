"""
Tests for new database operations (INSERT, UPDATE, DELETE, JOIN, CREATE).
"""

import pytest
from sql_mongo_converter import sql_to_mongo, mongo_to_sql
from sql_mongo_converter.sql_to_mongo import (
    sql_insert_to_mongo,
    sql_update_to_mongo,
    sql_delete_to_mongo,
    sql_join_to_mongo,
    sql_create_table_to_mongo,
    sql_create_index_to_mongo
)
from sql_mongo_converter.mongo_to_sql import (
    mongo_insert_to_sql,
    mongo_update_to_sql,
    mongo_delete_to_sql
)


class TestInsertOperations:
    """Test INSERT operations."""

    def test_insert_single_row_with_columns(self):
        """Test INSERT with specified columns."""
        sql = "INSERT INTO users (name, age) VALUES ('Alice', 30)"
        result = sql_insert_to_mongo(sql)

        assert result["collection"] == "users"
        assert result["operation"] == "insertOne"
        assert result["document"] == {"name": "Alice", "age": 30}

    def test_insert_single_row_without_columns(self):
        """Test INSERT without specified columns."""
        sql = "INSERT INTO users VALUES ('Bob', 25)"
        result = sql_insert_to_mongo(sql)

        assert result["collection"] == "users"
        assert result["operation"] == "insertOne"
        assert "col0" in result["document"]
        assert "col1" in result["document"]

    def test_insert_multiple_rows(self):
        """Test INSERT with multiple value sets."""
        sql = "INSERT INTO users (name, age) VALUES ('Alice', 30), ('Bob', 25)"
        result = sql_insert_to_mongo(sql)

        assert result["collection"] == "users"
        assert result["operation"] == "insertMany"
        assert len(result["documents"]) == 2
        assert result["documents"][0] == {"name": "Alice", "age": 30}
        assert result["documents"][1] == {"name": "Bob", "age": 25}

    def test_mongo_insert_to_sql_single(self):
        """Test MongoDB insertOne to SQL."""
        mongo_obj = {
            "collection": "users",
            "operation": "insertOne",
            "document": {"name": "Alice", "age": 30}
        }
        result = mongo_insert_to_sql(mongo_obj)

        assert "INSERT INTO users" in result
        assert "Alice" in result
        assert "30" in result

    def test_mongo_insert_to_sql_many(self):
        """Test MongoDB insertMany to SQL."""
        mongo_obj = {
            "collection": "users",
            "operation": "insertMany",
            "documents": [
                {"name": "Alice", "age": 30},
                {"name": "Bob", "age": 25}
            ]
        }
        result = mongo_insert_to_sql(mongo_obj)

        assert "INSERT INTO users" in result
        assert "Alice" in result
        assert "Bob" in result


class TestUpdateOperations:
    """Test UPDATE operations."""

    def test_update_with_where(self):
        """Test UPDATE with WHERE clause."""
        sql = "UPDATE users SET age = 31, status = 'active' WHERE name = 'Alice'"
        result = sql_update_to_mongo(sql)

        assert result["collection"] == "users"
        assert result["operation"] == "updateMany"
        assert result["filter"] == {"name": "Alice"}
        assert result["update"] == {"$set": {"age": 31, "status": "active"}}

    def test_update_without_where(self):
        """Test UPDATE without WHERE clause."""
        sql = "UPDATE users SET status = 'inactive'"
        result = sql_update_to_mongo(sql)

        assert result["collection"] == "users"
        assert result["operation"] == "updateMany"
        assert result["filter"] == {}
        assert result["update"] == {"$set": {"status": "inactive"}}

    def test_mongo_update_to_sql(self):
        """Test MongoDB update to SQL."""
        mongo_obj = {
            "collection": "users",
            "operation": "updateMany",
            "filter": {"name": "Alice"},
            "update": {"$set": {"age": 31, "status": "active"}}
        }
        result = mongo_update_to_sql(mongo_obj)

        assert "UPDATE users" in result
        assert "SET" in result
        assert "WHERE name" in result


class TestDeleteOperations:
    """Test DELETE operations."""

    def test_delete_with_where(self):
        """Test DELETE with WHERE clause."""
        sql = "DELETE FROM users WHERE age < 18"
        result = sql_delete_to_mongo(sql)

        assert result["collection"] == "users"
        assert result["operation"] == "deleteMany"
        assert result["filter"] == {"age": {"$lt": 18}}

    def test_delete_without_where(self):
        """Test DELETE without WHERE clause."""
        sql = "DELETE FROM users"
        result = sql_delete_to_mongo(sql)

        assert result["collection"] == "users"
        assert result["operation"] == "deleteMany"
        assert result["filter"] == {}

    def test_mongo_delete_to_sql(self):
        """Test MongoDB delete to SQL."""
        mongo_obj = {
            "collection": "users",
            "operation": "deleteMany",
            "filter": {"age": {"$lt": 18}}
        }
        result = mongo_delete_to_sql(mongo_obj)

        assert "DELETE FROM users" in result
        assert "WHERE age" in result


class TestJoinOperations:
    """Test JOIN operations."""

    def test_inner_join(self):
        """Test INNER JOIN conversion."""
        sql = "SELECT u.name, o.total FROM users u INNER JOIN orders o ON u.id = o.user_id"
        result = sql_join_to_mongo(sql)

        assert result["collection"] == "users"
        assert result["operation"] == "aggregate"
        assert len(result["pipeline"]) > 0

        # Check for $lookup stage
        lookup_stage = result["pipeline"][0]
        assert "$lookup" in lookup_stage
        assert lookup_stage["$lookup"]["from"] == "orders"
        assert lookup_stage["$lookup"]["localField"] == "id"
        assert lookup_stage["$lookup"]["foreignField"] == "user_id"

    def test_left_join(self):
        """Test LEFT JOIN conversion."""
        sql = "SELECT u.name, o.total FROM users u LEFT JOIN orders o ON u.id = o.user_id"
        result = sql_join_to_mongo(sql)

        assert result["collection"] == "users"
        assert result["operation"] == "aggregate"

        # Check for preserveNullAndEmptyArrays
        has_preserve = any(
            "$unwind" in stage and
            isinstance(stage["$unwind"], dict) and
            stage["$unwind"].get("preserveNullAndEmptyArrays") == True
            for stage in result["pipeline"]
        )
        assert has_preserve


class TestCreateOperations:
    """Test CREATE TABLE and CREATE INDEX operations."""

    def test_create_table(self):
        """Test CREATE TABLE conversion."""
        sql = "CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100), age INT NOT NULL)"
        result = sql_create_table_to_mongo(sql)

        assert result["operation"] == "createCollection"
        assert result["collection"] == "users"
        assert "schema" in result
        assert result["schema"]["id"] == "INT"
        assert result["schema"]["name"] == "VARCHAR(100)"
        assert result["schema"]["age"] == "INT"

        # Check validator
        assert "validator" in result
        assert "$jsonSchema" in result["validator"]
        schema = result["validator"]["$jsonSchema"]
        assert "id" in schema["required"]
        assert "age" in schema["required"]
        assert schema["properties"]["id"]["bsonType"] == "int"
        assert schema["properties"]["name"]["bsonType"] == "string"

    def test_create_index(self):
        """Test CREATE INDEX conversion."""
        sql = "CREATE INDEX idx_name ON users (name)"
        result = sql_create_index_to_mongo(sql)

        assert result["operation"] == "createIndex"
        assert result["collection"] == "users"
        assert result["index"] == {"name": 1}
        assert result["indexName"] == "idx_name"

    def test_create_index_desc(self):
        """Test CREATE INDEX with DESC."""
        sql = "CREATE INDEX idx_age ON users (age DESC)"
        result = sql_create_index_to_mongo(sql)

        assert result["operation"] == "createIndex"
        assert result["collection"] == "users"
        assert result["index"] == {"age": -1}

    def test_create_composite_index(self):
        """Test CREATE INDEX with multiple columns."""
        sql = "CREATE INDEX idx_name_age ON users (name, age DESC)"
        result = sql_create_index_to_mongo(sql)

        assert result["operation"] == "createIndex"
        assert result["collection"] == "users"
        assert result["index"]["name"] == 1
        assert result["index"]["age"] == -1


class TestConverterRouting:
    """Test that the main converter routes operations correctly."""

    def test_select_routing(self):
        """Test SELECT is routed correctly."""
        sql = "SELECT * FROM users"
        result = sql_to_mongo(sql)
        assert "collection" in result
        assert result["collection"] == "users"

    def test_insert_routing(self):
        """Test INSERT is routed correctly."""
        sql = "INSERT INTO users (name) VALUES ('Alice')"
        result = sql_to_mongo(sql, allow_mutations=True)
        assert result["operation"] == "insertOne"

    def test_update_routing(self):
        """Test UPDATE is routed correctly."""
        sql = "UPDATE users SET age = 30"
        result = sql_to_mongo(sql, allow_mutations=True)
        assert result["operation"] == "updateMany"

    def test_delete_routing(self):
        """Test DELETE is routed correctly."""
        sql = "DELETE FROM users WHERE age < 18"
        result = sql_to_mongo(sql, allow_mutations=True)
        assert result["operation"] == "deleteMany"

    def test_join_routing(self):
        """Test JOIN is routed correctly."""
        sql = "SELECT * FROM users u INNER JOIN orders o ON u.id = o.user_id"
        result = sql_to_mongo(sql)
        assert result["operation"] == "aggregate"

    def test_create_table_routing(self):
        """Test CREATE TABLE is routed correctly."""
        sql = "CREATE TABLE users (id INT)"
        result = sql_to_mongo(sql)
        assert result["operation"] == "createCollection"

    def test_create_index_routing(self):
        """Test CREATE INDEX is routed correctly."""
        sql = "CREATE INDEX idx_name ON users (name)"
        result = sql_to_mongo(sql)
        assert result["operation"] == "createIndex"

    def test_mongo_to_sql_insert(self):
        """Test MongoDB to SQL for INSERT."""
        mongo_obj = {
            "operation": "insertOne",
            "collection": "users",
            "document": {"name": "Alice"}
        }
        result = mongo_to_sql(mongo_obj)
        assert "INSERT" in result

    def test_mongo_to_sql_update(self):
        """Test MongoDB to SQL for UPDATE."""
        mongo_obj = {
            "operation": "updateMany",
            "collection": "users",
            "filter": {},
            "update": {"$set": {"age": 30}}
        }
        result = mongo_to_sql(mongo_obj)
        assert "UPDATE" in result

    def test_mongo_to_sql_delete(self):
        """Test MongoDB to SQL for DELETE."""
        mongo_obj = {
            "operation": "deleteMany",
            "collection": "users",
            "filter": {}
        }
        result = mongo_to_sql(mongo_obj)
        assert "DELETE" in result


class TestComplexQueries:
    """Test complex real-world queries."""

    def test_insert_with_various_types(self):
        """Test INSERT with different data types."""
        sql = "INSERT INTO products (name, price, stock, active) VALUES ('Widget', 19.99, 100, 'true')"
        result = sql_insert_to_mongo(sql)

        assert result["document"]["name"] == "Widget"
        assert result["document"]["price"] == 19.99
        assert result["document"]["stock"] == 100

    def test_update_with_multiple_conditions(self):
        """Test UPDATE with complex WHERE."""
        sql = "UPDATE products SET price = 24.99 WHERE category = 'electronics' AND stock > 0"
        result = sql_update_to_mongo(sql)

        assert result["update"]["$set"]["price"] == 24.99
        assert "category" in result["filter"]
        assert "stock" in result["filter"]

    def test_delete_with_comparison_operators(self):
        """Test DELETE with various operators."""
        sql = "DELETE FROM logs WHERE timestamp < 1234567890 AND level = 'debug'"
        result = sql_delete_to_mongo(sql)

        assert result["filter"]["timestamp"] == {"$lt": 1234567890}
        assert result["filter"]["level"] == "debug"

    def test_roundtrip_insert(self):
        """Test INSERT roundtrip conversion."""
        original_sql = "INSERT INTO users (name, age) VALUES ('Alice', 30)"
        mongo_obj = sql_insert_to_mongo(original_sql)
        back_to_sql = mongo_insert_to_sql(mongo_obj)

        assert "INSERT INTO users" in back_to_sql
        assert "Alice" in back_to_sql
        assert "30" in back_to_sql

    def test_roundtrip_update(self):
        """Test UPDATE roundtrip conversion."""
        original_sql = "UPDATE users SET age = 31 WHERE name = 'Alice'"
        mongo_obj = sql_update_to_mongo(original_sql)
        back_to_sql = mongo_update_to_sql(mongo_obj)

        assert "UPDATE users" in back_to_sql
        assert "SET age = 31" in back_to_sql
        assert "WHERE name = 'Alice'" in back_to_sql

    def test_roundtrip_delete(self):
        """Test DELETE roundtrip conversion."""
        original_sql = "DELETE FROM users WHERE age < 18"
        mongo_obj = sql_delete_to_mongo(original_sql)
        back_to_sql = mongo_delete_to_sql(mongo_obj)

        assert "DELETE FROM users" in back_to_sql
        assert "WHERE age < 18" in back_to_sql
