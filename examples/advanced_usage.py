"""
Advanced usage examples for SQL-Mongo Query Converter.
Demonstrates validation, logging, and benchmarking features.
"""

import logging
from sql_mongo_converter import (
    sql_to_mongo,
    mongo_to_sql,
    QueryValidator,
    get_logger,
    ConverterBenchmark
)

# Example 1: Using validation
print("=" * 60)
print("Example 1: Query Validation")
print("=" * 60)

# Validate SQL query before conversion
sql_query = "SELECT * FROM users WHERE age > 25"
try:
    QueryValidator.validate_sql_query(sql_query)
    print(f"✓ SQL query validated: {sql_query}")
    result = sql_to_mongo(sql_query)
    print(f"Converted: {result}")
except Exception as e:
    print(f"✗ Validation failed: {e}")
print()

# Example 2: Using logging
print("=" * 60)
print("Example 2: Logging")
print("=" * 60)

# Configure logger
logger = get_logger('examples', level=logging.DEBUG)
logger.add_file_handler('converter.log')

logger.info("Starting conversion examples")
sql_query = "SELECT name, email FROM users WHERE status = 'active'"
logger.debug(f"Converting query: {sql_query}")
result = sql_to_mongo(sql_query)
logger.info("Conversion completed successfully")
print(f"Result: {result}")
print("Check 'converter.log' for detailed logs")
print()

# Example 3: Benchmarking conversions
print("=" * 60)
print("Example 3: Performance Benchmarking")
print("=" * 60)

benchmark = ConverterBenchmark(warmup_iterations=10)

# Benchmark SQL to MongoDB
sql_queries = [
    "SELECT * FROM users",
    "SELECT * FROM users WHERE age > 25",
    "SELECT name, email FROM users WHERE status = 'active' ORDER BY name LIMIT 100",
]

print("Benchmarking SQL to MongoDB conversions...")
results = benchmark.benchmark_sql_to_mongo(sql_to_mongo, sql_queries, iterations_per_query=100)

for i, result in enumerate(results, 1):
    print(f"\nQuery {i}:")
    print(f"  Throughput: {result.queries_per_second:.2f} queries/sec")
    print(f"  Mean time: {result.mean_time*1000:.3f}ms")
    print(f"  Min time: {result.min_time*1000:.3f}ms")
    print(f"  Max time: {result.max_time*1000:.3f}ms")

print()

# Benchmark MongoDB to SQL
mongo_queries = [
    {'collection': 'users', 'find': {}},
    {'collection': 'users', 'find': {'age': {'$gt': 25}}},
    {
        'collection': 'users',
        'find': {'status': 'active'},
        'projection': {'name': 1, 'email': 1},
        'sort': [('name', 1)],
        'limit': 100
    }
]

print("Benchmarking MongoDB to SQL conversions...")
results = benchmark.benchmark_mongo_to_sql(mongo_to_sql, mongo_queries, iterations_per_query=100)

for i, result in enumerate(results, 1):
    print(f"\nQuery {i}:")
    print(f"  Throughput: {result.queries_per_second:.2f} queries/sec")
    print(f"  Mean time: {result.mean_time*1000:.3f}ms")

print()
print(benchmark.get_summary())

# Example 4: Handling errors gracefully
print("=" * 60)
print("Example 4: Error Handling")
print("=" * 60)

from sql_mongo_converter.exceptions import ValidationError, ConverterError

# Try to validate a dangerous query
try:
    dangerous_query = "DROP TABLE users"
    QueryValidator.validate_sql_query(dangerous_query)
except ValidationError as e:
    print(f"✓ Dangerous query blocked: {e.message}")

# Try to convert invalid query
try:
    invalid_query = "SELECT * FROM users WHERE (unbalanced"
    QueryValidator.validate_sql_query(invalid_query)
except ValidationError as e:
    print(f"✓ Invalid query detected: {e.message}")

print()
print("All advanced examples completed!")
