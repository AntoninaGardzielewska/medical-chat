# 🏥 Medical Chat

An AI-powered medical chat assistant built with **FastAPI** (Python) on the backend and **Next.js** (Node.js) on the frontend.

> ⚠️ **Disclaimer:** This tool is for informational purposes only and does not constitute medical advice. Always consult a qualified healthcare professional.

---

## Architecture

```
medical-chat/
├── backend/          # FastAPI + Python (uv)
│   ├── src/          # Application source
│   └── tests/        # Pytest test suite
├── frontend/         # Next.js (TypeScript)
│   └── app/          # App Router pages
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
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# 3. Start both services
docker compose up --build

# 4. Open in browser
#    Frontend → http://localhost:3000
#    Backend  → http://localhost:8000/docs
```

---

## Local Development (without Docker)

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

See [`.env.example`](.env.example) for a full reference with descriptions.

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | API key from console.anthropic.com |
| `APP_ENV` | No | `development` \| `staging` \| `production` |
| `DATABASE_URL` | No | PostgreSQL connection string |
| `NEXT_PUBLIC_API_URL` | No | Backend URL visible to the browser |

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
