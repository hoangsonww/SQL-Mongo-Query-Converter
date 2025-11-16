import sqlparse
from sqlparse.sql import (
    IdentifierList,
    Identifier,
    Where,
    Token,
    Parenthesis,
    Function,
)
from sqlparse.tokens import Keyword, DML
import re


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
    columns, table_name, where_clause, order_by, group_by, limit_val, distinct, having_clause = parse_select_statement(statement)

    return build_mongo_query(
        table_name, columns, where_clause, order_by, group_by, limit_val, distinct, having_clause
    )


def parse_select_statement(statement):
    """
    Parse:
      SELECT [DISTINCT] <columns> FROM <table>
      [WHERE ...]
      [GROUP BY ...]
      [HAVING ...]
      [ORDER BY ...]
      [LIMIT ...]
    in that approximate order.

    Returns:
      columns, table_name, where_clause_dict, order_by_list, group_by_list, limit_val, distinct, having_clause

    :param statement: The parsed SQL statement.
    :return: A tuple containing columns, table_name, where_clause_dict, order_by_list, group_by_list, limit_val, distinct, having_clause
    """
    columns = []
    table_name = None
    where_clause = {}
    order_by = []  # e.g. [("age", 1), ("name", -1)]
    group_by = []  # e.g. ["department", "role"]
    limit_val = None
    distinct = False
    having_clause = {}

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

        # detect DISTINCT after SELECT
        if found_select and reading_columns and token.ttype is Keyword and token.value.upper() == "DISTINCT":
            distinct = True
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

        # handle HAVING
        if token.ttype is Keyword and token.value.upper() == "HAVING":
            if i + 1 < len(tokens):
                i += 1
                having_text = str(tokens[i]).strip()
                having_clause = parse_where_conditions(having_text)
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

    return columns, table_name, where_clause, order_by, group_by, limit_val, distinct, having_clause


def extract_columns(token):
    """
    If token is an IdentifierList => multiple columns
    If token is an Identifier => single column
    If token is '*' => wildcard
    Also handles aggregate functions like COUNT, SUM, AVG, etc.

    Return a list of columns or aggregate expressions.
    If no columns found, return an empty list.

    :param token: The SQL token to extract columns from.
    :return: A list of columns or aggregate expressions.
    """
    from sqlparse.sql import IdentifierList, Identifier, Function
    if isinstance(token, IdentifierList):
        cols = []
        for ident in token.get_identifiers():
            cols.append(str(ident).strip())
        return cols
    elif isinstance(token, Identifier):
        return [str(token).strip()]
    elif isinstance(token, Function):
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
    Enhanced WHERE clause parser supporting:
    - AND, OR operators
    - Comparison: =, >, <, >=, <=, !=, <>
    - BETWEEN: field BETWEEN val1 AND val2
    - LIKE: field LIKE '%pattern%'
    - IN: field IN (val1, val2, val3)
    - IS NULL / IS NOT NULL
    - NOT operator

    :param text: The WHERE clause text.
    :return: A dict of MongoDB conditions.
    """
    text = text.strip().rstrip(";")
    if not text:
        return {}

    # Check for OR conditions first (lower precedence than AND)
    if " OR " in text.upper():
        # Split by OR
        or_parts = re.split(r'\s+OR\s+', text, flags=re.IGNORECASE)
        conditions = []
        for part in or_parts:
            cond = parse_where_conditions(part.strip())
            if cond:
                conditions.append(cond)
        if len(conditions) > 1:
            return {"$or": conditions}
        elif len(conditions) == 1:
            return conditions[0]
        return {}

    # Check for AND conditions (but not within BETWEEN clauses)
    if " AND " in text.upper() and " BETWEEN " not in text.upper():
        and_parts = re.split(r'\s+AND\s+', text, flags=re.IGNORECASE)
        out = {}
        for part in and_parts:
            cond = parse_single_condition(part.strip())
            if cond:
                out.update(cond)
        return out
    elif " AND " in text.upper() and " BETWEEN " in text.upper():
        # Complex case: has both AND and BETWEEN
        # Need to split smarter - don't split AND that's part of BETWEEN
        parts = []
        current = ""
        in_between = False
        words = text.split()
        i = 0
        while i < len(words):
            word = words[i]
            if word.upper() == "BETWEEN":
                in_between = True
                current += " " + word
            elif word.upper() == "AND" and in_between:
                # This AND is part of BETWEEN
                current += " " + word
                in_between = False
            elif word.upper() == "AND" and not in_between:
                # This AND separates conditions
                if current.strip():
                    parts.append(current.strip())
                current = ""
            else:
                current += " " + word
            i += 1
        if current.strip():
            parts.append(current.strip())

        out = {}
        for part in parts:
            cond = parse_single_condition(part.strip())
            if cond:
                out.update(cond)
        return out

    # Single condition
    return parse_single_condition(text)


def parse_single_condition(text: str):
    """
    Parse a single WHERE condition.

    Supports:
    - field = value
    - field > value (and <, >=, <=, !=, <>)
    - field BETWEEN val1 AND val2
    - field LIKE '%pattern%'
    - field IN (val1, val2, val3)
    - field IS NULL / IS NOT NULL
    - NOT field = value

    :param text: A single condition string.
    :return: A dict representing the MongoDB condition.
    """
    text = text.strip()

    # Handle NOT
    if text.upper().startswith('NOT '):
        # Remove NOT and negate the condition
        inner_cond = parse_single_condition(text[4:].strip())
        # Convert to $not
        if inner_cond:
            field = list(inner_cond.keys())[0]
            value = inner_cond[field]
            return {field: {"$not": value} if isinstance(value, dict) else {"$ne": value}}
        return {}

    # Handle IS NULL / IS NOT NULL
    if ' IS NULL' in text.upper():
        field = text[:text.upper().index(' IS NULL')].strip()
        return {field: None}
    if ' IS NOT NULL' in text.upper():
        field = text[:text.upper().index(' IS NOT NULL')].strip()
        return {field: {"$ne": None}}

    # Handle BETWEEN
    if ' BETWEEN ' in text.upper():
        parts = re.split(r'\s+BETWEEN\s+', text, maxsplit=1, flags=re.IGNORECASE)
        if len(parts) == 2:
            field = parts[0].strip()
            range_part = parts[1].strip()
            # Extract val1 AND val2
            if ' AND ' in range_part.upper():
                range_vals = re.split(r'\s+AND\s+', range_part, maxsplit=1, flags=re.IGNORECASE)
                if len(range_vals) == 2:
                    val1 = convert_value(range_vals[0].strip().strip("'").strip('"'))
                    val2 = convert_value(range_vals[1].strip().strip("'").strip('"'))
                    return {field: {"$gte": val1, "$lte": val2}}
        return {}

    # Handle LIKE
    if ' LIKE ' in text.upper():
        parts = re.split(r'\s+LIKE\s+', text, maxsplit=1, flags=re.IGNORECASE)
        if len(parts) == 2:
            field = parts[0].strip()
            pattern = parts[1].strip().strip("'").strip('"')
            # Convert SQL wildcards (%) to regex
            regex_pattern = pattern.replace('%', '.*').replace('_', '.')
            # Add anchors if pattern doesn't have wildcards at start/end
            if not pattern.startswith('%'):
                regex_pattern = '^' + regex_pattern
            if not pattern.endswith('%'):
                regex_pattern = regex_pattern + '$'
            return {field: {"$regex": regex_pattern, "$options": "i"}}
        return {}

    # Handle NOT IN (before IN to avoid incorrect parsing)
    if ' NOT IN ' in text.upper():
        parts = re.split(r'\s+NOT\s+IN\s+', text, maxsplit=1, flags=re.IGNORECASE)
        if len(parts) == 2:
            field = parts[0].strip()
            values_str = parts[1].strip()
            # Remove parentheses
            if values_str.startswith('(') and values_str.endswith(')'):
                values_str = values_str[1:-1]
            # Parse comma-separated values
            values = []
            for val in re.split(r',\s*', values_str):
                val = val.strip().strip("'").strip('"')
                values.append(convert_value(val))
            return {field: {"$nin": values}}
        return {}

    # Handle IN
    if ' IN ' in text.upper():
        parts = re.split(r'\s+IN\s+', text, maxsplit=1, flags=re.IGNORECASE)
        if len(parts) == 2:
            field = parts[0].strip()
            values_str = parts[1].strip()
            # Remove parentheses
            if values_str.startswith('(') and values_str.endswith(')'):
                values_str = values_str[1:-1]
            # Parse comma-separated values
            values = []
            for val in re.split(r',\s*', values_str):
                val = val.strip().strip("'").strip('"')
                values.append(convert_value(val))
            return {field: {"$in": values}}
        return {}

    # Handle standard operators (=, >, <, >=, <=, !=, <>)
    operators = ['>=', '<=', '!=', '<>', '=', '>', '<']
    for op in operators:
        if f' {op} ' in text:
            parts = text.split(f' {op} ', 1)
            if len(parts) == 2:
                field = parts[0].strip()
                val = parts[1].strip().strip("'").strip('"')

                if op == "=":
                    return {field: convert_value(val)}
                elif op == ">":
                    return {field: {"$gt": convert_value(val)}}
                elif op == "<":
                    return {field: {"$lt": convert_value(val)}}
                elif op == ">=":
                    return {field: {"$gte": convert_value(val)}}
                elif op == "<=":
                    return {field: {"$lte": convert_value(val)}}
                elif op in ["!=", "<>"]:
                    return {field: {"$ne": convert_value(val)}}

    return {}


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


def build_mongo_query(table_name, columns, where_clause, order_by, group_by, limit_val, distinct=False, having_clause=None):
    """
    Build a MongoDB query object from parsed SQL components.

    We'll store everything in a single dict:
      {
        "collection": table_name,
        "find": {...},
        "projection": {...},
        "sort": [("col",1),("col2",-1)],
        "limit": int or None,
        "group": {...},
        "distinct": bool,
        "having": {...}
      }

    :param table_name: The name of the collection.
    :param columns: The list of columns to select.
    :param distinct: Whether to return distinct values.
    :param having_clause: HAVING clause conditions.
    """
    query_obj = build_mongo_find(table_name, where_clause, columns)

    # Add DISTINCT
    if distinct:
        # For DISTINCT, we use MongoDB's distinct() or aggregation pipeline
        if columns and len(columns) == 1 and '*' not in columns:
            # Single field DISTINCT
            query_obj["operation"] = "distinct"
            query_obj["field"] = columns[0]
        else:
            # Multiple fields DISTINCT - use aggregation pipeline
            query_obj["operation"] = "aggregate"
            pipeline = []
            if where_clause:
                pipeline.append({"$match": where_clause})
            if columns and '*' not in columns:
                project = {col: 1 for col in columns}
                pipeline.append({"$project": project})
            pipeline.append({"$group": {"_id": {col: f"${col}" for col in (columns if columns and '*' not in columns else [])}}})
            query_obj["pipeline"] = pipeline
            return query_obj

    # Add sort
    if order_by:
        query_obj["sort"] = order_by

    # Add limit
    if limit_val is not None:
        query_obj["limit"] = limit_val

    # If group_by is used - build aggregation pipeline
    if group_by or having_clause:
        query_obj["operation"] = "aggregate"
        pipeline = []

        # $match stage for WHERE
        if where_clause:
            pipeline.append({"$match": where_clause})

        # $group stage
        if group_by:
            group_stage = {"$group": {"_id": {}}}

            # Build _id for grouping
            if isinstance(group_by, list):
                if len(group_by) == 1:
                    group_stage["$group"]["_id"] = f"${group_by[0]}"
                else:
                    _id_obj = {}
                    for gb in group_by:
                        _id_obj[gb] = f"${gb}"
                    group_stage["$group"]["_id"] = _id_obj

            # Parse columns for aggregation functions
            for col in (columns if columns else []):
                agg_func, field = parse_aggregation_function(col)
                if agg_func:
                    # It's an aggregation function
                    if agg_func.upper() == "COUNT":
                        group_stage["$group"]["count"] = {"$sum": 1}
                    elif agg_func.upper() == "SUM":
                        group_stage["$group"][f"sum_{field}"] = {"$sum": f"${field}"}
                    elif agg_func.upper() == "AVG":
                        group_stage["$group"][f"avg_{field}"] = {"$avg": f"${field}"}
                    elif agg_func.upper() == "MIN":
                        group_stage["$group"][f"min_{field}"] = {"$min": f"${field}"}
                    elif agg_func.upper() == "MAX":
                        group_stage["$group"][f"max_{field}"] = {"$max": f"${field}"}

            # If no aggregation functions found, add count
            if len(group_stage["$group"]) == 1:
                group_stage["$group"]["count"] = {"$sum": 1}

            pipeline.append(group_stage)

        # $match stage for HAVING
        if having_clause:
            pipeline.append({"$match": having_clause})

        # $sort stage
        if order_by:
            sort_dict = {field: direction for field, direction in order_by}
            pipeline.append({"$sort": sort_dict})

        # $limit stage
        if limit_val:
            pipeline.append({"$limit": limit_val})

        query_obj["pipeline"] = pipeline

    return query_obj


def parse_aggregation_function(col_expr):
    """
    Parse aggregation functions like COUNT(*), SUM(price), AVG(age), etc.

    Returns: (function_name, field_name) or (None, None) if not an aggregation
    """
    col_expr = col_expr.strip()

    # Check for common aggregation functions
    agg_funcs = ['COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'GROUP_CONCAT']

    for func in agg_funcs:
        if col_expr.upper().startswith(func + '('):
            # Extract field name from function
            start = col_expr.index('(') + 1
            end = col_expr.rindex(')')
            field = col_expr[start:end].strip()

            # Handle COUNT(*) specially
            if func == 'COUNT' and field == '*':
                return (func, '*')

            return (func, field)

    return (None, None)


def sql_insert_to_mongo(sql_query: str):
    """
    Convert INSERT INTO ... VALUES ... to MongoDB insertOne/insertMany format.

    Examples:
      INSERT INTO users (name, age) VALUES ('Alice', 30)
      => {"collection": "users", "operation": "insertOne", "document": {"name": "Alice", "age": 30}}

      INSERT INTO users VALUES ('Bob', 25)
      => {"collection": "users", "operation": "insertOne", "document": {"col0": "Bob", "col1": 25}}

    :param sql_query: The SQL INSERT query as a string.
    :return: A MongoDB insert dict.
    """
    parsed = sqlparse.parse(sql_query)
    if not parsed:
        return {}

    statement = parsed[0]
    table_name, columns, values = parse_insert_statement(statement)

    if not table_name or not values:
        return {}

    # Build document(s)
    documents = []
    for value_set in values:
        doc = {}
        if columns:
            # Match columns with values
            for i, col in enumerate(columns):
                if i < len(value_set):
                    doc[col] = value_set[i]
        else:
            # No columns specified, use generic names
            for i, val in enumerate(value_set):
                doc[f"col{i}"] = val
        documents.append(doc)

    # Return format
    result = {
        "collection": table_name,
        "operation": "insertMany" if len(documents) > 1 else "insertOne",
    }

    if len(documents) == 1:
        result["document"] = documents[0]
    else:
        result["documents"] = documents

    return result


def parse_insert_statement(statement):
    """
    Parse INSERT INTO table (columns) VALUES (values) [, (values)]

    Returns:
      table_name, columns_list, values_list_of_lists

    :param statement: The parsed SQL statement.
    :return: A tuple containing table_name, columns, values.
    """
    table_name = None
    columns = []
    values = []

    tokens = [t for t in statement.tokens if not t.is_whitespace]

    i = 0
    found_insert = False
    reading_into = False

    while i < len(tokens):
        token = tokens[i]

        # Detect INSERT
        if token.ttype is DML and token.value.upper() == "INSERT":
            found_insert = True
            i += 1
            continue

        # Detect INTO
        if found_insert and token.ttype is Keyword and token.value.upper() == "INTO":
            reading_into = True
            i += 1
            continue

        # Parse table name and possibly columns after INTO
        if reading_into and not table_name:
            if token.ttype is not Keyword:
                # Check if it's a Function (sqlparse treats "table(cols)" as Function)
                if isinstance(token, Function):
                    # Extract table name and columns from Function
                    func_str = str(token)
                    if '(' in func_str:
                        table_name = func_str.split('(')[0].strip()
                        # Parse columns from the parenthesis part
                        cols_part = func_str[func_str.index('(')+1:func_str.rindex(')')]
                        columns = [c.strip().strip('"').strip("'") for c in cols_part.split(',')]
                    else:
                        table_name = func_str.strip()
                elif isinstance(token, Identifier):
                    table_name = str(token.get_real_name()).strip()
                elif isinstance(token, Parenthesis):
                    # This is the columns list without table
                    columns = parse_columns_list(token)
                else:
                    # Simple table name
                    table_name = str(token).strip()
                reading_into = False
            i += 1
            continue

        # Handle standalone parenthesis for columns
        if table_name and isinstance(token, Parenthesis) and not columns:
            # Check if this is before VALUES - it's columns
            if i + 1 < len(tokens):
                next_tok = tokens[i + 1]
                if next_tok.ttype is Keyword and next_tok.value.upper() == "VALUES":
                    columns = parse_columns_list(token)
            i += 1
            continue

        # Detect VALUES - could be keyword or Values object
        if (token.ttype is Keyword and token.value.upper() == "VALUES") or \
           (hasattr(token, '__class__') and token.__class__.__name__ == 'Values'):
            # If it's a Values object, parse it directly
            if token.__class__.__name__ == 'Values':
                # Extract value sets from Values object
                values_str = str(token)
                # Remove 'VALUES ' prefix if present
                if values_str.upper().startswith('VALUES'):
                    values_str = values_str[6:].strip()
                # Parse all parenthesis groups
                import re
                # Find all (...) groups
                paren_groups = re.findall(r'\([^)]+\)', values_str)
                for group in paren_groups:
                    # Create a Parenthesis-like string and parse
                    value_set = parse_values_from_string(group)
                    if value_set:
                        values.append(value_set)
            i += 1
            continue

        # Parse individual value parentheses
        if isinstance(token, Parenthesis) and table_name:
            value_set = parse_values_list(token)
            if value_set:
                values.append(value_set)
            i += 1
            continue

        i += 1

    return table_name, columns, values


def parse_values_from_string(paren_str: str):
    """
    Parse values from a parenthesis string like '(val1, val2)'.

    :param paren_str: String with parentheses.
    :return: List of values.
    """
    content = paren_str.strip()
    if content.startswith('(') and content.endswith(')'):
        content = content[1:-1]

    values = []
    parts = re.split(r",(?=(?:[^'\"]*['\"][^'\"]*['\"])*[^'\"]*$)", content)
    for part in parts:
        part = part.strip()
        if (part.startswith("'") and part.endswith("'")) or (part.startswith('"') and part.endswith('"')):
            values.append(part[1:-1])
        else:
            values.append(convert_value(part))

    return values


def parse_columns_list(parenthesis_token):
    """
    Parse (col1, col2, col3) into a list of column names.

    :param parenthesis_token: The parenthesis token containing columns.
    :return: A list of column names.
    """
    content = str(parenthesis_token).strip()
    # Remove outer parentheses
    if content.startswith('(') and content.endswith(')'):
        content = content[1:-1]

    # Split by comma
    cols = [c.strip().strip('"').strip("'") for c in content.split(',')]
    return cols


def parse_values_list(parenthesis_token):
    """
    Parse (val1, val2, val3) into a list of values.

    :param parenthesis_token: The parenthesis token containing values.
    :return: A list of values.
    """
    content = str(parenthesis_token).strip()
    # Remove outer parentheses
    if content.startswith('(') and content.endswith(')'):
        content = content[1:-1]

    # Parse values - handle strings in quotes
    values = []
    # Use regex to split by comma but respect quotes
    parts = re.split(r",(?=(?:[^'\"]*['\"][^'\"]*['\"])*[^'\"]*$)", content)
    for part in parts:
        part = part.strip()
        # Remove quotes if present
        if (part.startswith("'") and part.endswith("'")) or (part.startswith('"') and part.endswith('"')):
            values.append(part[1:-1])
        else:
            # Try to convert to number
            values.append(convert_value(part))

    return values


def sql_update_to_mongo(sql_query: str):
    """
    Convert UPDATE ... SET ... WHERE ... to MongoDB updateOne/updateMany format.

    Example:
      UPDATE users SET age = 31, status = 'active' WHERE name = 'Alice'
      => {
           "collection": "users",
           "operation": "updateMany",
           "filter": {"name": "Alice"},
           "update": {"$set": {"age": 31, "status": "active"}}
         }

    :param sql_query: The SQL UPDATE query as a string.
    :return: A MongoDB update dict.
    """
    parsed = sqlparse.parse(sql_query)
    if not parsed:
        return {}

    statement = parsed[0]
    table_name, set_clause, where_clause = parse_update_statement(statement)

    if not table_name or not set_clause:
        return {}

    result = {
        "collection": table_name,
        "operation": "updateMany",
        "filter": where_clause or {},
        "update": {"$set": set_clause}
    }

    return result


def parse_update_statement(statement):
    """
    Parse UPDATE table SET col1=val1, col2=val2 WHERE conditions

    Returns:
      table_name, set_dict, where_dict

    :param statement: The parsed SQL statement.
    :return: A tuple containing table_name, set_clause, where_clause.
    """
    table_name = None
    set_clause = {}
    where_clause = {}

    tokens = [t for t in statement.tokens if not t.is_whitespace]

    i = 0
    found_update = False
    reading_set = False

    while i < len(tokens):
        token = tokens[i]

        # Detect UPDATE
        if token.ttype is DML and token.value.upper() == "UPDATE":
            found_update = True
            i += 1
            continue

        # Parse table name after UPDATE
        if found_update and not table_name:
            if token.ttype is not Keyword:
                if isinstance(token, Identifier):
                    table_name = str(token.get_real_name()).strip()
                else:
                    table_name = str(token).strip()
            i += 1
            continue

        # Detect SET
        if token.ttype is Keyword and token.value.upper() == "SET":
            reading_set = True
            i += 1
            continue

        # Parse SET clause
        if reading_set and not isinstance(token, Where) and token.ttype is not Keyword:
            set_clause = parse_set_clause(str(token))
            reading_set = False
            i += 1
            continue

        # Parse WHERE
        if isinstance(token, Where):
            where_clause = extract_where_clause(token)
            i += 1
            continue

        if token.ttype is Keyword and token.value.upper() == "WHERE":
            if i + 1 < len(tokens):
                next_token = tokens[i + 1]
                if isinstance(next_token, Where):
                    where_clause = extract_where_clause(next_token)
                    i += 2
                    continue
                else:
                    where_text = str(next_token).strip()
                    where_clause = parse_where_conditions(where_text)
                    i += 2
                    continue
            i += 1
            continue

        i += 1

    return table_name, set_clause, where_clause


def parse_set_clause(text: str):
    """
    Parse "col1 = val1, col2 = val2" into a dict.

    :param text: The SET clause text.
    :return: A dict of column-value pairs.
    """
    text = text.strip().rstrip(";")
    if not text:
        return {}

    # Split by comma
    parts = re.split(r",(?=(?:[^'\"]*['\"][^'\"]*['\"])*[^'\"]*$)", text)
    result = {}

    for part in parts:
        part = part.strip()
        if '=' in part:
            field, val = part.split('=', 1)
            field = field.strip()
            val = val.strip().strip("'").strip('"')
            result[field] = convert_value(val)

    return result


def sql_delete_to_mongo(sql_query: str):
    """
    Convert DELETE FROM ... WHERE ... to MongoDB deleteMany format.

    Example:
      DELETE FROM users WHERE age < 18
      => {
           "collection": "users",
           "operation": "deleteMany",
           "filter": {"age": {"$lt": 18}}
         }

    :param sql_query: The SQL DELETE query as a string.
    :return: A MongoDB delete dict.
    """
    parsed = sqlparse.parse(sql_query)
    if not parsed:
        return {}

    statement = parsed[0]
    table_name, where_clause = parse_delete_statement(statement)

    if not table_name:
        return {}

    result = {
        "collection": table_name,
        "operation": "deleteMany",
        "filter": where_clause or {}
    }

    return result


def parse_delete_statement(statement):
    """
    Parse DELETE FROM table WHERE conditions

    Returns:
      table_name, where_dict

    :param statement: The parsed SQL statement.
    :return: A tuple containing table_name and where_clause.
    """
    table_name = None
    where_clause = {}

    tokens = [t for t in statement.tokens if not t.is_whitespace]

    i = 0
    found_delete = False
    reading_from = False

    while i < len(tokens):
        token = tokens[i]

        # Detect DELETE
        if token.ttype is DML and token.value.upper() == "DELETE":
            found_delete = True
            i += 1
            continue

        # Detect FROM
        if found_delete and token.ttype is Keyword and token.value.upper() == "FROM":
            reading_from = True
            i += 1
            continue

        # Parse table name after FROM
        if reading_from and not table_name:
            if token.ttype is not Keyword:
                if isinstance(token, Identifier):
                    table_name = str(token.get_real_name()).strip()
                else:
                    table_name = str(token).strip()
                reading_from = False
            i += 1
            continue

        # Parse WHERE
        if isinstance(token, Where):
            where_clause = extract_where_clause(token)
            i += 1
            continue

        if token.ttype is Keyword and token.value.upper() == "WHERE":
            if i + 1 < len(tokens):
                next_token = tokens[i + 1]
                if isinstance(next_token, Where):
                    where_clause = extract_where_clause(next_token)
                    i += 2
                    continue
                else:
                    where_text = str(next_token).strip()
                    where_clause = parse_where_conditions(where_text)
                    i += 2
                    continue
            i += 1
            continue

        i += 1

    return table_name, where_clause


def sql_join_to_mongo(sql_query: str):
    """
    Convert SQL JOIN queries to MongoDB $lookup aggregation pipeline.

    Example:
      SELECT u.name, o.total FROM users u INNER JOIN orders o ON u.id = o.user_id
      => {
           "collection": "users",
           "operation": "aggregate",
           "pipeline": [
             {
               "$lookup": {
                 "from": "orders",
                 "localField": "id",
                 "foreignField": "user_id",
                 "as": "joined_orders"
               }
             },
             {"$project": {"name": 1, "joined_orders.total": 1}}
           ]
         }

    :param sql_query: The SQL JOIN query as a string.
    :return: A MongoDB aggregation pipeline dict.
    """
    parsed = sqlparse.parse(sql_query)
    if not parsed:
        return {}

    statement = parsed[0]
    result = parse_join_statement(statement)
    return result


def parse_join_statement(statement):
    """
    Parse SQL JOIN statement.

    Returns:
      MongoDB aggregation pipeline with $lookup

    :param statement: The parsed SQL statement.
    :return: A dict representing the MongoDB aggregation pipeline.
    """
    from sqlparse.sql import Comparison

    tokens = [t for t in statement.tokens if not t.is_whitespace]

    main_table = None
    join_table = None
    join_type = "INNER"
    local_field = None
    foreign_field = None
    columns = []

    # Simpler approach using enumeration
    for i, token in enumerate(tokens):
        # Detect SELECT and parse columns
        if token.ttype is DML and token.value.upper() == "SELECT":
            # Next non-keyword token is columns
            if i + 1 < len(tokens) and tokens[i+1].ttype is not Keyword:
                possible_cols = extract_columns(tokens[i+1])
                if possible_cols:
                    columns = possible_cols

        # Get main table after FROM
        if i > 0 and tokens[i-1].ttype is Keyword and tokens[i-1].value.upper() == "FROM":
            if isinstance(token, Identifier):
                table_str = str(token).strip()
                main_table = table_str.split()[0]
            else:
                table_str = str(token).strip()
                main_table = table_str.split()[0]

        # Detect JOIN and get join table
        if token.ttype is Keyword and 'JOIN' in token.value.upper():
            join_type = token.value.upper().replace(' ', '')
            # Next token should be the table name
            if i + 1 < len(tokens) and isinstance(tokens[i+1], Identifier):
                table_str = str(tokens[i+1]).strip()
                join_table = table_str.split()[0]

        # Handle Comparison objects for ON clause
        if isinstance(token, Comparison):
            on_condition = str(token).strip()
            if '=' in on_condition:
                left, right = on_condition.split('=', 1)
                left = left.strip()
                right = right.strip()

                # Remove table aliases (e.g., "u.id" -> "id")
                local_field = left.split('.', 1)[1] if '.' in left else left
                foreign_field = right.split('.', 1)[1] if '.' in right else right

    # Build MongoDB $lookup pipeline
    if not main_table or not join_table:
        return {}

    pipeline = []

    # Add $lookup stage
    lookup_stage = {
        "$lookup": {
            "from": join_table,
            "localField": local_field or "_id",
            "foreignField": foreign_field or "_id",
            "as": f"joined_{join_table}"
        }
    }
    pipeline.append(lookup_stage)

    # For LEFT JOIN, add $unwind with preserveNullAndEmptyArrays
    if 'LEFT' in join_type:
        pipeline.append({
            "$unwind": {
                "path": f"$joined_{join_table}",
                "preserveNullAndEmptyArrays": True
            }
        })
    else:
        pipeline.append({
            "$unwind": f"$joined_{join_table}"
        })

    # Add projection if columns specified
    if columns and '*' not in columns:
        project = {}
        for col in columns:
            # Handle aliased columns (e.g., "u.name")
            if '.' in col:
                table_alias, field = col.split('.', 1)
                project[field] = 1
            else:
                project[col] = 1
        pipeline.append({"$project": project})

    return {
        "collection": main_table,
        "operation": "aggregate",
        "pipeline": pipeline
    }


def sql_create_table_to_mongo(sql_query: str):
    """
    Convert CREATE TABLE to MongoDB createCollection command.

    Example:
      CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100), age INT)
      => {
           "operation": "createCollection",
           "collection": "users",
           "schema": {
             "id": "INT",
             "name": "VARCHAR(100)",
             "age": "INT"
           },
           "validator": {
             "$jsonSchema": {
               "bsonType": "object",
               "required": ["id"],
               "properties": {
                 "id": {"bsonType": "int"},
                 "name": {"bsonType": "string"},
                 "age": {"bsonType": "int"}
               }
             }
           }
         }

    :param sql_query: The SQL CREATE TABLE query as a string.
    :return: A MongoDB createCollection command dict.
    """
    parsed = sqlparse.parse(sql_query)
    if not parsed:
        return {}

    statement = parsed[0]
    table_name, columns_def = parse_create_table_statement(statement)

    if not table_name:
        return {}

    # Build MongoDB schema validator
    properties = {}
    required = []

    for col_name, col_type, constraints in columns_def:
        # Map SQL types to BSON types
        bson_type = map_sql_type_to_bson(col_type)
        properties[col_name] = {"bsonType": bson_type}

        # Check for PRIMARY KEY or NOT NULL
        if 'PRIMARY KEY' in constraints.upper() or 'NOT NULL' in constraints.upper():
            required.append(col_name)

    result = {
        "operation": "createCollection",
        "collection": table_name,
        "schema": {col[0]: col[1] for col in columns_def}
    }

    if properties:
        result["validator"] = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": required if required else [],
                "properties": properties
            }
        }

    return result


def parse_create_table_statement(statement):
    """
    Parse CREATE TABLE statement.

    Returns:
      table_name, columns_definition

    :param statement: The parsed SQL statement.
    :return: A tuple containing table_name and columns definition.
    """
    table_name = None
    columns_def = []

    tokens = [t for t in statement.tokens if not t.is_whitespace]

    i = 0
    while i < len(tokens):
        token = tokens[i]

        # Find TABLE keyword
        if token.ttype is Keyword and token.value.upper() == "TABLE":
            # Next token should be table name
            if i + 1 < len(tokens):
                i += 1
                next_token = tokens[i]
                if isinstance(next_token, Identifier):
                    table_name = str(next_token.get_real_name()).strip()
                else:
                    table_name = str(next_token).strip()
            i += 1
            continue

        # Find column definitions in parentheses
        if isinstance(token, Parenthesis):
            columns_def = parse_column_definitions(str(token))
            i += 1
            continue

        i += 1

    return table_name, columns_def


def parse_column_definitions(columns_text: str):
    """
    Parse column definitions from CREATE TABLE.

    :param columns_text: The columns definition text.
    :return: A list of tuples (column_name, data_type, constraints).
    """
    # Remove outer parentheses
    if columns_text.startswith('(') and columns_text.endswith(')'):
        columns_text = columns_text[1:-1]

    columns = []
    # Split by comma (simple approach)
    parts = columns_text.split(',')

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # Parse: column_name data_type [constraints]
        tokens = part.split(None, 2)
        if len(tokens) >= 2:
            col_name = tokens[0].strip()
            col_type = tokens[1].strip()
            constraints = tokens[2] if len(tokens) > 2 else ""
            columns.append((col_name, col_type, constraints))

    return columns


def map_sql_type_to_bson(sql_type: str) -> str:
    """
    Map SQL data types to BSON types.

    :param sql_type: The SQL data type.
    :return: The corresponding BSON type.
    """
    sql_type_upper = sql_type.upper()

    if 'INT' in sql_type_upper or 'SERIAL' in sql_type_upper:
        return 'int'
    elif 'BIGINT' in sql_type_upper:
        return 'long'
    elif 'DECIMAL' in sql_type_upper or 'NUMERIC' in sql_type_upper:
        return 'decimal'
    elif 'FLOAT' in sql_type_upper or 'DOUBLE' in sql_type_upper or 'REAL' in sql_type_upper:
        return 'double'
    elif 'BOOL' in sql_type_upper:
        return 'bool'
    elif 'DATE' in sql_type_upper or 'TIME' in sql_type_upper:
        return 'date'
    elif 'CHAR' in sql_type_upper or 'TEXT' in sql_type_upper or 'VARCHAR' in sql_type_upper:
        return 'string'
    elif 'BLOB' in sql_type_upper or 'BINARY' in sql_type_upper:
        return 'binData'
    else:
        return 'string'  # Default


def sql_create_index_to_mongo(sql_query: str):
    """
    Convert CREATE INDEX to MongoDB createIndex command.

    Example:
      CREATE INDEX idx_name ON users (name)
      => {
           "operation": "createIndex",
           "collection": "users",
           "index": {"name": 1},
           "indexName": "idx_name"
         }

    :param sql_query: The SQL CREATE INDEX query as a string.
    :return: A MongoDB createIndex command dict.
    """
    parsed = sqlparse.parse(sql_query)
    if not parsed:
        return {}

    statement = parsed[0]
    index_name, table_name, columns = parse_create_index_statement(statement)

    if not table_name or not columns:
        return {}

    # Build index specification
    index_spec = {}
    for col in columns:
        col = col.strip()
        # Check for DESC
        if col.upper().endswith(' DESC'):
            col = col[:-5].strip()
            index_spec[col] = -1
        elif col.upper().endswith(' ASC'):
            col = col[:-4].strip()
            index_spec[col] = 1
        else:
            index_spec[col] = 1

    result = {
        "operation": "createIndex",
        "collection": table_name,
        "index": index_spec
    }

    if index_name:
        result["indexName"] = index_name

    return result


def parse_create_index_statement(statement):
    """
    Parse CREATE INDEX statement.

    Returns:
      index_name, table_name, columns

    :param statement: The parsed SQL statement.
    :return: A tuple containing index_name, table_name, and columns.
    """
    index_name = None
    table_name = None
    columns = []

    tokens = [t for t in statement.tokens if not t.is_whitespace]

    for i, token in enumerate(tokens):
        # Get index name after INDEX keyword
        if i > 0 and tokens[i-1].ttype is Keyword and tokens[i-1].value.upper() == "INDEX":
            if token.ttype is not Keyword:
                index_name = str(token).strip()

        # Get table and columns after ON keyword
        if i > 0 and tokens[i-1].ttype is Keyword and tokens[i-1].value.upper() == "ON":
            # Could be a Function like "users (name)"
            if isinstance(token, Function):
                func_str = str(token)
                if '(' in func_str:
                    table_name = func_str.split('(')[0].strip()
                    cols_part = func_str[func_str.index('(')+1:func_str.rindex(')')]
                    columns = [c.strip() for c in cols_part.split(',')]
                else:
                    table_name = func_str.strip()
            elif isinstance(token, Identifier):
                table_name = str(token).strip()
            else:
                table_name = str(token).strip()

    return index_name, table_name, columns


def sql_drop_to_mongo(sql_query: str):
    """
    Convert DROP TABLE/INDEX to MongoDB drop commands.

    Examples:
      DROP TABLE users
      => {"operation": "drop", "collection": "users"}

      DROP INDEX idx_name ON users
      => {"operation": "dropIndex", "collection": "users", "index": "idx_name"}

    :param sql_query: The SQL DROP query as a string.
    :return: A MongoDB drop command dict.
    """
    parsed = sqlparse.parse(sql_query)
    if not parsed:
        return {}

    statement = parsed[0]
    query_upper = sql_query.upper().strip()

    if query_upper.startswith('DROP TABLE'):
        # Parse DROP TABLE
        table_name = parse_drop_table(statement)
        if table_name:
            return {
                "operation": "drop",
                "collection": table_name
            }

    elif query_upper.startswith('DROP INDEX'):
        # Parse DROP INDEX
        index_name, table_name = parse_drop_index(statement)
        if index_name and table_name:
            return {
                "operation": "dropIndex",
                "collection": table_name,
                "index": index_name
            }

    return {}


def parse_drop_table(statement):
    """Parse DROP TABLE statement."""
    tokens = [t for t in statement.tokens if not t.is_whitespace]

    for i, token in enumerate(tokens):
        if i > 0 and tokens[i-1].ttype is Keyword and tokens[i-1].value.upper() == "TABLE":
            if isinstance(token, Identifier):
                return str(token.get_real_name()).strip()
            else:
                return str(token).strip()

    return None


def parse_drop_index(statement):
    """Parse DROP INDEX statement. Returns (index_name, table_name)."""
    tokens = [t for t in statement.tokens if not t.is_whitespace]

    index_name = None
    table_name = None

    for i, token in enumerate(tokens):
        # Get index name after INDEX keyword
        if i > 0 and tokens[i-1].ttype is Keyword and tokens[i-1].value.upper() == "INDEX":
            if token.ttype is not Keyword:
                index_name = str(token).strip()

        # Get table name after ON keyword
        if i > 0 and tokens[i-1].ttype is Keyword and tokens[i-1].value.upper() == "ON":
            if token.ttype is not Keyword:
                if isinstance(token, Identifier):
                    table_name = str(token.get_real_name()).strip()
                else:
                    table_name = str(token).strip()

    return index_name, table_name
