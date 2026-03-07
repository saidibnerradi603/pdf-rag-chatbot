<p align="center">
  <h1 align="center">PDF RAG QA System — Backend</h1>
  <p align="center">
    <em>FastAPI backend for PDF ingestion, vector search, and AI-powered conversational Q&A</em>
  </p>
</p>



## Overview

REST API that powers the **PDF RAG QA System**. Handles user authentication, PDF document management, a full RAG ingestion pipeline (parse → chunk → embed → store), semantic vector search, and **real-time streamed conversations** with an AI assistant grounded in document content.



## Tech Stack

| Category | Technology |
|---|---|
| **Framework** | FastAPI 0.119 |
| **Language** | Python 3.13+ |
| **Validation** | Pydantic v2 |
| **Database** | Supabase (PostgreSQL + pgvector) |
| **File Storage** | Supabase Storage |
| **Auth** | Supabase Auth + JWT (ES256 / JWKS) |
| **PDF Parsing** | LlamaParse |
| **Embeddings** | Cohere embed-english-v3.0 |
| **LLM** | Google Gemini 2.5 Flash |
| **Orchestration** | LangChain 0.3 |
| **HTTP Server** | Uvicorn |
| **Package Manager** | uv |


## Project Structure

```
backend/
├── .env.example              # Environment variable template
├── pyproject.toml             # Project dependencies & metadata
├── requirements.txt           # Pip-compatible dependency list
│
└── src/
    ├── main.py                # FastAPI app entry point, CORS, health check
    ├── core/
    │   ├── config.py          # Pydantic Settings (env vars, app config)
    │   └── clients.py         # Singleton factories (Supabase, LlamaParse, Cohere, Gemini)
    ├── api/
    │   ├── dependencies.py    # DI container: JWT auth, service factories
    │   └── v1/
    │       ├── router.py      # Central API router
    │       └── endpoints/     # auth, document, parse, chunk, embed, process, retrieve, chat
    ├── schemas/               # Pydantic request/response models
    ├── services/              # Business logic (auth, document, parse, chunk, embed, process, retrieval, chat)
    ├── sql/
    │   └── db.sql             # Full DB schema, RLS policies, vector search function
    └── utils/
        └── file_utils.py      # File validation, SHA-256 hashing
```



## Key Features

- **JWT Authentication** — signup/login with JWKS-based ES256 token verification
- **PDF Upload** — file validation, size limits (5 MB), SHA-256 duplicate detection
- **RAG Ingestion Pipeline** — parse (LlamaParse) → chunk (header-aware + recursive) → embed (Cohere) → store (pgvector)
- **Vector Search** — cosine similarity via `match_documents` RPC with HNSW index
- **Conversational RAG** — context-grounded answers with citations using Gemini 2.5 Flash
- **SSE Streaming** — token-by-token streamed responses via Server-Sent Events
- **Row Level Security** — all tables enforce per-user data isolation
- **Swagger & ReDoc** — auto-generated interactive API docs



## API Endpoints

| Group | Prefix | Endpoints |
|---|---|---|
| **Auth** | `/api/v1/auth` | signup, login, refresh, me, logout |
| **Documents** | `/api/v1/documents` | upload, list, get, status, download, delete |
| **Processing** | `/api/v1/documents` | process, parse, chunk, embed, retrieve |
| **Chat** | `/api/v1/conversations` | create, list, history, chat, chat/stream, delete |



## Environment Variables

Create a `.env` file based on `.env.example`:

```env
GOOGLE_API_KEY=your_google_api_key
COHERE_API_KEY=your_cohere_api_key
LLAMA_CLOUD_API_KEY=your_llama_cloud_api_key
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your_supabase_service_role_key
BACKEND_CORS_ORIGIN=http://localhost:3000
```



## Getting Started

```bash
# Install dependencies with uv (recommended)
uv sync

# Or with pip
pip install -r requirements.txt

# Start the server (port 8000)
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

API docs available at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

> Make sure to run `src/sql/db.sql` in your Supabase SQL Editor before starting.


