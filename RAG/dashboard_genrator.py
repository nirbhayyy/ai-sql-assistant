from sqlalchemy import text
from .executor import engine
from .schema_analyzer import get_primary_table,get_schema,detect_columns

def genrate_dashboards():
    schema=get_schema()
    table=get_primary_table(schema)
    info=detect_columns(schema)

    cols=info[table]

    cat=cols['categorical'][-1] if cols['categorical'] else None
    date=cols['date'][0] if cols['date'] else None

    with engine.connect() as conn:

        # KPI
        total = conn.execute(
            text(f"SELECT COUNT(*) FROM {table}")
        ).scalar()

        # Pie
        pie = []

        if cat:

            pie = conn.execute(text(f"""
                SELECT {cat},
                       COUNT(*) AS total
                FROM {table}
                GROUP BY {cat}
                ORDER BY total DESC
            """)).fetchall()

        # Line
        line = []

        if date:

            line = conn.execute(text(f"""
                SELECT
                    EXTRACT(YEAR FROM {date}) AS year,
                    COUNT(*) AS total
                FROM {table}
                GROUP BY year
                ORDER BY year
            """)).fetchall()

    return {

        "table": table,

        "total": total,

        "pie": {
            "labels": [r[0] for r in pie],
            "values": [r[1] for r in pie]
        },

        "line": {
            "labels": [str(int(r[0])) for r in line],
            "values": [r[1] for r in line]
        }
    }