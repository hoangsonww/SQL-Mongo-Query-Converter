import sqlparse
from sqlparse.sql import (
    IdentifierList,
    Identifier,
    Where,
    Token,
    Parenthesis,
)
from sqlparse.tokens import Keyword, DML


def sql_select_to_mongo(sql_query: str):
    """
    Convert a SELECT...FROM...WHERE...ORDER BY...GROUP BY...LIMIT...
    into a Mongo dict:

    {
      "collection": <table>,
      "find": { ...where... },
      "projection": { col1:1, col2:1 } or None,
      "sort": [...],
      "limit": int,
      "group": { ... }
    }

    :param sql_query: The SQL SELECT query as a string.
    :return: A naive MongoDB find dict.
    """
    parsed = sqlparse.parse(sql_query)
    if not parsed:
        return {}

    statement = parsed[0]
    columns, table_name, where_clause, order_by, group_by, limit_val = parse_select_statement(statement)

    return build_mongo_query(
        table_name, columns, where_clause, order_by, group_by, limit_val
    )


def parse_select_statement(statement):
    """
    Parse:
      SELECT <columns> FROM <table>
      [WHERE ...]
      [GROUP BY ...]
      [ORDER BY ...]
      [LIMIT ...]
    in that approximate order.

    Returns:
      columns, table_name, where_clause_dict, order_by_list, group_by_list, limit_val

    :param statement: The parsed SQL statement.
    :return: A tuple containing columns, table_name, where_clause_dict, order_by_list, group_by_list, limit_val
    """
    columns = []
    table_name = None
    where_clause = {}
    order_by = []  # e.g. [("age", 1), ("name", -1)]
    group_by = []  # e.g. ["department", "role"]
    limit_val = None

    found_select = False
    reading_columns = False
    reading_from = False

    tokens = [t for t in statement.tokens if not t.is_whitespace]

    # We'll do multiple passes or a single pass with states
    # Single pass approach:
    i = 0
    while i < len(tokens):
        token = tokens[i]

        # detect SELECT
        if token.ttype is DML and token.value.upper() == "SELECT":
            found_select = True
            reading_columns = True
            i += 1
            continue

        # parse columns until we see FROM
        if reading_columns:
            if token.ttype is Keyword and token.value.upper() == "FROM":
                reading_columns = False
                reading_from = True
                i += 1
                continue
            else:
                possible_cols = extract_columns(token)
                if possible_cols:
                    columns = possible_cols
                i += 1
                continue

        # parse table name right after FROM
        if reading_from:
            # if token is Keyword (like WHERE, GROUP, ORDER), we skip
            if token.ttype is Keyword:
                # no table name found => might be incomplete
                reading_from = False
                # don't advance i, we'll handle logic below
            else:
                # assume table name
                table_name = str(token).strip()
                reading_from = False
            i += 1
            continue

        # check if token is a Where object => parse WHERE
        if isinstance(token, Where):
            where_clause = extract_where_clause(token)
            i += 1
            continue

        # or check if token is a simple 'WHERE' keyword
        if token.ttype is Keyword and token.value.upper() == "WHERE":
            # next token might be the actual conditions or a Where
            # try to gather the text
            # but often sqlparse lumps everything into a Where
            if i + 1 < len(tokens):
                next_token = tokens[i + 1]
                if isinstance(next_token, Where):
                    where_clause = extract_where_clause(next_token)
                    i += 2
                    continue
                else:
                    # fallback substring approach if needed
                    where_clause_text = str(next_token).strip()
                    where_clause = parse_where_conditions(where_clause_text)
                    i += 2
                    continue
            i += 1
            continue

        # handle ORDER BY
        if token.ttype is Keyword and token.value.upper() == "ORDER":
            # next token should be BY
            i += 1
            if i < len(tokens):
                nxt = tokens[i]
                if nxt.ttype is Keyword and nxt.value.upper() == "BY":
                    i += 1
                    # parse the next token as columns
                    if i < len(tokens):
                        order_by = parse_order_by(tokens[i])
                        i += 1
                        continue
            else:
                i += 1
                continue

        # handle GROUP BY
        if token.ttype is Keyword and token.value.upper() == "GROUP":
            # next token should be BY
            i += 1
            if i < len(tokens):
                nxt = tokens[i]
                if nxt.ttype is Keyword and nxt.value.upper() == "BY":
                    i += 1
                    # parse group by columns
                    if i < len(tokens):
                        group_by = parse_group_by(tokens[i])
                        i += 1
                        continue
            else:
                i += 1
                continue

        # handle LIMIT
        if token.ttype is Keyword and token.value.upper() == "LIMIT":
            # next token might be the limit number
            if i + 1 < len(tokens):
                limit_val = parse_limit_value(tokens[i + 1])
                i += 2
                continue

        i += 1

    return columns, table_name, where_clause, order_by, group_by, limit_val


def extract_columns(token):
    """
    If token is an IdentifierList => multiple columns
    If token is an Identifier => single column
    If token is '*' => wildcard

    Return a list of columns.
    If no columns found, return an empty list.

    :param token: The SQL token to extract columns from.
    :return: A list of columns.
    """
    from sqlparse.sql import IdentifierList, Identifier
    if isinstance(token, IdentifierList):
        return [str(ident).strip() for ident in token.get_identifiers()]
    elif isinstance(token, Identifier):
        return [str(token).strip()]
    else:
        raw = str(token).strip()
        raw = raw.replace(" ", "")
        if not raw:
            return []
        return [raw]


def extract_where_clause(where_token):
    """
    If where_token is a Where object => parse out 'WHERE' prefix, then parse conditions
    If where_token is a simple 'WHERE' keyword => parse conditions directly

    Return a dict of conditions.

    :param where_token: The SQL token to extract the WHERE clause from.
    :return: A dict of conditions.
    """
    raw = str(where_token).strip()
    if raw.upper().startswith("WHERE"):
        raw = raw[5:].strip()
    return parse_where_conditions(raw)


def parse_where_conditions(text: str):
    """
    e.g. "age > 30 AND name = 'Alice'"
    => { "age":{"$gt":30}, "name":"Alice" }
    We'll strip trailing semicolon as well.

    Supports:
        - direct equality: {field: value}
        - inequality: {field: {"$gt": value}}
        - other operators: {field: {"$op?": value}}

    :param text: The WHERE clause text.
    :return: A dict of conditions.
    """
    text = text.strip().rstrip(";")
    if not text:
        return {}

    # naive split on " AND "
    parts = text.split(" AND ")
    out = {}
    for part in parts:
        tokens = part.split(None, 2)  # e.g. ["age", ">", "30"]
        if len(tokens) < 3:
            continue
        field, op, val = tokens[0], tokens[1], tokens[2]
        val = val.strip().rstrip(";").strip("'").strip('"')
        if op == "=":
            out[field] = val
        elif op == ">":
            out[field] = {"$gt": convert_value(val)}
        elif op == "<":
            out[field] = {"$lt": convert_value(val)}
        elif op == ">=":
            out[field] = {"$gte": convert_value(val)}
        elif op == "<=":
            out[field] = {"$lte": convert_value(val)}
        else:
            out[field] = {"$op?": val}
    return out


def parse_order_by(token):
    """
    e.g. "age ASC, name DESC"
    Return [("age",1), ("name",-1)]

    :param token: The SQL token to extract the ORDER BY clause from.
    :return: A list of tuples (field, direction).
    """
    raw = str(token).strip().rstrip(";")
    if not raw:
        return []
    # might be multiple columns
    parts = raw.split(",")
    order_list = []
    for part in parts:
        sub = part.strip().split()
        if len(sub) == 1:
            # e.g. "age"
            order_list.append((sub[0], 1))  # default ASC
        elif len(sub) == 2:
            # e.g. "age ASC" or "name DESC"
            field, direction = sub[0], sub[1].upper()
            if direction == "ASC":
                order_list.append((field, 1))
            elif direction == "DESC":
                order_list.append((field, -1))
            else:
                order_list.append((field, 1))  # fallback
        else:
            # fallback
            order_list.append((part.strip(), 1))
    return order_list


def parse_group_by(token):
    """
    e.g. "department, role"
    => ["department", "role"]

    :param token: The SQL token to extract the GROUP BY clause from.
    :return: A list of columns.
    """
    raw = str(token).strip().rstrip(";")
    if not raw:
        return []
    return [x.strip() for x in raw.split(",")]


def parse_limit_value(token):
    """
    e.g. "100"
    => 100 (int)

    :param token: The SQL token to extract the LIMIT value from.
    :return: The LIMIT value as an integer, or None if not a valid integer.
    """
    raw = str(token).strip().rstrip(";")
    try:
        return int(raw)
    except ValueError:
        return None


def convert_value(val: str):
    """
    Convert a value to an int, float, or string.

    :param val: The value to convert.
    :return: The value as an int, float, or string.
    """
    try:
        return int(val)
    except ValueError:
        try:
            return float(val)
        except ValueError:
            return val


def build_mongo_find(table_name, where_clause, columns):
    """
    Build a MongoDB find query.

    :param table_name: The name of the collection.
    :param where_clause: The WHERE clause as a dict.
    :param columns: The list of columns to select.
    :return: A dict representing the MongoDB find query.
    """
    filter_query = where_clause or {}
    projection = {}
    if columns and "*" not in columns:
        for col in columns:
            projection[col] = 1
    return {
        "collection": table_name,
        "find": filter_query,
        "projection": projection if projection else None
    }


def build_mongo_query(table_name, columns, where_clause, order_by, group_by, limit_val):
    """
    Build a MongoDB query object from parsed SQL components.

    We'll store everything in a single dict:
      {
        "collection": table_name,
        "find": {...},
        "projection": {...},
        "sort": [("col",1),("col2",-1)],
        "limit": int or None,
        "group": {...}
      }

    :param table_name: The name of the collection.
    :param columns: The list of columns to select.
    """
    query_obj = build_mongo_find(table_name, where_clause, columns)

    # Add sort
    if order_by:
        query_obj["sort"] = order_by

    # Add limit
    if limit_val is not None:
        query_obj["limit"] = limit_val

    # If group_by is used:
    if group_by:
        # e.g. group_by = ["department","role"]
        # We'll store a $group pipeline
        # Real logic depends on what columns are selected
        group_pipeline = {
            "$group": {
                "_id": {},
                "count": {"$sum": 1}
            }
        }
        # e.g. _id => { department: "$department", role: "$role" }
        _id_obj = {}
        for gb in group_by:
            _id_obj[gb] = f"${gb}"
        group_pipeline["$group"]["_id"] = _id_obj
        query_obj["group"] = group_pipeline
    return query_obj
