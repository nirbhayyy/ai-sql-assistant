from sqlalchemy import create_engine,text
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
