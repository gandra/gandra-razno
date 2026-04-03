# Gandra Tools App — Elaboracija arhitekture

> **Datum:** 2026-04-03
> **Autor:** Dragan Mijatović
> **Status:** DRAFT v3
> **Referentni projekti:** `sistemi/zabbix-ai-backend`, `companydevs/companydevs-ai`

---

## 1. Pregled zahteva

Gandra Tools App je "švajcarski nožić" — modularan toolset koji se koristi na **4 načina**:

| # | Način pozivanja | Opis |
|---|----------------|------|
| a | **Web UI** | Chat interface + dedicirane stranice za specifične alate |
| b | **REST API** | FastAPI endpoints, Swagger/ReDoc |
| c | **CLI** | Terminal sa help, parametrima, subcommands |
| d | **Python file** | Direktno `python -m gandra_tools.tools.youtube.transcript` |

### Inicijalni alati

| Alat | Kategorija | Opis |
|------|-----------|------|
| YouTube Transcript | Media | Ekstrakcija kompletnog teksta sa timestamp-ovima |
| YouTube Images | Media | Ekstrakcija frame-ova sa timestamp-ovima |
| RAG Research | AI/Research | Istraživanje teme iz liste linkova — verodostojnost, narativ, analiza |
| File Search | FileOps | Napredna pretraga fajlova (naziv, sadržaj, regex) |
| File Rename | FileOps | Batch rename sa strategijama (prefix, suffix, slugify, uppercase...) |
| API Tester | DevTools | Testiranje API poziva sa reporting-om |
| Code Review | DevTools | Provera kvaliteta koda |
| Image Text Extract | ImageOps | Skidanje pozadine sa slike, output PNG sa tekstom na transparent bg |

### Ključni koncepti

- **BYOK** (Bring Your Own Key) — korisnik unosi svoj API ključ
- **Multi-provider LLM** — OpenAI, Anthropic (Claude), Ollama (lokalni)
- **Model selekcija** na UI i backend nivou, sa default-ovima u settings
- **Jedan korisnik** za sada (dragan.mijatovic@cramick-it.com), proširivo na više

---

## 2. Pristupi za arhitekturu backend-a

### Pristup A: Flat modules — po uzoru na companydevs-ai

```
src/gandra_tools/
├── main.py
├── config.py
├── routers/          # FastAPI routers po alatu
├── services/         # Biznis logika po alatu
│   └── llm/          # LLM apstrakcija
├── models/           # Pydantic schemas
└── db/               # Storage (pgvector, SQLite)
```

| Prednosti | Mane |
|-----------|------|
| Jednostavno, brz start | Ne skalira dobro sa 10+ alata |
| Manji boilerplate | Teže naći gde šta pripada |
| Dokazan pattern (companydevs-ai) | Mešanje domena u jednom folderu |

### Pristup B: Domain modules — po uzoru na zabbix-ai-backend

```
src/gandra_tools/
├── main.py
├── core/             # Config, auth, settings, shared utils
├── api/v1/           # FastAPI routers (thin layer)
├── modules/
│   ├── youtube/      # YouTube alati (transcript, images)
│   ├── research/     # RAG research, link analysis
│   ├── fileops/      # File search, rename
│   └── devtools/     # API tester, code review
├── services/
│   └── llm/          # LLM apstrakcija (OpenAI, Claude, Ollama)
├── models/           # Shared Pydantic schemas
└── db/               # Storage layer
```

| Prednosti | Mane |
|-----------|------|
| Čist domain separation | Više boilerplate-a na početku |
| Lako dodavanje novih modula | Može biti overkill za 3-4 alata |
| Svaki modul ima svoju logiku | — |
| Skalira na 20+ alata | — |

### Pristup C: Plugin arhitektura — autodiscovery ⭐ (PREPORUKA)

```
src/gandra_tools/
├── main.py                # FastAPI app + plugin autodiscovery
├── core/
│   ├── config.py          # Settings (Pydantic BaseSettings)
│   ├── auth.py            # JWT auth, BYOK
│   ├── plugin.py          # Base plugin class / registry
│   └── llm/               # LLM apstrakcija
│       ├── base.py
│       ├── openai_client.py
│       ├── anthropic_client.py
│       ├── ollama_client.py
│       └── factory.py
├── tools/                 # Svaki tool = self-contained plugin
│   ├── youtube/
│   │   ├── __init__.py    # ToolPlugin metadata (name, category, description)
│   │   ├── router.py      # FastAPI router (/api/v1/youtube/...)
│   │   ├── service.py     # Biznis logika
│   │   ├── schemas.py     # Request/Response modeli
│   │   └── cli.py         # CLI subcommand (Typer)
│   ├── research/
│   │   ├── __init__.py
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── schemas.py
│   │   └── cli.py
│   ├── fileops/
│   │   └── ...
│   └── devtools/
│       └── ...
├── cli.py                 # Typer CLI entry point (autodiscovers tools/*/cli.py)
├── models/                # Shared schemas (LLM request/response, pagination)
└── db/                    # Storage (conversations, cache)
```

| Prednosti | Mane |
|-----------|------|
| Svaki tool potpuno self-contained | Autodiscovery zahteva konvenciju |
| Dodavanje novog tool-a = novi folder | Malo složeniji bootstrap |
| Svaki tool ima i router i CLI i standalone | — |
| Best of both referentnih projekata | — |
| Prirodno skalira bez refaktora | — |

**Zašto preporuka:** Zahtev je "širok spektar namena" koji će rasti. Plugin pattern omogućava da svaki novi alat bude folder sa 4-5 fajlova bez diranja ostatka sistema. Autodiscovery automatski registruje routere i CLI komande.

---

## 3. Dijagram arhitekture

```
+------------------------------------------------------------------+
|                        GANDRA TOOLS APP                           |
+------------------------------------------------------------------+
|                                                                    |
|  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  |
|  │  Web UI  │  │ REST API │  │   CLI    │  │  Python Direct   │  |
|  │ (React/  │  │ (Swagger │  │ (Typer)  │  │ python -m tools. │  |
|  │  Vue)    │  │  /ReDoc) │  │          │  │  youtube.service │  |
|  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────┬─────────┘  |
|       │              │              │                 │            |
|       └──────────────┴──────┬───────┴─────────────────┘            |
|                             │                                      |
|                    ┌────────▼────────┐                              |
|                    │   FastAPI App   │                              |
|                    │   (main.py)     │                              |
|                    └────────┬────────┘                              |
|                             │                                      |
|              ┌──────────────┼──────────────┐                       |
|              │              │              │                       |
|     ┌────────▼──┐  ┌───────▼───┐  ┌───────▼────┐                  |
|     │   core/   │  │  tools/   │  │    db/     │                  |
|     │ config    │  │ youtube/  │  │ SQLite /   │                  |
|     │ auth      │  │ research/ │  │ PostgreSQL │                  |
|     │ llm/      │  │ fileops/  │  │            │                  |
|     │  factory  │  │ devtools/ │  │            │                  |
|     └───────────┘  └──────────┘  └────────────┘                   |
|                                                                    |
+------------------------------------------------------------------+
|                       LLM Providers                                |
|  ┌──────────┐  ┌──────────────┐  ┌──────────┐                     |
|  │  OpenAI  │  │  Anthropic   │  │  Ollama  │                     |
|  │  (API)   │  │  (Claude)    │  │  (local) │                     |
|  └──────────┘  └──────────────┘  └──────────┘                     |
+------------------------------------------------------------------+
```

---

## 4. Docker Compose — lokalni servisi

Fajl `gandra-tools-app/docker-compose-local.yml` pokreće sve zavisne servise.

```yaml
# docker-compose-local.yml
version: "3.9"

services:
  # ── Ollama (lokalni LLM) ──────────────────────────────────
  ollama:
    image: ollama/ollama:latest
    container_name: gandra-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: [gpu]    # GPU ako postoji, inače CPU
    restart: unless-stopped

  # ── PostgreSQL + pgvector (faza 2, RAG) ───────────────────
  postgres:
    image: pgvector/pgvector:pg16
    container_name: gandra-postgres
    ports:
      - "5450:5432"
    environment:
      POSTGRES_DB: gandra_tools
      POSTGRES_USER: gandra
      POSTGRES_PASSWORD: gandra_dev_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  # ── Redis (cache, rate limiting, opciono task queue) ──────
  redis:
    image: redis:7-alpine
    container_name: gandra-redis
    ports:
      - "6395:6379"
    restart: unless-stopped

  # ── ChromaDB (alternativa pgvector, lightweight) ──────────
  # chromadb:
  #   image: chromadb/chroma:latest
  #   container_name: gandra-chromadb
  #   ports:
  #     - "8100:8000"
  #   volumes:
  #     - chroma_data:/chroma/chroma
  #   restart: unless-stopped

volumes:
  ollama_data:
  postgres_data:
  # chroma_data:
```

### Port alokacija — infrastruktura

| Servis | Port (host) | Port (container) | Napomena |
|--------|-------------|-------------------|----------|
| Ollama | 11434 | 11434 | Lokalni LLM (llama3, mistral, codellama) |
| PostgreSQL | 5450 | 5432 | pgvector za RAG, ne kolizira sa 5429 (companydevs/scouseit) |
| Redis | 6395 | 6379 | Ne kolizira sa 6378 (scouseit), 6399 (zabbix) |

### Inicijalizacija Ollama modela

```bash
# Posle docker compose up -d
docker exec -it gandra-ollama ollama pull llama3.2
docker exec -it gandra-ollama ollama pull mistral
docker exec -it gandra-ollama ollama pull nomic-embed-text   # Za embeddings

# Provera
docker exec -it gandra-ollama ollama list
```

### Pokretanje

```bash
cd gandra-tools-app

# Svi servisi
docker compose -f docker-compose-local.yml up -d

# Samo Ollama (ako ne treba DB/Redis)
docker compose -f docker-compose-local.yml up -d ollama

# Status
docker compose -f docker-compose-local.yml ps

# Zaustavi
docker compose -f docker-compose-local.yml down
```

---

## 5. Pozivanje alata — 4 načina

### a) Web UI

```
Browser → http://localhost:3001
  ├── /chat            → Chat UI (kao zabbix-ai-chat-ui)
  ├── /youtube         → YouTube transcript/images extractor
  ├── /research        → Link analysis + RAG istraživanje
  ├── /fileops         → File search/rename
  ├── /imageops        → Image text extractor
  ├── /settings        → BYOK keys, default model, embeddings
  └── /api-tester      → API testing interface
```

### b) REST API

```
FastAPI → http://localhost:8095
  ├── POST /api/v1/youtube/transcript     { url, interval_minutes }
  ├── POST /api/v1/youtube/images         { url, interval_seconds }
  ├── POST /api/v1/research/analyze       { links[], depth, focus }
  ├── POST /api/v1/fileops/search         { path, pattern, content }
  ├── POST /api/v1/fileops/rename         { path, strategy, options }
  ├── POST /api/v1/imageops/text-extract   { image_path, mode, font_color }
  ├── POST /api/v1/devtools/api-test      { method, url, headers, body }
  ├── POST /api/v1/devtools/code-review   { path, language }
  ├── GET  /api/v1/tools                  → Lista svih registrovanih alata
  ├── POST /api/v1/chat                   → Chat sa AI (streaming)
  ├── POST /api/v1/auth/login             → JWT login
  ├── GET  /api/v1/settings               → User settings (BYOK keys, defaults)
  └── PUT  /api/v1/settings               → Update settings
```

### c) CLI (Typer)

```bash
# Globalni help
gandra-tools --help

# YouTube transcript
gandra-tools youtube transcript "https://youtube.com/watch?v=..." --interval 2
gandra-tools youtube images "https://youtube.com/watch?v=..." --every 30s

# Research
gandra-tools research analyze --file links.txt --depth deep --focus credibility
gandra-tools research analyze --links "url1,url2,url3"

# File operations
gandra-tools files search /path/to/folder --pattern "*.py" --content "def main"
gandra-tools files rename /path/to/folder --strategy slugify --prefix "2026_"

# Image operations
gandra-tools imageops text-extract ./screenshot.jpg --mode ocr --font-color black
gandra-tools imageops text-extract ./photo.png --output-dir ./clean/

# DevTools
gandra-tools api-test GET https://api.example.com/health
gandra-tools code-review /path/to/file.py

# Settings
gandra-tools config set llm.provider openai
gandra-tools config set llm.model gpt-4o
gandra-tools config show
```

### d) Python Direct

```python
# Kao standalone Python modul
from gandra_tools.tools.youtube.service import YouTubeTranscriptService

svc = YouTubeTranscriptService()
result = svc.extract_transcript("https://youtube.com/watch?v=...", interval_minutes=2)
print(result.text)

# Ili direktno iz CLI:
python -m gandra_tools.tools.youtube.service --url "https://..." --interval 2
```

---

## 6. LLM apstrakcija — BYOK pattern

```
┌─────────────────────────────────────────────────┐
│                  LLM Factory                     │
│                                                  │
│  Settings:                                       │
│    default_provider: "openai"                    │
│    default_model: "gpt-4o"                       │
│    default_embedding: "text-embedding-3-small"   │
│                                                  │
│  BYOK Keys (per user):                           │
│    openai_api_key: "sk-..."                      │
│    anthropic_api_key: "sk-ant-..."               │
│    ollama_base_url: "http://localhost:11434"      │
│                                                  │
│  Request Flow:                                   │
│    UI/CLI šalje → { provider?, model?, prompt }  │
│    Ako provider/model nisu zadati → koristi       │
│    default iz settings                            │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌────────────┐ ┌──────────────┐ ┌────────────┐ │
│  │  OpenAI    │ │  Anthropic   │ │   Ollama   │ │
│  │  Client    │ │  Client      │ │   Client   │ │
│  │            │ │              │ │            │ │
│  │ gpt-4o     │ │ claude-sonnet│ │ llama3     │ │
│  │ gpt-4o-mini│ │ claude-haiku │ │ mistral    │ │
│  │ o1         │ │ claude-opus  │ │ codellama  │ │
│  └────────────┘ └──────────────┘ └────────────┘ │
└─────────────────────────────────────────────────┘
```

**Implementacija** (iz oba referentna projekta):

```python
# core/llm/base.py — Apstraktni klijent
class BaseLLMClient(ABC):
    async def chat(self, messages, model, tools=None) -> LLMResponse
    async def embed(self, text) -> list[float]

# core/llm/factory.py — Factory sa BYOK
class LLMFactory:
    def get_client(provider, api_key=None) -> BaseLLMClient
    def get_default_client() -> BaseLLMClient
```

---

## 7. Web UI — izbor stack-a

### Opcija 1: React + Vite + Tailwind + shadcn/ui

| Prednosti | Mane |
|-----------|------|
| Korišćen u zabbix-ai-chat-ui (poznato) | Veći bundle nego Vue |
| shadcn/ui komponente su odlične | — |
| Velika ekosistem, lako naći primere | — |

### Opcija 2: Vue 3 + Vite + Tailwind ⭐ (PREPORUKA)

| Prednosti | Mane |
|-----------|------|
| Konzistentno sa ostalim projektima (companydevs, kosmodrom) | Chat UI primeri češći u React-u |
| Composition API + `<script setup>` = čist kod | — |
| Manji bundle | — |
| Pinia za state (poznato) | — |

### Opcija 3: Nuxt 3

| Prednosti | Mane |
|-----------|------|
| SSR/SSG out of the box | Overkill za personal tool app |
| Poznato iz companydevs-nuxt | Sporiji dev start |
| Auto-imports, file-based routing | Nepotrebna kompleksnost |

**Preporuka: Vue 3 + Vite + Tailwind.** Konzistentno sa workspace stack-om, lagano, bez overkill-a.

### UI folder struktura

```
gandra-tools-ui/
├── index.html
├── package.json
├── vite.config.ts
├── tailwind.config.js
├── tsconfig.json
├── src/
│   ├── App.vue
│   ├── main.ts
│   ├── router/index.ts
│   ├── stores/
│   │   ├── auth.ts            # Auth + JWT
│   │   └── settings.ts        # LLM provider, model, keys
│   ├── composables/
│   │   ├── useChat.ts         # Chat streaming
│   │   ├── useYoutube.ts      # YouTube tool API
│   │   ├── useResearch.ts     # Research tool API
│   │   ├── useImageOps.ts     # Image text extract API
│   │   └── useApi.ts          # Axios/fetch wrapper
│   ├── components/
│   │   ├── chat/              # ChatContainer, MessageBubble, ModelSelector
│   │   ├── layout/            # Sidebar, Header, SettingsPanel
│   │   └── ui/                # Reusable (Button, Input, Card)
│   ├── pages/
│   │   ├── ChatPage.vue
│   │   ├── YoutubePage.vue
│   │   ├── ResearchPage.vue
│   │   ├── FileOpsPage.vue
│   │   ├── ImageOpsPage.vue
│   │   └── SettingsPage.vue
│   └── lib/
│       └── api.ts             # API client config
└── public/
```

---

## 8. Tool kategorije i moduli

```
tools/
├── youtube/          # Kategorija: MEDIA
│   ├── transcript    #   YouTube → tekst sa timestamps
│   └── images        #   YouTube → frame extraction
├── research/         # Kategorija: AI_RESEARCH
│   ├── analyze       #   Multi-link RAG analiza
│   ├── credibility   #   Verodostojnost vesti
│   └── summarize     #   Sažetak sa source tracking
├── fileops/          # Kategorija: FILE_OPERATIONS
│   ├── search        #   Napredna pretraga (naziv, sadržaj, regex)
│   └── rename        #   Batch rename (slugify, prefix, suffix, uppercase)
├── imageops/         # Kategorija: IMAGE_OPERATIONS
│   └── text_extract  #   Ukloni pozadinu, zadrži tekst → transparent PNG
├── devtools/         # Kategorija: DEVELOPER_TOOLS
│   ├── api_test      #   HTTP request tester
│   └── code_review   #   AI code review
└── chat/             # Kategorija: GENERAL
    └── conversation  #   Slobodan razgovor sa AI
```

### Plugin registracija

Svaki tool definiše metadata u `__init__.py`:

```python
# tools/youtube/__init__.py
TOOL_META = {
    "name": "youtube",
    "display_name": "YouTube Tools",
    "category": "media",
    "description": "Extract transcripts and images from YouTube videos",
    "version": "1.0.0",
    "tools": [
        {"name": "transcript", "description": "Extract transcript with timestamps"},
        {"name": "images", "description": "Extract video frames with timestamps"},
    ]
}
```

`main.py` skenira `tools/*/` i automatski:
1. Registruje FastAPI routere (`router.py`)
2. Registruje Typer CLI subcommands (`cli.py`)
3. Izlaže listu alata na `GET /api/v1/tools`

---

## 9. RAG Research — dizajn

Najkompleksniji tool. Kombinuje best practices iz oba referentna projekta.

```
Input:
  ├── Lista linkova (URL-ovi)         # Iz fajla ili direktno
  ├── Ključni delovi teksta           # Opciono, za fokus
  ├── Dubina analize                  # shallow / medium / deep
  └── Fokus                           # credibility / narrative / summary / all

Pipeline:
  1. Web Scraping       → Preuzmi sadržaj svih linkova
  2. Chunking           → Podeli na smislene segmente
  3. Embedding          → Generiši vektore (configurable model)
  4. Vector Store       → Sačuvaj u pgvector ili ChromaDB
  5. LLM Analysis       → Multi-pass analiza:
     ├── Pass 1: Sumarizacija svakog izvora
     ├── Pass 2: Cross-source poređenje
     ├── Pass 3: Verodostojnost + bias detekcija
     └── Pass 4: Finalni izveštaj

Output dokument:
  ┌─────────────────────────────────────┐
  │ 1. EXECUTIVE SUMMARY               │
  │    - Ključni nalaz (3-5 rečenica)  │
  │    - Confidence score               │
  ├─────────────────────────────────────┤
  │ 2. SADRŽAJ                          │
  ├─────────────────────────────────────┤
  │ 3. DETALJNA ANALIZA                 │
  │    - Po izvoru: sažetak, bias, ton │
  │    - Uporedna tabela               │
  ├─────────────────────────────────────┤
  │ 4. NARATIVNE PERSPEKTIVE            │
  │    - Strana A: argumenti, slabosti │
  │    - Strana B: argumenti, slabosti │
  │    - Neutralno: šta se može        │
  │      objektivno potvrditi          │
  ├─────────────────────────────────────┤
  │ 5. VERODOSTOJNOST                   │
  │    - Reliability score po izvoru   │
  │    - Ekstremi i outlier-i          │
  │    - Faktografske provere          │
  ├─────────────────────────────────────┤
  │ 6. ZAKLJUČAK + PREPORUKE           │
  └─────────────────────────────────────┘
```

---

## 9a. YouTube Transcript Tool — detaljan UX flow

YouTube Transcript je referentni tool koji demonstrira kako svaki tool funkcioniše kroz sve 4 invocation metode. Ovde je detaljno razrađen UX za **Web UI** i **Python file** mode.

### Parametri

| Parametar | Tip | Default | Obavezan | Opis |
|-----------|-----|---------|:--------:|------|
| `url` | string | — | Da (jedini obavezan) | YouTube video URL |
| `output_dir` | string | `./output/youtube/` | Ne | Folder gde se čuva rezultat |
| `file_name` | string | auto-generisan | Ne | Ime fajla (bez ekstenzije) |
| `interval_minutes` | int | `2` | Ne | Grupisanje transkripta po minutama |
| `language` | string | `"auto"` | Ne | Jezik transkripta |
| `output_format` | enum | `"md"` | Ne | Format outputa (md, json, txt, html) |

### File name generisanje (default)

Ako `file_name` nije naveden, generiše se automatski:

```
Pravilo: slugify(video_title) + "_" + YYYYMMDD

Primeri:
  Video: "How to Build a REST API with FastAPI"
  →  how-to-build-a-rest-api-with-fastapi_20260403.md

  Video: "Šta je DevOps? (Objašnjenje za početnike)"
  →  sta-je-devops-objasnjenje-za-pocetnike_20260403.md

  Video: "React vs Vue in 2026 🔥"
  →  react-vs-vue-in-2026_20260403.md
```

Slug pravila:
- Lowercase
- Ukloni specijalne karaktere i emotikone
- Razmaci → `-`
- Ćirilica → latinica transliteracija
- Max 80 karaktera (truncate sa `-` na kraju)
- Dupli `-` → single `-`

### a) Web UI — YouTube stranica

```
┌─────────────────────────────────────────────────────────────┐
│  🎬 YouTube Transcript Extractor                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  YouTube URL *                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ https://youtube.com/watch?v=dQw4w9WgXcQ             │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌─── Opcije (collapse/expand) ─────────────────────────┐   │
│  │                                                        │  │
│  │  Output Folder          File Name                      │  │
│  │  ┌──────────────────┐   ┌──────────────────────────┐   │  │
│  │  │ ./output/youtube │   │ (auto: slug_YYYYMMDD)    │   │  │
│  │  └──────────────────┘   └──────────────────────────┘   │  │
│  │                                                        │  │
│  │  Interval (min)   Language      Format                 │  │
│  │  ┌─────┐          ┌─────────┐   ┌──────┐              │  │
│  │  │  2  │          │  Auto   │   │  MD ▾│              │  │
│  │  └─────┘          └─────────┘   └──────┘              │  │
│  │                                                        │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌────────────────┐                                          │
│  │  ▶ Ekstrahuj   │                                          │
│  └────────────────┘                                          │
│                                                              │
│  ── Rezultat ──────────────────────────────────────────────  │
│                                                              │
│  📄 how-to-build-a-rest-api_20260403.md                     │
│  📁 ./output/youtube/                                        │
│  ⏱  14:32 | 8 segmenata | 2847 reči                         │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ ## 00:00 - 02:00                                     │    │
│  │ U ovom videu ćemo napraviti REST API koristeći...    │    │
│  │                                                       │    │
│  │ ## 02:00 - 04:00                                     │    │
│  │ Prvo, instalirajmo FastAPI i uvicorn...               │    │
│  │ ...                                                   │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                    │
│  │ 📋 Copy  │ │ 💾 Save  │ │ ↗ Open   │                    │
│  └──────────┘ └──────────┘ └──────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

**Web UI flow:**
1. Korisnik unosi YouTube URL (jedino obavezno polje)
2. Opcione vrednosti su sakrivene u collapsible sekciji sa pametnim default-ovima
3. Klik "Ekstrahuj" → poziva `POST /api/v1/youtube/transcript`
4. Rezultat se prikazuje u preview-u sa opcijama Copy/Save/Open

### b) Python file — standalone mode

```python
# Pokretanje: python -m gandra_tools.tools.youtube.transcript

# ══════════════════════════════════════════════════════════
# SCENARIO 1: Svi parametri zadati — odmah radi
# ══════════════════════════════════════════════════════════

python -m gandra_tools.tools.youtube.transcript \
    --url "https://youtube.com/watch?v=dQw4w9WgXcQ" \
    --output-dir "./my-transcripts/" \
    --file-name "my-custom-name" \
    --interval 5 \
    --format md

# Rezultat: ./my-transcripts/my-custom-name.md
# Nema pitanja, nema interakcije — odmah izvršava.


# ══════════════════════════════════════════════════════════
# SCENARIO 2: Samo URL — koristi default-ove, odmah radi
# ══════════════════════════════════════════════════════════

python -m gandra_tools.tools.youtube.transcript \
    --url "https://youtube.com/watch?v=dQw4w9WgXcQ"

# Rezultat: ./output/youtube/how-to-build-a-rest-api_20260403.md
# URL je dovoljan, svi ostali imaju default → odmah izvršava.


# ══════════════════════════════════════════════════════════
# SCENARIO 3: Bez parametara — interaktivni mode
# ══════════════════════════════════════════════════════════

python -m gandra_tools.tools.youtube.transcript

# Program pita redom:
#
# 🎬 YouTube Transcript Extractor
# ─────────────────────────────────
#
# YouTube URL: █                              ← Obavezno, čeka unos
#   > https://youtube.com/watch?v=dQw4w9WgXcQ
#
# Output folder [./output/youtube/]: █        ← Enter = default
#   >                                         ← (Enter → koristi default)
#
# File name [how-to-build-a-rest-api_20260403]: █
#   > moj-transkript                          ← Ili Enter za auto
#
# Interval (min) [2]: █
#   >                                         ← (Enter → 2)
#
# Format (md/json/txt/html) [md]: █
#   >                                         ← (Enter → md)
#
# ✅ Sačuvano: ./output/youtube/moj-transkript.md
# ⏱  14:32 | 8 segmenata | 2847 reči
```

### Implementacija interactive mode-a

```python
# tools/youtube/transcript.py  (standalone entry point)

from gandra_tools.tools.youtube.service import YouTubeTranscriptService
from gandra_tools.tools.youtube.schemas import TranscriptInput

def _prompt_for_input() -> TranscriptInput:
    """Interaktivno prikupljanje parametara kad nijedan nije zadat."""
    print("🎬 YouTube Transcript Extractor")
    print("─" * 35)

    url = input("YouTube URL: ").strip()
    if not url:
        print("❌ URL je obavezan.")
        sys.exit(1)

    output_dir = input(f"Output folder [{DEFAULT_OUTPUT_DIR}]: ").strip()
    output_dir = output_dir or DEFAULT_OUTPUT_DIR

    # Za file_name treba prvo fetch-ovati video title za preview
    default_name = generate_default_filename(url)  # Placeholder dok ne fetchujemo title
    file_name = input(f"File name [{default_name}]: ").strip()
    file_name = file_name or None  # None → auto-generate posle fetch

    interval = input("Interval (min) [2]: ").strip()
    interval = int(interval) if interval else 2

    fmt = input("Format (md/json/txt/html) [md]: ").strip()
    fmt = fmt or "md"

    return TranscriptInput(
        url=url,
        output_dir=output_dir,
        file_name=file_name,
        interval_minutes=interval,
        output_format=fmt,
    )

def main():
    import sys
    args = parse_args(sys.argv[1:])  # argparse ili typer standalone

    if args.url:
        # Ima URL → odmah izvršava (ostalo ima default)
        input_data = TranscriptInput(
            url=args.url,
            output_dir=args.output_dir,     # default ako None
            file_name=args.file_name,        # auto-generate ako None
            interval_minutes=args.interval,
            output_format=args.format,
        )
    else:
        # Nema parametara → interaktivni mode
        input_data = _prompt_for_input()

    # Izvrši
    service = YouTubeTranscriptService()
    result = service.extract(input_data)

    print(f"\n✅ Sačuvano: {result.file_path}")
    print(f"⏱  {result.duration_formatted} | {result.segment_count} segmenata | {result.word_count} reči")

if __name__ == "__main__":
    main()
```

### Decision flow dijagram

```
python -m gandra_tools.tools.youtube.transcript [args...]
                          │
                          ▼
                   ┌──────────────┐
                   │  Ima --url?  │
                   └──────┬───────┘
                    yes   │   no
              ┌───────────┴──────────┐
              ▼                      ▼
     ┌─────────────────┐   ┌──────────────────┐
     │ Popuni defaults │   │ Interactive mode  │
     │ za ostale params│   │ Pitaj redom:      │
     │                 │   │  1. url (required) │
     │ output_dir →    │   │  2. output_dir    │
     │  ./output/yt/   │   │  3. file_name     │
     │ file_name →     │   │  4. interval      │
     │  slug_YYYYMMDD  │   │  5. format        │
     │ interval → 2    │   │                   │
     │ format → md     │   │ Enter = default   │
     └────────┬────────┘   └────────┬──────────┘
              │                      │
              └──────────┬───────────┘
                         ▼
              ┌──────────────────────┐
              │ Pydantic validation  │
              │ TranscriptInput      │
              └──────────┬───────────┘
                         ▼
              ┌──────────────────────┐
              │ YouTubeTranscript    │
              │ Service.extract()    │
              └──────────┬───────────┘
                         ▼
              ┌──────────────────────┐
              │ Publisher.publish()  │
              │ format → file       │
              └──────────────────────┘
```

### Ažurirana YouTube schema

```python
# tools/youtube/schemas.py

from datetime import date

DEFAULT_OUTPUT_DIR = "./output/youtube/"

class TranscriptInput(ToolInputBase):
    """Input za YouTube transcript ekstrakciju."""
    url: HttpUrl                                               # OBAVEZNO
    output_dir: str = Field(default=DEFAULT_OUTPUT_DIR)        # Gde čuvati
    file_name: str | None = None                               # None = auto-generate
    interval_minutes: int = Field(default=2, ge=1, le=30)
    language: str = Field(default="auto")
    include_timestamps: bool = True
    merge_short_segments: bool = True

    @field_validator("url")
    @classmethod
    def validate_youtube_url(cls, v):
        url_str = str(v)
        if "youtube.com" not in url_str and "youtu.be" not in url_str:
            raise ValueError("URL mora biti YouTube link")
        return v

    def get_resolved_file_name(self, video_title: str) -> str:
        """Vrati file name: eksplicitni ili auto-generisani."""
        if self.file_name:
            return self.file_name
        slug = slugify(video_title, max_length=80)
        return f"{slug}_{date.today():%Y%m%d}"

    def get_full_output_path(self, video_title: str) -> Path:
        """Puna putanja: output_dir / file_name.format"""
        name = self.get_resolved_file_name(video_title)
        ext = self.output_format.value  # "md", "json", "txt", "html"
        return Path(self.output_dir) / f"{name}.{ext}"


class TranscriptOutput(BaseModel):
    """Output za YouTube transcript."""
    video_title: str
    video_url: str
    video_duration_seconds: int
    duration_formatted: str                # "14:32"
    language: str
    segment_count: int
    word_count: int
    segments: list[TranscriptSegment]
    full_text: str                         # Kompletni tekst bez timestamps
    file_path: str | None                  # Gde je sačuvano
    metadata: dict

class TranscriptSegment(BaseModel):
    start_time: float                      # Sekunde
    end_time: float
    start_formatted: str                   # "00:02:30"
    end_formatted: str                     # "00:04:00"
    text: str
```

### Svi invocation načini — uporedni pregled za YouTube tool

```
┌──────────────────┬──────────────────────────────────────────────────┐
│  Web UI          │  Forma sa URL (obavezan) + collapsible opcije   │
│                  │  Klik → API poziv → preview + Save/Copy/Open    │
├──────────────────┼──────────────────────────────────────────────────┤
│  REST API        │  POST /api/v1/youtube/transcript                │
│                  │  Body: { url, output_dir?, file_name?,          │
│                  │          interval?, format? }                    │
│                  │  Samo url je obavezan, ostalo ima defaults      │
├──────────────────┼──────────────────────────────────────────────────┤
│  CLI (Typer)     │  gandra-tools youtube transcript --url "..."    │
│                  │  Svi flag-ovi opcioni osim --url                 │
│                  │  Bez --url → error sa usage help               │
├──────────────────┼──────────────────────────────────────────────────┤
│  Python file     │  python -m gandra_tools.tools.youtube.transcript│
│                  │  Sa --url → odmah izvršava (defaults za ostalo) │
│                  │  Bez args → interaktivni mode (pita redom)     │
└──────────────────┴──────────────────────────────────────────────────┘
```

**Ključna razlika:** Python file mode je jedini koji ima **interactive fallback**. Web UI, API i CLI zahtevaju da `url` bude uvek eksplicitno zadat (jer su non-interactive po prirodi).

---

## 9b. Image Text Extractor Tool — detaljan dizajn

### Koncept

Alat koji prima sliku (screenshot, foto dokumenta, whiteboard, meme...), detektuje tekstualne regione, uklanja pozadinu i generiše **PNG sa tekstom na transparent background**. Korisno za:
- Izvlačenje teksta iz screenshot-ova za overlay u prezentacije
- Čist tekst layer iz foto-dokumenta
- Izdvajanje teksta sa meme/infografika za dalju obradu
- Priprema tekst-overlay-a za video editing

### Pipeline

```
Input slika                    Output PNG
┌─────────────────┐           ┌─────────────────┐
│                  │           │ (transparent)    │
│  Hello World!   │    ──▶    │  Hello World!   │
│  ┌──────────┐   │           │                  │
│  │  photo   │   │           │  Some text here  │
│  └──────────┘   │           │                  │
│  Some text here │           │                  │
└─────────────────┘           └─────────────────┘
  (sa pozadinom)               (samo tekst, bg=transparent)
```

### Pristupi za implementaciju

#### Pristup A: OCR + Rendering ⭐ (PREPORUKA)

```
Input → OCR (detektuj tekst + pozicije) → Renderuj tekst na transparent canvas
```

| Korak | Opis | Biblioteka |
|-------|------|------------|
| 1. OCR detekcija | Prepoznaj tekst, bounding box-ove, font size | EasyOCR ili Tesseract |
| 2. Font matching | Proceni font, veličinu, boju iz originala | OpenCV analiza |
| 3. Rendering | Nacrtaj tekst na RGBA transparent sliku | Pillow (PIL) |

| Prednosti | Mane |
|-----------|------|
| Čist vektorski tekst na outputu | OCR može pogrešiti |
| Manja veličina fajla | Font matching je aproksimacija |
| Tekst je re-editable (ako se čuva i OCR result) | Složeni layout-i teži |
| Radi offline (EasyOCR) | — |

#### Pristup B: Segmentacija piksela (mask-based)

```
Input → Detektuj tekst regione → Mask pozadinu → Zadrži samo tekst piksele
```

| Korak | Opis | Biblioteka |
|-------|------|------------|
| 1. Text detection | Nađi bounding box-ove teksta | EAST / CRAFT detector |
| 2. Segmentacija | Razdvoji tekst piksele od pozadine | OpenCV / GrabCut |
| 3. Mask apply | Primeni masku, pozadina → transparent | Pillow RGBA |

| Prednosti | Mane |
|-----------|------|
| Zadržava originalni izgled teksta (font, stil) | Piksel-based, ne vektorski |
| Ne zavisi od OCR tačnosti | Veća veličina fajla |
| Bolji za stilizovan tekst / handwriting | Može zahvatiti artefakte pozadine |

#### Pristup C: Hibridni (OCR + segment) — za buduće verzije

Kombinacija: OCR za čist tekst, segmentacija za stilizovane/rukopisne delove.

**Preporuka: Pristup A (OCR + Rendering)** za v1.0 jer daje najčistiji output i radi offline. Pristup B se može dodati kao alternativni `mode` parametar.

### Parametri

| Parametar | Tip | Default | Obavezan | Opis |
|-----------|-----|---------|:--------:|------|
| `image_path` | string | — | Da | Putanja do input slike (ili URL) |
| `output_dir` | string | `./output/imageops/` | Ne | Folder za output |
| `file_name` | string | auto-generisan | Ne | Ime output fajla (bez .png) |
| `mode` | enum | `"ocr"` | Ne | `"ocr"` (render) ili `"mask"` (pixel segmentation) |
| `language` | string | `"auto"` | Ne | OCR jezik hint (`"sr"`, `"en"`, `"auto"`) |
| `font_color` | string | `"auto"` | Ne | `"auto"` (iz originala), `"black"`, hex (#FF0000) |
| `min_confidence` | float | `0.5` | Ne | Min OCR confidence za uključivanje teksta |
| `preserve_layout` | bool | `True` | Ne | Zadrži originalne pozicije teksta |
| `extract_text` | bool | `True` | Ne | Uz PNG, vrati i čist tekst (string) |
| `dpi` | int | `300` | Ne | Rezolucija output PNG |

### File name generisanje (default)

```
Pravilo: slugify(input_filename_bez_ext) + "_text_" + YYYYMMDD

Primeri:
  Input: "screenshot_meeting.jpg"
  →  screenshot-meeting_text_20260403.png

  Input: "IMG_20260403_142530.jpg"
  →  img-20260403-142530_text_20260403.png

  Input: URL slika (https://example.com/photo.jpg)
  →  photo_text_20260403.png
```

### Schemas

```python
# tools/imageops/schemas.py

class ImageTextExtractInput(ToolInputBase):
    """Input za ekstrakciju teksta sa slike."""
    image_path: str                                          # OBAVEZNO: putanja ili URL
    output_dir: str = Field(default="./output/imageops/")
    file_name: str | None = None                             # None = auto-generate
    mode: ImageExtractMode = ImageExtractMode.OCR
    language: str = Field(default="auto")
    font_color: str = Field(default="auto")                  # "auto", "black", "#FF0000"
    min_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    preserve_layout: bool = True
    extract_text: bool = True
    dpi: int = Field(default=300, ge=72, le=600)

    @field_validator("image_path")
    @classmethod
    def validate_image_path(cls, v):
        if v.startswith(("http://", "https://")):
            return v  # URL — biće downloadovana
        path = Path(v)
        if not path.exists():
            raise ValueError(f"Fajl ne postoji: {v}")
        if path.suffix.lower() not in (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"):
            raise ValueError(f"Nepodržan format slike: {path.suffix}")
        return v

class ImageExtractMode(str, Enum):
    OCR = "ocr"        # OCR → render tekst na transparent
    MASK = "mask"       # Pixel segmentacija → mask pozadinu

class TextRegion(BaseModel):
    """Detektovani tekstualni region."""
    text: str
    confidence: float
    bbox: tuple[int, int, int, int]       # (x1, y1, x2, y2)
    font_size_estimate: int | None
    color_hex: str | None                 # Detektovana boja teksta

class ImageTextExtractOutput(BaseModel):
    """Output sa rezultatom ekstrakcije."""
    output_path: str                       # Putanja do generisanog PNG
    input_path: str
    mode: ImageExtractMode
    image_dimensions: tuple[int, int]      # (width, height) output slike
    regions_detected: int
    regions_included: int                  # Posle confidence filtera
    extracted_text: str | None             # Sav tekst kao string (ako extract_text=True)
    regions: list[TextRegion]
    processing_time_ms: int
    file_size_bytes: int
```

### Web UI — ImageOps stranica

```
┌─────────────────────────────────────────────────────────────┐
│  🖼️ Image Text Extractor                                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Upload sliku ili unesi URL                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  📁 Drag & drop ili klikni za upload                │    │
│  │     (.png, .jpg, .bmp, .tiff, .webp)               │    │
│  └─────────────────────────────────────────────────────┘    │
│  ili URL: ┌──────────────────────────────────────────┐      │
│           │ https://example.com/image.jpg            │      │
│           └──────────────────────────────────────────┘      │
│                                                              │
│  ┌─── Opcije (collapse) ────────────────────────────────┐   │
│  │  Mode              Language         Font Color        │  │
│  │  ┌──────────┐      ┌─────────┐      ┌──────────┐     │  │
│  │  │  OCR  ▾ │      │  Auto  ▾│      │  Auto  ▾│     │  │
│  │  └──────────┘      └─────────┘      └──────────┘     │  │
│  │                                                        │  │
│  │  Min Confidence    DPI        Preserve Layout          │  │
│  │  ┌─────┐           ┌─────┐   ☑ Da                     │  │
│  │  │ 0.5 │           │ 300 │                             │  │
│  │  └─────┘           └─────┘                             │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌────────────────┐                                          │
│  │  ▶ Ekstrahuj   │                                          │
│  └────────────────┘                                          │
│                                                              │
│  ── Rezultat ──────────────────────────────────────────────  │
│                                                              │
│  ┌────────────────────────┬────────────────────────────┐    │
│  │      ORIGINAL          │      REZULTAT (PNG)        │    │
│  │  ┌──────────────────┐  │  ┌──────────────────┐      │    │
│  │  │                  │  │  │ (checkerboard bg) │      │    │
│  │  │  Hello World!   │  │  │  Hello World!     │      │    │
│  │  │  ┌──────────┐   │  │  │                   │      │    │
│  │  │  │  photo   │   │  │  │  Some text here   │      │    │
│  │  │  └──────────┘   │  │  │                   │      │    │
│  │  │  Some text here │  │  │                   │      │    │
│  │  └──────────────────┘  │  └──────────────────┘      │    │
│  └────────────────────────┴────────────────────────────┘    │
│                                                              │
│  📊 12 regiona detektovano | 10 uključeno (conf > 0.5)     │
│  📝 Extracted text: "Hello World! Some text here"            │
│                                                              │
│  ┌──────────┐ ┌──────────────┐ ┌──────────┐                │
│  │ 💾 Save  │ │ 📋 Copy Text │ │ ↗ Open   │                │
│  └──────────┘ └──────────────┘ └──────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

### Python file — standalone mode

```python
# ══════════════════════════════════════════════════════════
# SCENARIO 1: Sa parametrima — odmah radi
# ══════════════════════════════════════════════════════════

python -m gandra_tools.tools.imageops.text_extract \
    --image "./screenshots/meeting_notes.jpg" \
    --mode ocr \
    --font-color black \
    --dpi 300

# Rezultat: ./output/imageops/meeting-notes_text_20260403.png


# ══════════════════════════════════════════════════════════
# SCENARIO 2: Samo slika — odmah radi sa defaults
# ══════════════════════════════════════════════════════════

python -m gandra_tools.tools.imageops.text_extract \
    --image "./photo.jpg"

# Rezultat: ./output/imageops/photo_text_20260403.png


# ══════════════════════════════════════════════════════════
# SCENARIO 3: Bez parametara — interaktivni mode
# ══════════════════════════════════════════════════════════

python -m gandra_tools.tools.imageops.text_extract

# 🖼️ Image Text Extractor
# ─────────────────────────
#
# Image path or URL: █
#   > ./screenshots/meeting_notes.jpg
#
# Output folder [./output/imageops/]: █
#   >                                          ← (Enter → default)
#
# Mode (ocr/mask) [ocr]: █
#   >                                          ← (Enter → ocr)
#
# Language [auto]: █
#   >                                          ← (Enter → auto)
#
# ✅ Sačuvano: ./output/imageops/meeting-notes_text_20260403.png
# 📊 12 regiona | 10 uključeno | 847ms
# 📝 "Hello World! Some text here..."
```

### Zavisnosti (Python paketi)

```toml
# pyproject.toml — dodatni dependencies za imageops
[project.optional-dependencies]
imageops = [
    "easyocr>=1.7",           # OCR engine (offline, multilingual)
    "Pillow>=10.0",           # Image manipulation, RGBA rendering
    "opencv-python>=4.8",     # Text detection, segmentacija, font analysis
]
```

**Napomena:** EasyOCR je ~100MB download (modeli). Prvi pokretanje downloaduje model za odabrani jezik. Podržava 80+ jezika uključujući srpski (ćirilica i latinica).

### Tech stack izbor za OCR

| Biblioteka | Offline | Brzina | Tačnost | Srpski | Veličina |
|-----------|:-------:|--------|---------|:------:|----------|
| **EasyOCR** ⭐ | Da | Srednja | Visoka | Da (sr) | ~100MB |
| Tesseract | Da | Brza | Srednja | Da | ~30MB |
| Google Vision API | Ne | Brza | Vrlo visoka | Da | 0 (API) |
| PaddleOCR | Da | Brza | Visoka | Ne | ~150MB |

**Preporuka: EasyOCR** — offline, dobar za srpski, visoka tačnost, dobra bounding box detekcija.

---

## 10. Publisher modul — multi-format output

### Koncept

Publisher je **core modul** (ne tool-specifičan) koji prima strukturiran rezultat bilo kog procesa i generiše output u traženom formatu. Dizajniran je kao reusable komponenta koja se može koristiti:
- Iz RAG research tool-a (publikacija analize)
- Iz YouTube transcript tool-a (export transkripta)
- Iz bilo kog budućeg tool-a ili čak drugog projekta

```
┌──────────────────────────────────────────────────────────────┐
│                     PUBLISHER MODUL                           │
│                                                               │
│  Pozicija: core/publisher/  (NE u tools/, jer je shared)     │
│  Razlog: svaki tool ga može koristiti, reusable cross-project│
│                                                               │
│  ┌─────────────┐     ┌───────────────┐     ┌──────────────┐ │
│  │ PublishReq   │────▶│  Publisher    │────▶│  Formatters  │ │
│  │              │     │  Service      │     │              │ │
│  │ content      │     │              │     │ ┌──────────┐ │ │
│  │ format       │     │ validate()   │     │ │ JSON     │ │ │
│  │ template     │     │ render()     │     │ │ Markdown │ │ │
│  │ metadata     │     │ export()     │     │ │ TXT      │ │ │
│  │ output_path  │     │              │     │ │ HTML     │ │ │
│  └─────────────┘     └───────────────┘     │ │ PDF (v2) │ │ │
│                                             │ └──────────┘ │ │
│                                             └──────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

### Podržani formati

| Format | Ekstenzija | Opis | Biblioteka |
|--------|-----------|------|------------|
| **JSON** | `.json` | Strukturirani podaci, mašinski čitljiv | stdlib `json` |
| **Markdown** | `.md` | Čitljiv dokument sa formatiranjem | Jinja2 templates |
| **Plain Text** | `.txt` | Čist tekst bez formatiranja | Jinja2 templates |
| **HTML** | `.html` | Web-ready sa CSS stilizacijom | Jinja2 + inline CSS |
| **PDF** | `.pdf` | Print-ready (faza 2) | weasyprint ili reportlab |

### Arhitektura

```python
# core/publisher/__init__.py
# core/publisher/service.py        — PublisherService (orchestrator)
# core/publisher/formatters/
#   ├── __init__.py
#   ├── base.py                    — BaseFormatter ABC
#   ├── json_formatter.py
#   ├── markdown_formatter.py
#   ├── text_formatter.py
#   └── html_formatter.py
# core/publisher/templates/        — Jinja2 šabloni
#   ├── research_analysis.md.j2
#   ├── research_analysis.html.j2
#   ├── research_analysis.txt.j2
#   ├── youtube_transcript.md.j2
#   └── generic.md.j2             — Fallback šablon
# core/publisher/schemas.py        — PublishRequest, PublishResponse, FormatEnum
```

### PublisherService API

```python
from enum import Enum
from pydantic import BaseModel

class OutputFormat(str, Enum):
    JSON = "json"
    MARKDOWN = "md"
    TEXT = "txt"
    HTML = "html"

class PublishRequest(BaseModel):
    """Zahtev za publikaciju."""
    content: dict                          # Strukturirani sadržaj (tool-specific)
    content_type: str                      # "research_analysis", "youtube_transcript", ...
    format: OutputFormat                   # Traženi output format
    template: str | None = None            # Custom šablon (override default)
    output_path: str | None = None         # Gde sačuvati (None = return in response)
    metadata: dict | None = None           # Autor, datum, tags, verzija
    options: dict | None = None            # Format-specifične opcije (CSS theme, indent...)

class PublishResponse(BaseModel):
    """Rezultat publikacije."""
    format: OutputFormat
    content: str                           # Renderovani sadržaj
    file_path: str | None                  # Ako je sačuvan na disk
    size_bytes: int
    content_type_mime: str                 # "application/json", "text/markdown", ...

class PublisherService:
    def publish(self, request: PublishRequest) -> PublishResponse: ...
    def publish_multi(self, content, content_type, formats: list[OutputFormat]) -> list[PublishResponse]: ...
    def list_templates(self, content_type: str) -> list[str]: ...
    def get_supported_formats(self) -> list[OutputFormat]: ...
```

### Primer korišćenja iz tool-a

```python
# tools/research/service.py
from gandra_tools.core.publisher.service import PublisherService, OutputFormat

class ResearchService:
    def __init__(self):
        self.publisher = PublisherService()

    async def analyze_and_publish(self, links, depth, format=OutputFormat.MARKDOWN):
        # 1. Izvrši RAG analizu
        analysis_result = await self._run_analysis(links, depth)

        # 2. Publikuj u traženom formatu
        response = self.publisher.publish(PublishRequest(
            content=analysis_result.model_dump(),
            content_type="research_analysis",
            format=format,
            output_path=f"./output/analysis_{datetime.now():%Y%m%d_%H%M}.{format.value}",
            metadata={"author": "gandra-tools", "sources": len(links)}
        ))
        return response
```

### Primer korišćenja iz CLI

```bash
# Publikuj postojeći JSON rezultat u Markdown
gandra-tools publish ./output/analysis.json --format md --output ./output/analysis.md

# Multi-format export
gandra-tools publish ./output/analysis.json --format md,html,txt --output-dir ./output/

# Sa custom šablonom
gandra-tools publish ./output/analysis.json --format html --template custom_report.html.j2
```

### REST API endpoint

```
POST /api/v1/publish
  Body: PublishRequest
  Response: PublishResponse

POST /api/v1/publish/multi
  Body: { content, content_type, formats: ["md", "html", "json"] }
  Response: PublishResponse[]

GET  /api/v1/publish/formats
  Response: ["json", "md", "txt", "html"]

GET  /api/v1/publish/templates?content_type=research_analysis
  Response: ["research_analysis.md.j2", "research_analysis.html.j2", ...]
```

### Reusability — korišćenje u drugim projektima

Publisher modul je dizajniran da se može izvući kao standalone package:

```python
# Opcija A: Direktan import (isti workspace)
from gandra_tools.core.publisher import PublisherService

# Opcija B: Kao pip package (buduće)
# pip install gandra-publisher
# from gandra_publisher import PublisherService
```

Za korišćenje u drugom projektu, potrebno je samo:
1. Definisati Jinja2 šablon za svoj `content_type`
2. Proslediti strukturirani `content` dict
3. Publisher se brine za renderovanje i export

---

## 11. Input specifikacija i validacija

### Koncept: Typed Input Definitions

Svaki tool ima svoju **input definiciju** (Pydantic schema) koja specificira:
- Obavezna i opciona polja
- Validacione pravila
- Default vrednosti
- Opis (za Swagger docs i CLI help)

### Bazni input model

```python
# models/schemas.py — Shared base

class ToolInputBase(BaseModel):
    """Bazni model za sve tool inpute."""
    model_config = ConfigDict(extra="forbid")  # Odbij nepoznata polja

    # Opcioni LLM override (BYOK)
    llm_provider: str | None = None       # "openai" | "anthropic" | "ollama"
    llm_model: str | None = None          # "gpt-4o" | "claude-sonnet-4-6" | ...
    llm_api_key: str | None = None        # Override za BYOK key

    # Opcioni output
    output_format: OutputFormat = OutputFormat.MARKDOWN
    output_path: str | None = None
```

### Input definicije po use case-u

#### YouTube Transcript

> **Detaljno razrađeno u sekciji 9a** — uključuje parametre, defaults, file naming, Web UI wireframe, Python interactive mode, decision flow dijagram.

Referenca: `TranscriptInput` i `TranscriptOutput` schemas su definisane u sekciji 9a sa svim poljima, validacijom i `get_resolved_file_name()` / `get_full_output_path()` metodama.

#### RAG Research — analiza članaka

```python
# tools/research/schemas.py

class ResearchAnalysisInput(ToolInputBase):
    """Input za RAG analizu članaka/vesti."""
    links: list[HttpUrl] = Field(..., min_length=1, max_length=50)
    annotations: list[LinkAnnotation] | None = None      # Opcione napomene po linku
    depth: AnalysisDepth = AnalysisDepth.MEDIUM
    focus: list[AnalysisFocus] = [AnalysisFocus.ALL]
    language: str = "sr"                                  # Jezik izveštaja
    max_tokens_per_source: int = Field(default=4000, le=16000)

class LinkAnnotation(BaseModel):
    """Napomena za specifičan link — fokus, kontekst."""
    url: HttpUrl
    note: str | None = None              # "Ovo je pro-X narativ"
    key_quotes: list[str] | None = None  # Bitni delovi teksta

class AnalysisDepth(str, Enum):
    SHALLOW = "shallow"     # Samo sumarizacija
    MEDIUM = "medium"       # Sumarizacija + poređenje
    DEEP = "deep"           # Pun pipeline (verodostojnost, narativ, bias)

class AnalysisFocus(str, Enum):
    ALL = "all"
    CREDIBILITY = "credibility"      # Verodostojnost, reliability
    NARRATIVE = "narrative"          # Narativne perspektive, strane
    SUMMARY = "summary"              # Samo sažetak
    FACT_CHECK = "fact_check"        # Faktografske provere
    SENTIMENT = "sentiment"          # Ton i sentiment analiza

class ResearchAnalysisOutput(BaseModel):
    """Strukturirani output RAG analize."""
    executive_summary: str
    confidence_score: float              # 0.0 - 1.0
    sources_analyzed: int
    table_of_contents: list[str]
    detailed_analysis: list[SourceAnalysis]
    narrative_perspectives: list[NarrativePerspective] | None
    credibility_assessment: CredibilityReport | None
    conclusion: str
    recommendations: list[str]
    metadata: AnalysisMetadata

class SourceAnalysis(BaseModel):
    url: str
    title: str
    summary: str
    bias_indicators: list[str]
    tone: str                            # "neutral", "positive", "negative", "sensational"
    reliability_score: float             # 0.0 - 1.0
    key_claims: list[str]

class NarrativePerspective(BaseModel):
    label: str                           # "Strana A", "Strana B", "Neutralno"
    description: str
    arguments: list[str]
    weaknesses: list[str]
    supporting_sources: list[str]

class CredibilityReport(BaseModel):
    overall_score: float
    per_source_scores: dict[str, float]  # url → score
    extremes: list[str]                  # Outlier stavovi
    verifiable_facts: list[FactCheck]

class FactCheck(BaseModel):
    claim: str
    verdict: str                         # "confirmed", "unconfirmed", "disputed", "false"
    evidence: str
```

#### Image Text Extract

> **Detaljno razrađeno u sekciji 9b** — uključuje pipeline (OCR vs mask), parametar tabelu, schemas (`ImageTextExtractInput`, `ImageTextExtractOutput`, `TextRegion`), Web UI wireframe, Python interactive mode, tech stack izbor za OCR.

#### Generički input — budući use case-ovi

```python
# tools/devtools/schemas.py

class CodeReviewInput(ToolInputBase):
    """Input za AI code review."""
    path: str                                    # Fajl ili folder
    language: str | None = None                  # Auto-detect ako None
    focus: list[str] = ["bugs", "security", "performance"]
    max_files: int = Field(default=10, le=50)
    ignore_patterns: list[str] = ["*.test.*", "__pycache__"]

class ApiTestInput(ToolInputBase):
    """Input za API testiranje."""
    method: str = Field(..., pattern="^(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)$")
    url: HttpUrl
    headers: dict[str, str] | None = None
    body: dict | str | None = None
    expected_status: int | None = None
    timeout_seconds: int = Field(default=30, le=120)
    repeat: int = Field(default=1, ge=1, le=100)

class FileRenameInput(ToolInputBase):
    """Input za batch rename."""
    path: str
    strategy: RenameStrategy
    prefix: str | None = None
    suffix: str | None = None
    pattern: str | None = None           # Regex za match
    replacement: str | None = None       # Regex replacement
    dry_run: bool = True                 # Samo prikaži šta bi se desilo
    recursive: bool = False

class RenameStrategy(str, Enum):
    SLUGIFY = "slugify"
    UPPERCASE = "uppercase"
    LOWERCASE = "lowercase"
    SNAKE_CASE = "snake_case"
    KEBAB_CASE = "kebab-case"
    CAMEL_CASE = "camelCase"
    PREFIX = "prefix"
    SUFFIX = "suffix"
    REGEX = "regex"
    DATE_PREFIX = "date_prefix"          # "2026-04-03_filename"
```

### Validacioni dijagram

```
Input Request
     │
     ▼
┌────────────────┐
│ Pydantic       │ ── Schema validacija (tipovi, required, ranges)
│ Validation     │    Automatski iz field definitions
└───────┬────────┘
        │ PASS
        ▼
┌────────────────┐
│ Business       │ ── Custom validatori (@field_validator)
│ Validation     │    Npr: YouTube URL format, max links, valid paths
└───────┬────────┘
        │ PASS
        ▼
┌────────────────┐
│ LLM Provider   │ ── Provera da provider/model kombinacija postoji
│ Validation     │    Provera BYOK key validity (dry-call)
└───────┬────────┘
        │ PASS
        ▼
┌────────────────┐
│ Tool Service   │ ── Executes the tool logic
│ Execution      │
└────────────────┘

Na svakom nivou → 422 Unprocessable Entity sa detaljnim error opisom
```

### Input validacija — error response format

```json
{
    "detail": [
        {
            "loc": ["body", "links", 0],
            "msg": "Invalid URL: not a valid HTTP URL",
            "type": "value_error",
            "input": "not-a-url"
        },
        {
            "loc": ["body", "depth"],
            "msg": "Input should be 'shallow', 'medium' or 'deep'",
            "type": "enum",
            "input": "ultra"
        }
    ]
}
```

### Više input definicija za različite providere — pristup

Umesto da pravimo odvojene input klase po LLM provideru, koristimo **unified input sa opcionalnim provider override-om**:

```
┌────────────────────────────────────────────────────────┐
│                   Unified Input Model                   │
│                                                         │
│  ToolInputBase (shared):                                │
│    llm_provider: optional   ──┐                         │
│    llm_model: optional        │  Ako nisu zadati,       │
│    llm_api_key: optional    ──┘  koristi default iz     │
│                                   user settings         │
│                                                         │
│  ResearchAnalysisInput (tool-specific):                 │
│    links, depth, focus...    ── Tool logika je ista     │
│                                  nezavisno od providera │
└────────────────────────────────────────────────────────┘
```

**Obrazloženje:** Tool logika (YouTube ekstrakcija, RAG analiza) je **ista** bez obzira koji LLM se koristi. Razlika je samo u `llm_provider` + `llm_model` polju. Nema smisla praviti `ResearchAnalysisOpenAIInput` vs `ResearchAnalysisClaudeInput` jer su identični osim tog jednog polja.

Izuzetak: ako neki provider zahteva **specifične parametre** (npr. Ollama `num_ctx`, OpenAI `temperature`), ti se prosleđuju kroz generički `llm_options` dict:

```python
class ToolInputBase(BaseModel):
    llm_provider: str | None = None
    llm_model: str | None = None
    llm_api_key: str | None = None
    llm_options: dict | None = None      # Provider-specifične opcije
    # Primeri llm_options:
    # OpenAI:    {"temperature": 0.7, "max_tokens": 4000}
    # Anthropic: {"temperature": 0.7, "max_tokens": 4000}
    # Ollama:    {"temperature": 0.7, "num_ctx": 8192, "num_predict": 2048}
```

---

## 12. Test plan

### Struktura testova

```
tests/
├── __init__.py
├── conftest.py                    # Shared fixtures (test client, mock LLM, temp dirs)
├── unit/                          # Brzi, bez eksternih zavisnosti
│   ├── __init__.py
│   ├── core/
│   │   ├── test_config.py         # Settings loading, defaults, env override
│   │   ├── test_auth.py           # JWT create/verify, password hashing
│   │   ├── test_plugin_registry.py # Autodiscovery, registration
│   │   └── test_llm_factory.py    # Factory routing, provider selection
│   ├── publisher/
│   │   ├── test_json_formatter.py
│   │   ├── test_markdown_formatter.py
│   │   ├── test_text_formatter.py
│   │   ├── test_html_formatter.py
│   │   ├── test_publisher_service.py
│   │   └── test_templates.py      # Jinja2 template rendering
│   ├── tools/
│   │   ├── test_youtube_schemas.py    # Input validacija
│   │   ├── test_youtube_service.py    # Logika (mocked YT API)
│   │   ├── test_research_schemas.py   # Input validacija
│   │   ├── test_research_service.py   # RAG pipeline (mocked LLM + scraper)
│   │   ├── test_fileops_search.py
│   │   ├── test_fileops_rename.py     # Dry-run strategije
│   │   └── test_devtools_api_test.py
│   └── models/
│       └── test_schemas.py        # Shared schema validation
├── integration/                   # Zahteva pokrenute servise (Docker)
│   ├── __init__.py
│   ├── test_ollama_client.py      # Pravi pozivi ka Ollama
│   ├── test_openai_client.py      # Pravi pozivi ka OpenAI (rate limited)
│   ├── test_publisher_e2e.py      # Full pipeline: content → format → file
│   ├── test_research_e2e.py       # Scraping + LLM + publish
│   └── test_db_session.py         # SQLite/PostgreSQL session management
├── api/                           # FastAPI TestClient testovi
│   ├── __init__.py
│   ├── test_auth_api.py           # Login, JWT flow
│   ├── test_youtube_api.py        # Router endpoints
│   ├── test_research_api.py
│   ├── test_publish_api.py
│   ├── test_tools_api.py          # GET /api/v1/tools lista
│   └── test_settings_api.py       # BYOK CRUD
└── cli/                           # CLI invocation testovi
    ├── __init__.py
    ├── test_youtube_cli.py        # Typer CliRunner
    ├── test_research_cli.py
    ├── test_fileops_cli.py
    └── test_config_cli.py
```

### Kategorije testova

| Kategorija | Br. testova (target) | Runner | Zavisnosti |
|-----------|---------------------|--------|------------|
| **Unit** | ~115 | `uv run pytest tests/unit/` | Nema (mocked) |
| **Integration** | ~25 | `uv run pytest tests/integration/` | Docker servisi |
| **API** | ~35 | `uv run pytest tests/api/` | Nema (TestClient) |
| **CLI** | ~25 | `uv run pytest tests/cli/` | Nema (CliRunner) |
| **Ukupno** | ~200 | `uv run pytest` | — |

### Ključni test scenariji

#### Publisher modul — prioritet

```
test_json_formatter.py:
  ✓ test_format_research_analysis_to_json        — Puni output, sva polja
  ✓ test_format_with_metadata                     — Metadata u JSON output
  ✓ test_format_empty_content                     — Prazan sadržaj → valid JSON
  ✓ test_format_unicode_content                   — Ćirilica, emotikoni

test_markdown_formatter.py:
  ✓ test_format_research_analysis_to_md           — Headings, tabele, liste
  ✓ test_template_rendering                       — Jinja2 šablon sa varijablama
  ✓ test_custom_template_override                 — User-provided šablon
  ✓ test_table_of_contents_generation             — Auto-generisan TOC

test_html_formatter.py:
  ✓ test_format_with_inline_css                   — Standalone HTML (no external CSS)
  ✓ test_format_with_syntax_highlighting          — Code blokovi
  ✓ test_format_responsive_layout                 — Mobile-friendly

test_publisher_service.py:
  ✓ test_publish_single_format                    — MD output
  ✓ test_publish_multi_format                     — Isti content → JSON + MD + HTML
  ✓ test_publish_to_file                          — Fajl kreiran na disku
  ✓ test_publish_return_content                   — output_path=None → vrati sadržaj
  ✓ test_unknown_content_type_uses_generic        — Fallback šablon
  ✓ test_invalid_format_returns_error             — 422 za nepoznat format
```

#### Input validacija — po tool-u

```
test_youtube_schemas.py:
  ✓ test_valid_youtube_url                        — https://youtube.com/watch?v=...
  ✓ test_invalid_youtube_url_rejected             — random URL → ValidationError
  ✓ test_short_youtube_url                        — https://youtu.be/... OK
  ✓ test_interval_range_validation                — 0 → error, 31 → error, 5 → OK
  ✓ test_defaults_applied                         — interval=2, language="auto", output_dir default
  ✓ test_file_name_auto_generated                 — None → slugified_title_YYYYMMDD
  ✓ test_file_name_explicit                       — "my-name" → koristi eksplicitni
  ✓ test_slugify_unicode_title                    — Ćirilica → latinica, emotikoni uklonjeni
  ✓ test_slugify_max_length                       — Truncate na 80 karaktera
  ✓ test_full_output_path_resolved                — output_dir + file_name + .format

test_youtube_service.py:
  ✓ test_extract_transcript_returns_segments      — Mock YT API → segments sa timestamps
  ✓ test_extract_merges_short_segments            — Segmenti < 5s spojeni
  ✓ test_extract_saves_to_file                    — Publisher pozvan, fajl kreiran
  ✓ test_extract_default_output_dir_created       — ./output/youtube/ kreiran ako ne postoji

test_youtube_interactive.py:  (CLI tests)
  ✓ test_interactive_mode_prompts_all             — Bez args → pita svih 5 pitanja
  ✓ test_url_only_skips_interactive               — Sa --url → odmah izvršava
  ✓ test_partial_args_no_interactive              — --url + --interval → odmah, defaults za ostalo
  ✓ test_interactive_enter_uses_defaults          — Enter na svako pitanje → svi defaults

test_research_schemas.py:
  ✓ test_valid_analysis_input                     — 3 linka, depth=deep
  ✓ test_empty_links_rejected                     — [] → min_length error
  ✓ test_too_many_links_rejected                  — 51 linkova → max_length error
  ✓ test_invalid_url_in_links                     — Jedan loš URL → error sa loc
  ✓ test_annotations_match_links                  — Opcione napomene validne
  ✓ test_all_focus_types_valid                    — Svi AnalysisFocus enum-i

test_fileops_rename.py:
  ✓ test_dry_run_no_changes                       — dry_run=True → 0 fajlova promenjeno
  ✓ test_slugify_strategy                         — "My File (1).txt" → "my-file-1.txt"
  ✓ test_prefix_strategy                          — "file.txt" → "2026_file.txt"
  ✓ test_regex_strategy                           — Pattern match + replace

test_imageops_schemas.py:
  ✓ test_valid_local_image_path                   — ./photo.jpg → OK
  ✓ test_valid_url_image                          — https://...jpg → OK
  ✓ test_nonexistent_file_rejected                — /nope.jpg → ValidationError
  ✓ test_unsupported_format_rejected              — .gif, .svg → error
  ✓ test_confidence_range_validation              — -0.1 → error, 1.1 → error, 0.7 → OK
  ✓ test_dpi_range_validation                     — 50 → error, 700 → error, 300 → OK
  ✓ test_defaults_applied                         — mode=ocr, dpi=300, output_dir default
  ✓ test_file_name_auto_generated                 — None → slugified_input_text_YYYYMMDD

test_imageops_service.py:
  ✓ test_ocr_mode_detects_text_regions            — Mock EasyOCR → TextRegion list
  ✓ test_ocr_mode_renders_transparent_png         — Output je RGBA PNG sa alpha channel
  ✓ test_confidence_filter_excludes_low           — confidence < 0.5 → isključen
  ✓ test_preserve_layout_positions_text           — bbox pozicije korektne
  ✓ test_font_color_auto_detection                — Detektuje dominantnu boju teksta
  ✓ test_font_color_explicit_override             — --font-color black → sav tekst crn
  ✓ test_extract_text_returns_string              — extract_text=True → full text string
  ✓ test_output_file_created                      — PNG fajl kreiran na disku
  ✓ test_mask_mode_pixel_segmentation             — mode=mask → piksel-based output

test_imageops_interactive.py:
  ✓ test_interactive_mode_prompts_all             — Bez args → pita sva pitanja
  ✓ test_image_path_only_skips_interactive        — Sa --image → odmah izvršava
  ✓ test_interactive_enter_uses_defaults          — Enter na svako pitanje → defaults
```

#### LLM i BYOK

```
test_llm_factory.py:
  ✓ test_create_openai_client                     — Factory → OpenAI client
  ✓ test_create_anthropic_client                  — Factory → Anthropic client
  ✓ test_create_ollama_client                     — Factory → Ollama client
  ✓ test_default_provider_from_settings           — No provider in request → use default
  ✓ test_byok_key_override                        — Request API key > settings key
  ✓ test_unknown_provider_error                   — "google" → ValueError
  ✓ test_llm_options_passed_through               — temperature, max_tokens forwarded
```

### Test fixtures (conftest.py)

```python
# tests/conftest.py

@pytest.fixture
def test_client():
    """FastAPI TestClient sa test settings."""
    app.dependency_overrides[get_settings] = lambda: TestSettings()
    with TestClient(app) as client:
        yield client

@pytest.fixture
def mock_llm():
    """Mocked LLM client — vraća predefinisan odgovor."""
    with patch("gandra_tools.core.llm.factory.LLMFactory") as mock:
        client = AsyncMock()
        client.chat.return_value = LLMResponse(content="Test response", ...)
        mock.get_client.return_value = client
        yield client

@pytest.fixture
def temp_output_dir(tmp_path):
    """Privremeni folder za publisher output."""
    return tmp_path / "output"

@pytest.fixture
def sample_research_result():
    """Fiksiran RAG analysis result za publisher testove."""
    return { "executive_summary": "...", "sources_analyzed": 5, ... }
```

### CI pipeline (buduće)

```bash
# Brzi testovi (< 30s) — svaki PR
uv run pytest tests/unit/ tests/api/ tests/cli/ -x --timeout=10

# Puni testovi (sa integracijom) — pre merge
docker compose -f docker-compose-local.yml up -d ollama postgres
uv run pytest --timeout=60
docker compose -f docker-compose-local.yml down
```

---

## 13. Baza podataka

### Za početak: SQLite (zero-config)

| Što čuva | Format |
|----------|--------|
| Conversations (chat history) | JSON |
| User settings (BYOK keys, defaults) | Key-value |
| Research cache (scraped content) | Text + metadata |
| Tool execution log | Structured log |

### Kasnije (opciono): PostgreSQL + pgvector

Kad RAG research bude zahtevao vector search, migracija na PostgreSQL.

```
SQLite (faza 1)  →  PostgreSQL + pgvector (faza 2)
```

---

## 14. Auth model

```
Faza 1 (sada):
  - Jedan user, hardcoded u settings
  - dragan.mijatovic@cramick-it.com / "topsecret"
  - JWT token za API pristup
  - API keys čuvani u SQLite (encrypted)

Faza 2 (kasnije):
  - Multi-user sa registracijom
  - Svaki user ima svoj BYOK key store
  - Role-based access (admin/user)
```

---

## 15. Port alokacija

| Servis | Port | Opis |
|--------|------|------|
| gandra-tools-api | 8095 | FastAPI backend |
| gandra-tools-ui | 3001 | Vue 3 dev server |
| Ollama | 11434 | Lokalni LLM |
| PostgreSQL | 5450 | pgvector (faza 2) |
| Redis | 6395 | Cache |

Izbor portova ne kolizira sa postojećim projektima:
- companydevs-api=8083, scouseit-api=8082
- companydevs-ai=8094, scouseit-ai=8091
- zabbix-ai-backend=8000
- PostgreSQL 5429 (companydevs/scouseit), 5442 (zabbix)
- Redis 6378 (scouseit), 6399 (zabbix)

---

## 16. Tech stack — rezime

### Backend

| Komponenta | Izbor | Obrazloženje |
|-----------|-------|-------------|
| Runtime | Python 3.11+ | Konzistentno sa workspace |
| Framework | FastAPI | Async, Swagger, proven |
| Package manager | uv (Astral) | Konzistentno sa workspace |
| CLI | Typer | Moderan, type hints, auto-help |
| LLM | openai, anthropic, ollama SDK | Multi-provider BYOK |
| Embeddings | sentence-transformers ili API | Konfigurisano u settings |
| Web scraping | httpx + BeautifulSoup | Za RAG research |
| YouTube | yt-dlp + youtube-transcript-api | Transcript + frame extraction |
| OCR/Image | EasyOCR + Pillow + OpenCV | Text extraction, transparent PNG rendering |
| DB | SQLite (faza 1) → PostgreSQL (faza 2) | Zero-config start |
| Auth | python-jose (JWT) + passlib | Lightweight |
| Validation | Pydantic v2 | Standard |
| Linting | Ruff + Black | Konzistentno sa workspace |

### Frontend

| Komponenta | Izbor | Obrazloženje |
|-----------|-------|-------------|
| Framework | Vue 3 + Vite | Konzistentno sa workspace |
| Styling | Tailwind CSS | Brz razvoj |
| State | Pinia | Standard za Vue 3 |
| Router | Vue Router 4 | Standard |
| HTTP | Axios ili fetch | API pozivi |
| Package manager | bun | Brz, korišćen u willhaben-ui |
| TypeScript | Da | Type safety |

---

## 17. Finalna preporučena folder struktura

```
gandra-tools-app/
├── PYTHON_ENVIRONMENT_GANDRA_TOOL_APP.MD    # Python env setup guide
├── README.md
├── docker-compose-local.yml                 # Ollama, PostgreSQL, Redis
├── docs/
│   ├── requirements-gandra-tools-app.txt    # Originalni zahtevi
│   └── architecture-elaboration.md          # Ovaj dokument
│
├── gandra-tools-api/                        # ══ BACKEND ══
│   ├── pyproject.toml
│   ├── .python-version                      # 3.11.x
│   ├── .env.example
│   ├── .gitignore
│   ├── src/
│   │   └── gandra_tools/
│   │       ├── __init__.py
│   │       ├── main.py                      # FastAPI app + plugin registry
│   │       ├── cli.py                       # Typer entry point
│   │       ├── core/
│   │       │   ├── __init__.py
│   │       │   ├── config.py                # Pydantic BaseSettings
│   │       │   ├── auth.py                  # JWT + password hashing
│   │       │   ├── plugin.py                # Plugin base class + registry
│   │       │   ├── llm/
│   │       │   │   ├── __init__.py
│   │       │   │   ├── base.py              # BaseLLMClient ABC
│   │       │   │   ├── openai_client.py
│   │       │   │   ├── anthropic_client.py
│   │       │   │   ├── ollama_client.py
│   │       │   │   └── factory.py           # LLMFactory
│   │       │   └── publisher/               # ══ PUBLISHER MODUL ══
│   │       │       ├── __init__.py
│   │       │       ├── service.py           # PublisherService
│   │       │       ├── schemas.py           # PublishRequest/Response, OutputFormat
│   │       │       ├── formatters/
│   │       │       │   ├── __init__.py
│   │       │       │   ├── base.py          # BaseFormatter ABC
│   │       │       │   ├── json_formatter.py
│   │       │       │   ├── markdown_formatter.py
│   │       │       │   ├── text_formatter.py
│   │       │       │   └── html_formatter.py
│   │       │       └── templates/           # Jinja2 šabloni
│   │       │           ├── research_analysis.md.j2
│   │       │           ├── research_analysis.html.j2
│   │       │           ├── research_analysis.txt.j2
│   │       │           ├── youtube_transcript.md.j2
│   │       │           └── generic.md.j2
│   │       ├── models/
│   │       │   ├── __init__.py
│   │       │   ├── schemas.py               # Shared schemas (ToolInputBase)
│   │       │   └── database.py              # SQLAlchemy models
│   │       ├── db/
│   │       │   ├── __init__.py
│   │       │   └── session.py               # DB session management
│   │       ├── tools/
│   │       │   ├── __init__.py              # Tool autodiscovery
│   │       │   ├── youtube/
│   │       │   │   ├── __init__.py          # TOOL_META
│   │       │   │   ├── router.py
│   │       │   │   ├── service.py
│   │       │   │   ├── schemas.py           # TranscriptInput/Output
│   │       │   │   └── cli.py
│   │       │   ├── research/
│   │       │   │   ├── __init__.py
│   │       │   │   ├── router.py
│   │       │   │   ├── service.py
│   │       │   │   ├── schemas.py           # ResearchAnalysisInput/Output
│   │       │   │   └── cli.py
│   │       │   ├── fileops/
│   │       │   │   ├── __init__.py
│   │       │   │   ├── router.py
│   │       │   │   ├── service.py
│   │       │   │   ├── schemas.py           # FileRenameInput, FileSearchInput
│   │       │   │   └── cli.py
│   │       │   ├── imageops/
│   │       │   │   ├── __init__.py          # TOOL_META
│   │       │   │   ├── router.py
│   │       │   │   ├── service.py           # OCR + rendering logika
│   │       │   │   ├── schemas.py           # ImageTextExtractInput/Output
│   │       │   │   ├── text_extract.py      # Standalone entry point (__main__)
│   │       │   │   └── cli.py
│   │       │   └── devtools/
│   │       │       ├── __init__.py
│   │       │       ├── router.py
│   │       │       ├── service.py
│   │       │       ├── schemas.py           # ApiTestInput, CodeReviewInput
│   │       │       └── cli.py
│   │       └── routers/
│   │           ├── __init__.py
│   │           ├── auth.py                  # /api/v1/auth/*
│   │           ├── settings.py              # /api/v1/settings
│   │           ├── health.py                # /api/v1/health
│   │           ├── publish.py               # /api/v1/publish/*
│   │           └── tools.py                 # /api/v1/tools (lista alata)
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py                      # Shared fixtures
│       ├── unit/
│       │   ├── core/
│       │   │   ├── test_config.py
│       │   │   ├── test_auth.py
│       │   │   ├── test_plugin_registry.py
│       │   │   └── test_llm_factory.py
│       │   ├── publisher/
│       │   │   ├── test_json_formatter.py
│       │   │   ├── test_markdown_formatter.py
│       │   │   ├── test_text_formatter.py
│       │   │   ├── test_html_formatter.py
│       │   │   ├── test_publisher_service.py
│       │   │   └── test_templates.py
│       │   └── tools/
│       │       ├── test_youtube_schemas.py
│       │       ├── test_youtube_service.py
│       │       ├── test_research_schemas.py
│       │       ├── test_research_service.py
│       │       ├── test_fileops_search.py
│       │       ├── test_fileops_rename.py
│       │       ├── test_imageops_schemas.py
│       │       ├── test_imageops_service.py
│       │       └── test_devtools_api_test.py
│       ├── integration/
│       │   ├── test_ollama_client.py
│       │   ├── test_publisher_e2e.py
│       │   ├── test_research_e2e.py
│       │   └── test_imageops_e2e.py
│       ├── api/
│       │   ├── test_auth_api.py
│       │   ├── test_youtube_api.py
│       │   ├── test_research_api.py
│       │   ├── test_imageops_api.py
│       │   ├── test_publish_api.py
│       │   └── test_settings_api.py
│       └── cli/
│           ├── test_youtube_cli.py
│           ├── test_research_cli.py
│           ├── test_imageops_cli.py
│           └── test_fileops_cli.py
│
└── gandra-tools-ui/                         # ══ FRONTEND ══
    ├── package.json
    ├── vite.config.ts
    ├── tailwind.config.js
    ├── tsconfig.json
    ├── index.html
    └── src/
        ├── App.vue
        ├── main.ts
        ├── router/index.ts
        ├── stores/
        │   ├── auth.ts
        │   └── settings.ts
        ├── composables/
        │   ├── useChat.ts
        │   ├── useYoutube.ts
        │   ├── useResearch.ts
        │   └── useApi.ts
        ├── components/
        │   ├── chat/
        │   ├── layout/
        │   └── ui/
        └── pages/
            ├── ChatPage.vue
            ├── YoutubePage.vue
            ├── ResearchPage.vue
            ├── FileOpsPage.vue
            ├── ImageOpsPage.vue
            └── SettingsPage.vue
```

---

## 18. Faze implementacije

| Faza | Opis | Deliverables |
|------|------|-------------|
| **1** | Scaffold + core infra | pyproject.toml, docker-compose-local.yml, config, auth, LLM factory |
| **2** | Publisher modul | Formatteri (JSON/MD/TXT/HTML), Jinja2 templates, ~20 testova |
| **3** | YouTube transcript | Prvi tool end-to-end (API + CLI + standalone + publish) |
| **4** | CLI framework | Typer sa autodiscovery, config subcommand |
| **5** | Image Text Extractor | OCR pipeline, transparent PNG rendering, interactive mode |
| **6** | RAG Research | Web scraping, embedding, multi-pass analysis, publish |
| **7** | File operations | Search + rename (sa dry-run) |
| **8** | Web UI | Vue 3 scaffold, chat page, tool pages (YT, Research, ImageOps, FileOps), settings |
| **9** | DevTools | API tester, code review |
| **10** | Polish | Error handling, logging, CI pipeline, docs |

---

## 19. Zaključak

**Preporučeni pristup: Plugin arhitektura (Pristup C)** sa:
- **Autodiscovery** za zero-config dodavanje novih alata
- **4 invocation metode** (Web UI, API, CLI, Python) — sve dele isti `service.py`
- **BYOK** sa multi-provider LLM factory (preuzeto iz oba referentna projekta)
- **Publisher modul** u `core/` — reusable multi-format output (JSON, MD, TXT, HTML)
- **Typed input specifikacije** — Pydantic v2 sa validacijom, per-tool schemas
- **Unified LLM input** — isti input model za sve providere, `llm_options` za specifičnosti
- **Docker Compose** za lokalne servise (Ollama, PostgreSQL, Redis)
- **Vue 3 + Vite** za UI (konzistentno sa workspace-om)
- **Typer** za CLI (moderan, auto-help, type hints)
- **~200 testova** (unit, integration, API, CLI) sa jasnom strukturom
- **SQLite** za početak, migracija na PostgreSQL kad zatreba pgvector

Ključna prednost: svaki novi tool = **jedan folder sa 5 fajlova**, bez diranja `main.py`, CLI entry pointa, niti bilo čega drugog u sistemu. Publisher modul se može koristiti i u drugim projektima.
