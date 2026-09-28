from sqlalchemy import text
from .executor import engine

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
    "query_history"
}

def get_schema():
    query = text("""
        SELECT
            table_name,
            column_name,
            data_type
        FROM information_schema.columns
        WHERE table_schema='public'
        ORDER BY table_name, ordinal_position
    """)

    schema={}
    with engine.connect() as conn:
        result=conn.execute(query)
        for row in result:
            table=row.table_name

            if row.table_name in EXCLUDED_TABLES:
                continue
            if table not in schema:
                schema[table]=[]

            schema[table].append({
                "column": row.column_name,
                "type": row.data_type
            })

    return schema

def detect_columns(schema):

    info = {}

    for table, cols in schema.items():

        categorical = []
        numeric = []
        dates = []

        for c in cols:

            t = c["type"]

            if t in ("text","character varying"):
                categorical.append(c["column"])

            elif t in ("integer","bigint","numeric","double precision"):
                numeric.append(c["column"])

            elif t in ("date","timestamp without time zone","timestamp"):
                dates.append(c["column"])

        info[table] = {
            "categorical": categorical,
            "numeric": numeric,
            "date": dates
        }

    return info

def get_primary_table(schema):

    largest_table = None
    max_columns = 0

    for table, cols in schema.items():

        if len(cols) > max_columns:
            max_columns = len(cols)
            largest_table = table

    return largest_table