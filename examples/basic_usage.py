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

print("All examples completed successfully!")
