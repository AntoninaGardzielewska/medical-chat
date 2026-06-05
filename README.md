# 🏥 Medical Chat

An AI-powered medical chat assistant built with **FastAPI** (Python) on the backend and **Next.js** (Node.js) on the frontend. The project is designed to support a RAG-style retrieval pipeline and local Ollama LLM integration, while the current backend chat endpoint remains a placeholder response.

> ⚠️ **Disclaimer:** This tool is for informational purposes only and does not constitute medical advice. Always consult a qualified healthcare professional.

---

## Architecture

```
medical-chat/
├── backend/                  # FastAPI + Python
│   ├── ingestion/            # Data preparation helpers
│   │   ├── chunk.py
│   │   ├── embed_and_store.py
│   │   ├── fetch.py
│   │   ├── inspect_db.py
│   │   ├── run_ingestion.py
│   │   └── articles.json
│   ├── rag/                  # RAG / Ollama helper modules
│   │   ├── llm.py            # Ollama HTTP client
│   │   ├── retrieve.py
│   │   ├── rewrite.py
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
│   │   ├── layout.jsx
│   │   └── page.js
│   ├── Dockerfile
│   └── package.json
└── docker-compose.yml
```

---

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

# 4. Pull the LLM model (run once after first startup)
docker exec -it medical-chat-ollama ollama pull llama3.2:1b

# 5. Open in browser
#    Frontend → http://localhost:3000
#    Backend  → http://localhost:8000/docs
```

> **Note:** Step 4 downloads ~600MB and only needs to be run once. The model is stored in a Docker volume (`ollama`) and persists across restarts.

---

## Local Development (without Docker)

### Ollama (required for LLM features)

Install Ollama and pull the model before starting the backend:

```bash
# Install Ollama (Linux/WSL)
curl -fsSL https://ollama.com/install.sh | sh

# Pull the model (run once, ~600MB download)
ollama pull llama3.2:1b

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
| `OLLAMA_BASE_URL` | No | `http://localhost:11434` | Ollama server URL (set to `http://ollama:11434` inside Docker automatically) |
| `APP_ENV` | No | `development` | `development` \| `staging` \| `production` |
| `LOG_LEVEL` | No | `INFO` | Application log verbosity |
| `CORS_ORIGINS` | No | `["http://localhost:3000"]` | Allowed CORS origins for the backend |
| `ANTHROPIC_API_KEY` | No | — | Anthropic API key placeholder for future integration |
| `DATABASE_URL` | No | — | PostgreSQL connection string |
| `CHROMA_DB_PATH` | No | `./chroma_db` | Path to ChromaDB storage |
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

- The backend currently exposes a placeholder `/api/v1/chat` endpoint.
- The `backend/ingestion` and `backend/rag` packages contain helper modules that support ingestion, embedding, retrieval, and Ollama integration, but the chat API is not yet fully wired to the RAG pipeline.

---

## CI / CD

GitHub Actions runs on every push and pull request to `main`:

- **Tests** — pytest with coverage (Python 3.12 & 3.13)
- **Style** — Ruff lint + format check
- **Types** — mypy strict mode
- **Security** — Bandit SAST scan
- **Coverage** — uploaded to Codecov

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Commit your changes (pre-commit hooks run automatically)
4. Open a pull request against `main`

---

## License

MIT
