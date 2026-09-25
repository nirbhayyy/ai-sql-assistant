from executor import execuute_sql,save_history
from genrator import genrate_sql

question=input('ASK : ')
sql=genrate_sql(question)
print("\nGenerated SQL:\n")
print(sql)

df,t=execuute_sql(sql)
save=save_history(question,sql,t)

print("\nResult:\n")
print(df)

print(f"\nExecution Time: {t}s")