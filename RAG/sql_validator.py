import re 
def is_sql_safe(sql):
    if not sql:
        return False ,"sql is empty"
    sql=sql.strip()
    sql=sql.rstrip(';').strip()

    if not sql:
       return False ,"sql is empty"

    sql_lower=sql.lower()

    if not sql_lower.startswith('select'):
        return False,"only select query are allowed" 


    blocked_keywords = [
        "insert",
        "update",
        "delete",
        "drop",
        "alter",
        "truncate",
        "create",
        "replace",
        "grant",
        "revoke",
        "commit",
        "rollback",
    ]

    for keyword in blocked_keywords:
       pattern = rf"\b{keyword}\b"
       if re.search(pattern,sql_lower):
           return False,(
               f"Blocked SQL keyword detected: {keyword}"
           )

    if ';' in sql:
        return False, "Multiple SQL statements are not allowed."
    return True ,'SQL query is safe'

def extract_table(sql):
    table=[]
    from_match=re.findall(
         r"\bFROM\s+([a-zA-Z_][a-zA-Z0-9_]*)",
         sql,
         re.IGNORECASE
    )

    table.extend(from_match)

    join_matches = re.findall(
        r"\bJOIN\s+([a-zA-Z_][a-zA-Z0-9_]*)",
        sql,
        re.IGNORECASE
    )
    table.extend(join_matches)

    return list(set(table))


def validate_table(sql,schema):
    tables=extract_table(sql)
    if not  tables:
        return False,"no tabke found in SQL"
    valid_tables=set(schema.keys())

    for table in tables:
        if table not in valid_tables:
            return False,f"Unknown table: {table}"

    return True ,'All tables are valid'


def extract_columns(sql):

    columns = []


    select_match = re.search(
        r"\bSELECT\s+(.*?)\s+\bFROM\b",
        sql,
        re.IGNORECASE | re.DOTALL
    )

    if select_match:

        select_part = select_match.group(1).strip()

        select_part = re.sub(
            r"^\s*DISTINCT\s+",
            "",
            select_part,
            flags=re.IGNORECASE
        )

        parts = select_part.split(",")

        for part in parts:

            part = part.strip()

            # Remove AS alias
            part = re.sub(
                r"\s+AS\s+[a-zA-Z_][a-zA-Z0-9_]*$",
                "",
                part,
                flags=re.IGNORECASE
            ).strip()

            

            function_match = re.fullmatch(
                r"(COUNT|SUM|AVG|MIN|MAX)\s*\(\s*(.*?)\s*\)",
                part,
                re.IGNORECASE
            )

            if function_match:

                function_column = function_match.group(2).strip()

                # COUNT(*)
                if function_column == "*":
                    continue

                # table.column inside function
                table_column_match = re.fullmatch(
                    r"([a-zA-Z_][a-zA-Z0-9_]*)\."
                    r"([a-zA-Z_][a-zA-Z0-9_]*)",
                    function_column
                )

                if table_column_match:

                    columns.append({
                        "table": table_column_match.group(1),
                        "column": table_column_match.group(2)
                    })

                else:

                    columns.append({
                        "table": None,
                        "column": function_column
                    })

                continue

            

            match = re.fullmatch(
                r"([a-zA-Z_][a-zA-Z0-9_]*)\."
                r"([a-zA-Z_][a-zA-Z0-9_]*)",
                part
            )

            if match:

                columns.append({
                    "table": match.group(1),
                    "column": match.group(2)
                })

                continue

            

            match = re.fullmatch(
                r"[a-zA-Z_][a-zA-Z0-9_]*",
                part
            )

            if match:

                columns.append({
                    "table": None,
                    "column": part
                })

    

    where_match = re.search(
        r"\bWHERE\s+(.*?)(?=\bGROUP\s+BY\b|\bORDER\s+BY\b|\bLIMIT\b|$)",
        sql,
        re.IGNORECASE | re.DOTALL
    )

    if where_match:

        where_part = where_match.group(1)

        # Remove quoted string values
        cleaned_where = re.sub(
            r"'(?:''|[^'])*'|\"(?:\"\"|[^\"])*\"",
            "",
            where_part
        )

        # table.column
        matches = re.findall(
            r"\b([a-zA-Z_][a-zA-Z0-9_]*)\."
            r"([a-zA-Z_][a-zA-Z0-9_]*)\b",
            cleaned_where
        )

        for table, column in matches:

            columns.append({
                "table": table,
                "column": column
            })

        # Remove table.column expressions
        cleaned_where = re.sub(
            r"\b[a-zA-Z_][a-zA-Z0-9_]*\."
            r"[a-zA-Z_][a-zA-Z0-9_]*\b",
            "",
            cleaned_where
        )

        # Find simple column names
        words = re.findall(
            r"\b[a-zA-Z_][a-zA-Z0-9_]*\b",
            cleaned_where
        )

        sql_words = {
            "and",
            "or",
            "not",
            "in",
            "is",
            "null",
            "like",
            "between",
            "true",
            "false"
        }

        for word in words:

            if word.lower() in sql_words:
                continue

            columns.append({
                "table": None,
                "column": word
            })

   

    join_on_matches = re.finditer(
        r"\bON\s+(.*?)(?=\bJOIN\b|\bWHERE\b|\bGROUP\s+BY\b|\bORDER\s+BY\b|\bLIMIT\b|$)",
        sql,
        re.IGNORECASE | re.DOTALL
    )

    for match in join_on_matches:

        on_part = match.group(1)

        # table.column
        column_matches = re.findall(
            r"\b([a-zA-Z_][a-zA-Z0-9_]*)\."
            r"([a-zA-Z_][a-zA-Z0-9_]*)\b",
            on_part
        )

        for table, column in column_matches:

            columns.append({
                "table": table,
                "column": column
            })

    

    group_match = re.search(
        r"\bGROUP\s+BY\s+(.*?)(?=\bORDER\s+BY\b|\bLIMIT\b|$)",
        sql,
        re.IGNORECASE | re.DOTALL
    )

    if group_match:

        group_part = group_match.group(1)

        # table.column
        matches = re.findall(
            r"\b([a-zA-Z_][a-zA-Z0-9_]*)\."
            r"([a-zA-Z_][a-zA-Z0-9_]*)\b",
            group_part
        )

        for table, column in matches:

            columns.append({
                "table": table,
                "column": column
            })

        # Remove table.column
        cleaned_group = re.sub(
            r"\b[a-zA-Z_][a-zA-Z0-9_]*\."
            r"[a-zA-Z_][a-zA-Z0-9_]*\b",
            "",
            group_part
        )

        words = re.findall(
            r"\b[a-zA-Z_][a-zA-Z0-9_]*\b",
            cleaned_group
        )

        for word in words:

            if word.isdigit():
                continue

            columns.append({
                "table": None,
                "column": word
            })

   

    order_match = re.search(
        r"\bORDER\s+BY\s+(.*?)(?=\bLIMIT\b|$)",
        sql,
        re.IGNORECASE | re.DOTALL
    )

    if order_match:

        order_part = order_match.group(1)

        # Remove ASC / DESC
        order_part = re.sub(
            r"\bASC\b|\bDESC\b",
            "",
            order_part,
            flags=re.IGNORECASE
        )

        # table.column
        matches = re.findall(
            r"\b([a-zA-Z_][a-zA-Z0-9_]*)\."
            r"([a-zA-Z_][a-zA-Z0-9_]*)\b",
            order_part
        )

        for table, column in matches:

            columns.append({
                "table": table,
                "column": column
            })

        # Remove table.column
        cleaned_order = re.sub(
            r"\b[a-zA-Z_][a-zA-Z0-9_]*\."
            r"[a-zA-Z_][a-zA-Z0-9_]*\b",
            "",
            order_part
        )

        words = re.findall(
            r"\b[a-zA-Z_][a-zA-Z0-9_]*\b",
            cleaned_order
        )

        for word in words:

            columns.append({
                "table": None,
                "column": word
            })

    return columns

def validate_columns(sql, schema):

    columns = extract_columns(sql)

    

    select_aliases = set()

    select_match = re.search(
        r"\bSELECT\s+(.*?)\s+\bFROM\b",
        sql,
        re.IGNORECASE | re.DOTALL
    )

    if select_match:

        select_part = select_match.group(1)

        alias_matches = re.findall(
            r"\bAS\s+([a-zA-Z_][a-zA-Z0-9_]*)\b",
            select_part,
            re.IGNORECASE
        )

        select_aliases.update(alias_matches)

   

    if not columns:

        return True, "No columns to validate."

   

    aliases = {}

    
    from_match = re.search(
        r"\bFROM\s+"
        r"([a-zA-Z_][a-zA-Z0-9_]*)"
        r"(?:\s+(?:AS\s+)?"
        r"([a-zA-Z_][a-zA-Z0-9_]*))?",
        sql,
        re.IGNORECASE
    )

    if from_match:

        table = from_match.group(1)
        alias = from_match.group(2)

        aliases[table] = table

        if alias:
            aliases[alias] = table

   

    join_matches = re.finditer(
        r"\bJOIN\s+"
        r"([a-zA-Z_][a-zA-Z0-9_]*)"
        r"(?:\s+(?:AS\s+)?"
        r"([a-zA-Z_][a-zA-Z0-9_]*))?",
        sql,
        re.IGNORECASE
    )

    for match in join_matches:

        table = match.group(1)
        alias = match.group(2)

        aliases[table] = table

        if alias:
            aliases[alias] = table

   

    for item in columns:

        table_name = item["table"]
        column_name = item["column"]

       

        if (
            table_name is None
            and column_name in select_aliases
        ):
            continue

        

        if table_name is None:

            valid_column = False

            for table_columns in schema.values():

                if any(
                    column["column"] == column_name
                    for column in table_columns
                ):

                    valid_column = True
                    break

            if not valid_column:

                return False, (
                    f"Unknown column: {column_name}"
                )

            continue

        # ----------------------------------------------------
        # Resolve table alias
        #
        # Example:
        # c.name
        #
        # c → customers
        # ----------------------------------------------------

        actual_table = aliases.get(table_name)

        if not actual_table:

            return False, (
                f"Unknown table or alias: {table_name}"
            )

        # ----------------------------------------------------
        # Check table exists
        # ----------------------------------------------------

        if actual_table not in schema:

            return False, (
                f"Unknown table: {actual_table}"
            )

        # ----------------------------------------------------
        # Get valid columns for table
        # ----------------------------------------------------

        valid_columns = {
            column["column"]
            for column in schema[actual_table]
        }

        # ----------------------------------------------------
        # Check column
        # ----------------------------------------------------

        if column_name not in valid_columns:

            return False, (
                f"Unknown column: "
                f"{actual_table}.{column_name}"
            )

    return True, "All columns are valid."