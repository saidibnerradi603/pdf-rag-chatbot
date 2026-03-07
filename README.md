<p align="center">
  <h1 align="center">PDF RAG QA System</h1>
  <p align="center">
    <em>Full-stack Retrieval-Augmented Generation system for intelligent question answering over PDF documents</em>
  </p>
  <p align="center">
    <img src="https://img.shields.io/badge/Python-3.13+-3776AB?logo=python&logoColor=white" alt="Python" />
    <img src="https://img.shields.io/badge/FastAPI-0.119-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
    <img src="https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=white" alt="React" />
    <img src="https://img.shields.io/badge/Vite-7-646CFF?logo=vite&logoColor=white" alt="Vite" />
    <img src="https://img.shields.io/badge/LangChain-0.3-1C3C3C?logo=langchain&logoColor=white" alt="LangChain" />
    <img src="https://img.shields.io/badge/Supabase-PostgreSQL-3FCF8E?logo=supabase&logoColor=white" alt="Supabase" />
    <img src="https://img.shields.io/badge/Gemini_2.5_Flash-LLM-4285F4?logo=google&logoColor=white" alt="Gemini" />
    <img src="https://img.shields.io/badge/pgvector-Vector_Search-336791?logo=postgresql&logoColor=white" alt="pgvector" />
    <img src="https://img.shields.io/badge/Cohere-Embeddings-39594D?logo=cohere&logoColor=white" alt="Cohere" />
    <img src="https://img.shields.io/badge/LlamaParse-V2-6B4EFF?logo=Ollama&logoColor=white" alt="LlamaParse" />
    <img src="https://img.shields.io/badge/Pydantic-v2-E92063?logo=pydantic&logoColor=white" alt="Pydantic"/>

  </p>
</p>



## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [RAG Pipeline Workflow](#rag-pipeline-workflow)
- [API Request Lifecycle](#api-request-lifecycle)
- [Database Schema](#database-schema)
- [API Reference](#api-reference)
  - [Authentication](#authentication-endpoints)
  - [Documents](#document-endpoints)
  - [Processing & Semantic Search Endpoints](#processing--semantic-search-endpoints)
  - [Conversations & Chat](#conversation--chat-endpoints)
- [AI / LLM Integrations](#ai--llm-integrations)
- [Security & Middleware](#security--middleware)
- [Environment Configuration](#environment-configuration)
- [Getting Started](#getting-started)



## Overview

A  **PDF-based Retrieval-Augmented Generation (RAG)** system that allows users to:

1. **Upload** PDF documents to cloud storage  
2. **Process** them through an automated ingestion pipeline (parse → chunk → embed → store)  
3. **Chat** with their documents using an AI assistant grounded in the document's content  
4. **Receive cited answers** with source references and similarity scores  

The **backend** (FastAPI) leverages **LlamaParse** for PDF parsing, **Cohere** for semantic embeddings, **Google Gemini 2.5 Flash** for conversational AI, and **Supabase** (PostgreSQL + pgvector) as the unified backend for authentication, storage, and vector search.

The **frontend** (React 19 + Vite) provides a modern SPA with drag-and-drop PDF upload, real-time SSE streaming chat, rich Markdown rendering (GFM, LaTeX, syntax highlighting), and animated UI powered by Framer Motion.



## System Architecture

```mermaid
graph TB
    Client["React Frontend"]

    Client -->|HTTP / SSE| MW

    subgraph Backend["FastAPI Backend"]
        MW["CORS Middleware"]
        MW --> JWT["JWT Auth"]

        JWT --> AuthEP["Auth Routes"]
        JWT --> DocEP["Document Routes"]
        JWT --> ProcEP["Process Route"]
        JWT --> RetEP["Retrieval Route"]
        JWT --> ChatEP["Chat Routes"]

        AuthEP --> AuthSvc["AuthService"]
        DocEP --> DocSvc["DocumentService"]
        ProcEP --> ProcSvc["ProcessService"]
        RetEP --> RetSvc["RetrievalService"]
        ChatEP --> ChatSvc["ChatService"]

        ProcSvc --> ParseSvc["ParseService"]
        ProcSvc --> ChunkSvc["ChunkService"]
        ProcSvc --> EmbedSvc["EmbedService"]

        ChatSvc --> RetSvc
    end

    AuthSvc --> SB_Auth["Supabase Auth"]
    DocSvc --> SB_Store["Supabase Storage </ br> (PDFs)"]
    DocSvc --> SB_DB["Supabase PostgreSQL + </ br> pgvector"]
    ParseSvc --> Llama["LlamaParse </ br> (PDF → Markdown)"]
    EmbedSvc --> Cohere["Cohere </ br> (embed-english-v3.0)"]
    EmbedSvc --> SB_DB
    RetSvc --> Cohere
    RetSvc --> SB_DB
    ChatSvc --> Gemini["Gemini 2.5 Flash"]
    ChatSvc --> SB_DB

    %% Styling
    style Client fill:#4A90E2,stroke:#2E5C8A,stroke-width:2px,color:#FFFFFF
    style Backend fill:#F8F9FA,stroke:#6C63FF,stroke-width:3px,color:#2C3E50

    style MW fill:#9B59B6,stroke:#6C3483,stroke-width:2px,color:#FFFFFF
    style JWT fill:#8E44AD,stroke:#6C3483,stroke-width:2px,color:#FFFFFF

    style AuthEP fill:#3498DB,stroke:#2874A6,stroke-width:2px,color:#FFFFFF
    style DocEP fill:#3498DB,stroke:#2874A6,stroke-width:2px,color:#FFFFFF
    style ProcEP fill:#3498DB,stroke:#2874A6,stroke-width:2px,color:#FFFFFF
    style RetEP fill:#3498DB,stroke:#2874A6,stroke-width:2px,color:#FFFFFF
    style ChatEP fill:#3498DB,stroke:#2874A6,stroke-width:2px,color:#FFFFFF

    style AuthSvc fill:#5DADE2,stroke:#3498DB,stroke-width:2px,color:#FFFFFF
    style DocSvc fill:#5DADE2,stroke:#3498DB,stroke-width:2px,color:#FFFFFF
    style ProcSvc fill:#5DADE2,stroke:#3498DB,stroke-width:2px,color:#FFFFFF
    style ParseSvc fill:#85C1E9,stroke:#5DADE2,stroke-width:2px,color:#000000
    style ChunkSvc fill:#85C1E9,stroke:#5DADE2,stroke-width:2px,color:#000000
    style EmbedSvc fill:#85C1E9,stroke:#5DADE2,stroke-width:2px,color:#000000
    style RetSvc fill:#5DADE2,stroke:#3498DB,stroke-width:2px,color:#FFFFFF
    style ChatSvc fill:#5DADE2,stroke:#3498DB,stroke-width:2px,color:#FFFFFF

    style SB_Auth fill:#50C878,stroke:#2D7A4A,stroke-width:2px,color:#FFFFFF
    style SB_Store fill:#50C878,stroke:#2D7A4A,stroke-width:2px,color:#FFFFFF
    style SB_DB fill:#50C878,stroke:#2D7A4A,stroke-width:2px,color:#FFFFFF
    style Llama fill:#E67E22,stroke:#A04000,stroke-width:2px,color:#FFFFFF
    style Cohere fill:#E67E22,stroke:#A04000,stroke-width:2px,color:#FFFFFF
    style Gemini fill:#E67E22,stroke:#A04000,stroke-width:2px,color:#FFFFFF
```



## Tech Stack

### Backend

| Layer | Technology | Purpose |
|---|---|---|
| **Framework** | FastAPI 0.119 | Async REST API with auto-generated OpenAPI docs |
| **Language** | Python 3.13+ | Runtime |
| **Validation** | Pydantic v2 | Request/response schemas with field validation |
| **Settings** | Pydantic Settings | Environment-based configuration (`.env`) |
| **Database** | Supabase (PostgreSQL) | Relational data, RLS-secured tables |
| **Vector Store** | pgvector (via Supabase) | 1024-dim embeddings with HNSW cosine index |
| **File Storage** | Supabase Storage | PDF bucket with per-user folder isolation |
| **Auth** | Supabase Auth + JWT (ES256) | User sign-up/login, JWKS-based token verification |
| **PDF Parsing** | LlamaParse  | Parse PDFs into Markdown,JSON,Text for use in LLM and RAG pipelines |
| **Embeddings** | Cohere `embed-english-v3.0` | 1024-dimensional semantic embeddings |
| **LLM** | Google Gemini 2.5 Flash | Conversational RAG with streaming support |
| **Orchestration** | LangChain 0.3 | Prompt templates, text splitters, model abstraction |
| **HTTP Server** | Uvicorn | ASGI server |
| **Package Manager** | uv | Fast Python package management |

### Frontend

| Layer | Technology | Purpose |
|---|---|---|
| **UI Framework** | React 19 | Component-based SPA |
| **Build Tool** | Vite 7 | Fast dev server with HMR |
| **Routing** | React Router v7 | Client-side routing with auth guards |
| **HTTP Client** | Axios | API calls with auto-refresh interceptor |
| **Streaming** | Fetch + ReadableStream | SSE-based real-time chat |
| **Animations** | Framer Motion | Page transitions and micro-interactions |
| **Markdown** | react-markdown + rehype-katex + remark-gfm | Rich AI response rendering |
| **Styling** | Vanilla CSS | Custom properties-based design system |



## Project Structure

```
pdf_RAG_App/
│
├── backend/
│   ├── .env.example              # Environment variable template
│   ├── pyproject.toml             # Project dependencies & metadata
│   ├── requirements.txt           # Pip-compatible dependency list
│   └── src/
│       ├── main.py                # FastAPI app entry point, CORS, health check
│       ├── core/
│       │   ├── config.py          # Pydantic Settings (env vars, app config)
│       │   └── clients.py         # Singleton factories (Supabase, LlamaParse, Cohere, Gemini)
│       ├── api/
│       │   ├── dependencies.py    # DI container: JWT auth, service factories
│       │   └── v1/
│       │       ├── router.py      # Central API router (wires all endpoints)
│       │       └── endpoints/     # auth, document, parse, chunk, embed, process, retrieve, chat
│       ├── schemas/               # Pydantic request/response models
│       ├── services/              # Business logic (auth, document, parse, chunk, embed, process, retrieval, chat)
│       ├── sql/
│       │   └── db.sql             # Full DB schema, RLS policies, vector search function
│       └── utils/
│           └── file_utils.py      # File validation, SHA-256 hashing
│
└── frontend/
    ├── .env                       # VITE_API_BASE_URL
    ├── package.json               # Dependencies & scripts
    ├── vite.config.js             # Vite config with dev proxy to backend
    └── src/
        ├── main.jsx               # App bootstrap (Router, AuthProvider, Toaster)
        ├── App.jsx                # Route definitions + auth guards
        ├── index.css              # Global styles & design tokens
        ├── api/                   # Axios client, auth, documents, conversations, SSE stream
        ├── context/               # AuthContext (user state, login, logout, auto-refresh)
        ├── hooks/                 # useChat, useConversations, useDocuments, useProcessing
        ├── pages/                 # LoginPage, SignupPage, DashboardPage
        ├── components/            # auth, chat, documents, layout, ui
        └── utils/                 # Date helpers, error extraction
```



## RAG Pipeline Workflow

### Ingestion Pipeline

```mermaid
    flowchart TB
    A["Upload PDF"] --> B["Validate & Store"]
    B --> C["Process Pipeline"]
    
    C --> Pipeline
    
    subgraph Pipeline["ProcessService.run_pipeline()"]
        direction TB
        P1["1.Validate Status <br/>(reject if <br/> processing/completed)"]
        P2["2.Mark as 'processing'"]
        P3["3.Parse PDF<br/>(LlamaParse → Markdown)"]
        P4["4.Chunk Markdown<br/>(Header-aware + <br> Recursive split)"]
        P5["5.Embed Chunks<br/>Cohere embed-english-v3.0"]
        P6["6.Store Vectors<br/>pgvector in Supabase"]
        P7["7.Mark as 'completed'"]
        
        P1 --> P2 --> P3 --> P4 --> P5 --> P6 --> P7
    end
    
    Pipeline --> D["Ready for Chat"]
    
    %% Modern Color Palette
    style A fill:#4A90E2,stroke:#2E5C8A,stroke-width:2px,color:#FFFFFF
    style B fill:#50C878,stroke:#2D7A4A,stroke-width:2px,color:#FFFFFF
    style C fill:#9B59B6,stroke:#6C3483,stroke-width:2px,color:#FFFFFF
    style D fill:#E67E22,stroke:#A04000,stroke-width:2px,color:#FFFFFF
    
    style P1 fill:#3498DB,stroke:#2874A6,stroke-width:2px,color:#FFFFFF
    style P2 fill:#5DADE2,stroke:#3498DB,stroke-width:2px,color:#FFFFFF
    style P3 fill:#85C1E9,stroke:#5DADE2,stroke-width:2px,color:#000000
    style P4 fill:#AED6F1,stroke:#85C1E9,stroke-width:2px,color:#000000
    style P5 fill:#D6EAF8,stroke:#AED6F1,stroke-width:2px,color:#000000
    style P6 fill:#5DADE2,stroke:#3498DB,stroke-width:2px,color:#FFFFFF
    style P7 fill:#28B463,stroke:#1E8449,stroke-width:2px,color:#FFFFFF
    
    style Pipeline fill:#F8F9FA,stroke:#6C63FF,stroke-width:3px,color:#2C3E50
```
### Query Pipeline
```mermaid
graph LR
    subgraph Query["Query Pipeline"]
        UQ["User Question"]
        QE["Cohere Embeddings<br/>(Query Embedding)"]
        VS["Vector Search<br/>(match_documents RPC)"]
        PM["Prompt Builder<br/>(LangChain ChatPromptTemplate)"]
        LLM["Google Gemini 2.5 Flash<br/>(streaming capable)"]
        
        UQ -->|Text| QE
        QE -->|Query Vector| VS
        VS -->|Top-K Chunks| PM
        UQ -->|Question| PM
        PM -->|Formatted Messages| LLM
        LLM -->|AI Response| RES["Response + Citations"]
    end
    
    %% Professional Color Palette
    style Query fill:#e3f2fd,stroke:#2196f3,stroke-width:3px,color:#0d47a1
    
    style UQ fill:#64b5f6,stroke:#42a5f5,stroke-width:2px,color:#ffffff
    style QE fill:#42a5f5,stroke:#2196f3,stroke-width:2px,color:#ffffff
    style VS fill:#2196f3,stroke:#1e88e5,stroke-width:2px,color:#ffffff
    style PM fill:#1e88e5,stroke:#1976d2,stroke-width:2px,color:#ffffff
    style LLM fill:#1976d2,stroke:#1565c0,stroke-width:2px,color:#ffffff
    style RES fill:#1565c0,stroke:#0d47a1,stroke-width:2px,color:#ffffff
```


## API Request Lifecycle

```mermaid
sequenceDiagram
    actor User
    participant Client as Frontend
    participant API as FastAPI
    participant Auth as JWT / JWKS
    participant DI as Dependencies
    participant Svc as Service Layer
    participant DB as Supabase DB
    participant AI as AI Services

    User->>Client: Interact with UI
    Client->>API: HTTP Request + Bearer Token
    API->>Auth: Validate JWT (ES256 via JWKS)
    Auth-->>API: UserResponse (id, email)
    API->>DI: Resolve service dependencies
    DI-->>API: Injected service instance
    API->>Svc: Call business logic
    
    alt Document Operations
        Svc->>DB: Query/Insert/Delete
        DB-->>Svc: Result
    else RAG Chat
        Svc->>AI: Embed query (Cohere)
        AI-->>Svc: Query vector
        Svc->>DB: RPC match_documents()
        DB-->>Svc: Relevant chunks
        Svc->>AI: LLM invoke (Gemini)
        AI-->>Svc: AI response
        Svc->>DB: Save message + citations
    end
    
    Svc-->>API: Response model
    API-->>Client: JSON / SSE stream
    Client-->>User: Display result
```



## Database Schema

The database uses **5 core tables** with Row Level Security (RLS) enforced on all tables:

```mermaid
erDiagram
    USERS ||--o{ DOCUMENTS : owns
    USERS ||--o{ CONVERSATIONS : owns
    DOCUMENTS ||--o{ CHUNKS : contains
    DOCUMENTS ||--o{ CONVERSATIONS : "discussed in"
    CONVERSATIONS ||--o{ MESSAGES : contains
    MESSAGES ||--o{ CITATIONS : references
    CHUNKS ||--o{ CITATIONS : "cited by"

    USERS {
        uuid id PK
    }

    DOCUMENTS {
        uuid id PK
        uuid user_id FK
        text file_name
        text bucket_path
        text status "pending | processing | completed | failed"
        text file_hash "SHA-256"
        jsonb metadata
        timestamptz created_at
        timestamptz updated_at
    }

    CHUNKS {
        uuid id PK
        uuid document_id FK
        text content
        jsonb metadata "file_name, page_number"
        vector_1024 embedding "Cohere embed-english-v3.0"
        timestamptz created_at
    }

    CONVERSATIONS {
        uuid id PK
        uuid user_id FK
        uuid document_id FK
        text title "auto-generated from first message"
        timestamptz created_at
    }

    MESSAGES {
        uuid id PK
        uuid conversation_id FK
        text role "user | assistant"
        text content
        timestamptz created_at
    }

    CITATIONS {
        uuid id PK
        uuid message_id FK
        uuid chunk_id FK
        text cited_text
        jsonb metadata
        float similarity_score
        timestamptz created_at
    }
```

### Key Database Features

- **`pgvector` extension** — Enables native vector storage and similarity search  
- **HNSW index** — Approximate nearest-neighbor index on `chunks.embedding` using cosine distance  
- **`match_documents()` RPC** — Server-side function for cosine-similarity search scoped to a specific document and user  
- **Row Level Security** — Every table has RLS policies ensuring users can only access their own data  
- **Storage Policies** — PDF bucket uses folder-based isolation (`{user_id}/...`)  
- **Cascade Deletes** — Deleting a document cascades to chunks, conversations, messages, and citations  
- **Auto-updated timestamps** — Trigger on `documents` updates `updated_at` automatically  

## API Reference

All endpoints are prefixed with `/api/v1`. Interactive docs are available at `/docs` (Swagger) and `/redoc` (ReDoc).

### Health & Root

| Method | Endpoint  | Description |
|---|---|---|
| `GET` | `/`  | Root endpoint — returns welcome message and links |
| `GET` | `/health`  | Health check — returns service status and version |



### Authentication Endpoints

**Prefix:** `/api/v1/auth`

| Method | Endpoint  | Description |
|---|---|---|
| `POST` | `/signup`  | Register a new user (email + strong password) |
| `POST` | `/login`  | Authenticate, returns JWT access token + refresh cookie |
| `POST` | `/refresh`  | Exchange refresh cookie for a new access token |
| `GET` | `/me`  | Get current user profile |
| `POST` | `/logout`  | Clear refresh token cookie |




### Document Endpoints

**Prefix:** `/api/v1/documents`

| Method | Endpoint  | Description |
|---|---|---|
| `POST` | `/upload`  | Upload a PDF (max 5 MB, hash-based duplicate detection) |
| `GET` | `/`  | List documents (filterable by status, paginated) |
| `GET` | `/{document_id}`  | Get document metadata |
| `GET` | `/{document_id}/status`  | Poll processing status (lightweight) |
| `GET` | `/{document_id}/download`  | Generate a pre-signed download URL (configurable expiry) |
| `DELETE` | `/{document_id}`  | Delete document + storage file (cascades to all related data) |




### Processing & Semantic Search Endpoints

**Prefix:** `/api/v1/documents`

| Method | Endpoint  | Description |
|---|---|---|
| `POST` | `/{document_id}/process` |  Run the full **parse → chunk → embed** pipeline |
| `POST` | `/{document_id}/parse` |  Parse PDF via LlamaParse (individual step) |
| `POST` | `/chunk` |  Split markdown into semantic chunks (individual step) |
| `POST` | `/{document_id}/embed` |  Embed chunks & store vectors (individual step) |
| `POST` | `/{document_id}/retrieve` |  Run semantic vector search over embedded chunks |




### Conversation & Chat Endpoints

**Prefix:** `/api/v1/conversations`

| Method | Endpoint |  Description |
|---|---|---|
| `POST` | `/`  | Create a new conversation for a processed document |
| `GET` | `/`  | List all user conversations |
| `GET` | `/{conversation_id}/history`  | Get full message history with citations |
| `POST` | `/{conversation_id}/chat`  | Send a message, get a grounded AI response |
| `POST` | `/{conversation_id}/chat/stream`  | Same as chat, but **streamed via SSE** |
| `DELETE` | `/{conversation_id}`  | Delete conversation and all messages |




## AI / LLM Integrations


| Service | Provider | Model / Config | Purpose |
|---|---|---|---|
| **PDF Parsing** | LlamaParse  | Tiers: `fast`, `cost_effective`, `agentic`, `agentic_plus` | Converts PDF to structured Markdown or Text |
| **Embeddings** | Cohere | `embed-english-v3.0` (1024 dims) | Generates semantic vectors for chunks and queries |
| **Chat LLM** | Google Gemini | `gemini-2.5-flash` (temp=0.2, streaming) | Generates grounded answers with citations |
| **Prompt Engineering** | LangChain | `ChatPromptTemplate` + `MessagesPlaceholder` | RAG prompt with context, history, and formatting instructions |



## Security & Middleware

### Authentication Flow

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI
    participant JWKS as Supabase JWKS Endpoint
    participant SupaAuth as Supabase Auth

    Note over Client,SupaAuth: Login Flow
    Client->>FastAPI: POST /auth/login {email, password}
    FastAPI->>SupaAuth: sign_in_with_password()
    SupaAuth-->>FastAPI: {access_token, refresh_token}
    FastAPI-->>Client: Body: {access_token} + Set-Cookie: refresh_token

    Note over Client,SupaAuth: Protected Request
    Client->>FastAPI: GET /documents (Authorization: Bearer {token})
    FastAPI->>JWKS: Fetch signing key
    JWKS-->>FastAPI: ES256 public key
    FastAPI->>FastAPI: jwt.decode(token, key, alg=ES256, aud=authenticated)
    FastAPI-->>Client: 200 OK + data
```

### Security Layers

| Layer | Implementation | Details |
|---|---|---|
| **JWT Validation** | PyJWT + JWKS (ES256) | Tokens verified against Supabase's JWKS endpoint with audience/issuer checks |
| **CORS** | `CORSMiddleware` | Origins restricted to `BACKEND_CORS_ORIGIN`, credentials enabled |
| **Row Level Security** | PostgreSQL RLS policies | Every table enforces `auth.uid() = user_id` — users can only access their own data |
| **Storage Isolation** | Folder-based bucket policies | Files stored under `{user_id}/` path, policies enforce folder ownership |
| **Password Validation** | Pydantic `field_validator` | Enforces complexity requirements (uppercase, lowercase, digit, special) |
| **File Validation** | `validate_file()` utility | MIME type check, extension check, size limit (5 MB), empty file rejection |
| **Duplicate Detection** | SHA-256 hash check | Prevents re-uploading identical PDFs |
| **Refresh Token Security** | HttpOnly, Secure, SameSite=None cookie | 7-day TTL, scoped to `/api/v1/auth/refresh`, rotated on each use |



## Environment Configuration

### Backend (`backend/.env`)

```env
# ──── AI Service Keys ────
GOOGLE_API_KEY=your_google_api_key           # Google Gemini API key
COHERE_API_KEY=your_cohere_api_key           # Cohere embeddings API key
LLAMA_CLOUD_API_KEY=your_llama_cloud_api_key # LlamaParse API key

# ──── Supabase ────
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your_supabase_service_role_key

# ──── CORS ────
BACKEND_CORS_ORIGIN=http://localhost:3000    # Frontend URL
```

### Frontend (`frontend/.env`)

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

### Application Defaults (configured in `config.py`)

| Setting | Default | Description |
|---|---|---|
| `APP_NAME` | `PDF RAG QA System` | Application display name |
| `APP_VERSION` | `1.0.0` | Current version |
| `API_V1_PREFIX` | `/api/v1` | API route prefix |
| `ALGORITHM` | `ES256` | JWT signing algorithm |
| `MAX_FILE_SIZE_MB` | `5` | Maximum upload size |
| `ALLOWED_MIME_TYPES` | `["application/pdf"]` | Accepted file types |
| `STORAGE_BUCKET_NAME` | `pdfs` | Supabase storage bucket name |



## Getting Started

### Prerequisites

- **Python 3.13+** and **uv** (or pip)
- **Node.js 18+** and npm
- A **Supabase** project with:
  - Auth enabled
  - Storage bucket named `pdfs` created
  - Database schema applied (run `backend/src/sql/db.sql` in the SQL Editor)
- API keys for **Google AI**, **Cohere**, and **Llama Cloud**

### Database Setup

Run the SQL schema in your Supabase SQL Editor to create all tables, indexes, RLS policies, and the `match_documents` function:

```bash
# Copy the contents of backend/src/sql/db.sql and run in Supabase SQL Editor
```

### Backend

```bash
cd backend

# Install dependencies with uv (recommended)
uv sync

# Or with pip
pip install -r requirements.txt

# Start the server (port 8000)
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

API docs available at:
- **Swagger UI for Interactive Testing**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc for Reading and Reference**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server (port 3000)
npm run dev
```

The app will be available at **http://localhost:3000**.