# RAG Module — AI SQL Assistant

## Overview

The RAG (Retrieval-Augmented Generation) module is a core component of the AI SQL Assistant. It helps the application understand database schemas and relationships so that an LLM can generate SQL queries based on natural-language questions.

The module combines schema analysis, document processing, vector embeddings, semantic retrieval, and SQL generation to support natural-language interaction with relational databases.

## Architecture

The RAG workflow follows these steps:

1. **Schema Extraction:** Retrieves database schema information, including tables, columns, and relationships.
2. **Schema Analysis:** Analyzes database metadata and identifies relationships between tables.
3. **Document Preparation:** Converts schema information into text documents and splits them into manageable chunks.
4. **Embedding Generation:** Converts document chunks into vector representations using a sentence-transformer embedding model.
5. **Vector Indexing:** Stores the embeddings in a FAISS vector index for efficient similarity search.
6. **Semantic Retrieval:** Retrieves relevant schema context based on the user's natural-language question.
7. **SQL Generation:** Supplies the retrieved context to an LLM to generate an SQL query.
8. **Query Execution:** Passes the generated query to the database execution layer, subject to the application's validation and safety checks.

## Directory Structure

```text
RAG/
├── app.py
├── credential_encryption.py
├── dashboard_generator.py
├── database_connection.py
├── embedder.py
├── executor.py
├── generator.py
├── loader.py
├── metadata.json
├── relationship_analyzer.py
├── retriever.py
├── schema.sql
├── schema_analyzer.py
├── splitter.py
├── user_database.py
├── faiss_index/
│   ├── index.faiss
│   └── index.pkl
└── README.MD
```

## Core Components

| Component | Responsibility |
|---|---|
| `app.py` | RAG application entry point or orchestration |
| `database_connection.py` | Database connection handling |
| `user_database.py` | User database-related functionality |
| `credential_encryption.py` | Database credential encryption utilities |
| `loader.py` | Loads schema or source information |
| `schema_analyzer.py` | Analyzes database schema information |
| `relationship_analyzer.py` | Identifies relationships between tables |
| `splitter.py` | Splits schema documents into smaller chunks |
| `embedder.py` | Generates vector embeddings |
| `retriever.py` | Retrieves relevant context from the vector store |
| `generator.py` | Generates SQL using an LLM |
| `executor.py` | Executes validated SQL queries |
| `dashboard_generator.py` | Supports dashboard generation |
| `schema.sql` | SQL schema reference |
| `metadata.json` | Stores metadata used by the application |
| `faiss_index/` | Stores the FAISS index and associated document data |

*Note: Component descriptions are based on the filenames and intended architecture. Adjust them if the implementation in your code differs.*

## Technology Stack

- **Python** — core implementation
- **LangChain** — document processing and vector-store integration, where used
- **Sentence Transformers** — text embedding generation
- **FAISS** — vector similarity search
- **PostgreSQL** — relational database integration
- **Large Language Models (LLMs)** — natural-language-to-SQL generation
- **Django REST Framework** — API integration with the main application

## How It Works

**Example question:**

> Show all customers from Pune.

The RAG module retrieves relevant schema context, such as the `customers` table and its `city` column. The SQL generation component can then produce a query similar to:

```sql
SELECT *
FROM customers
WHERE city = 'Pune';
```

The application should validate the generated SQL and apply its execution policies before running it against the connected database.

## Vector Index

The `faiss_index/` directory contains the saved FAISS vector index and associated serialized document data.

If the underlying schema or embedding configuration changes, regenerate the index using the project's embedding and indexing workflow.

Only load serialized index files from trusted sources. The index should be reproducible from the source schema and document-processing pipeline.

## Security Considerations

- Store database credentials and Django secrets in environment variables.
- Never commit `.env` files or real database credentials.
- Validate generated SQL before execution.
- Apply database permissions and query restrictions appropriate to the application.
- Avoid loading serialized vector-store files from untrusted sources.

## Future Improvements

- Support additional relational databases.
- Improve schema-aware SQL generation.
- Add more comprehensive SQL validation and error handling.
- Make vector-index generation reproducible.
- Expand automated testing for retrieval and query generation.

## Project

**AI SQL Assistant** — a natural-language interface for querying relational databases using retrieval-augmented generation and large language models.