from RAG.executor import execuute_sql

sql = """
SELECT *
FROM customers
WHERE city='Pune'
LIMIT 5;
"""

df,t=execuute_sql(sql)
print(df)
print(f"EXecution time : {t}s")