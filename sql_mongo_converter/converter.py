from .sql_to_mongo import (
    sql_select_to_mongo,
    sql_insert_to_mongo,
    sql_update_to_mongo,
    sql_delete_to_mongo,
    sql_join_to_mongo,
    sql_create_table_to_mongo,
    sql_create_index_to_mongo,
    sql_drop_to_mongo
)
from .mongo_to_sql import (
    mongo_find_to_sql,
    mongo_insert_to_sql,
    mongo_update_to_sql,
    mongo_delete_to_sql
)


def sql_to_mongo(sql_query: str, allow_mutations: bool = True):
    """
    Converts a SQL query to MongoDB format.

    Supports:
    - SELECT queries -> MongoDB find/aggregate
    - INSERT queries -> MongoDB insertOne/insertMany
    - UPDATE queries -> MongoDB updateMany
    - DELETE queries -> MongoDB deleteMany
    - JOIN queries -> MongoDB $lookup aggregation
    - CREATE TABLE -> MongoDB createCollection
    - CREATE INDEX -> MongoDB createIndex

    :param sql_query: The SQL query as a string.
    :param allow_mutations: Whether to allow write operations (INSERT, UPDATE, DELETE).
    :return: A MongoDB operation dict.
    """
    query_upper = sql_query.strip().upper()

    # Route based on query type
    if query_upper.startswith('SELECT'):
        # Check if it's a JOIN query
        if 'JOIN' in query_upper:
            return sql_join_to_mongo(sql_query)
        else:
            return sql_select_to_mongo(sql_query)

    elif query_upper.startswith('INSERT'):
        if not allow_mutations:
            raise ValueError("INSERT operations require allow_mutations=True")
        return sql_insert_to_mongo(sql_query)

    elif query_upper.startswith('UPDATE'):
        if not allow_mutations:
            raise ValueError("UPDATE operations require allow_mutations=True")
        return sql_update_to_mongo(sql_query)

    elif query_upper.startswith('DELETE'):
        if not allow_mutations:
            raise ValueError("DELETE operations require allow_mutations=True")
        return sql_delete_to_mongo(sql_query)

    elif query_upper.startswith('CREATE TABLE'):
        return sql_create_table_to_mongo(sql_query)

    elif query_upper.startswith('CREATE INDEX'):
        return sql_create_index_to_mongo(sql_query)

    elif query_upper.startswith('DROP'):
        return sql_drop_to_mongo(sql_query)

    else:
        raise ValueError(f"Unsupported SQL operation: {sql_query[:50]}...")


def mongo_to_sql(mongo_obj: dict):
    """
    Converts a MongoDB operation dict to SQL query.

    Supports:
    - find operations -> SELECT queries
    - insertOne/insertMany -> INSERT queries
    - updateMany/updateOne -> UPDATE queries
    - deleteMany/deleteOne -> DELETE queries

    :param mongo_obj: The MongoDB operation dict.
    :return: The SQL query as a string.
    """
    operation = mongo_obj.get("operation", "find")

    # Route based on operation type
    if operation in ["find", "aggregate"]:
        return mongo_find_to_sql(mongo_obj)

    elif operation in ["insertOne", "insertMany"]:
        return mongo_insert_to_sql(mongo_obj)

    elif operation in ["updateOne", "updateMany"]:
        return mongo_update_to_sql(mongo_obj)

    elif operation in ["deleteOne", "deleteMany"]:
        return mongo_delete_to_sql(mongo_obj)

    else:
        # Default to find if no operation specified (backward compatibility)
        return mongo_find_to_sql(mongo_obj)
