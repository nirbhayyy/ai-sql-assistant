import os
import pandas as pd
import re
import time
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from dotenv import load_dotenv
from sqlalchemy import text
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

def is_safe_query(sql: str):

    if not sql or not sql.strip():
        return False

    sql = sql.strip()

    # Remove trailing semicolon
    sql = sql.rstrip(";").strip()

    sql_lower = sql.lower()

    # Only SELECT queries
    if not sql_lower.startswith("select"):
        return False

    blocked_keywords = [
        "insert",
        "update",
        "delete",
        "drop",
        "alter",
        "truncate",
        "create",
        "replace",
        "grant",
        "revoke",
        "commit",
        "rollback",
    ]

    for keyword in blocked_keywords:

        if f" {keyword} " in f" {sql_lower} ":
            return False

    # Prevent multiple statements
    if ";" in sql:
        return False

    return True


def execuute_sql(sql:str):
    if not is_safe_query(sql):
        raise ValueError('Only SELECT queries are allowed.')
    start=time.time()
    df=pd.read_sql(sql,engine)
    execution_time=round(time.time()-start,3)
    return df,execution_time


def save_history(quesion,sql,execution_time):
    query = text("""
        INSERT INTO query_history
        (question, generated_sql, execution_time)
        VALUES (:q, :s, :t)
    """)
    with engine.begin() as conn:
        conn.execute(query,{
            'q':quesion,
            's':sql,
            't':execution_time
        })

if __name__ == "__main__":

    tests = [

        "SELECT * FROM customers",

        "SELECT name FROM customers WHERE city = 'Pune'",

        "DELETE FROM customers",

        "DROP TABLE customers",

        "UPDATE customers SET city = 'Pune'",

        "SELECT * FROM customers; DROP TABLE customers",

        "INSERT INTO customers VALUES (1, 'Test')"

    ]

    for query in tests:

        print(query)
        print("SAFE:", is_safe_query(query))
        print("-" * 50)