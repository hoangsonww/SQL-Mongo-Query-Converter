"""
Basic usage examples for SQL-Mongo Query Converter.
"""

from sql_mongo_converter import sql_to_mongo, mongo_to_sql

# Example 1: Simple SQL to MongoDB
print("=" * 60)
print("Example 1: Simple SQL to MongoDB")
print("=" * 60)

sql_query = "SELECT * FROM users WHERE age > 25"
mongo_result = sql_to_mongo(sql_query)
print(f"SQL: {sql_query}")
print(f"MongoDB: {mongo_result}")
print()

# Example 2: SQL with multiple conditions
print("=" * 60)
print("Example 2: SQL with multiple conditions")
print("=" * 60)

sql_query = "SELECT name, email FROM users WHERE age >= 18 AND status = 'active' ORDER BY name DESC LIMIT 100"
mongo_result = sql_to_mongo(sql_query)
print(f"SQL: {sql_query}")
print(f"MongoDB: {mongo_result}")
print()

# Example 3: MongoDB to SQL
print("=" * 60)
print("Example 3: MongoDB to SQL")
print("=" * 60)

mongo_query = {
    'collection': 'users',
    'find': {'age': {'$gte': 18}, 'status': 'active'},
    'projection': {'name': 1, 'email': 1},
    'sort': [('name', -1)],
    'limit': 100
}
sql_result = mongo_to_sql(mongo_query)
print(f"MongoDB: {mongo_query}")
print(f"SQL: {sql_result}")
print()

# Example 4: Complex MongoDB operators
print("=" * 60)
print("Example 4: Complex MongoDB operators")
print("=" * 60)

mongo_query = {
    'collection': 'products',
    'find': {
        'price': {'$gte': 10, '$lte': 100},
        'category': {'$in': ['electronics', 'computers']},
        'status': {'$ne': 'discontinued'}
    },
    'sort': [('price', 1)],
    'limit': 50
}
sql_result = mongo_to_sql(mongo_query)
print(f"MongoDB: {mongo_query}")
print(f"SQL: {sql_result}")
print()

# Example 5: INSERT operations
print("=" * 60)
print("Example 5: INSERT operations")
print("=" * 60)

sql_insert = "INSERT INTO users (name, age, email) VALUES ('Alice', 30, 'alice@example.com')"
mongo_result = sql_to_mongo(sql_insert, allow_mutations=True)
print(f"SQL: {sql_insert}")
print(f"MongoDB: {mongo_result}")
print()

# Example 6: UPDATE operations
print("=" * 60)
print("Example 6: UPDATE operations")
print("=" * 60)

sql_update = "UPDATE users SET age = 31, status = 'verified' WHERE name = 'Alice'"
mongo_result = sql_to_mongo(sql_update, allow_mutations=True)
print(f"SQL: {sql_update}")
print(f"MongoDB: {mongo_result}")
print()

# Example 7: DELETE operations
print("=" * 60)
print("Example 7: DELETE operations")
print("=" * 60)

sql_delete = "DELETE FROM users WHERE age < 18"
mongo_result = sql_to_mongo(sql_delete, allow_mutations=True)
print(f"SQL: {sql_delete}")
print(f"MongoDB: {mongo_result}")
print()

# Example 8: JOIN operations
print("=" * 60)
print("Example 8: JOIN operations")
print("=" * 60)

sql_join = "SELECT u.name, o.total FROM users u INNER JOIN orders o ON u.id = o.user_id"
mongo_result = sql_to_mongo(sql_join)
print(f"SQL: {sql_join}")
print(f"MongoDB: {mongo_result}")
print()

# Example 9: CREATE TABLE
print("=" * 60)
print("Example 9: CREATE TABLE")
print("=" * 60)

sql_create_table = "CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100), age INT NOT NULL)"
mongo_result = sql_to_mongo(sql_create_table)
print(f"SQL: {sql_create_table}")
print(f"MongoDB: {mongo_result}")
print()

# Example 10: CREATE INDEX
print("=" * 60)
print("Example 10: CREATE INDEX")
print("=" * 60)

sql_create_index = "CREATE INDEX idx_user_email ON users (email)"
mongo_result = sql_to_mongo(sql_create_index)
print(f"SQL: {sql_create_index}")
print(f"MongoDB: {mongo_result}")
print()

# Example 11: MongoDB to SQL (INSERT)
print("=" * 60)
print("Example 11: MongoDB INSERT to SQL")
print("=" * 60)

mongo_insert = {
    "collection": "users",
    "operation": "insertOne",
    "document": {"name": "Bob", "age": 25, "email": "bob@example.com"}
}
sql_result = mongo_to_sql(mongo_insert)
print(f"MongoDB: {mongo_insert}")
print(f"SQL: {sql_result}")
print()

# Example 12: MongoDB to SQL (UPDATE)
print("=" * 60)
print("Example 12: MongoDB UPDATE to SQL")
print("=" * 60)

mongo_update = {
    "collection": "users",
    "operation": "updateMany",
    "filter": {"age": {"$lt": 18}},
    "update": {"$set": {"status": "minor"}}
}
sql_result = mongo_to_sql(mongo_update)
print(f"MongoDB: {mongo_update}")
print(f"SQL: {sql_result}")
print()

print("All examples completed successfully!")
