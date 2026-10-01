from sqlalchemy import text,create_engine
from sqlalchemy.engine import URL


EXCLUDED_TABLES = {
    "django_migrations",
    "django_content_type",
    "django_admin_log",
    "django_session",

    "auth_permission",
    "auth_group",
    "auth_group_permissions",
    "auth_user",
    "auth_user_groups",
    "auth_user_user_permissions",

    "sql_api_databaseconnection",
    "query_history",
}


def get_relationships(engine):

    query = text("""
        SELECT
            tc.table_name AS source_table,
            kcu.column_name AS source_column,
            ccu.table_name AS target_table,
            ccu.column_name AS target_column
        FROM information_schema.table_constraints AS tc

        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema

        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema

        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND tc.table_schema = 'public'

        ORDER BY
            tc.table_name,
            kcu.column_name
    """)

    relationships = []

    with engine.connect() as connection:

        result = connection.execute(query)

        for row in result:

            # Ignore Django/internal tables
            if (
                row.source_table in EXCLUDED_TABLES
                or row.target_table in EXCLUDED_TABLES
            ):
                continue

            relationships.append({
                "source_table": row.source_table,
                "source_column": row.source_column,
                "target_table": row.target_table,
                "target_column": row.target_column,
            })

    return relationships

def create_user_engine(connection):
    """
    Create a SQLAlchemy engine using a user's
    DatabaseConnection object.
    """

    db_url = URL.create(
        "postgresql+psycopg2",
        username=connection.username,
        password=connection.password,
        host=connection.host,
        port=connection.port,
        database=connection.database_name,
    )

    engine = create_engine(
        db_url,
        pool_pre_ping=True
    )

    return engine


def test_postgresql_connection(
    host,
    port,
    database_name,
    username,
    password
):
    db_url = URL.create(
        "postgresql+psycopg2",
        username=username,
        password=password,
        host=host,
        port=port,
        database=database_name,
    )

    engine = create_engine(
        db_url,
        pool_pre_ping=True
    )

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return True, "Database connection successful."

    except Exception as e:
        return False, str(e)

    finally:
        engine.dispose()