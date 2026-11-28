# AI RAG Lab

AI RAG Lab is a small, NotebookLM-inspired document Q&A application. Upload documents, ask questions about their contents, and get answers grounded in passages retrieved from those documents, with source and page citations where available.

It is a learning project and a lightweight “NotebookLM copy” in spirit—not a copy of Google's product. It uses a locally stored ChromaDB vector database and a configurable language model provider, rather than NotebookLM's private services and features.

## What it does

- Upload PDF, TXT, Markdown, DOCX, CSV, and JSON files through a Vue web interface or the API.
- Extract and split document text into overlapping chunks.
- Generate local text embeddings with `sentence-transformers/all-MiniLM-L6-v2` and store them in ChromaDB.
- Retrieve relevant passages when a question is asked, then send those passages and the question to the configured LLM.
- Return an answer, retrieved context, and source citations (including page numbers when the loader provides them).
- Run a FastAPI backend and Vue 3 frontend locally.

The answers are intended to be based on retrieved document context. Like any LLM application, responses are not guaranteed to be correct; check the cited sources.

## Frontend

The Vue 3 frontend is a two-pane workspace: upload or drag and drop a document on the left, preview it where supported, and chat with the RAG assistant on the right. It shows whether the backend is online, displays answers with source citations, and lets you view retrieved context. The browser sends uploads and questions to the FastAPI backend at `http://localhost:8000`; it does not perform the document indexing or AI generation itself.

## How it works

```text
Documents
   │
   ▼
FastAPI upload endpoint
   │
   ▼
Load text → split into chunks → create local embeddings
   │
   ▼
ChromaDB (./chroma_db)
   │
Question from the Vue frontend
   │
   ▼
Retrieve relevant chunks → send context and question to the LLM
   │
   ▼
Grounded answer, context, and source citations
```

## Project structure

```text
ai_rag_lab/
├── main.py           # FastAPI API for health, upload, and question answering
├── rag_app.py        # Embedding/vector-store setup and LLM prompt configuration
├── vector_store.py   # Document loading, chunking, embedding, and storage
├── ingest.py         # Document ingestion utilities
├── search.py         # Semantic search utility
├── requirements.txt  # Python dependencies
└── rag-web/          # Vue 3 + Vite frontend
```

## Requirements

- Python 3
- Node.js matching the frontend requirement: `^22.18.0` or `>=24.12.0`
- A key for the configured LLM provider. The default model is `groq/qwen/qwen3.8-27b`, which uses a Groq API key.

## Setup

Open PowerShell in the `ai_rag_lab` project directory:

```powershell
cd D:\Projects\rag_app\ai_rag_lab
```

### 1. Create a Python environment and install dependencies

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell prevents environment activation, you can invoke the environment's Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2. Configure the LLM provider

Create a `.env` file in the `ai_rag_lab` directory. For the default model, add:

```env
GROQ_API_KEY=your_groq_api_key
```

Keep `.env` private; it is excluded from Git. If you change `MODEL` in `rag_app.py`, provide the API key required by that provider. An Ollama model can be used with a local Ollama installation.

### 3. Start the backend

From `ai_rag_lab`, with the virtual environment active:

```powershell
python -m uvicorn main:app --reload --port 8000
```

- API documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health check: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)

### 4. Start the frontend

Open a second terminal:

```powershell
cd D:\Projects\rag_app\ai_rag_lab\rag-web
npm install
npm run dev
```

Open the local URL printed by Vite in your terminal. The frontend connects to the backend at `http://localhost:8000`.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/v1/health` | Check that the backend is running |
| `POST` | `/api/v1/upload` | Upload a PDF, TXT, Markdown, DOCX, CSV, or JSON file for indexing |
| `POST` | `/api/v1/ask` | Ask a question; optionally include `document_name` to filter by a document |

## Data and privacy

Uploaded documents are processed by the backend and their embeddings are stored in the local `chroma_db` directory. Questions and retrieved document context are sent to the configured LLM provider to generate answers. Avoid uploading sensitive documents unless you have reviewed the provider's data handling terms. Local database and temporary upload files are excluded from Git.

## Tech stack

| Technology | Role |
|---|---|
| FastAPI + Uvicorn | Backend REST API |
| Vue 3 + Vite | Browser-based frontend |
| LangChain | Document loading, text splitting, retrieval, and prompt orchestration |
| Hugging Face sentence-transformers | Local document and query embeddings |
| ChromaDB | Persistent local vector store |
| LiteLLM | Configurable LLM provider integration |
