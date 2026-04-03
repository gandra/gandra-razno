# Gandra Tools App — Backlog

> **Poslednje ažuriranje:** 2026-04-03 (Faza 1 implementirana)
> **Arhitektura:** `gandra-tools-app/docs/architecture-elaboration.md` (DRAFT v4)

---

## Status implementacije

| Faza | Opis | Status | Napomena |
|------|------|--------|----------|
| **1** | Scaffold + core infra | **DONE** | 16 src + 8 test fajlova, 27 testova |
| **2** | Publisher modul | **DONE** | 8 formattera + service + router + 30 testova |
| **3** | YouTube transcript | **DONE** | schemas, service, router, CLI (interactive), 22 testova |
| **4** | CLI framework | **DONE** | Autodiscovery, publish CLI, 13 testova |
| **5** | Image Text Extractor | **DONE** | schemas, OCR service, router, CLI, 15 testova |
| **6** | RAG Research | PLANIRANO | Multi-link analiza |
| **7** | File operations | PLANIRANO | Search + rename |
| **8** | Web UI | PLANIRANO | Vue 3 + Vite + Tailwind |
| **9** | DevTools | PLANIRANO | API tester, code review |
| **10** | Polish | PLANIRANO | Error handling, logging, CI |

---

## Faza 1 — Scaffold + core infra

### Deliverables

| # | Stavka | Status | Fajl/Folder |
|---|--------|--------|-------------|
| 1.1 | pyproject.toml | **DONE** | `gandra-tools-api/pyproject.toml` |
| 1.2 | .python-version | **DONE** | `gandra-tools-api/.python-version` |
| 1.3 | .gitignore | **DONE** | `gandra-tools-app/.gitignore` (+ gandra-output/) |
| 1.4 | .env.example | **DONE** | `gandra-tools-api/.env.example` |
| 1.5 | docker-compose-local.yml | **DONE** | `gandra-tools-app/docker-compose-local.yml` |
| 1.6 | Folder struktura (src/) | **DONE** | 23 `__init__.py` + tool subdirs |
| 1.7 | config.py | **DONE** | `core/config.py` (Pydantic BaseSettings) |
| 1.8 | auth.py | **DONE** | `core/auth.py` (JWT, bcrypt, CLI no-auth) |
| 1.9 | plugin.py | **DONE** | `core/plugin.py` (autodiscovery registry) |
| 1.10 | settings_service.py | **DONE** | `core/settings_service.py` (4-layer resolution) |
| 1.11 | LLM factory + clients | **DONE** | `core/llm/` (OpenAI, Anthropic, Ollama, Factory) |
| 1.12 | main.py (FastAPI) | **DONE** | `main.py` (lifespan, CORS, plugin routers) |
| 1.13 | cli.py (Typer) | **DONE** | `cli.py` (auth, config, env subcommands) |
| 1.14 | DB models + session | **DONE** | `models/database.py`, `db/session.py` |
| 1.15 | Health + Auth routers | **DONE** | `routers/health.py`, `routers/auth.py` |
| 1.16 | Testovi (27) | **DONE** | 5 unit test files + 2 API test files |
| 1.17 | PYTHON_ENVIRONMENT doc | **DONE** | `PYTHON_ENVIRONMENT_GANDRA_TOOL_APP.MD` |
| 1.18 | Fix pyproject.toml bugs | **DONE** | hatchling.build + typer (no [all] extra) |
| 1.19 | Fix test failures | **DONE** | bcrypt truncate_error + greenlet dependency |

---

## Faza 2 — Publisher modul

| # | Stavka | Status |
|---|--------|--------|
| 2.1 | BaseFormatter ABC | **DONE** |
| 2.2 | JSON formatter | **DONE** |
| 2.3 | Markdown formatter + generic.md.j2 | **DONE** |
| 2.4 | Text formatter | **DONE** |
| 2.5 | HTML formatter + generic.html.j2 | **DONE** |
| 2.6 | Facebook formatter | **DONE** |
| 2.7 | LinkedIn formatter | **DONE** |
| 2.8 | Instagram formatter | **DONE** |
| 2.9 | X (Twitter) formatter | **DONE** |
| 2.10 | PublisherService | **DONE** |
| 2.11 | Jinja2 templates (generic.md.j2, generic.html.j2) | **DONE** |
| 2.12 | Publisher router + main.py registration | **DONE** |
| 2.13 | Publisher testovi (30: 4 json + 4 text + 3 md + 3 html + 12 social + 12 service + 4 api) | **DONE** |

---

## Faza 3 — YouTube Transcript

| # | Stavka | Status |
|---|--------|--------|
| 3.1 | YouTube schemas (TranscriptInput/Output, slugify_title) | **DONE** |
| 3.2 | YouTube service (extract, merge segments, publish) | **DONE** |
| 3.3 | YouTube router (POST /api/v1/youtube/transcript) | **DONE** |
| 3.4 | YouTube CLI (`gandra-tools youtube transcript`) | **DONE** |
| 3.5 | YouTube standalone (`python -m gandra_tools.tools.youtube.transcript`) | **DONE** |
| 3.6 | YouTube TOOL_META (plugin autodiscovery) | **DONE** |
| 3.7 | YouTube testovi (22: 12 schema + 10 service) | **DONE** |

---

## Buduće faze (4-10)

Detaljno se razrađuju kad prethodne faze budu završene.

---

## Odluke i napomene

| Datum | Odluka |
|-------|--------|
| 2026-04-03 | Preporuka: Plugin arhitektura (Pristup C) sa autodiscovery |
| 2026-04-03 | UI: Vue 3 + Vite + Tailwind |
| 2026-04-03 | OCR: EasyOCR (offline, multilingual) |
| 2026-04-03 | Auth: CLI bez auth, Web/API sa JWT |
| 2026-04-03 | Settings: 4-layer resolution (user→env→global→default) |
| 2026-04-03 | Publisher: 8 formata (json, md, txt, html, facebook, linkedin, instagram, x) |
| 2026-04-03 | Output dir: `gandra-output/` u root-u, .gitignore-d |
