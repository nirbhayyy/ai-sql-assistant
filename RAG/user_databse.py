from sqlalchemy import create_engine,text,inspect
from sqlalchemy.engine import URL

def test_prostgres_connection(host,port,database,username,password):
    url=URL.create(
        drivername="postgresql+psycopg2",
        username=username,
        password=password,
        host=host,
        port=int(port),
        database=database
    )

    engine=create_engine(
        url,pool_pre_ping=True,connect_args={"connect_timeout": 5}
    )

    try:
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))

            return {
            "success": True,
            "message": "Database connection successful"
        }

    finally:
        engine.dispose()


def get_database_schema(host, port, database, username, password):
    url = URL.create(
        drivername="postgresql+psycopg2",
        username=username,
        password=password,
        host=host,
        port=int(port),
        database=database
    )

    engine = create_engine(
        url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 5}
    )

    try:
        inspector=inspect(engine)
        print("Database:", database)
        print("Default schema:", inspector.default_schema_name)
        print("Public tables:", inspector.get_table_names(schema="public"))
        print("All schemas:", inspector.get_schema_names()) 
        schema={}

        tables=inspector.get_table_names(schema='public')

        for table in tables:
            columns = inspector.get_columns(
                table,
                schema="public"
            )

            foreign_keys = inspector.get_foreign_keys(
                table,
                schema="public"
            )
            schema[table] = {
                "columns": [
                    {
                        "name": column["name"],
                        "type": str(column["type"]),
                        "nullable": column["nullable"]
                    }
                    for column in columns
                ],
                "foreign_keys": [
                    {
                        "columns": fk["constrained_columns"],
                        "referenced_table": fk["referred_table"],
                        "referenced_columns": fk["referred_columns"]
                    }
                    for fk in foreign_keys
                ]
            }
        return schema
    finally:
        engine.dispose()