import os
import pandas as pd
import re
import time
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from dotenv import load_dotenv
load_dotenv()

DB_URL = URL.create(
    "postgresql+psycopg2",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT")),
    database=os.getenv("DB_NAME"),
)

engine=create_engine(DB_URL)

def is_safe_query(sql:str):
    sql=sql.strip().lower()
    if not sql.startswith('select'):
        return False

    blocked = [
        "insert",
        "update",
        "delete",
        "drop",
        "alter",
        "truncate",
        "create",
    ]
    return not any(word in sql for word in blocked)


def execuute_sql(sql:str):
    if not is_safe_query(sql):
        raise ValueError('Only SELECT queries are allowed.')
    start=time.time()
    df=pd.read_sql(sql,engine)
    execution_time=round(time.time()-start,3)
    return df,execution_time

