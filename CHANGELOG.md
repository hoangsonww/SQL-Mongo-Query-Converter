# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-01-16

### Added

#### New Modules
- **exceptions.py**: Comprehensive custom exception classes
  - `ConverterError`: Base exception for all converter errors
  - `SQLParseError`: SQL parsing errors
  - `MongoParseError`: MongoDB parsing errors
  - `ValidationError`: Query validation failures
  - `InvalidQueryError`: Malformed queries
  - `ConversionError`: Conversion failures
  - `TypeConversionError`: Type conversion issues
  - `UnsupportedOperationError`: Unsupported operations

- **logger.py**: Production-grade logging system
  - Configurable logging levels
  - File and console logging support
  - Structured log format
  - Logger instance management

- **validator.py**: Query validation and sanitization
  - SQL injection prevention
  - Query syntax validation
  - Dangerous keyword detection
  - MongoDB operator validation
  - Query length limits
  - Nesting depth limits
  - String and identifier sanitization

- **benchmark.py**: Performance benchmarking utilities
  - Function execution timing
  - Statistical analysis (mean, median, std dev)
  - Batch query benchmarking
  - Performance comparison tools
  - Results export to dictionary

- **cli.py**: Command-line interface
  - Interactive mode
  - Batch conversion from files
  - Colorized output (with colorama)
  - Validation before conversion
  - Verbose logging option
  - File-based log output

#### Testing Infrastructure
- **Comprehensive pytest test suite**:
  - `test_sql_to_mongo.py`: 40+ tests for SQL to MongoDB conversion
  - `test_mongo_to_sql.py`: 35+ tests for MongoDB to SQL conversion
  - `test_validator.py`: 30+ tests for validation and sanitization
  - `test_benchmark.py`: 20+ tests for benchmarking utilities
  - `conftest.py`: Pytest fixtures and test data
  - Test coverage for edge cases and error handling

#### Code Quality Tools
- **Black**: Code formatting
- **Flake8**: Linting
- **Pylint**: Advanced linting
- **isort**: Import sorting
- **MyPy**: Type checking
- **pytest-cov**: Code coverage reporting

#### Configuration Files
- `pyproject.toml`: Modern Python project configuration
- `.flake8`: Flake8 configuration
- `.pylintrc`: Pylint configuration
- `.coveragerc`: Coverage configuration
- `pytest.ini`: Pytest configuration
- `requirements-dev.txt`: Development dependencies

#### Documentation & Examples
- `examples/basic_usage.py`: Basic conversion examples
- `examples/advanced_usage.py`: Advanced features (validation, logging, benchmarking)
- Comprehensive docstrings throughout codebase

### Changed
- **Package version**: Bumped from 1.2.2 to 2.0.0
- **setup.py**: Updated with new features and CLI entry point
- **__init__.py**: Expanded exports to include all new modules
- **Package classifiers**: Updated to "Production/Stable" status

### Improved
- Error handling throughout the codebase
- Code organization and modularity
- Documentation and examples
- Test coverage (from ~10% to comprehensive coverage)
- Type safety with better type hints
- Security with query validation and sanitization

### Technical Details
- Minimum Python version: 3.7+
- New dependencies:
  - Core: `sqlparse>=0.4.0`
  - CLI (optional): `click>=8.0.0`, `colorama>=0.4.6`
  - Dev (optional): `pytest`, `pytest-cov`, `black`, `flake8`, `mypy`, etc.

## [1.2.2] - Previous Release

### Features
- Basic SQL to MongoDB conversion
- Basic MongoDB to SQL conversion
- Support for SELECT, WHERE, ORDER BY, LIMIT, GROUP BY
- Support for MongoDB operators: $gt, $gte, $lt, $lte, $eq, $ne, $in, $nin, $regex
- Docker containerization
- PyPI package

---

For more information, see the [README.md](README.md) file.
