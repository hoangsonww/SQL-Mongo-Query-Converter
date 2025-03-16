import os
from setuptools import setup, find_packages

# Get the directory where setup.py resides
here = os.path.abspath(os.path.dirname(__file__))

# Read the long description from README.md
with open(os.path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="sql_mongo_converter",
    version="1.1.1",
    description="Convert SQL queries to MongoDB queries and vice versa.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Son Nguyen",
    author_email="hoangson091104@gmail.com",
    url="https://github.com/yourusername/sql-mongo-converter",
    packages=find_packages(),
    install_requires=[
        "sqlparse",  # for basic SQL parsing
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
