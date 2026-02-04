# AI Market Research Assistant

A professional-grade, multi-agent AI system for automated competitive market research and analysis. Built with MCP (Model Context Protocol), A2A (Agent-to-Agent) architecture, and a modern full-stack microservices framework. Nine containerized services orchestrate 8 specialized AI agents across a sequential research pipeline, delivering comprehensive market reports with real-time progress tracking.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [System Architecture Diagram](#system-architecture-diagram)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Service Map](#service-map)
- [Quick Start](#quick-start)
- [Multi-Agent Research Pipeline](#multi-agent-research-pipeline)
- [MCP Tool Server](#mcp-tool-server)
- [API Reference](#api-reference)
- [WebSocket Real-Time Updates](#websocket-real-time-updates)
- [Authentication & Security](#authentication--security)
- [Database Schema](#database-schema)
- [Redis Architecture](#redis-architecture)
- [Celery Task Queue](#celery-task-queue)
- [Frontend Architecture](#frontend-architecture)
- [API Gateway](#api-gateway)
- [Environment Variables](#environment-variables)
- [Project Structure](#project-structure)
- [Management Scripts](#management-scripts)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     Frontend (React 18 + TypeScript)                     │
│                     Nginx :3063 — Zustand / Recharts / Axios            │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │ HTTP + JWT / WebSocket
┌───────────────────────────────▼─────────────────────────────────────────┐
│                  API Gateway (Node.js + Express) :4063                   │
│          Rate Limiting (Redis) │ JWT Verify │ HTTP Proxy │ WS Relay      │
└────────┬──────────────────────┬──────────────────────┬──────────────────┘
         │                      │                      │
┌────────▼────────┐   ┌────────▼──────────┐   ┌───────▼──────────────┐
│  Django API     │   │ A2A Orchestrator   │   │   MCP Tool Server    │
│  :8063          │   │ :7063 (FastAPI)    │   │   :9063 (FastAPI)    │
│                 │   │                    │   │                      │
│  Auth / JWT     │   │  8 AI Agents       │◄─►│  9 Research Tools    │
│  Research CRUD  │   │  Sequential        │   │  DuckDuckGo Search   │
│  Reports/Export │   │  Pipeline          │   │  Web Scraping        │
│  Watchlist      │   │  WebSocket Stream  │   │  Redis Cache (1h)    │
│  Notifications  │   │  Redis State       │   │                      │
│  Dashboard      │   │                    │   │                      │
└────────┬────────┘   └─────────┬──────────┘   └──────────┬───────────┘
         │                      │                          │
         │           ┌──────────▼──────────┐               │
         │           │   OpenAI API        │               │
         │           │   (GPT-4o-mini)     │               │
         │           │   Function Calling  │               │
         │           └─────────────────────┘               │
         │                                                 │
┌────────▼────────┐   ┌─────────────────┐                  │
│  PostgreSQL 16  │   │     Redis 7     │◄─────────────────┘
│  :5432          │   │     :6379       │
│                 │   │                 │
│  Users          │   │  DB0: Django    │   ┌─────────────────┐
│  Projects       │   │  DB1: Celery    │   │  Celery Workers  │
│  Tasks/Results  │   │  DB2: MCP Cache │◄─►│  + Beat Schedule │
│  Reports        │   │  DB3: A2A State │   │                  │
│  Watchlist      │   │  DB4: Rate Lim  │   │  Async research  │
│  Notifications  │   │  + Channels     │   │  Watchlist (6h)  │
└─────────────────┘   └─────────────────┘   │  Cleanup (daily) │
                                            └─────────────────┘
```

---

## System Architecture Diagram

Detailed architecture diagrams are available in the `docs/` directory:

- **`docs/architecture.drawio`** — Editable draw.io diagram (open with [diagrams.net](https://app.diagrams.net))
- **`docs/AI_Market_Research_Architecture.pptx`** — 5-slide PowerPoint presentation covering system architecture, pipeline flow, tech stack, data flow, and security

---

## Features

### Core Research Capabilities

| Feature | Description |
|---------|-------------|
| **Company Validation** | Verify company existence via DuckDuckGo web search with confidence scoring (high/medium/low) |
| **Sector Identification** | Multi-strategy sector analysis using general search, Wikipedia/LinkedIn, and financial sources |
| **Competitor Discovery** | Identify top 3-5 competitors with ranking by mention frequency and relevance |
| **Financial Data Gathering** | Revenue, market cap, growth metrics, and key financial indicators |
| **Deep Market Research** | Comprehensive web research on company strategies, products, and market position |
| **Sentiment Analysis** | Market sentiment scoring from news and social mentions, normalized to 0-100 scale |
| **Trend Analysis** | Emerging, growing, stable, and declining market trend identification |
| **SWOT Analysis** | Company-specific Strengths, Weaknesses, Opportunities, and Threats with concrete evidence |
| **Report Generation** | Full markdown competitive analysis reports with executive summary and recommendations |

### Platform Features

| Feature | Description |
|---------|-------------|
| **Multi-Agent Orchestration** | 8 specialized AI agents coordinating via Agent-to-Agent (A2A) protocol |
| **MCP Tool Server** | 9 tools exposed via Model Context Protocol with Redis-cached results |
| **Real-Time Progress** | WebSocket-based live research status with per-stage progress tracking |
| **JWT Authentication** | Secure auth with auto-rotating access (60min) and refresh (7-day) tokens |
| **Report Export** | Save, share, and download reports in PDF, Markdown, CSV, and HTML formats |
| **Company Watchlist** | Monitor companies with configurable news and competitor change alerts |
| **Dashboard Analytics** | Research stats, top sectors, monthly activity charts |
| **Notification System** | Real-time notifications for research completion and watchlist alerts |
| **Scheduled Tasks** | Celery Beat for periodic watchlist refreshes (6h) and task cleanup (daily) |
| **Rate Limiting** | Redis-backed distributed rate limiting at gateway and Django levels |
| **PDF Generation** | ReportLab-powered PDF export with styled headings, bullet points, and footer |

---

## Technology Stack

| Layer | Technologies | Purpose |
|-------|-------------|---------|
| **Frontend** | React 18, TypeScript, Zustand, React Router v6, Recharts, Axios, React Markdown, Lucide Icons | Single-page application with real-time updates |
| **API Gateway** | Node.js 20, Express.js, ws (WebSocket), express-rate-limit | Reverse proxy, WebSocket relay, rate limiting, JWT verification |
| **Backend API** | Django 5.1, Django REST Framework 3.15, Django Channels, SimpleJWT | REST API, authentication, data models, WebSocket layer |
| **AI Orchestrator** | Python, FastAPI, OpenAI API (GPT-4o-mini), A2A Protocol | Multi-agent pipeline coordination with function calling |
| **MCP Server** | Python, FastAPI, DuckDuckGo Search, BeautifulSoup4, httpx | Tool execution (search, scraping, analysis) |
| **Task Queue** | Celery 5.4, Celery Beat, Redis broker | Background job execution and scheduling |
| **Database** | PostgreSQL 16 | Persistent storage for all application data |
| **Cache/Messaging** | Redis 7 (5 databases) | Caching, message broker, pub/sub, rate limiting, channel layer |
| **PDF Export** | ReportLab 4.2 | Pure-Python PDF generation from markdown content |
| **Deployment** | Docker, Docker Compose, Nginx | 9 containerized services with health checks |

---

## Service Map

| Service | Container | Port (Host) | Port (Internal) | Health Check |
|---------|-----------|-------------|-----------------|--------------|
| React Frontend | `amr-frontend` | 3063 | 80 (Nginx) | `http://localhost/` |
| API Gateway | `amr-gateway` | 4063 | 4063 | `http://localhost:4063/health` |
| Django API | `amr-django-api` | 8063 | 8063 | `http://localhost:8063/api/health/` |
| A2A Orchestrator | `amr-a2a-orchestrator` | 7063 | 7063 | `http://localhost:7063/health` |
| MCP Server | `amr-mcp-server` | 9063 | 9063 | `http://localhost:9063/health` |
| Celery Worker | `amr-celery-worker` | — | — | Depends on Django |
| Celery Beat | `amr-celery-beat` | — | — | Depends on Django |
| PostgreSQL | `amr-postgres` | 5463 | 5432 | `pg_isready` |
| Redis | `amr-redis` | 6479 | 6379 | `redis-cli ping` |

All services run on a Docker bridge network (`amr-network`) and communicate via internal hostnames.

---

## Quick Start

### Prerequisites

- Docker and Docker Compose (v2+)
- OpenAI API key (or compatible API endpoint)
- 4GB+ RAM recommended

### Setup

1. **Clone and configure:**
   ```bash
   cd ai-market-research
   cp .env.example .env
   ```

2. **Edit `.env` and set your API key:**
   ```bash
   OPENAI_API_KEY=sk-your-openai-api-key-here
   ```

3. **Start all services:**
   ```bash
   ./scripts/start.sh
   ```
   This builds all 9 Docker images and starts the containers. The Django container automatically runs database migrations and creates a default admin user on first startup.

4. **Access the application:**
   - Open `http://localhost:3063` (or your host IP on port 3063)
   - Login with default admin: `admin@amr.local` / `admin123456`

5. **Start a research:**
   - Navigate to "New Research"
   - Enter a company name (e.g., "Nvidia", "Tesla", "Microsoft")
   - Watch the 8-stage multi-agent pipeline process in real-time
   - View results across Overview, Competitors, Analysis, SWOT, and Full Report tabs

### Stopping & Resetting

```bash
./scripts/stop.sh     # Stop all services (preserves data)
./scripts/reset.sh    # Remove all data, volumes, and containers
./scripts/logs.sh all # View logs (or specify: django-api, gateway, etc.)
```

---

## Multi-Agent Research Pipeline

When a research task is started, 8 specialized AI agents execute sequentially. Each agent's output is accumulated as context and passed to the next agent, building progressively richer analysis.

| # | Stage | Agent | Progress | MCP Tool | Description |
|---|-------|-------|----------|----------|-------------|
| 1 | Validation | `validation_agent` | 5% | `validate_company` | Verifies company exists via web search; returns confidence score |
| 2 | Sector ID | `sector_agent` | 25% | `identify_sector` | Classifies industry sector using multiple search strategies |
| 3 | Competitors | `competitor_agent` | 40% | `identify_competitors` | Discovers top 3-5 competitors ranked by mention frequency |
| 4 | Financial | `financial_agent` | 50% | `financial_data` | Gathers revenue, market cap, growth metrics from financial sites |
| 5 | Deep Research | `research_agent` | 60% | `browse_page` | Comprehensive web research on strategies, products, market position |
| 6 | Sentiment | `sentiment_agent` | 70% | `sentiment_analysis` | Analyzes news sentiment; score normalized from [-1,1] to [0,1] |
| 7 | Trends | `trend_agent` | 85% | `trend_analysis` | Identifies emerging, growing, stable, and declining trends |
| 8 | Report | `report_agent` | 95% | `generate_report` + `swot_analysis` | Synthesizes all data into markdown report with SWOT and recommendations |

### Pipeline Data Flow

```
User Input (company name)
    │
    ▼
[Validation] ─── is_valid, confidence ───────────────────────────►
    │                                                              │
    ▼                                                              │
[Sector ID] ── sector, sub_sector ───────────────────────────────►│
    │                                                              │
    ▼                                                              │ Context
[Competitors] ── competitors[] ──────────────────────────────────►│ accumulates
    │                                                              │ at each
    ▼                                                              │ stage
[Financial] ── revenue, market_cap, metrics ─────────────────────►│
    │                                                              │
    ▼                                                              │
[Deep Research] ── market_research, strategies ──────────────────►│
    │                                                              │
    ▼                                                              │
[Sentiment] ── overall_score, company_sentiments[] ──────────────►│
    │                                                              │
    ▼                                                              │
[Trends] ── emerging[], growing[], declining[] ──────────────────►│
    │                                                              │
    ▼                                                              │
[Report Gen] ◄────────────── Full accumulated context ────────────┘
    │
    ▼
Final Report (markdown + SWOT + executive summary + recommendations)
```

### Agent Architecture

Each agent extends `BaseAgent` (defined in `a2a_agents/agents/base_agent.py`):

- Manages an `AsyncOpenAI` client for LLM reasoning
- Calls MCP tools via HTTP `POST /mcp/tools/call`
- Implements `handle_request(TaskRequest) -> TaskResponse`
- Tracks execution duration and errors
- Generates an `AgentCard` describing its capabilities
- Uses OpenAI function calling with MCP tool definitions

---

## MCP Tool Server

The MCP (Model Context Protocol) server exposes 9 tools that agents call during research. All tools feature:

- **DuckDuckGo search** with retry logic (3 attempts, exponential backoff)
- **Inter-query delays** (1 second) to avoid rate limiting
- **Redis caching** with 1-hour TTL per unique query
- **Graceful degradation** when search results are sparse

| Tool | Input | Output | Search Queries |
|------|-------|--------|---------------|
| `validate_company` | company_name | is_valid, confidence, evidence | 1 query |
| `identify_sector` | company_name | sector, sub_sector, confidence | 3 queries |
| `identify_competitors` | company_name, sector | competitors[], rankings | 3 queries |
| `browse_page` | url, instructions | extracted_content, title | 0 (direct HTTP) |
| `financial_data` | company_name, sector | revenue, market_cap, metrics | 3-5 queries |
| `sentiment_analysis` | company_name, sector | score [-1,1], articles[] | 3-5 queries |
| `trend_analysis` | company_name, sector | emerging[], declining[] | 3-5 queries |
| `swot_analysis` | company_name, sector, context | strengths[], weaknesses[], opportunities[], threats[] | 3-5 queries |
| `generate_report` | company_name, all_data | report_markdown | 0 (synthesis) |

### Tool Endpoints

```
POST /mcp/tools/list    → Returns all tool schemas (name, description, input_schema)
POST /mcp/tools/call    → Executes a tool: { "name": "tool_name", "arguments": {...} }
GET  /health            → Health check
```

---

## API Reference

All API requests go through the gateway at `:4063`. The gateway proxies `/api/*` to Django and `/api/agents/*` to the A2A orchestrator.

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/register/` | Register new user. Body: `{ email, password, password_confirm, first_name, last_name }` |
| `POST` | `/api/auth/login/` | Login. Returns `{ user, tokens: { access, refresh } }` |
| `POST` | `/api/auth/token/refresh/` | Refresh JWT. Body: `{ refresh }`. Returns new token pair |
| `GET` | `/api/auth/profile/` | Get authenticated user profile |
| `PUT` | `/api/auth/profile/` | Update profile (first_name, last_name, company, preferences) |
| `POST` | `/api/auth/change-password/` | Change password. Body: `{ current_password, new_password }` |

### Research

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/research/tasks/start_research/` | Start research. Body: `{ company_name }`. Returns task with UUID |
| `GET` | `/api/research/tasks/` | List all user's research tasks |
| `GET` | `/api/research/tasks/{task_id}/` | Get task details (status, progress, timestamps) |
| `GET` | `/api/research/tasks/{task_id}/result/` | Get research result (all analysis data) |
| `POST` | `/api/research/tasks/{task_id}/cancel/` | Cancel a running task |
| `GET` | `/api/research/projects/` | List research projects |
| `POST` | `/api/research/projects/` | Create project. Body: `{ name, description }` |
| `GET` | `/api/research/search/?q=query` | Search companies by name |

### Reports

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/reports/saved/` | List saved reports |
| `POST` | `/api/reports/saved/` | Save report. Body: `{ task_id, title, description }` |
| `GET` | `/api/reports/saved/{id}/` | Get report details |
| `DELETE` | `/api/reports/saved/{id}/` | Delete a report |
| `POST` | `/api/reports/saved/{id}/share/` | Make report public, get share URL |
| `GET` | `/api/reports/saved/{id}/export/pdf/` | Download as PDF |
| `GET` | `/api/reports/saved/{id}/export/markdown/` | Download as Markdown |
| `GET` | `/api/reports/saved/{id}/export/csv/` | Download as CSV |
| `GET` | `/api/reports/saved/{id}/export/html/` | Download as HTML |

### Watchlist

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/research/watchlist/` | List watchlist items |
| `POST` | `/api/research/watchlist/` | Add company. Body: `{ company_name, alert_on_news, alert_on_competitor_change }` |
| `PATCH` | `/api/research/watchlist/{id}/` | Update alerts/notes (partial update) |
| `DELETE` | `/api/research/watchlist/{id}/` | Remove from watchlist |

### Notifications

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/notifications/` | List all notifications |
| `GET` | `/api/notifications/unread-count/` | Get unread notification count |
| `PUT` | `/api/notifications/{id}/mark-read/` | Mark single notification as read |
| `PUT` | `/api/notifications/mark-all-read/` | Mark all as read |

### Dashboard

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/dashboard/` | Dashboard stats: total/completed/active researches, watchlist count, top sectors, monthly activity |

### Agents (Direct A2A Access)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/agents` | List all available agents with capabilities |
| `GET` | `/api/agents/{name}` | Get specific agent details |
| `POST` | `/api/agents/research` | Start research via A2A directly |
| `GET` | `/api/agents/research/{taskId}/status` | Get pipeline status |
| `GET` | `/api/agents/research/{taskId}/result` | Get pipeline result |

---

## WebSocket Real-Time Updates

Research progress is streamed in real-time via WebSocket connections:

```
Frontend ──ws──► Gateway :4063/ws/research/{taskId}
                      │
                      ▼ (upstream relay)
                 A2A :7063/a2a/ws/{taskId}
                      │
                      ▼ (Redis pub/sub)
                 a2a:progress:{taskId}
```

### Connection

```javascript
ws://hostname:4063/ws/research/{taskId}?token={jwt_access_token}
```

### Message Format

```json
{
  "type": "progress",
  "task_id": "uuid",
  "stage": "sector_identification",
  "stage_name": "sector_identification",
  "status": "running",
  "progress": 25,
  "message": "Identifying company sector...",
  "data": { "duration": 3.2 }
}
```

### Message Types

| Type | Description |
|------|-------------|
| `initial_state` | Sent on connection with current pipeline state (all stages + their statuses) |
| `progress` | Stage transition or progress update |
| `completion` | Pipeline completed successfully |
| `error` | Stage or pipeline failure |
| `keepalive` | Periodic ping to detect stale connections |

### Reconnection

The frontend implements exponential backoff reconnection:
- Delays: 1s, 2s, 4s, 8s, 16s, max 30s
- Maximum 10 reconnection attempts
- Automatically stops when task completes or fails

---

## Authentication & Security

### JWT Flow

1. User registers or logs in → server returns `access` token (60 min) + `refresh` token (7 days)
2. Tokens stored in `localStorage`
3. Every request includes `Authorization: Bearer {access_token}` header
4. On 401 response → auto-refresh via `POST /api/auth/token/refresh/`
5. Refresh tokens rotate on use (`ROTATE_REFRESH_TOKENS = True`)
6. Failed refresh → redirect to `/login`

### Rate Limiting

| Scope | Limit | Backend |
|-------|-------|---------|
| Gateway - Auth routes | 5 req/min | Redis |
| Gateway - Research routes | 20 req/min | Redis |
| Gateway - General routes | 60 req/min | Redis |
| Django - Anonymous | 120 req/min | DRF Throttling |
| Django - Authenticated | 600 req/min | DRF Throttling |
| Research quota | 10 per day per user | User model (auto-resets daily) |

### Security Headers

- Helmet.js security headers (CSP, XSS protection, HSTS)
- CORS configured for specific origins
- gzip compression enabled

---

## Database Schema

### Core Tables

```
accounts_user (extends Django AbstractUser)
├── email (unique), password, username
├── role (admin / analyst / viewer)
├── max_daily_research (default: 10)
├── research_count_today (auto-resets daily)
├── company, avatar, preferences (JSON)
└── created_at, updated_at

research_researchproject
├── user (FK) → accounts_user
├── name, description
├── status (draft / active / completed / archived)
└── created_at, updated_at

research_researchtask
├── project (FK) → research_researchproject
├── task_id (UUID, unique) — used for WebSocket + API lookups
├── company_name
├── status (pending → validating → ... → completed / failed)
├── progress (0-100)
├── started_at, completed_at, error_message
└── created_at

research_researchresult (1-to-1 with researchtask)
├── company_validated, company_sector
├── competitors (JSON), financial_data (JSON)
├── market_research (JSON), sentiment_data (JSON), trend_data (JSON)
├── report_markdown, report_html, executive_summary
├── swot_analysis (JSON), recommendations (JSON)
├── raw_agent_data (JSON)
└── created_at

research_companyprofile
├── name (unique), sector, description
├── website, logo_url
├── research_count, last_researched
├── cached_data (JSON)
└── created_at, updated_at

research_watchlistitem
├── user (FK), company (FK) — unique_together
├── alert_on_news (bool), alert_on_competitor_change (bool)
├── notes
└── created_at

reports_savedreport
├── user (FK), task (FK)
├── title, description, report_data (JSON)
├── format (markdown / html / pdf)
├── is_public, share_token (UUID)
├── download_count
└── created_at, updated_at

notifications_notification
├── user (FK)
├── type (research_complete / watchlist_alert / system)
├── title, message, data (JSON)
├── is_read
└── created_at
```

---

## Redis Architecture

Redis 7 is used with 5 separate databases for isolated concerns:

| Database | Purpose | Key Patterns | TTL |
|----------|---------|-------------|-----|
| DB 0 | Django cache layer | Framework-managed | Varies |
| DB 1 | Celery broker + result backend | `celery-task-meta-*` | Task-dependent |
| DB 2 | MCP tool result cache | `mcp:tool:{name}:{args_hash}` | 1 hour |
| DB 3 | A2A orchestrator state + pub/sub | `a2a:task:{id}`, `a2a:progress:{id}` | 24 hours |
| DB 4 | Gateway rate limiting | `rl:{scope}:{user_id\|ip}` | 1 minute |

Additionally, Redis serves as the Django Channels layer backend for WebSocket group messaging.

---

## Celery Task Queue

### Tasks

| Task | Schedule | Description |
|------|----------|-------------|
| `run_research_task` | On demand | Dispatched when user starts research. Calls A2A orchestrator, polls status every 5s, stores results |
| `cleanup_old_tasks` | Daily (midnight) | Deletes completed/failed tasks older than 30 days |
| `refresh_watchlist` | Every 6 hours | Refreshes data for all watched companies; creates notifications on significant changes |

### Configuration

- **Broker:** `redis://redis:6379/1`
- **Result backend:** `redis://redis:6379/1`
- **Concurrency:** 4 workers
- **Scheduler:** `django_celery_beat.schedulers:DatabaseScheduler`

---

## Frontend Architecture

### State Management

Zustand stores manage client-side state:

- **`authStore`** — User authentication, token management, profile
- **`researchStore`** — Research tasks, results, task status polling

### Pages

| Route | Page | Description |
|-------|------|-------------|
| `/login` | Login | Email/password authentication |
| `/register` | Register | New user registration |
| `/` | Dashboard | Stats, top sectors, monthly activity chart |
| `/research` | ResearchList | All research tasks with status badges |
| `/research/new` | NewResearch | Start new research form |
| `/research/:id` | ResearchDetail | Task results with tabbed view (Overview, Competitors, Analysis, SWOT, Report) |
| `/reports` | Reports | Saved reports list |
| `/reports/:id` | ReportDetail | Individual report viewer |
| `/watchlist` | Watchlist | Monitored companies with alert toggles |
| `/agents` | Agents | Available AI agent cards |
| `/profile` | Profile | User settings, password change |

### Key Components

- **`ResearchProgress`** — Real-time stepper showing pipeline stage advancement
- **`CompetitorTable`** — Sortable competitor comparison table
- **`SwotChart`** — Visual SWOT analysis grid
- **`SentimentGauge`** — Sentiment score visualization (0-100)
- **`TrendList`** — Categorized trend display
- **`ReportRenderer`** — Markdown-to-HTML report viewer
- **`NotificationBell`** — Header notification indicator with dropdown

---

## API Gateway

The Node.js gateway (`gateway/src/index.js`) serves as the single entry point for all client requests:

### Routing

| Path Pattern | Target | Middleware |
|-------------|--------|------------|
| `/api/auth/*` | Django :8063 | `authLimiter` (5/min) |
| `/api/research/*` | Django :8063 | `generalLimiter` (60/min) |
| `/api/reports/*` | Django :8063 | `generalLimiter` |
| `/api/notifications/*` | Django :8063 | `generalLimiter` |
| `/api/dashboard/*` | Django :8063 | `generalLimiter` |
| `/api/agents/*` | A2A :7063 | `authenticate` + `researchLimiter` (20/min) |
| `/api/mcp/*` | MCP :9063 | `authenticate` + `generalLimiter` |
| `/ws/research/:taskId` | A2A :7063 (WebSocket) | Token via query param |
| `/health` | Self | None |

### Features

- **HTTP proxying** via httpx with configurable timeouts
- **WebSocket relay** with automatic upstream reconnection (exponential backoff)
- **Rate limiting** backed by Redis (DB 4) with in-memory fallback
- **JWT verification** for agent/MCP routes (Django handles its own auth)
- **Helmet** security headers, **CORS** configuration, **gzip** compression

---

## Environment Variables

Create a `.env` file from `.env.example`:

```bash
cp .env.example .env
```

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | *required* | OpenAI API key for LLM agents |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | LLM API base URL (for custom endpoints) |
| `LLM_MODEL_ID` | `gpt-4o-mini` | LLM model identifier |
| `DJANGO_SECRET_KEY` | dev key | Django security key (change in production) |
| `DJANGO_DEBUG` | `True` | Django debug mode |
| `DJANGO_ALLOWED_HOSTS` | `*` | Allowed host headers |
| `POSTGRES_DB` | `ai_market_research` | Database name |
| `POSTGRES_USER` | `amr_user` | Database user |
| `POSTGRES_PASSWORD` | `amr_secure_password_2024` | Database password |
| `JWT_SECRET_KEY` | dev key | JWT signing secret |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | `60` | Access token lifetime |
| `FRONTEND_PORT` | `3063` | Frontend host port |
| `GATEWAY_PORT` | `4063` | Gateway host port |
| `DJANGO_API_PORT` | `8063` | Django host port |
| `A2A_ORCHESTRATOR_PORT` | `7063` | Orchestrator host port |
| `MCP_SERVER_PORT` | `9063` | MCP server host port |
| `RATE_LIMIT_PER_MINUTE` | `60` | Gateway general rate limit |

---

## Project Structure

```
ai-market-research/
├── docker-compose.yml              # All 9 services definition
├── .env.example                    # Environment variable template
├── README.md                       # This file
├── docs/
│   ├── architecture.drawio         # Draw.io architecture diagram
│   └── AI_Market_Research_Architecture.pptx  # PowerPoint presentation
│
├── frontend/                       # React 18 + TypeScript SPA
│   ├── Dockerfile                  # Multi-stage build (Node → Nginx)
│   ├── nginx.conf                  # Nginx configuration
│   ├── package.json                # Dependencies
│   └── src/
│       ├── App.tsx                 # Route definitions
│       ├── App.css                 # Global styles
│       ├── services/
│       │   ├── api.ts              # Axios HTTP client + all API endpoints
│       │   └── websocket.ts        # WebSocket connection manager
│       ├── store/
│       │   ├── authStore.ts        # Authentication state (Zustand)
│       │   └── researchStore.ts    # Research state (Zustand)
│       ├── hooks/
│       │   └── useResearchProgress.ts  # WebSocket progress hook
│       ├── pages/
│       │   ├── Dashboard.tsx       # Stats + charts
│       │   ├── ResearchList.tsx    # Task list
│       │   ├── ResearchDetail.tsx  # Results with tabs
│       │   ├── NewResearch.tsx     # Start research form
│       │   ├── Reports.tsx         # Saved reports
│       │   ├── Watchlist.tsx       # Company monitoring
│       │   ├── Agents.tsx          # Agent cards
│       │   ├── Profile.tsx         # User settings
│       │   ├── Login.tsx           # Login form
│       │   └── Register.tsx        # Registration form
│       ├── components/
│       │   ├── ResearchProgress.tsx    # Pipeline stepper
│       │   ├── CompetitorTable.tsx     # Competitor grid
│       │   ├── SwotChart.tsx           # SWOT visualization
│       │   ├── SentimentGauge.tsx      # Sentiment meter
│       │   ├── TrendList.tsx           # Trend categories
│       │   ├── ReportRenderer.tsx      # Markdown viewer
│       │   ├── NotificationBell.tsx    # Notification dropdown
│       │   └── Layout.tsx              # App shell + navigation
│       ├── types/
│       │   └── index.ts            # TypeScript interfaces
│       └── utils/
│           └── helpers.ts          # Utility functions
│
├── gateway/                        # Node.js API Gateway
│   ├── Dockerfile
│   ├── package.json
│   └── src/
│       ├── index.js                # Express app + route registration
│       ├── middleware/
│       │   ├── auth.js             # JWT verification
│       │   ├── rateLimiter.js      # Redis-backed rate limiting
│       │   └── errorHandler.js     # Error handling
│       ├── routes/
│       │   ├── agents.js           # A2A orchestrator routes
│       │   └── mcp.js              # MCP tool routes
│       └── services/
│           ├── proxyService.js     # HTTP reverse proxy
│           └── wsService.js        # WebSocket relay manager
│
├── backend/                        # Django REST API
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── manage.py
│   ├── config/
│   │   ├── settings.py             # Django settings (DRF, JWT, Channels, Celery)
│   │   ├── urls.py                 # URL patterns + health check + dashboard
│   │   ├── celery.py               # Celery app + Beat schedule
│   │   ├── asgi.py                 # ASGI config (Channels)
│   │   └── wsgi.py                 # WSGI config
│   └── apps/
│       ├── accounts/               # User management
│       │   ├── models.py           # User model (roles, quota, preferences)
│       │   ├── views.py            # Auth views (register, login, profile)
│       │   ├── serializers.py      # User serializers
│       │   └── urls.py             # Auth routes
│       ├── research/               # Core research functionality
│       │   ├── models.py           # Project, Task, Result, CompanyProfile, WatchlistItem
│       │   ├── views.py            # ViewSets (tasks, projects, watchlist, search)
│       │   ├── tasks.py            # Celery tasks (research, cleanup, watchlist refresh)
│       │   ├── serializers.py      # DRF serializers
│       │   ├── admin.py            # Django admin registration
│       │   └── urls.py             # Research routes
│       ├── reports/                # Report management
│       │   ├── models.py           # SavedReport, ReportTemplate
│       │   ├── views.py            # CRUD + export (PDF/MD/CSV/HTML) + sharing
│       │   ├── serializers.py      # Report serializers
│       │   └── urls.py             # Report routes
│       └── notifications/          # Notification system
│           ├── models.py           # Notification model
│           ├── views.py            # List, mark-read, unread-count
│           ├── serializers.py      # Notification serializer
│           └── urls.py             # Notification routes
│
├── a2a_agents/                     # AI Agent Orchestrator
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── orchestrator.py             # FastAPI app + pipeline coordinator
│   ├── protocols/
│   │   └── a2a_protocol.py         # TaskRequest, TaskResponse, PipelineStage models
│   └── agents/
│       ├── base_agent.py           # BaseAgent ABC (OpenAI client, MCP integration)
│       ├── validation_agent.py     # Company validation
│       ├── sector_agent.py         # Sector identification
│       ├── competitor_agent.py     # Competitor discovery
│       ├── financial_agent.py      # Financial data gathering
│       ├── research_agent.py       # Deep market research
│       ├── sentiment_agent.py      # Sentiment analysis
│       ├── trend_agent.py          # Trend identification
│       └── report_agent.py         # Report generation + SWOT
│
├── mcp_server/                     # MCP Tool Server
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── server.py                   # FastAPI app + tool registration
│   └── tools/
│       ├── validate_company.py     # Company validation tool
│       ├── identify_sector.py      # Sector identification tool
│       ├── identify_competitors.py # Competitor discovery tool
│       ├── browse_page.py          # Web scraping tool
│       ├── financial_data.py       # Financial metrics tool
│       ├── sentiment_analysis.py   # Sentiment analysis tool
│       ├── trend_analysis.py       # Trend analysis tool
│       ├── swot_analysis.py        # SWOT analysis tool
│       └── generate_report.py      # Report generation tool
│
├── scripts/
│   ├── start.sh                    # Build + start all services
│   ├── stop.sh                     # Stop all services
│   ├── reset.sh                    # Full reset (volumes + containers)
│   └── logs.sh                     # View service logs
│
└── docker/
    └── init-db.sql                 # PostgreSQL initialization
```

---

## Management Scripts

```bash
# Build and start all 9 services
./scripts/start.sh

# Stop all services (data preserved in volumes)
./scripts/stop.sh

# Full reset: remove containers, volumes, and all data
./scripts/reset.sh

# View logs for all services or a specific one
./scripts/logs.sh all
./scripts/logs.sh django-api
./scripts/logs.sh a2a-orchestrator
./scripts/logs.sh gateway
./scripts/logs.sh celery-worker
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| 429 Too Many Requests on start_research | Daily research quota exceeded (10/day) | Quota auto-resets at midnight; or restart the Django container |
| WebSocket not connecting | Gateway can't reach A2A orchestrator | Check `amr-a2a-orchestrator` container health |
| Blank research results | Celery worker not processing tasks | Check `amr-celery-worker` logs for errors |
| All neutral sentiment (0/100) | DuckDuckGo rate limiting | Retry logic is built in; wait a few minutes between researches |
| PDF export fails | ReportLab not installed | Rebuild Django container: `docker compose build django-api` |
| Database migration errors | New model fields not migrated | Restart Django container (runs `makemigrations` + `migrate` on startup) |

### Checking Service Health

```bash
# All services health
curl http://localhost:4063/health        # Gateway
curl http://localhost:8063/api/health/   # Django
curl http://localhost:7063/health        # A2A Orchestrator
curl http://localhost:9063/health        # MCP Server

# Check container status
docker compose ps

# View specific service logs
docker compose logs -f amr-django-api
docker compose logs -f amr-celery-worker
docker compose logs -f amr-a2a-orchestrator
```

---

## License

MIT
