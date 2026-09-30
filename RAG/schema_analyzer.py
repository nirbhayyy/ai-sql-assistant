from sqlalchemy import text
from executor import engine
from relationship_analyzer import get_relationships

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
        ids = []
        text_colunm = []

        for c in cols:

            name = c['column'].lower()
            dtype = c['type'].lower()

            # ID columns
            if name == "id" or name.endswith("_id"):
                ids.append(c['column'])
                continue

            # Email columns
            if 'email' in name:
                text_colunm.append(c['column'])
                continue

            # Date columns
            if dtype in (
                "date",
                "timestamp without time zone",
                "timestamp",
                "timestamp with time zone"
            ):
                dates.append(c['column'])
                continue

            # Numeric columns
            if dtype in (
                "integer",
                "bigint",
                "smallint",
                "numeric",
                "decimal",
                "real",
                "double precision"
            ):
                numeric.append(c['column'])
                continue

            # Text / categorical columns
            if dtype in (
                "text",
                "character varying",
                "character"
            ):
                text_colunm.append(c['column'])
                categorical.append(c['column'])

        # IMPORTANT:
        # This must be INSIDE the table loop
        info[table] = {
            "categorical": categorical,
            "numeric": numeric,
            "date": dates,
            "ids": ids,
            "text": text_colunm
        }

    return info

def get_best_category(columns):

    categorical = columns["categorical"]

    if not categorical:
        return None

    preferred_words = [
        "city",
        "category",
        "department",
        "type",
        "status",
        "country",
        "state",
        "region",
        "gender"
    ]

    # First check preferred names
    for column in categorical:

        column_lower = column.lower()

        for word in preferred_words:

            if word in column_lower:
                return column

    # Otherwise return first candidate
    return categorical[0]

def get_best_date(columns):
    dates=columns['date']

    if not dates:
        return None


    preferred_words = [
        "date",
        "created",
        "joined",
        "joining",
        "registered",
        "updated"
    ]

    for col in dates:
        col_lower=col.lower()
        for world in preferred_words:
            if world in col_lower:
                return col

    return dates[0]




def get_primary_table(schema, info):

    best_table = None
    best_score = -1

    for table in schema.keys():

        if table not in info:
            continue

        columns = info[table]

        score = 0

        # Useful categorical columns
        score += len(columns["categorical"]) * 2

        # Useful numeric columns
        score += len(columns["numeric"]) * 2

        # Date columns
        score += len(columns["date"]) * 2

        # IDs should not increase importance
        score -= len(columns["ids"])

        # Tables with dates are useful for dashboards
        if columns["date"]:
            score += 3

        # Tables with categories are useful for charts
        if columns["categorical"]:
            score += 3

        if score > best_score:

            best_score = score
            best_table = table

    return best_table

def build_database_context():

    schema = get_schema()

    relationships = get_relationships()

    context = []

    context.append("DATABASE SCHEMA")
    context.append("================")

    for table, columns in schema.items():

        context.append(f"\nTable: {table}")

        for column in columns:

            context.append(
                f"- {column['column']}: {column['type']}"
            )

    context.append("\n\nTABLE RELATIONSHIPS")
    context.append("===================")

    for relationship in relationships:

        context.append(
            f"- "
            f"{relationship['source_table']}."
            f"{relationship['source_column']}"
            f" → "
            f"{relationship['target_table']}."
            f"{relationship['target_column']}"
        )

    return "\n".join(context)

if __name__ == "__main__":

    context = build_database_context()

    print("\n")
    print(context)