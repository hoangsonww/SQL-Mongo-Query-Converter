import os
from setuptools import setup, find_packages

# Get the directory where setup.py resides
here = os.path.abspath(os.path.dirname(__file__))

# Read the long description from README.md
with open(os.path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="sql_mongo_converter",
    version="2.1.0",
    description="Production-ready converter for SQL and MongoDB queries with full CRUD operations, JOINs, and advanced SQL support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Son Nguyen",
    author_email="hoangson091104@gmail.com",
    url="https://github.com/hoangsonww/SQL-Mongo-Query-Converter",
    packages=find_packages(exclude=["tests", "tests.*"]),
    install_requires=[
        "sqlparse>=0.4.0",
    ],
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
            'pytest-benchmark>=4.0.0',
            'mypy>=1.0.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
            'isort>=5.12.0',
            'pylint>=3.0.0',
        ],
        'cli': [
            'click>=8.0.0',
            'colorama>=0.4.6',
        ],
    },
    entry_points={
        'console_scripts': [
            'sql-mongo-converter=sql_mongo_converter.cli:main',
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Topic :: Database",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.7",
)
