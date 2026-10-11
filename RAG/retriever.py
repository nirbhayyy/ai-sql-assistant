def retrieve_schema(question, schema):

    question = question.lower()

    relevant_tables = {}

    keywords = {
        "customer": ["customer", "customers", "client", "clients"],
        "city": ["city", "cities", "location", "pune", "mumbai", "delhi"],
        "email": ["email", "mail"],
        "name": ["name", "customer name"],
        "date": ["date", "year", "month", "day"],
        "order": ["order", "orders", "ordered"],
        "quantity": ["quantity", "amount", "number"],
        "product": ["product", "products", "item", "items"],
        "category": ["category", "categories", "type"],
        "price": ["price", "cost", "revenue", "spending"],
    }

    for table, columns in schema.items():

        score = 0
        matched_columns = []

        

        table_name = table.lower()

        if table_name in question:
            score += 5

        

        for column in columns:

            column_name = column["column"].lower()

            # Direct column match
            if column_name in question:
                score += 3

                matched_columns.append(column)

                continue

            # Keyword match
            for keyword, words in keywords.items():

                if column_name == keyword:

                    if any(word in question for word in words):
                        score += 2

                        matched_columns.append(column)

                        break

        

        if score > 0:

            relevant_tables[table] = {
                "score": score,
                "columns": matched_columns
            }

    return relevant_tables