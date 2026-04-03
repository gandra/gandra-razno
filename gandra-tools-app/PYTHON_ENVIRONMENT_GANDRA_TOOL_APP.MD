# Python Environment Setup — Gandra Tools App

> **Tool:** uv (Astral) — Modern Python package and environment manager
> **Python Version:** 3.11+
> **Purpose:** Local development environment setup for Gandra Tools API backend

---

## Prerequisites

### 1. Install Python Version Manager (pyenv)

```bash
# macOS with Homebrew
brew install pyenv

# Linux
curl https://pyenv.run | bash
```

**Add to shell profile** (`~/.zshrc` or `~/.bashrc`):
```bash
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
```

Reload shell:
```bash
source ~/.zshrc  # or ~/.bashrc
```

### 2. Install Python 3.11

```bash
# List available Python versions
pyenv install --list | grep "^  3.11"

# Install Python 3.11.x (latest patch)
pyenv install 3.11.3

# Set as local version for this project
cd gandra-razno/gandra-tools-app/gandra-tools-api
pyenv local 3.11.3

# Verify
python --version
# Expected: Python 3.11.3
```

This creates a `.python-version` file that tells pyenv and uv which Python version to use.

### 3. Install uv Package Manager

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with Homebrew (macOS)
brew install uv

# Verify installation
uv --version
```

**Documentation:** https://docs.astral.sh/uv/

---

## Environment Setup

### Step 1: Navigate to Backend

```bash
cd gandra-razno/gandra-tools-app/gandra-tools-api
```

### Step 2: Create Virtual Environment + Install Dependencies

```bash
# One command does it all — creates .venv + installs from pyproject.toml
uv sync

# Output:
# Using CPython 3.11.3 interpreter at: ...
# Creating virtual environment at: .venv
# Resolved 132 packages in ...
# Installed 132 packages in ...
```

**What happens:**
- Creates `.venv/` directory with isolated Python environment
- Reads `pyproject.toml` for dependencies
- Installs all core + dev dependencies
- Creates `uv.lock` for reproducible builds

### Step 3: Activate Virtual Environment (optional)

```bash
# Activate (optional — uv commands auto-detect .venv)
source .venv/bin/activate

# You'll see (.venv) prefix in your terminal:
# (.venv) user@machine:~/gandra-tools-api$

# Verify
which python
# Expected: .../gandra-tools-api/.venv/bin/python
```

**Note:** With uv, you can skip activation and use `uv run <command>` instead.

### Step 4: Create .env File

```bash
# Copy example
cp .env.example .env

# Edit with your API keys
nano .env   # or code .env
```

**Minimum required for development:**
```bash
SECRET_KEY=your-random-secret-key-here
OPENAI_API_KEY=sk-your-openai-key      # Or leave empty if using Ollama
```

### Step 5: Verify Installation

```bash
# Check imports work
uv run python -c "import fastapi; import typer; import sqlalchemy; print('All imports OK')"

# Run tests
uv run pytest -v

# Expected: all tests pass
```

---

## Running the Application

### FastAPI Server (development)

```bash
cd gandra-razno/gandra-tools-app/gandra-tools-api

# Option 1: Using uv run (recommended — no activation needed)
uv run uvicorn gandra_tools.main:app --reload --host 0.0.0.0 --port 8095

# Option 2: With activated environment
source .venv/bin/activate
uvicorn gandra_tools.main:app --reload --host 0.0.0.0 --port 8095
```

**Access:**
- API: http://localhost:8095
- Swagger UI: http://localhost:8095/docs
- ReDoc: http://localhost:8095/redoc
- Health check: http://localhost:8095/api/v1/health

### CLI Tool

```bash
# Using uv run
uv run gandra-tools --help
uv run gandra-tools config show
uv run gandra-tools env current

# Or with activated .venv
gandra-tools --help
```

---

## Running Tests

```bash
cd gandra-razno/gandra-tools-app/gandra-tools-api

# All tests
uv run pytest -v

# With coverage
uv run pytest --cov=gandra_tools --cov-report=html

# Specific test file
uv run pytest tests/unit/core/test_config.py -v

# Specific test
uv run pytest tests/unit/core/test_auth.py::test_hash_and_verify_password -v

# Only unit tests
uv run pytest tests/unit/ -v

# Only API tests
uv run pytest tests/api/ -v
```

---

## Code Formatting and Linting

```bash
# Lint check
uv run ruff check src/

# Auto-fix linting issues
uv run ruff check src/ --fix

# Format code
uv run ruff format src/

# Type checking (optional)
uv run mypy src/gandra_tools/
```

---

## Adding New Dependencies

**⚠️ IMPORTANT: zsh Users (macOS default shell)**

If you're using zsh, you MUST quote package names with square brackets:

```bash
# ❌ WRONG — zsh fails
uv add uvicorn[standard]
# zsh: no matches found: uvicorn[standard]

# ✅ CORRECT — quote the package name
uv add 'uvicorn[standard]'
```

**Why?** zsh treats `[]` as glob pattern characters.

### Adding packages

```bash
# Add a runtime dependency
uv add some-package

# Add a dev dependency
uv add --dev some-dev-tool

# Add an optional dependency group
uv add --optional youtube youtube-transcript-api

# Install optional groups
uv sync --extra youtube
uv sync --extra all    # All optional groups
```

---

## Docker Services (Local Infrastructure)

```bash
cd gandra-razno/gandra-tools-app

# Start all services (Ollama, PostgreSQL, Redis)
docker compose -f docker-compose-local.yml up -d

# Start only Ollama
docker compose -f docker-compose-local.yml up -d ollama

# Pull Ollama models
docker exec -it gandra-ollama ollama pull llama3.2
docker exec -it gandra-ollama ollama pull nomic-embed-text

# Check status
docker compose -f docker-compose-local.yml ps

# Stop
docker compose -f docker-compose-local.yml down
```

### Ports

| Service | Port | Credentials |
|---------|------|-------------|
| FastAPI (gandra-tools) | 8095 | JWT from /api/v1/auth/login |
| Ollama | 11434 | — |
| PostgreSQL | 5450 | gandra / gandra_dev_password |
| Redis | 6395 | — |

---

## Deactivate / Remove Environment

```bash
# Deactivate (if activated)
deactivate

# Remove and recreate from scratch
rm -rf .venv
uv sync
```

---

## Troubleshooting

### Problem 1: `uv` command not found

```bash
which uv

# If not found, reinstall
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add to PATH (if needed)
export PATH="$HOME/.cargo/bin:$PATH"
source ~/.zshrc
```

### Problem 2: Wrong Python version

```bash
python --version
pyenv versions
pyenv local 3.11.3
rm -rf .venv && uv sync
```

### Problem 3: "no matches found" error (zsh)

```bash
# Always quote packages with extras in zsh
uv add 'package[extra]'
```

### Problem 4: Build backend error (hatchling)

The `pyproject.toml` uses hatchling as build backend:
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/gandra_tools"]
```

If you see build errors:
```bash
rm -rf .venv uv.lock
uv sync
```

### Problem 5: Import errors

```bash
# Verify .venv is active or use uv run
uv run python -c "import gandra_tools; print('OK')"

# Resync
uv sync
```

### Problem 6: Database errors

```bash
# SQLite DB is auto-created on first run
# To reset:
rm gandra_tools.db
uv run uvicorn gandra_tools.main:app --reload --port 8095
# DB will be recreated on startup
```

---

## Quick Reference

```bash
# ── Environment ──────────────────────────────────
uv sync                          # Install/sync all deps
uv run <command>                 # Run in .venv context
source .venv/bin/activate        # Activate (optional)
deactivate                       # Deactivate

# ── Server ───────────────────────────────────────
uv run uvicorn gandra_tools.main:app --reload --port 8095

# ── CLI ──────────────────────────────────────────
uv run gandra-tools --help
uv run gandra-tools config show
uv run gandra-tools env current

# ── Tests ────────────────────────────────────────
uv run pytest -v                 # All tests
uv run pytest tests/unit/ -v     # Unit only
uv run pytest tests/api/ -v      # API only

# ── Linting ──────────────────────────────────────
uv run ruff check src/ --fix
uv run ruff format src/

# ── Packages ─────────────────────────────────────
uv add <package>                 # Add dependency
uv add --dev <package>           # Add dev dependency
uv remove <package>              # Remove
uv pip list                      # List installed
```

---

## Project Structure

```
gandra-tools-api/
├── .python-version              # Python 3.11 (pyenv)
├── .env                         # Environment variables (git-ignored)
├── .env.example                 # Example env vars (committed)
├── .venv/                       # Virtual environment (git-ignored)
├── pyproject.toml               # Dependencies + tools config
├── uv.lock                      # Locked deps (git-ignored)
├── src/
│   └── gandra_tools/
│       ├── main.py              # FastAPI application
│       ├── cli.py               # Typer CLI entry point
│       ├── core/                # Config, auth, settings, LLM, plugin
│       ├── models/              # Pydantic + SQLAlchemy models
│       ├── db/                  # Database session
│       ├── tools/               # Plugin tools (youtube, research, ...)
│       └── routers/             # FastAPI route handlers
└── tests/
    ├── conftest.py              # Shared fixtures
    ├── unit/                    # Fast, no external deps
    ├── api/                     # FastAPI TestClient
    ├── integration/             # Requires Docker services
    └── cli/                     # Typer CliRunner
```

---

**Last Updated:** 2026-04-03
**Python Version:** 3.11.3
**uv Version:** Latest stable
**Platform:** macOS / Linux
