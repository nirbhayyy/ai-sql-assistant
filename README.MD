# AI SQL Assistant

An AI-powered application that helps users interact with relational databases using natural-language questions. The project combines Django REST Framework, PostgreSQL, Retrieval-Augmented Generation (RAG), and large language models to support natural-language-to-SQL workflows.

## Overview

AI SQL Assistant aims to simplify database querying by allowing users to ask questions in plain English instead of writing SQL manually.

The application uses database schema context and semantic retrieval to help an LLM generate relevant SQL queries.

## Key Features

- Natural-language-to-SQL generation
- Retrieval-Augmented Generation (RAG) for schema-aware query generation
- Database connection management
- Database schema analysis and relationship identification
- SQL query execution through a dedicated execution layer
- Credential encryption utilities
- Dashboard generation capabilities

*Feature availability depends on the current implementation and configuration.*

## Technology Stack

**Backend**
- Python
- Django
- Django REST Framework

**Database**
- PostgreSQL
- SQLAlchemy

**AI and Retrieval**
- Large Language Models (LLMs)
- LangChain components, where used
- Sentence Transformers
- FAISS vector search

**Frontend**
- HTML
- CSS
- JavaScript

## Architecture

The application follows a workflow that connects the API, retrieval pipeline, SQL generation, and database execution.

1. The user submits a natural-language question.
2. The application identifies the relevant database context.
3. The RAG pipeline retrieves useful schema information.
4. The LLM generates a SQL query using the question and retrieved context.
5. The query passes through the application's validation and safety checks.
6. The execution layer runs permitted queries against the connected database.
7. The application returns the results to the user.

## Project Structure

```text
AI SQL Assistant/
├── config/                  # Django project configuration
├── sql_api/                 # API, frontend assets, and application logic
├── RAG/                     # Retrieval and SQL-generation components
│   ├── README.md            # RAG module documentation
│   ├── embedder.py
│   ├── retriever.py
│   ├── generator.py
│   ├── executor.py
│   └── faiss_index/
├── manage.py
├── .gitignore
└── README.md
```

This is a simplified overview; consult the repository for the complete structure.

## Getting Started

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd <your-repository-folder>
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it in PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

If a `requirements.txt` file is provided:

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a local `.env` file in the project root. Configure the variables required by your application, including:

```dotenv
DJANGO_SECRET_KEY=replace-with-a-generated-secret
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_HOST=localhost
DB_PORT=5432
```

Add any LLM API keys or additional configuration required by your implementation.

**Never commit your actual `.env` file, API keys, Django secret key, or database credentials.**

### 5. Run Django Checks

```bash
python manage.py check
```

### 6. Start the Development Server

```bash
python manage.py runserver
```

Use the API routes configured in your Django application to access its functionality.

## RAG Module

The RAG module contains components for schema analysis, document processing, embeddings, semantic retrieval, SQL generation, and query execution.

See [`RAG/README.md`](RAG/README.md) for details about the retrieval pipeline and its components.

## Security Considerations

- Keep secrets and database credentials in environment variables.
- Validate generated SQL before execution.
- Apply least-privilege database permissions.
- Restrict potentially destructive SQL operations according to application policy.
- Load serialized vector-store artifacts only from trusted sources.

## Future Improvements

- Extend support to additional relational database engines.
- Improve SQL-generation accuracy using schema-aware retrieval.
- Expand automated tests.
- Improve query validation, error handling, and execution controls.
- Make vector-index generation reproducible.

## Project Status

This project is under active development. Features and setup requirements may change as the implementation evolves.