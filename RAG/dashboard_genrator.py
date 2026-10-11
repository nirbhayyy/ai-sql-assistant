
from sqlalchemy import text
from .executor import engine
from .schema_analyzer import (
    get_primary_table,
    get_schema,
    detect_columns,
)


def genrate_dashboards():
    schema = get_schema(engine)

    table = get_primary_table(schema)
    info = detect_columns(schema)

    cols = info[table]

    cat = (
        cols["categorical"][-1]
        if cols["categorical"]
        else None
    )

    date = (
        cols["date"][0]
        if cols["date"]
        else None
    )

    # Table and column names come from inspected database schema.
    with engine.connect() as conn:

        # KPI
        total = conn.execute(
            text(f'SELECT COUNT(*) FROM "{table}"')
        ).scalar()

        # Pie chart
        pie = []

        if cat:
            pie = conn.execute(
                text(
                    f'''
                    SELECT "{cat}", COUNT(*) AS total
                    FROM "{table}"
                    GROUP BY "{cat}"
                    ORDER BY total DESC
                    LIMIT 10
                    '''
                )
            ).fetchall()

        # Line chart
        line = []

        if date:
            line = conn.execute(
                text(
                    f'''
                    SELECT EXTRACT(YEAR FROM "{date}") AS year,
                           COUNT(*) AS total
                    FROM "{table}"
                    WHERE "{date}" IS NOT NULL
                    GROUP BY year
                    ORDER BY year
                    '''
                )
            ).fetchall()

    return {
        "table": table,
        "total": total or 0,
        "pie": {
            "labels": [
                str(row[0]) if row[0] is not None else "Unknown"
                for row in pie
            ],
            "values": [row[1] for row in pie],
        },
        "line": {
            "labels": [str(int(row[0])) for row in line],
            "values": [row[1] for row in line],
        },
    }
