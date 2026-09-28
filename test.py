from RAG.schema_analyzer import get_schema,get_primary_table,detect_columns
schema=get_schema()

print(schema)
print("="*137)
print(get_primary_table(schema))
print("="*137)
print(detect_columns(schema))
print("="*137)
