import os
import django

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings"
)

django.setup()

from sql_api.models import DatabaseConnection
from RAG.database_connection import create_user_engine
from RAG.schema_analyzer import build_database_context
from RAG.relationship_analyzer import get_relationships


connection = DatabaseConnection.objects.get(id=1)

engine = create_user_engine(connection)

try:

    relationships = get_relationships(engine)

    context = build_database_context(
        engine,
        relationships
    )

    print("\n===== DATABASE CONTEXT =====")
    print(context)

finally:
    engine.dispose()