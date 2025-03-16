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

- **SQL to MongoDB Conversion:**  
  Convert SQL SELECT queries—including complex WHERE clauses with multiple conditions—into MongoDB query dictionaries with filters and projections.

- **MongoDB to SQL Conversion:**  
  Translate MongoDB find dictionaries, including support for comparison operators, logical operators, and list conditions, into SQL SELECT statements with WHERE clauses, ORDER BY, and optional LIMIT/OFFSET.

- **Extensible & Robust:**  
  Built to handle a wide range of query patterns. Easily extended to support additional SQL functions, advanced operators, and more complex query structures.

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

Use the `sql_to_mongo` function to convert a SQL SELECT query into a MongoDB query dictionary. The output dictionary contains:
- **collection:** The table name.
- **find:** The filter dictionary derived from the WHERE clause.
- **projection:** The columns to return (if not all).

#### Example

```python
from sql_mongo_converter import sql_to_mongo

sql_query = "SELECT name, age FROM users WHERE age > 30 AND name = 'Alice';"
mongo_query = sql_to_mongo(sql_query)
print(mongo_query)
# Expected output:
# {
#   "collection": "users",
#   "find": { "age": {"$gt": 30}, "name": "Alice" },
#   "projection": { "name": 1, "age": 1 }
# }
```

### Converting MongoDB to SQL

Use the `mongo_to_sql` function to convert a MongoDB query dictionary into a SQL SELECT statement. It supports operators such as `$gt`, `$gte`, `$lt`, `$lte`, `$in`, `$nin`, and `$regex`, as well as logical operators like `$and` and `$or`.

#### Example

```python
from sql_mongo_converter import mongo_to_sql

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
# Example output:
# SELECT age, status, tags FROM users WHERE ((age >= 25) OR (status = 'ACTIVE')) AND (tags IN ('dev', 'qa'))
# ORDER BY age ASC, name DESC LIMIT 10 OFFSET 5;
```

---

## API Reference

### `sql_to_mongo(sql_query: str) -> dict`
- **Description:**  
  Parses a SQL SELECT query and converts it into a MongoDB query dictionary.
- **Parameters:**  
  - `sql_query`: A valid SQL SELECT query string.
- **Returns:**  
  A dictionary containing:
  - `collection`: The table name.
  - `find`: The filter derived from the WHERE clause.
  - `projection`: A dictionary specifying the columns to return.

### `mongo_to_sql(mongo_obj: dict) -> str`
- **Description:**  
  Converts a MongoDB query dictionary into a SQL SELECT statement.
- **Parameters:**  
  - `mongo_obj`: A dictionary representing a MongoDB find query, including keys such as `collection`, `find`, `projection`, `sort`, `limit`, and `skip`.
- **Returns:**  
  A SQL SELECT statement as a string.

---

## Testing

The package includes a unittest suite to verify conversion functionality.

### Running Tests

1. **Create a virtual environment (optional but recommended):**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install test dependencies:**

   ```bash
   pip install -r requirements.txt
   pip install pytest
   ```

3. **Run tests:**

   ```bash
   python -m unittest discover tests
   # or using pytest:
   pytest --maxfail=1 --disable-warnings -q
   ```
   
### Demo Script

A demo script in the `tests` directory is provided to showcase the conversion capabilities. It can be run directly to see examples of SQL to MongoDB and MongoDB to SQL conversions.

```bash
python demo.py
```

The script demonstrates various conversion scenarios.

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

**SQL-Mongo Converter** is a powerful, lightweight tool that bridges SQL and MongoDB query languages. It is ideal for developers migrating between SQL and MongoDB data models, or those who want to prototype and test queries quickly. Extend and customize the converter as needed to support more advanced queries or additional SQL constructs.

Happy converting! 🍃
