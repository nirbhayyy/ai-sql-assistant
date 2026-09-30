import re
from schema_analyzer import get_schema
from executor import is_safe_query
from relationship_analyzer import get_relationships

def extract_tables(sql):

    tables = []

    # FROM table
    from_match = re.search(
        r'\bFROM\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        sql,
        re.IGNORECASE
    )

    if from_match:
        tables.append(from_match.group(1))

    # JOIN table
    join_matches = re.findall(
        r'\bJOIN\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        sql,
        re.IGNORECASE
    )

    tables.extend(join_matches)

    return list(set(tables))

def extract_columns(sql):

    columns = []

    # Find columns after SELECT
    select_match = re.search(
        r'\bSELECT\s+(.*?)\s+\bFROM\b',
        sql,
        re.IGNORECASE | re.DOTALL
    )

    if not select_match:
        return columns

    select_part = select_match.group(1)

    # Split SELECT columns
    select_columns = select_part.split(",")

    for column in select_columns:

        column = column.strip()

        # Remove aliases
        column = re.sub(
            r'\s+AS\s+\w+$',
            '',
            column,
            flags=re.IGNORECASE
        )

        # Ignore *
        if column == "*":
            continue

        # Handle table.column
        if "." in column:

            table, col = column.split(".", 1)

            columns.append({
                "table": table.strip(),
                "column": col.strip()
            })

    return columns

def validate_tables(sql, schema):

    tables = extract_tables(sql)

    valid_tables = set(schema.keys())

    for table in tables:

        if table not in valid_tables:

            return False, f"Unknown table: {table}"

    return True, "All tables are valid."

def validate_columns(sql, schema):

    columns = extract_columns(sql)

    if not columns:
        return True, "Columns cannot be validated."

    # Build alias map
    aliases = {}

    for table in extract_tables(sql):

        pattern = rf'\b{table}\s+([a-zA-Z_][a-zA-Z0-9_]*)'

        match = re.search(
            pattern,
            sql,
            re.IGNORECASE
        )

        if match:
            aliases[match.group(1)] = table

    for item in columns:

        table_name = item["table"]
        column_name = item["column"]

        # Convert alias → actual table
        actual_table = aliases.get(
            table_name,
            table_name
        )

        if actual_table not in schema:

            return False, f"Unknown table: {actual_table}"

        valid_columns = {
            column["column"]
            for column in schema[actual_table]
        }

        if column_name not in valid_columns:

            return False, (
                f"Unknown column: "
                f"{actual_table}.{column_name}"
            )

    return True, "All columns are valid."
def validate_relationships(sql):
    relationships = get_relationships()

    if not relationships:
        return True, "No relationships found."

    join_pattern = re.compile(
        r'\bJOIN\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        r'(?:\s+([a-zA-Z_][a-zA-Z0-9_]*))?'
        r'\s+ON\s+'
        r'([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)'
        r'\s*=\s*'
        r'([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)',
        re.IGNORECASE
    )

    matches = join_pattern.findall(sql)

    if not matches:
        return True, "No JOIN relationships to validate."

    aliases = {}

    # Find FROM table + alias
    from_match = re.search(
        r'\bFROM\s+([a-zA-Z_][a-zA-Z0-9_]*)(?:\s+([a-zA-Z_][a-zA-Z0-9_]*))?',
        sql,
        re.IGNORECASE
    )

    if from_match:
        table = from_match.group(1)
        alias = from_match.group(2)

        aliases[alias or table] = table

    # Find JOIN tables + aliases
    join_tables = re.finditer(
        r'\bJOIN\s+([a-zA-Z_][a-zA-Z0-9_]*)(?:\s+([a-zA-Z_][a-zA-Z0-9_]*))?',
        sql,
        re.IGNORECASE
    )

    for match in join_tables:
        table = match.group(1)
        alias = match.group(2)

        aliases[alias or table] = table

    for match in matches:
        left_alias = match[2]
        left_column = match[3]

        right_alias = match[4]
        right_column = match[5]

        left_table = aliases.get(left_alias)
        right_table = aliases.get(right_alias)

        if not left_table or not right_table:
            return False, "Could not resolve JOIN aliases."

        valid_relationship = False

        for relationship in relationships:

            source_table = relationship["source_table"]
            source_column = relationship["source_column"]

            target_table = relationship["target_table"]
            target_column = relationship["target_column"]

            # Normal direction
            if (
                left_table == source_table
                and left_column == source_column
                and right_table == target_table
                and right_column == target_column
            ):
                valid_relationship = True
                break

            # Reverse direction
            if (
                left_table == target_table
                and left_column == target_column
                and right_table == source_table
                and right_column == source_column
            ):
                valid_relationship = True
                break

        if not valid_relationship:
            return False, (
                f"Invalid JOIN relationship: "
                f"{left_table}.{left_column} = "
                f"{right_table}.{right_column}"
            )

    return True, "All JOIN relationships are valid."

def validate_sql(sql):

    if not is_safe_query(sql):
        return False, "Unsafe SQL query."

    schema = get_schema()

    valid, message = validate_tables(sql, schema)

    if not valid:
        return False, message

    valid, message = validate_columns(sql, schema)

    if not valid:
        return False, message

    valid, message = validate_relationships(sql)

    if not valid:
        return False, message

    return True, "SQL is valid."

if __name__ == "__main__":

    tests = [

        """
    SELECT c.name, o.quantity
    FROM customers c
    JOIN orders o
    ON c.c_id = o.c_id
    """,

    # Invalid JOIN
    """
    SELECT c.name, o.quantity
    FROM customers c
    JOIN orders o
    ON c.c_id = o.p_id
    """,

    # Valid product JOIN
    """
    SELECT p.p_name, o.quantity
    FROM products p
    JOIN orders o
    ON p.p_id = o.p_id
    """,

    # Invalid relationship
    """
    SELECT c.name, p.p_name
    FROM customers c
    JOIN products p
    ON c.c_id = p.p_id
    """
    ]

    for sql in tests:

        valid, message = validate_sql(sql)

        print("\nSQL:")
        print(sql)

        print("VALID:", valid)
        print("MESSAGE:", message)