# 🏥 Medical Chat

An AI-powered medical chat assistant built with **FastAPI** (Python) on the backend and **Next.js** (Node.js) on the frontend. The project is built around a RAG-style retrieval pipeline and local Ollama LLM integration. The backend `/api/v1/chat` endpoint is implemented and wired to retrieve from ChromaDB and synthesize answers via Ollama.

> ⚠️ **Disclaimer:** This tool is for informational purposes only and does not constitute medical advice. Always consult a qualified healthcare professional.

---

## Architecture

```
medical-chat/
├── backend/                  # FastAPI + Python
│   ├── chroma_db/            # Local ChromaDB persistence (created at runtime)
│   ├── ingestion/            # Data preparation helpers
│   │   ├── chunk.py
│   │   ├── embed_and_store.py
│   │   ├── fetch.py
│   │   ├── inspect_db.py
│   │   └── run_ingestion.py
│   ├── rag/                  # RAG / Ollama helper modules
│   │   ├── llm.py            # Ollama HTTP client
│   │   ├── retrieve.py
│   │   ├── rewrite.py
│   │   ├── synthesize.py
│   │   └── __init__.py
│   ├── src/                  # FastAPI application
│   │   ├── config.py
│   │   ├── main.py
│   │   └── routers/
│   │       ├── chat.py
│   │       └── health.py
│   └── tests/                # Python tests
├── frontend/                 # Next.js UI
│   ├── app/
│   │   ├── components/
│   │   ├── health/
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── Dockerfile
│   └── package.json
└── docker-compose.yml
```

---

## Current state

- Backend `/api/v1/chat` is implemented and uses the RAG pipeline: ChromaDB retrieval plus Ollama answer synthesis.
- Data ingestion is handled by `backend/ingestion/run_ingestion.py`, which creates `backend/chroma_db` and loads PubMed-derived chunks into ChromaDB.
- Docker uses a named volume for ChromaDB persistence (`chroma_data`), while local development stores the DB under `backend/chroma_db` by default.
- The frontend is configured to talk to the backend, but the project remains an experimental proof of concept and should not be used as medical advice.

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Docker | ≥ 24 | https://docs.docker.com/get-docker/ |
| Docker Compose | ≥ 2.20 | Bundled with Docker Desktop |
| uv *(local dev only)* | ≥ 0.4 | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Node.js *(local dev only)* | ≥ 20 | https://nodejs.org |

---

## Quick Start (Docker)

```bash
# 1. Clone the repository
git clone https://github.com/your-org/medical-chat.git
cd medical-chat

# 2. Configure environment variables
cp .env.example .env || true

# 3. Start all services (backend, frontend, Ollama)
docker compose up --build

# 4. Populate the ChromaDB store (required for evidence retrieval)
docker compose exec backend python -m ingestion.run_ingestion

# 5. Pull the LLM model (run once after first startup)
docker exec -it medical-chat-ollama ollama pull llama3.2:latest

# 6. Open in browser
#    Frontend → http://localhost:3000
#    Backend  → http://localhost:8000/docs
```

> **Note:** Step 5 downloads ~600MB and only needs to be run once. The model is stored in a Docker volume (`ollama`) and persists across restarts.

---

## Initializing ChromaDB

The Chroma vector store folder and collection are created automatically when the backend initializes `ChromaDocumentStore` on first access. To actually populate the vector store with searchable PubMed chunks, run the ingestion script.

### Local development

From the repository root:

```bash
cd backend
python -m ingestion.run_ingestion
```

This performs the following on first run:
- fetches PubMed articles for the default terms
- chunks article text into `backend/ingestion/chunked_articles.json`
- creates the local ChromaDB store in `backend/chroma_db`
- populates the `pubmed_abstracts` collection with embeddings

### Docker

When using `docker compose up`, the backend container mounts a named volume at `/data/chroma_db`. The store is created and persisted inside the `chroma_data` volume on first backend startup or when the ingestion flow is run inside the container.

## Local Development (without Docker)

### Ollama (required for LLM features)

Install Ollama and pull the model before starting the backend:

```bash
# Install Ollama (Linux/WSL)
curl -fsSL https://ollama.com/install.sh | sh

# Pull the model (run once, ~600MB download)
ollama pull llama3.2:latest

# Ollama starts automatically after install
# If needed, start it manually:
ollama serve
```

> **WSL users:** If you see `Error: listen tcp 127.0.0.1:11434: bind: address already in use`, Ollama is already running — skip `ollama serve` and go straight to `ollama pull`.

### Backend

```bash
cd backend

# Install dependencies with uv
uv sync

# Run development server
uv run uvicorn src.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

---

## Running Tests

```bash
cd backend

# All tests with coverage
uv run pytest tests/ --cov=src --cov-report=term-missing

# Single test file
uv run pytest tests/test_endpoints.py -v
```

### Manual LLM test

To verify Ollama is reachable:

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2:1b",
  "prompt": "What is hypertension?",
  "stream": false
}'
```

Or via Python:

```bash
python3 -c "
from backend.rag.llm import OllamaChat
chat = OllamaChat(model='llama3.2:1b')
print(chat.ask_llm('What is hypertension?'))
"
```

---

## Code Quality

```bash
cd backend

# Lint & format
uvx ruff check .
uvx ruff format .

# Type checking
uv run mypy src/

# Security audit
uvx bandit -r src/
uv run pip-audit
```

---

## Pre-commit Hooks

```bash
# Install pre-commit (once)
pip install pre-commit
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

---

## Environment Variables

Create a `.env` file in the project root or set environment variables directly.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `APP_ENV` | No | `development` | `development` \| `staging` \| `production` |
| `LOG_LEVEL` | No | `INFO` | Application log verbosity |
| `CORS_ORIGINS` | No | `['http://localhost:3000']` | Allowed CORS origins for the backend |
| `ANTHROPIC_API_KEY` | No | — | Anthropic API key placeholder for future integration |
| `DATABASE_URL` | No | — | PostgreSQL connection string |
| `CHROMA_DB_PATH` | No | `./chroma_db` | Path to ChromaDB storage (current code uses `backend/chroma_db` by default) |
| `OLLAMA_BASE_URL` | No | `http://localhost:11434` | Ollama server URL (set to `http://ollama:11434` inside Docker automatically) |
| `OLLAMA_MODEL_NAME` | No | `llama3.2:latest` | Ollama model name used by the backend |
| `NEXT_PUBLIC_API_URL` | No | `http://localhost:8000` | Backend URL visible to the browser |

---

## Services

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 3000 | Next.js React UI |
| Backend | 8000 | FastAPI REST API + `/docs` Swagger UI |
| Ollama | 11434 | Local LLM server (llama3.2:1b) |

---

## Notes

- The backend exposes `/api/v1/chat`, and it is wired to the RAG pipeline with ChromaDB retrieval and Ollama-assisted synthesis.
- The `backend/ingestion` and `backend/rag` packages contain helper modules that support ingestion, embedding, retrieval, and Ollama integration. The current implementation uses PubMed-derived chunks stored in ChromaDB.

---

## CI / CD

GitHub Actions runs on every push and pull request to `main`:

- **Tests** — pytest with coverage (Python 3.12 & 3.13)
- **Style** — Ruff lint + format check
- **Types** — mypy strict mode
- **Security** — Bandit SAST scan
- **Coverage** — uploaded to Codecov

---

## License

MIT
