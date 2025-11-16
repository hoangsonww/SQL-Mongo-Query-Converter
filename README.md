# SQL-Mongo Converter - A Lightweight SQL to MongoDB (and Vice Versa) Query Converter 🍃

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat&logo=opensource)](LICENSE)  
[![Python Version](https://img.shields.io/badge/Python-%3E=3.7-brightgreen.svg?style=flat&logo=python)](https://www.python.org/)  
[![SQL](https://img.shields.io/badge/SQL-%23E34F26.svg?style=flat&logo=postgresql)](https://www.postgresql.org/)  
[![MongoDB](https://img.shields.io/badge/MongoDB-%23471240.svg?style=flat&logo=mongodb)](https://www.mongodb.com/)  
[![PyPI](https://img.shields.io/pypi/v/sql-mongo-converter.svg?style=flat&logo=pypi)](https://pypi.org/project/sql-mongo-converter/)

**SQL-Mongo Converter** is a lightweight Python library for converting SQL queries into MongoDB query dictionaries and converting MongoDB query dictionaries into SQL statements. It is designed for developers who need to quickly migrate or prototype between SQL-based and MongoDB-based data models without the overhead of a full ORM.

**Currently live on PyPI:** [https://pypi.org/project/sql-mongo-converter/](https://pypi.org/project/sql-mongo-converter/)

---

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
  - [Converting SQL to MongoDB](#converting-sql-to-mongodb)
  - [Converting MongoDB to SQL](#converting-mongodb-to-sql)
- [API Reference](#api-reference)
- [Testing](#testing)
- [Building & Publishing](#building--publishing)
- [Contributing](#contributing)
- [License](#license)
- [Final Remarks](#final-remarks)

---

## Features

- **Comprehensive SQL to MongoDB Conversion:**
  - **SELECT queries**: Simple and complex queries with WHERE, ORDER BY, GROUP BY, HAVING, LIMIT, OFFSET
  - **INSERT operations**: Single and bulk inserts with column specifications
  - **UPDATE operations**: Targeted updates with WHERE clauses
  - **DELETE operations**: Conditional and bulk deletions
  - **JOIN operations**: INNER JOIN and LEFT JOIN converted to MongoDB `$lookup` aggregation
  - **CREATE operations**: TABLE and INDEX creation with schema validation
  - **DROP operations**: TABLE and INDEX dropping
  - **DISTINCT queries**: Single and multiple field distinct operations
  - **Aggregation functions**: COUNT, SUM, AVG, MIN, MAX with GROUP BY/HAVING
  - **Advanced WHERE operators**: BETWEEN, LIKE (with wildcards), IN, NOT IN, IS NULL, IS NOT NULL, OR, NOT

- **Bidirectional MongoDB to SQL Conversion:**
  Translate MongoDB operations back to SQL:
  - `insertOne`/`insertMany` → INSERT statements
  - `updateMany` → UPDATE statements with `$set`, `$inc` operators
  - `deleteMany` → DELETE statements
  - Aggregation pipelines → SELECT with GROUP BY/HAVING
  - Complex queries with `$match`, `$group`, `$lookup`, `$project`, `$sort`, `$limit`

- **Production-Ready Features:**
  - Query validation and SQL injection prevention
  - Configurable mutation operations (`allow_mutations` flag)
  - Comprehensive error handling with custom exceptions
  - Production-grade logging system
  - Performance benchmarking utilities
  - Command-line interface (CLI)

- **Extensible & Robust:**
  Built to handle a wide range of query patterns with 103 passing tests and 59%+ code coverage. Easily extended to support additional SQL functions, advanced operators, and more complex query structures.

---

## Installation

### Prerequisites

- Python 3.7 or higher
- pip

### Install via PyPI

```bash
pip install sql-mongo-converter
```

### Installing from Source

Clone the repository and install dependencies:

```bash
git clone https://github.com/yourusername/sql-mongo-converter.git
cd sql-mongo-converter
pip install -r requirements.txt
python setup.py install
```

---

## Usage

### Converting SQL to MongoDB

The `sql_to_mongo` function converts various SQL statements into MongoDB query dictionaries. By default, write operations (INSERT, UPDATE, DELETE) are enabled via the `allow_mutations` parameter.

#### SELECT Queries

```python
from sql_mongo_converter import sql_to_mongo

# Basic SELECT
sql_query = "SELECT name, age FROM users WHERE age > 30 AND name = 'Alice';"
mongo_query = sql_to_mongo(sql_query)
print(mongo_query)
# Output:
# {
#   "collection": "users",
#   "find": { "age": {"$gt": 30}, "name": "Alice" },
#   "projection": { "name": 1, "age": 1 }
# }

# DISTINCT query
sql_query = "SELECT DISTINCT department FROM employees;"
mongo_query = sql_to_mongo(sql_query)
# Output: {"collection": "employees", "operation": "distinct", "field": "department"}

# Aggregation with GROUP BY and HAVING
sql_query = "SELECT department, COUNT(*) FROM employees GROUP BY department HAVING COUNT(*) > 5;"
mongo_query = sql_to_mongo(sql_query)
# Output: Aggregation pipeline with $group and $match stages
```

#### Advanced WHERE Clauses

```python
# BETWEEN operator
sql_query = "SELECT * FROM products WHERE price BETWEEN 10 AND 100;"
mongo_query = sql_to_mongo(sql_query)
# Output: {"find": {"price": {"$gte": 10, "$lte": 100}}}

# LIKE with wildcards (% and _)
sql_query = "SELECT * FROM users WHERE name LIKE 'John%';"
mongo_query = sql_to_mongo(sql_query)
# Output: {"find": {"name": {"$regex": "John.*", "$options": "i"}}}

# IN and NOT IN
sql_query = "SELECT * FROM users WHERE role IN ('admin', 'manager');"
mongo_query = sql_to_mongo(sql_query)
# Output: {"find": {"role": {"$in": ["admin", "manager"]}}}

# IS NULL and IS NOT NULL
sql_query = "SELECT * FROM users WHERE email IS NOT NULL;"
mongo_query = sql_to_mongo(sql_query)
# Output: {"find": {"email": {"$ne": None}}}

# OR and NOT operators
sql_query = "SELECT * FROM users WHERE age > 30 OR status = 'active';"
mongo_query = sql_to_mongo(sql_query)
# Output: {"find": {"$or": [{"age": {"$gt": 30}}, {"status": "active"}]}}
```

#### INSERT Operations

```python
# Single row insert
sql_query = "INSERT INTO users (name, age, email) VALUES ('Alice', 30, 'alice@example.com');"
mongo_query = sql_to_mongo(sql_query)
# Output: {"collection": "users", "operation": "insertOne", "document": {...}}

# Multiple rows insert
sql_query = "INSERT INTO users (name, age) VALUES ('Bob', 25), ('Charlie', 35);"
mongo_query = sql_to_mongo(sql_query)
# Output: {"operation": "insertMany", "documents": [{...}, {...}]}
```

#### UPDATE Operations

```python
# UPDATE with WHERE clause
sql_query = "UPDATE users SET age = 31, status = 'active' WHERE name = 'Alice';"
mongo_query = sql_to_mongo(sql_query)
# Output: {"collection": "users", "operation": "updateMany", "filter": {...}, "update": {"$set": {...}}}
```

#### DELETE Operations

```python
# DELETE with WHERE clause
sql_query = "DELETE FROM users WHERE age < 18;"
mongo_query = sql_to_mongo(sql_query)
# Output: {"collection": "users", "operation": "deleteMany", "filter": {"age": {"$lt": 18}}}
```

#### JOIN Operations

```python
# INNER JOIN
sql_query = """
SELECT u.name, o.order_id
FROM users u
INNER JOIN orders o ON u.user_id = o.user_id;
"""
mongo_query = sql_to_mongo(sql_query)
# Output: Aggregation pipeline with $lookup stage

# LEFT JOIN
sql_query = """
SELECT u.name, o.order_id
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id;
"""
mongo_query = sql_to_mongo(sql_query)
# Output: Aggregation pipeline with $lookup preserving unmatched documents
```

#### CREATE Operations

```python
# CREATE TABLE with schema
sql_query = """
CREATE TABLE users (
    id INT,
    name VARCHAR(100),
    age INT,
    email VARCHAR(255)
);
"""
mongo_query = sql_to_mongo(sql_query)
# Output: createCollection with schema validation

# CREATE INDEX
sql_query = "CREATE INDEX idx_age ON users (age DESC, name ASC);"
mongo_query = sql_to_mongo(sql_query)
# Output: {"operation": "createIndex", "keys": {"age": -1, "name": 1}}
```

#### DROP Operations

```python
# DROP TABLE
sql_query = "DROP TABLE users;"
mongo_query = sql_to_mongo(sql_query, allow_mutations=True)
# Output: {"collection": "users", "operation": "drop"}

# DROP INDEX
sql_query = "DROP INDEX idx_age ON users;"
mongo_query = sql_to_mongo(sql_query, allow_mutations=True)
# Output: {"collection": "users", "operation": "dropIndex", "index_name": "idx_age"}
```

### Converting MongoDB to SQL

The `mongo_to_sql` function translates MongoDB operations back into SQL statements.

#### Find Operations

```python
from sql_mongo_converter import mongo_to_sql

# Basic find with operators
mongo_obj = {
    "collection": "users",
    "find": {
        "$or": [
            {"age": {"$gte": 25}},
            {"status": "ACTIVE"}
        ],
        "tags": {"$in": ["dev", "qa"]}
    },
    "projection": {"age": 1, "status": 1, "tags": 1},
    "sort": [("age", 1), ("name", -1)],
    "limit": 10,
    "skip": 5
}
sql_query = mongo_to_sql(mongo_obj)
print(sql_query)
# Output:
# SELECT age, status, tags FROM users WHERE ((age >= 25) OR (status = 'ACTIVE')) AND (tags IN ('dev', 'qa'))
# ORDER BY age ASC, name DESC LIMIT 10 OFFSET 5;
```

#### Insert Operations

```python
# insertOne
mongo_obj = {
    "collection": "users",
    "operation": "insertOne",
    "document": {"name": "Alice", "age": 30, "email": "alice@example.com"}
}
sql_query = mongo_to_sql(mongo_obj)
# Output: INSERT INTO users (name, age, email) VALUES ('Alice', 30, 'alice@example.com');

# insertMany
mongo_obj = {
    "collection": "users",
    "operation": "insertMany",
    "documents": [
        {"name": "Bob", "age": 25},
        {"name": "Charlie", "age": 35}
    ]
}
sql_query = mongo_to_sql(mongo_obj)
# Output: INSERT INTO users (name, age) VALUES ('Bob', 25), ('Charlie', 35);
```

#### Update Operations

```python
mongo_obj = {
    "collection": "users",
    "operation": "updateMany",
    "filter": {"name": "Alice"},
    "update": {"$set": {"age": 31, "status": "active"}}
}
sql_query = mongo_to_sql(mongo_obj)
# Output: UPDATE users SET age = 31, status = 'active' WHERE name = 'Alice';
```

#### Delete Operations

```python
mongo_obj = {
    "collection": "users",
    "operation": "deleteMany",
    "filter": {"age": {"$lt": 18}}
}
sql_query = mongo_to_sql(mongo_obj)
# Output: DELETE FROM users WHERE age < 18;
```

---

## API Reference

### `sql_to_mongo(sql_query: str, allow_mutations: bool = True) -> dict`
- **Description:**
  Parses SQL statements (SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, JOIN) and converts them into MongoDB query dictionaries.
- **Parameters:**
  - `sql_query`: A valid SQL query string
  - `allow_mutations`: (Optional) Enable/disable write operations (INSERT, UPDATE, DELETE, CREATE, DROP). Default: `True`
- **Returns:**
  A dictionary containing the MongoDB operation specification. Structure varies by operation type:

  **SELECT queries:**
  ```python
  {
    "collection": str,           # Table name
    "find": dict,                # Filter from WHERE clause
    "projection": dict,          # Columns to return
    "sort": list,                # Optional: sort specification
    "limit": int,                # Optional: result limit
    "skip": int                  # Optional: offset
  }
  ```

  **Aggregation queries (with GROUP BY/HAVING/DISTINCT/JOIN):**
  ```python
  {
    "collection": str,
    "operation": "aggregate",
    "pipeline": [...]            # Aggregation pipeline stages
  }
  ```

  **INSERT operations:**
  ```python
  {
    "collection": str,
    "operation": "insertOne" | "insertMany",
    "document": dict,            # For insertOne
    "documents": [dict]          # For insertMany
  }
  ```

  **UPDATE operations:**
  ```python
  {
    "collection": str,
    "operation": "updateMany",
    "filter": dict,              # WHERE clause
    "update": {"$set": {...}}    # SET clause
  }
  ```

  **DELETE operations:**
  ```python
  {
    "collection": str,
    "operation": "deleteMany",
    "filter": dict               # WHERE clause
  }
  ```

  **CREATE/DROP operations:**
  ```python
  {
    "collection": str,
    "operation": "createCollection" | "createIndex" | "drop" | "dropIndex",
    # ... additional fields based on operation
  }
  ```

### `mongo_to_sql(mongo_obj: dict) -> str`
- **Description:**
  Converts a MongoDB query dictionary into SQL statements. Supports bidirectional conversion for all operation types.
- **Parameters:**
  - `mongo_obj`: A dictionary representing a MongoDB operation with keys such as:
    - `collection`: Collection/table name (required)
    - `operation`: Operation type (optional, defaults to "find")
    - `find`: Filter conditions for SELECT/UPDATE/DELETE
    - `projection`: Columns to select
    - `sort`: Sort specification
    - `limit`/`skip`: Result pagination
    - `document`/`documents`: For INSERT operations
    - `filter`/`update`: For UPDATE operations
    - `pipeline`: For aggregation operations
- **Returns:**
  A SQL statement string (SELECT, INSERT, UPDATE, DELETE)
- **Supported MongoDB Operators:**
  - Comparison: `$gt`, `$gte`, `$lt`, `$lte`, `$eq`, `$ne`
  - Array: `$in`, `$nin`
  - Logical: `$and`, `$or`, `$not`
  - Pattern: `$regex`
  - Update: `$set`, `$inc`, `$unset`
  - Aggregation: `$match`, `$group`, `$lookup`, `$project`, `$sort`, `$limit`, `$skip`

### Supported SQL Operations

#### Query Operations
- **SELECT**: Basic and complex queries with projections, filters, sorting
- **DISTINCT**: Single and multiple field distinct queries
- **WHERE**: Complex conditions with AND, OR, NOT, BETWEEN, LIKE, IN, IS NULL
- **JOIN**: INNER JOIN and LEFT JOIN (converted to `$lookup`)
- **GROUP BY**: With aggregation functions (COUNT, SUM, AVG, MIN, MAX)
- **HAVING**: Post-aggregation filtering
- **ORDER BY**: Single and multiple column sorting (ASC/DESC)
- **LIMIT/OFFSET**: Result pagination

#### Write Operations
- **INSERT**: Single and bulk inserts with column specifications
- **UPDATE**: Conditional updates with SET and WHERE clauses
- **DELETE**: Conditional and bulk deletions

#### DDL Operations
- **CREATE TABLE**: With column definitions and type mapping to BSON
- **CREATE INDEX**: With single/multiple columns and sort order
- **DROP TABLE**: Collection removal
- **DROP INDEX**: Index removal

#### Operators
- **Comparison**: `=`, `>`, `>=`, `<`, `<=`, `!=`, `<>`
- **Range**: `BETWEEN ... AND ...`
- **Pattern**: `LIKE` with wildcards (`%`, `_`)
- **List**: `IN (...)`, `NOT IN (...)`
- **Null**: `IS NULL`, `IS NOT NULL`
- **Logical**: `AND`, `OR`, `NOT`
- **Aggregation**: `COUNT`, `SUM`, `AVG`, `MIN`, `MAX`

---

## Testing

The package includes a comprehensive pytest test suite with **103 passing tests** and **59%+ code coverage**.

### Running Tests

1. **Create a virtual environment (optional but recommended):**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install test dependencies:**

   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-cov
   ```

3. **Run tests:**

   ```bash
   # Run all tests
   pytest tests/ -v

   # With coverage report
   pytest tests/ --cov=sql_mongo_converter --cov-report=html

   # Quick run
   pytest tests/ -q --tb=line
   ```

### Test Coverage

The test suite includes:
- **test_sql_to_mongo.py**: 40+ tests for SQL to MongoDB conversion
- **test_mongo_to_sql.py**: 35+ tests for MongoDB to SQL conversion
- **test_new_operations.py**: 33+ tests for INSERT, UPDATE, DELETE, JOIN, CREATE, DROP operations
- **test_validator.py**: 30+ tests for query validation and security
- **test_integration.py**: End-to-end integration tests
- **test_benchmark.py**: Performance benchmarking tests

All tests cover:
- Basic operations (SELECT, INSERT, UPDATE, DELETE)
- Advanced features (JOIN, GROUP BY, HAVING, DISTINCT)
- Complex WHERE clauses (BETWEEN, LIKE, IN, OR, NOT, IS NULL)
- Aggregation functions (COUNT, SUM, AVG, MIN, MAX)
- DDL operations (CREATE, DROP)
- Edge cases and error handling
- Bidirectional conversions (SQL↔MongoDB)

### Demo Scripts

Example scripts are provided in the `examples/` directory:

```bash
# Basic usage examples
python examples/basic_usage.py

# Advanced features (validation, logging, benchmarking)
python examples/advanced_usage.py
```

These scripts demonstrate various conversion scenarios and best practices.

---

## Building & Publishing

### Building the Package

1. **Ensure you have setuptools and wheel installed:**

   ```bash
   pip install setuptools wheel
   ```

2. **Build the package:**

   ```bash
   python setup.py sdist bdist_wheel
   ```

   This creates a `dist/` folder with the distribution files.

### Publishing to PyPI

1. **Install Twine:**

   ```bash
   pip install twine
   ```

2. **Upload your package:**

   ```bash
   twine upload dist/*
   ```

3. **Follow the prompts** for your PyPI credentials.

---

## Contributing

Contributions are welcome! To contribute:

1. **Fork the Repository**
2. **Create a Feature Branch:**

   ```bash
   git checkout -b feature/my-new-feature
   ```

3. **Commit Your Changes:**

   ```bash
   git commit -am "Add new feature or fix bug"
   ```

4. **Push Your Branch:**

   ```bash
   git push origin feature/my-new-feature
   ```

5. **Submit a Pull Request** on GitHub.

For major changes, please open an issue first to discuss your ideas.

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Final Remarks

**SQL-Mongo Converter** is a comprehensive, production-ready tool that bridges SQL and MongoDB query languages with full bidirectional conversion support.

### Key Highlights

- **Complete CRUD Operations**: Full support for SELECT, INSERT, UPDATE, DELETE with complex conditions
- **Advanced SQL Features**: JOIN, GROUP BY, HAVING, DISTINCT, aggregation functions, and more
- **Comprehensive Operator Support**: BETWEEN, LIKE, IN, IS NULL, OR, NOT - all major SQL operators
- **DDL Operations**: CREATE and DROP for tables and indexes
- **Production-Ready**: 103 passing tests, 59%+ code coverage, comprehensive error handling
- **Bidirectional**: Convert SQL→MongoDB and MongoDB→SQL seamlessly
- **Secure**: Built-in query validation and SQL injection prevention

### Use Cases

- **Database Migration**: Easily migrate between SQL and MongoDB databases
- **Query Translation**: Convert existing SQL queries to MongoDB for NoSQL adoption
- **Prototyping**: Quickly test query equivalents between SQL and MongoDB
- **Learning Tool**: Understand how SQL concepts map to MongoDB operations
- **API Development**: Dynamically convert between query formats in your application

### What's New in v2.1.0

This release massively expands query support beyond the basic SELECT-only functionality:
- ✅ Full CRUD operations (INSERT, UPDATE, DELETE)
- ✅ JOIN support with MongoDB `$lookup` aggregation
- ✅ CREATE/DROP TABLE and INDEX operations
- ✅ DISTINCT queries with single/multiple fields
- ✅ GROUP BY with HAVING clause
- ✅ Aggregation functions: COUNT, SUM, AVG, MIN, MAX
- ✅ Advanced WHERE operators: BETWEEN, LIKE, IN, NOT IN, IS NULL, OR, NOT
- ✅ Complex nested conditions with proper precedence
- ✅ Bidirectional conversion for all operations

The converter is ideal for developers migrating between SQL and MongoDB data models, building database abstraction layers, or learning NoSQL query patterns. Extend and customize as needed to support additional SQL constructs or MongoDB operators.

Happy converting! 🍃
