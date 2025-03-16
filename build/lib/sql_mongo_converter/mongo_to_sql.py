def mongo_find_to_sql(mongo_obj):
    """
    Expects a dict like:
    {
      "collection": "users",
      "find": { "age": {"$gt": 30}, "name": "Alice" },
      "projection": {"name": 1, "age": 1}
    }
    We'll convert to something like:
    SELECT name, age FROM users WHERE age > 30 AND name = 'Alice';
    """
    table = mongo_obj.get("collection", "UnknownTable")
    find_filter = mongo_obj.get("find", {})
    projection = mongo_obj.get("projection")

    columns = "*"
    if projection and isinstance(projection, dict):
        # e.g. {"name":1,"age":1}
        # we take the keys with 1
        col_list = []
        for k, v in projection.items():
            if v == 1:
                col_list.append(k)
        if col_list:
            columns = ", ".join(col_list)

    where_clauses = []
    for field, condition in find_filter.items():
        if isinstance(condition, dict):
            # e.g. {"$gt": 30}
            for op, val in condition.items():
                sql_op = map_mongo_op_to_sql(op)
                # if numeric, no quotes
                if isinstance(val, (int, float)):
                    where_clauses.append(f"{field} {sql_op} {val}")
                else:
                    where_clauses.append(f"{field} {sql_op} '{val}'")
        else:
            # direct equality
            if isinstance(condition, (int, float)):
                where_clauses.append(f"{field} = {condition}")
            else:
                where_clauses.append(f"{field} = '{condition}'")

    where_sql = ""
    if where_clauses:
        where_sql = " WHERE " + " AND ".join(where_clauses)

    return f"SELECT {columns} FROM {table}{where_sql};"


def map_mongo_op_to_sql(op: str):
    """
    Convert $gt to >, $gte to >=, etc.
    """
    op_map = {
        "$gt": ">",
        "$gte": ">=",
        "$lt": "<",
        "$lte": "<="
    }
    return op_map.get(op, "UNKNOWNOP")
