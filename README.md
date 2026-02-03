# AI Market Research Assistant

A professional-grade, multi-agent AI system for automated competitive market research and analysis. Built with MCP (Model Context Protocol), A2A (Agent-to-Agent) architecture, and a modern full-stack framework.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Frontend (React/TypeScript)                       │
│                    http://172.168.1.95:3063                          │
└─────────────────┬───────────────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────────────┐
│              API Gateway (Node.js/Express)                           │
│              Port 4063 - Rate limiting, Auth, WebSocket proxy        │
└────┬──────────────────┬─────────────────────────┬───────────────────┘
     │                  │                         │
┌────▼────┐    ┌────────▼────────┐    ┌───────────▼──────────┐
│ Django  │    │ A2A Orchestrator │    │    MCP Server        │
│  API    │    │   Port 7063      │    │    Port 9063         │
│Port 8063│    │                  │    │                      │
│         │    │ 8 Specialized    │◄──►│ 9 Research Tools     │
│ Auth    │    │ AI Agents        │    │ - validate_company   │
│ Models  │    │ - Validation     │    │ - identify_sector    │
│ Tasks   │    │ - Sector         │    │ - identify_competitors│
│ Reports │    │ - Competitor     │    │ - browse_page        │
│         │    │ - Financial      │    │ - generate_report    │
└────┬────┘    │ - Research       │    │ - sentiment_analysis │
     │         │ - Sentiment      │    │ - trend_analysis     │
┌────▼────┐    │ - Trend          │    │ - financial_data     │
│PostgreSQL│   │ - Report         │    │ - swot_analysis      │
│Port 5463│    └─────────────────┘    └──────────────────────┘
└─────────┘
     │
┌────▼────┐    ┌─────────────────┐
│  Redis  │    │  Celery Workers  │
│Port 6479│◄──►│  + Beat Schedule │
└─────────┘    └─────────────────┘
```

## Features

### From Original Notebook (Enhanced)
- **Company Validation** - Verify company existence via web search with confidence scoring
- **Sector Identification** - Multi-strategy sector analysis (general, Wikipedia/LinkedIn, financial)
- **Competitor Discovery** - Top 3 competitor identification with ranking by frequency/relevance
- **Web Page Browsing** - Intelligent web scraping with content extraction
- **Report Generation** - Markdown competitive analysis reports with comparison tables

### New Professional Features
- **SWOT Analysis** - Automated Strengths, Weaknesses, Opportunities, Threats assessment
- **Sentiment Analysis** - Market sentiment scoring from news and social mentions
- **Trend Analysis** - Emerging/declining market trend identification
- **Financial Data Gathering** - Revenue, market cap, and growth metrics collection
- **Multi-Agent Orchestration (A2A)** - 8 specialized agents coordinating via Agent-to-Agent protocol
- **MCP Tool Server** - 9 tools exposed via Model Context Protocol
- **Real-time Progress Tracking** - WebSocket-based live research status updates
- **User Authentication** - JWT-based auth with role management (admin/analyst/viewer)
- **Research Project Management** - Organize research into projects
- **Report Export** - Save, share, and export reports (Markdown/HTML)
- **Company Watchlist** - Monitor companies with alert configurations
- **Dashboard Analytics** - Research stats, sector distribution, activity charts
- **Notification System** - Real-time notifications for research completion and alerts
- **Scheduled Research** - Celery Beat for periodic watchlist refreshes
- **API Rate Limiting** - Redis-backed distributed rate limiting
- **Search & Filtering** - Full-text search across companies and research history

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Zustand, Recharts, React Markdown |
| API Gateway | Node.js, Express, WebSocket (ws) |
| Backend API | Django 5.1, Django REST Framework, Channels |
| Agent System | Python, OpenAI API, A2A Protocol |
| MCP Server | Python, FastAPI, DuckDuckGo Search |
| Database | PostgreSQL 16 |
| Cache/Queue | Redis 7 |
| Task Queue | Celery 5.4 with Beat scheduler |
| Containerization | Docker Compose |

## Port Assignments

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 3063 | Main site (React + Nginx) |
| API Gateway | 4063 | Node.js BFF/proxy |
| A2A Orchestrator | 7063 | Multi-agent coordinator |
| Django API | 8063 | Backend REST API |
| MCP Server | 9063 | Tool protocol server |
| PostgreSQL | 5463 | Database |
| Redis | 6479 | Cache & message broker |

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- OpenAI API key

### Setup

1. **Clone and configure:**
   ```bash
   cd ai-market-research
   cp .env.example .env
   # Edit .env and set OPENAI_API_KEY
   ```

2. **Start all services:**
   ```bash
   ./scripts/start.sh
   ```

3. **Access the application:**
   - Open http://172.168.1.95:3063
   - Login with default admin: `admin@amr.local` / `admin123456`

4. **Start a research:**
   - Navigate to "New Research"
   - Enter a company name (e.g., "Amazon", "Tesla", "Microsoft")
   - Watch the 8-stage multi-agent pipeline process in real-time

### Management Scripts

```bash
./scripts/start.sh    # Build and start all services
./scripts/stop.sh     # Stop all services
./scripts/reset.sh    # Remove all data and containers
./scripts/logs.sh all # View logs (or specify service name)
```

## Multi-Agent Pipeline

When you start a research task, 8 specialized agents execute in sequence:

| Stage | Agent | Purpose |
|-------|-------|---------|
| 1 | **Validation Agent** | Verifies the company is real |
| 2 | **Sector Agent** | Identifies industry sector |
| 3 | **Competitor Agent** | Discovers top 3 competitors |
| 4 | **Financial Agent** | Gathers financial metrics |
| 5 | **Research Agent** | Deep web research on strategies |
| 6 | **Sentiment Agent** | Analyzes market sentiment |
| 7 | **Trend Agent** | Identifies market trends |
| 8 | **Report Agent** | Generates comprehensive report |

Each agent's output feeds into the next, building a complete competitive analysis.

## API Endpoints

### Authentication
- `POST /api/auth/register/` - Register new user
- `POST /api/auth/login/` - Login (returns JWT)
- `GET /api/auth/profile/` - Get user profile

### Research
- `POST /api/research/tasks/start_research/` - Start new research
- `GET /api/research/tasks/` - List all tasks
- `GET /api/research/tasks/{id}/` - Get task details with results

### Reports
- `GET /api/reports/` - List saved reports
- `POST /api/reports/` - Save a report
- `GET /api/reports/{id}/share/` - Get shareable link

### Agents (via Gateway)
- `GET /api/agents/` - List all A2A agents
- `POST /api/agents/research` - Direct agent research
- `GET /api/agents/research/{taskId}/status` - Real-time status

### WebSocket
- `ws://172.168.1.95:4063/ws/research/{taskId}` - Live progress updates

## Environment Variables

See `.env.example` for all available configuration options.

Key variables:
- `OPENAI_API_KEY` - Required for LLM-powered agents
- `LLM_MODEL_ID` - Model to use (default: gpt-4o-mini)
- `DJANGO_SECRET_KEY` - Django security key
- `POSTGRES_PASSWORD` - Database password

## License

MIT
