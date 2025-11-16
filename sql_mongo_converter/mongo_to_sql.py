def mongo_find_to_sql(mongo_obj: dict) -> str:
    """
    Convert a Mongo find dictionary into an extended SQL SELECT query.

    Example input:
    {
      "collection": "users",
      "find": {
        "$or": [
          {"age": {"$gte": 25}},
          {"status": "ACTIVE"}
        ]
      },
      "projection": {"age": 1, "status": 1},
      "sort": [("age", 1), ("name", -1)],
      "limit": 10,
      "skip": 5
    }

    => Output:
    SELECT age, status FROM users
    WHERE ((age >= 25) OR (status = 'ACTIVE'))
    ORDER BY age ASC, name DESC
    LIMIT 10 OFFSET 5;

    :param mongo_obj: The MongoDB find dict.
    :return: The SQL SELECT query as a string.
    """
    table = mongo_obj.get("collection", "unknown_table")
    find_filter = mongo_obj.get("find", {})
    projection = mongo_obj.get("projection", {})
    sort_clause = mongo_obj.get("sort", [])  # e.g. [("field", 1), ("other", -1)]
    limit_val = mongo_obj.get("limit", None)
    skip_val = mongo_obj.get("skip", None)

    # 1) Build the column list from projection
    columns = "*"
    if isinstance(projection, dict) and len(projection) > 0:
        # e.g. { "age":1, "status":1 }
        col_list = []
        for field, include in projection.items():
            if include == 1:
                col_list.append(field)
        if col_list:
            columns = ", ".join(col_list)

    # 2) Build WHERE from find_filter
    where_sql = build_where_sql(find_filter)

    # 3) Build ORDER BY from sort
    order_sql = build_order_by_sql(sort_clause)

    # 4) Combine everything
    sql = f"SELECT {columns} FROM {table}"

    if where_sql:
        sql += f" WHERE {where_sql}"

    if order_sql:
        sql += f" ORDER BY {order_sql}"

    # 5) Limit + Skip
    # skip in Mongo ~ "OFFSET" in SQL
    if isinstance(limit_val, int) and limit_val > 0:
        sql += f" LIMIT {limit_val}"
        if isinstance(skip_val, int) and skip_val > 0:
            sql += f" OFFSET {skip_val}"
    else:
        # If no limit but skip is provided, you can handle or ignore
        if isinstance(skip_val, int) and skip_val > 0:
            # Some SQL dialects allow "OFFSET" without a limit, others do not
            sql += f" LIMIT 999999999 OFFSET {skip_val}"

    sql += ";"
    return sql


def build_where_sql(find_filter) -> str:
    """
    Convert a 'find' dict into a SQL condition string.
    Supports:
      - direct equality: {field: value}
      - comparison operators: {field: {"$gt": val, ...}}
      - $in / $nin
      - $regex => LIKE
      - $and / $or => combine subclauses

    :param find_filter: The 'find' dict from MongoDB.
    :return: The SQL WHERE clause as a string.
    """
    if not find_filter:
        return ""

    # If top-level is a dictionary with $and / $or
    if isinstance(find_filter, dict):
        # check for $and / $or in the top-level
        if "$and" in find_filter:
            conditions = [build_where_sql(sub) for sub in find_filter["$and"]]
            # e.g. (cond1) AND (cond2)
            return "(" + ") AND (".join(cond for cond in conditions if cond) + ")"
        elif "$or" in find_filter:
            conditions = [build_where_sql(sub) for sub in find_filter["$or"]]
            return "(" + ") OR (".join(cond for cond in conditions if cond) + ")"
        else:
            # parse normal fields
            return build_basic_conditions(find_filter)

    # If top-level is a list => not typical, handle or skip
    if isinstance(find_filter, list):
        # e.g. $or array
        # but typically you'd see it as { "$or": [ {}, {} ] }
        subclauses = [build_where_sql(sub) for sub in find_filter]
        return "(" + ") AND (".join(sc for sc in subclauses if sc) + ")"

    # fallback: if it's a scalar or something unexpected
    return ""


def build_basic_conditions(condition_dict: dict) -> str:
    """
    For each field in condition_dict:
      if it's a direct scalar => field = value
      if it's an operator dict => interpret $gt, $in, etc.
    Return "field1 = val1 AND field2 >= val2" etc. combined.

    :param condition_dict: A dictionary of conditions.
    :return: A SQL condition string.
    """
    clauses = []
    for field, expr in condition_dict.items():
        # e.g. field => "status", expr => "ACTIVE"
        if isinstance(expr, dict):
            # parse operator e.g. {"$gt": 30}
            for op, val in expr.items():
                clause = convert_operator(field, op, val)
                if clause:
                    clauses.append(clause)
        else:
            # direct equality
            if isinstance(expr, (int, float)):
                clauses.append(f"{field} = {expr}")
            else:
                clauses.append(f"{field} = '{escape_quotes(str(expr))}'")

    return " AND ".join(clauses)


def convert_operator(field: str, op: str, val):
    """
    Handle operators like $gt, $in, $regex, etc.

    :param field: The field name.
    :param op: The operator (e.g., "$gt", "$in").
    """
    # Convert val to string with quotes if needed
    if isinstance(val, (int, float)):
        val_str = str(val)
    elif isinstance(val, list):
        # handle lists for $in, $nin
        val_str = ", ".join(quote_if_needed(item) for item in val)
    else:
        # string or other
        val_str = f"'{escape_quotes(str(val))}'"

    op_map = {
        "$gt": ">",
        "$gte": ">=",
        "$lt": "<",
        "$lte": "<=",
        "$eq": "=",
        "$ne": "<>",
        "$regex": "LIKE"
    }

    if op in op_map:
        sql_op = op_map[op]
        # e.g. "field > 30" or "field LIKE '%abc%'"
        return f"{field} {sql_op} {val_str}"
    elif op == "$in":
        # e.g. field IN (1,2,3)
        return f"{field} IN ({val_str})"
    elif op == "$nin":
        return f"{field} NOT IN ({val_str})"
    else:
        # fallback
        return f"{field} /*unknown op {op}*/ {val_str}"


def build_order_by_sql(sort_list):
    """
    If we have "sort": [("age", 1), ("name", -1)],
    => "age ASC, name DESC"

    :param sort_list: List of tuples (field, direction)
    :return: SQL ORDER BY clause as a string.
    """
    if not sort_list or not isinstance(sort_list, list):
        return ""
    order_parts = []
    for field_dir in sort_list:
        if isinstance(field_dir, tuple) and len(field_dir) == 2:
            field, direction = field_dir
            dir_sql = "ASC" if direction == 1 else "DESC"
            order_parts.append(f"{field} {dir_sql}")
    return ", ".join(order_parts)


def quote_if_needed(val):
    """
    Return a numeric or quoted string

    :param val: The value to quote if it's a string.
    :return: The value as a string, quoted if it's a string.
    """
    if isinstance(val, (int, float)):
        return str(val)
    return f"'{escape_quotes(str(val))}'"


def escape_quotes(s: str) -> str:
    """
    Simple approach to escape single quotes

    :param s: The string to escape.
    :return: The escaped string.
    """
    return s.replace("'", "''")


def mongo_insert_to_sql(mongo_obj: dict) -> str:
    """
    Convert a MongoDB insert object to SQL INSERT statement.

    Example input:
    {
      "collection": "users",
      "operation": "insertOne",
      "document": {"name": "Alice", "age": 30}
    }

    => Output:
    INSERT INTO users (name, age) VALUES ('Alice', 30);

    :param mongo_obj: The MongoDB insert dict.
    :return: The SQL INSERT query as a string.
    """
    collection = mongo_obj.get("collection", "unknown_table")
    operation = mongo_obj.get("operation", "insertOne")

    if operation == "insertOne":
        document = mongo_obj.get("document", {})
        if not document:
            return ""

        columns = list(document.keys())
        values = []
        for col in columns:
            val = document[col]
            if isinstance(val, (int, float)):
                values.append(str(val))
            else:
                values.append(f"'{escape_quotes(str(val))}'")

        cols_str = ", ".join(columns)
        vals_str = ", ".join(values)
        return f"INSERT INTO {collection} ({cols_str}) VALUES ({vals_str});"

    elif operation == "insertMany":
        documents = mongo_obj.get("documents", [])
        if not documents:
            return ""

        # Build multiple INSERT statements or one with multiple value sets
        columns = list(documents[0].keys()) if documents else []
        cols_str = ", ".join(columns)

        all_values = []
        for doc in documents:
            values = []
            for col in columns:
                val = doc.get(col)
                if isinstance(val, (int, float)):
                    values.append(str(val))
                else:
                    values.append(f"'{escape_quotes(str(val))}'")
            all_values.append(f"({', '.join(values)})")

        return f"INSERT INTO {collection} ({cols_str}) VALUES {', '.join(all_values)};"

    return ""


def mongo_update_to_sql(mongo_obj: dict) -> str:
    """
    Convert a MongoDB update object to SQL UPDATE statement.

    Example input:
    {
      "collection": "users",
      "operation": "updateMany",
      "filter": {"name": "Alice"},
      "update": {"$set": {"age": 31, "status": "active"}}
    }

    => Output:
    UPDATE users SET age = 31, status = 'active' WHERE name = 'Alice';

    :param mongo_obj: The MongoDB update dict.
    :return: The SQL UPDATE query as a string.
    """
    collection = mongo_obj.get("collection", "unknown_table")
    filter_obj = mongo_obj.get("filter", {})
    update_obj = mongo_obj.get("update", {})

    # Extract $set operations
    set_clause = update_obj.get("$set", {})
    if not set_clause:
        return ""

    # Build SET clause
    set_parts = []
    for field, value in set_clause.items():
        if isinstance(value, (int, float)):
            set_parts.append(f"{field} = {value}")
        else:
            set_parts.append(f"{field} = '{escape_quotes(str(value))}'")

    set_sql = ", ".join(set_parts)

    # Build WHERE clause
    where_sql = build_where_sql(filter_obj)

    sql = f"UPDATE {collection} SET {set_sql}"
    if where_sql:
        sql += f" WHERE {where_sql}"
    sql += ";"

    return sql


def mongo_delete_to_sql(mongo_obj: dict) -> str:
    """
    Convert a MongoDB delete object to SQL DELETE statement.

    Example input:
    {
      "collection": "users",
      "operation": "deleteMany",
      "filter": {"age": {"$lt": 18}}
    }

    => Output:
    DELETE FROM users WHERE age < 18;

    :param mongo_obj: The MongoDB delete dict.
    :return: The SQL DELETE query as a string.
    """
    collection = mongo_obj.get("collection", "unknown_table")
    filter_obj = mongo_obj.get("filter", {})

    # Build WHERE clause
    where_sql = build_where_sql(filter_obj)

    sql = f"DELETE FROM {collection}"
    if where_sql:
        sql += f" WHERE {where_sql}"
    sql += ";"

    return sql
