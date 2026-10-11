from RAG.genrator import genrate_sql
from RAG.executor import execuute_sql, engine
from RAG.sql_validator import (
    is_sql_safe,
    validate_table,
    validate_columns
)
from RAG.schema_analyzer import get_schema


def run_pipeline(question):

    print("\nQUESTION")
    print("=" * 50)
    print(question)

    # ========================================================
    # 1. Generate SQL
    # ========================================================

    try:

        sql = genrate_sql(
            question,
            engine
        )

    except Exception as e:

        return {
            "success": False,
            "stage": "generation",
            "message": str(e)
        }

    print("\nGENERATED SQL")
    print("=" * 50)
    print(sql)

    # ========================================================
    # 2. Safety validation
    # ========================================================

    safe, message = is_sql_safe(sql)

    if not safe:

        return {
            "success": False,
            "stage": "safety",
            "message": message
        }

    # ========================================================
    # 3. Get schema
    # ========================================================

    schema = get_schema(engine)

    # ========================================================
    # 4. Table validation
    # ========================================================

    valid, message = validate_table(
        sql,
        schema
    )

    if not valid:

        return {
            "success": False,
            "stage": "table_validation",
            "message": message
        }

    # ========================================================
    # 5. Column validation
    # ========================================================

    valid, message = validate_columns(
        sql,
        schema
    )

    if not valid:

        return {
            "success": False,
            "stage": "column_validation",
            "message": message
        }

    # ========================================================
    # 6. Execute SQL
    # ========================================================

    try:

        df, execution_time = execuute_sql(sql)

        return {
            "success": True,
            "stage": "execution",
            "message": "Query executed successfully.",
            "sql": sql,
            "data": df,
            "execution_time": execution_time
        }

    except Exception as e:

        return {
            "success": False,
            "stage": "execution",
            "message": str(e)
        }


if __name__ == "__main__":

    question = "Show customer names, product names and quantities ordered"

    result = run_pipeline(question)

    print("\nRESULT")
    print("=" * 50)

    print("Success:", result["success"])
    print("Stage:", result["stage"])
    print("Message:", result["message"])

    if result["success"]:

        print("\nExecution Time:")
        print(result["execution_time"])

        print("\nData:")
        print(result["data"].head(10))

        print("\nTotal Rows:")
        print(len(result["data"]))