from setuptools import setup, find_packages

setup(
    name="sql-mongo-converter",
    version="1.0.0",
    description="Convert SQL queries to MongoDB queries and vice versa.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Son Nguyen",
    author_email="hoangson091104@gmail.com",
    url="https://github.com/yourusername/sql-mongo-converter",
    packages=find_packages(),
    install_requires=[
        "sqlparse"  # for basic SQL parsing
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
