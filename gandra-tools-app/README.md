# Gandra Tools App

Swiss-army toolset — YouTube transcripts, RAG research, file ops, image OCR, and more.

## Architecture

```
gandra-tools-app/
├── gandra-tools-api/       FastAPI backend (Python 3.11, uv)
├── gandra-tools-ui/        Vue 3 frontend (Vite, Tailwind)
├── gandra-output/           All tool outputs (gitignored)
├── docker-compose-local.yml Ollama, PostgreSQL, Redis
└── docs/                    Architecture elaboration
```

## 4 Ways to Use

| Method | Example |
|--------|---------|
| **Web UI** | `http://localhost:3001` |
| **REST API** | `curl -X POST http://localhost:8095/api/v1/youtube/transcript` |
| **CLI** | `gandra-tools youtube transcript --url "..."` |
| **Python** | `python -m gandra_tools.tools.youtube.transcript` |

## Tools

| Tool | Category | Description |
|------|----------|-------------|
| YouTube Transcript | Media | Extract transcript with timestamps |
| RAG Research | AI/Research | Multi-link analysis, credibility, narratives |
| Image Text Extract | ImageOps | OCR + transparent PNG rendering |
| File Search | FileOps | Search by name, content, regex |
| File Rename | FileOps | 10 strategies (slugify, snake_case, prefix...) |
| API Tester | DevTools | HTTP endpoint testing with repeat |
| Code Review | DevTools | AI-powered code review |

## Publisher Formats

json, md, txt, html, facebook, linkedin, instagram, x

## Quick Start

```bash
# Backend
cd gandra-tools-api
cp .env.example .env       # Edit API keys
uv sync
uv run uvicorn gandra_tools.main:app --reload --port 8095

# Frontend
cd gandra-tools-ui
bun install
bun run dev                # http://localhost:3001

# CLI
uv run gandra-tools --help

# Docker services (Ollama, PostgreSQL, Redis)
docker compose -f docker-compose-local.yml up -d
```

## Auth

- **CLI/Python**: No auth (trusted local machine)
- **Web UI/API**: JWT login required
- Default user: `dragan.mijatovic@cramick-it.com` / `topsecret`

## Settings

4-layer resolution: user → environment → global → default

## Ports

| Service | Port |
|---------|------|
| FastAPI | 8095 |
| Vue UI | 3001 |
| Ollama | 11434 |
| PostgreSQL | 5450 |
| Redis | 6395 |
