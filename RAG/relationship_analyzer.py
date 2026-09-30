from sqlalchemy import text
from executor import engine

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
def get_relationships():

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

        ORDER BY tc.table_name;
    """)

    relationships = []

    with engine.connect() as conn:

        result = conn.execute(query)

        for row in result:
            if(
                 row.source_table in EXCLUDED_TABLES
                or row.target_table in EXCLUDED_TABLES
            ):
                continue
            relationships.append({
                "source_table": row.source_table,
                "source_column": row.source_column,
                "target_table": row.target_table,
                "target_column": row.target_column
            })

    return relationships


if __name__ == "__main__":

    relationships = get_relationships()

    print("\nTABLE RELATIONSHIPS:")

    for relationship in relationships:

        print(
            f"{relationship['source_table']}."
            f"{relationship['source_column']}"
            f" → "
            f"{relationship['target_table']}."
            f"{relationship['target_column']}"
        )

def build_relationship_graph(relationships):

    graph = {}

    for relationship in relationships:

        source_table = relationship["source_table"]
        target_table = relationship["target_table"]

        graph.setdefault(source_table, [])

        graph[source_table].append({
            "table": target_table,
            "source_column": relationship["source_column"],
            "target_column": relationship["target_column"]
        })

    return graph



if __name__ == "__main__":

    relationships = get_relationships()

    print("\nTABLE RELATIONSHIPS:")

    for relationship in relationships:

        print(
            f"{relationship['source_table']}."
            f"{relationship['source_column']}"
            f" → "
            f"{relationship['target_table']}."
            f"{relationship['target_column']}"
        )

    graph = build_relationship_graph(relationships)

    print("\nRELATIONSHIP GRAPH:")
    print(graph)