import sqlparse
from sqlparse.sql import IdentifierList, Identifier, Where
from sqlparse.tokens import Keyword, DML

def sql_select_to_mongo(sql_query: str):
    """
    Convert a SELECT...FROM...WHERE... SQL query into a naive Mongo dict:
      {
        "collection": <table>,
        "find": { ...where... },
        "projection": { col1:1, col2:1 } or None
      }
    """
    parsed_stmts = sqlparse.parse(sql_query)
    if not parsed_stmts:
        return {}

    statement = parsed_stmts[0]
    columns, table_name, where_clause = parse_select_statement(statement)
    return build_mongo_find(table_name, where_clause, columns)

def parse_select_statement(statement):
    """
    Goes through the tokens in the statement to find:
      - columns (after SELECT, before FROM)
      - table name (after FROM)
      - Where object (if present)
    """
    columns = []
    table_name = None
    where_clause = {}

    found_select = False
    reading_columns = False
    reading_from = False

    for token in statement.tokens:
        if token.is_whitespace:
            continue

        # If token is SELECT
        if token.ttype is DML and token.value.upper() == "SELECT":
            found_select = True
            reading_columns = True
            continue

        # If reading columns until we see FROM
        if reading_columns:
            if token.ttype is Keyword and token.value.upper() == "FROM":
                reading_columns = False
                reading_from = True
                continue
            else:
                # Attempt to parse columns
                possible_cols = extract_columns(token)
                if possible_cols:
                    columns = possible_cols
            continue

        # If reading table name
        if reading_from:
            # If token is the 'WHERE' keyword or something else
            #   we assume we didn't see a normal table name yet
            if isinstance(token, Where):
                # If it lumps it as a Where object
                where_clause = extract_where_clause(token)
                reading_from = False
                continue
            elif token.ttype is Keyword and token.value.upper() == "WHERE":
                # We'll handle next token as Where or fallback
                reading_from = False
            elif token.ttype not in (Keyword, DML) and not token.is_whitespace:
                table_name = str(token).strip()
                reading_from = False
                continue

        # If it's a Where object, parse it
        if isinstance(token, Where):
            where_clause = extract_where_clause(token)
            continue

        # If it's the WHERE keyword but not a Where object
        if token.ttype is Keyword and token.value.upper() == "WHERE":
            # The next token might be a Where or conditions inline
            # We handle it if we see it as next
            # in some versions, the subsequent text is all in the next token
            pass

    return columns, table_name, where_clause

def extract_columns(token):
    """
    If token is an IdentifierList => multiple columns
    If token is an Identifier => single column
    If token is '*' => wildcard
    """
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
    If where_token is a Where object, it typically includes 'WHERE ...'
    We'll remove the 'WHERE ' prefix, then parse the rest.
    """
    raw = str(where_token).strip()
    if raw.upper().startswith("WHERE"):
        raw = raw[5:].strip()
    return parse_where_conditions(raw)

def parse_where_conditions(text: str):
    """
    e.g. "age > 30 AND name = 'Alice';"
    => { "age":{"$gt":30}, "name":"Alice" }
    We'll strip trailing semicolons as well.
    """
    text = text.strip().rstrip(";")  # remove trailing semicolon
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
        # remove any leftover semicolons or quotes
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
            # fallback
            out[field] = {"$op?": val}
    return out

def convert_value(val: str):
    try:
        return int(val)
    except ValueError:
        try:
            return float(val)
        except ValueError:
            return val

def build_mongo_find(table_name, where_clause, columns):
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
