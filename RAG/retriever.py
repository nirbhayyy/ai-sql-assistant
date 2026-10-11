
import re


def retrieve_schema(question, schema):
    question = question.lower()
    relevant_tables = {}

    keywords = {
        "customer": [
            "customer", "customers", "client", "clients",
            "registration", "registrations", "registered",
            "registration date", "joined", "join", "signup",
            "signups", "users",
        ],
        "city": [
            "city", "cities", "location", "pune", "mumbai",
            "delhi", "bangalore", "hyderabad", "nagpur",
        ],
        "email": ["email", "mail"],
        "name": ["name", "names", "customer name"],
        "date": [
            "date", "year", "years", "month", "months",
            "day", "daily", "monthly", "yearly", "annual",
            "annually", "over time", "trend", "trends",
        ],
        "order": [
            "order", "orders", "ordered", "purchase",
            "purchases", "purchased", "bought",
        ],
        "quantity": ["quantity", "amount", "number", "total"],
        "product": ["product", "products", "item", "items"],
        "category": ["category", "categories", "type"],
        "price": ["price", "cost", "revenue", "spending"],
    }

    # Normalize question into whole-word tokens
    question_words = set(re.findall(r"[a-z0-9_]+", question))

    for table, columns in schema.items():
        table_name = table.lower()
        table_words = set(re.findall(r"[a-z0-9_]+", table_name))

        score = 0
        matched_columns = []

        # Match table names and their common singular forms
        if table_name in question:
            score += 5

        if table_words & question_words:
            score += 5

        # Semantic table aliases
        if table_name == "customers" and question_words & {
            "customer", "customers", "client", "clients",
            "registration", "registrations", "registered",
            "signup", "signups", "joined",
        }:
            score += 4

        if table_name == "orders" and question_words & {
            "order", "orders", "ordered", "purchase",
            "purchases", "purchased", "bought",
        }:
            score += 4

        if table_name == "products" and question_words & {
            "product", "products", "item", "items",
        }:
            score += 4

        for column in columns:
            column_name = column["column"].lower()
            column_words = set(re.findall(r"[a-z0-9_]+", column_name))

            # Direct column-name matching
            if column_name in question or column_words & question_words:
                score += 3
                matched_columns.append(column)
                continue

            # Semantic matching based on column name and data type
            data_type = column.get("type", "").lower()
            aliases = set()

            if column_name in {"join_date", "registration_date", "created_at"}:
                aliases.update({
                    "registration", "registrations", "registered",
                    "joined", "join", "signup", "signups",
                    "year", "years", "yearly", "annual", "annually",
                    "date", "trend", "trends",
                })

            if column_name in {"name", "customer_name", "p_name"}:
                aliases.update({"name", "names"})

            if column_name == "city":
                aliases.update({"city", "cities", "location"})

            if column_name in {"quantity"}:
                aliases.update({"quantity", "amount"})

            if column_name in {"price"}:
                aliases.update({"price", "cost"})

            if aliases & question_words:
                score += 2
                matched_columns.append(column)
                continue

            # Date columns should be retrieved for temporal questions
            if (
                data_type == "date"
                or data_type.startswith("timestamp")
            ) and question_words & {
                "date", "year", "years", "month", "months",
                "day", "daily", "monthly", "yearly", "annual",
                "annually", "registration", "registrations",
                "registered", "joined", "signup", "signups",
                "trend", "trends", "time",
            }:
                score += 2
                matched_columns.append(column)

            # Keyword matching for common column concepts
            for keyword, words in keywords.items():
                if column_name == keyword and question_words & set(words):
                    score += 2
                    if column not in matched_columns:
                        matched_columns.append(column)
                    break

        if score > 0:
            # Include all columns for selected tables so JOINs and
            # SQL validation have the complete table schema.
            relevant_tables[table] = {
                "score": score,
                "columns": columns,
            }

    # Sort tables by relevance while preserving the expected dictionary format
    relevant_tables = dict(
        sorted(
            relevant_tables.items(),
            key=lambda item: item[1]["score"],
            reverse=True,
        )
    )

    return relevant_tables
