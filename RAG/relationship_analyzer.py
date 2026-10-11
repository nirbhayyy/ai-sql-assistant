from sqlalchemy import text


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
    """)

    with engine.connect() as connection:

        result = connection.execute(query)

        relationships = []

        for row in result:

            source_table = row.source_table
            target_table = row.target_table

            # Ignore Django/application relationships
            if source_table in EXCLUDED_TABLES:
                continue

            if target_table in EXCLUDED_TABLES:
                continue

            relationships.append({
                "source_table": source_table,
                "source_column": row.source_column,
                "target_table": target_table,
                "target_column": row.target_column,
            })

    return relationships