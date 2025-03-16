from .sql_to_mongo import sql_select_to_mongo
from .mongo_to_sql import mongo_find_to_sql


def sql_to_mongo(sql_query: str):
    """
    Converts a SQL SELECT query to a naive MongoDB find dict.

    :param sql_query: The SQL SELECT query as a string.
    :return: A naive MongoDB find dict.
    """
    return sql_select_to_mongo(sql_query)


def mongo_to_sql(mongo_obj: dict):
    """
    Converts a naive Mongo 'find' dict to a basic SQL SELECT.

    :param mongo_obj: The MongoDB find dict.
    :return: The SQL SELECT query as a string.
    """
    return mongo_find_to_sql(mongo_obj)
