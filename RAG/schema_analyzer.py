from sqlalchemy import text
import pandas as pd




EXCLUDED_TABLES = {
    "django_migrations",
    "django_content_type",
    "django_session",
    "django_admin_log",

    "auth_user",
    "auth_group",
    "auth_permission",
    "auth_user_groups",
    "auth_user_user_permissions",
    "auth_group_permissions",

    "sql_api_databaseconnection",
    "query_history",
}




def get_schema(engine):

    query = text("""
        SELECT
            table_name,
            column_name,
            data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position
    """)

    # Execute query using the supplied database engine
    df = pd.read_sql(query, engine)

    schema = {}

    for _, row in df.iterrows():

        table = row["table_name"]

        # Ignore Django/application tables
        if table in EXCLUDED_TABLES:
            continue

        # Create table entry if it doesn't exist
        if table not in schema:
            schema[table] = []

        # Add column information
        schema[table].append({
            "column": row["column_name"],
            "type": row["data_type"]
        })

    return schema

def build_database_context(engine, relationships):

    schema = get_schema(engine)

    context = "## Database Schema\n"

   

    for table, columns in schema.items():

        context += f"\nTable: {table}\n"

        for column in columns:

            context += (
                f"- {column['column']} "
                f"({column['type']})\n"
            )

    

    context += "\n## Relationships\n"

    if relationships:

        for relationship in relationships:

            context += (
                f"- {relationship['source_table']}."
                f"{relationship['source_column']} → "
                f"{relationship['target_table']}."
                f"{relationship['target_column']}\n"
            )

    else:

        context += "- No foreign-key relationships detected.\n"

    return context


def get_primary_table(schema):
    """
    Select the main business table for dashboard analytics.
    Prefer customers, then orders, then products.
    """
    preferred_tables = ["customers", "orders", "products"]

    for table in preferred_tables:
        if table in schema:
            return table

    # Fallback: choose the first available business table
    if schema:
        return next(iter(schema))

    raise ValueError("No business tables found in the database.")


def detect_columns(schema):
    """
    Classify each table's columns into categorical, date,
    and numeric columns using PostgreSQL data types.
    """
    info = {}

    categorical_types = {
        "character varying",
        "character",
        "text",
        "name",
        "boolean",
        "uuid",
        "USER-DEFINED",
    }

    date_types = {
        "date",
        "timestamp without time zone",
        "timestamp with time zone",
        "timestamp",
    }

    numeric_types = {
        "smallint",
        "integer",
        "bigint",
        "numeric",
        "decimal",
        "real",
        "double precision",
    }

    for table, columns in schema.items():
        info[table] = {
            "categorical": [],
            "date": [],
            "numeric": [],
        }

        for column in columns:
            name = column["column"]
            data_type = column["type"].lower()

            if data_type in date_types or data_type.startswith("timestamp"):
                info[table]["date"].append(name)

            elif data_type in numeric_types:
                info[table]["numeric"].append(name)

            elif data_type in categorical_types:
                info[table]["categorical"].append(name)

    return info
