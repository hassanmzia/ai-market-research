#!/usr/bin/env bash
# =============================================================================
# AI Market Research Assistant - Startup Script
# =============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Check for .env file
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo "=========================================================="
    echo "  IMPORTANT: Edit .env and set your OPENAI_API_KEY"
    echo "=========================================================="
    echo ""
fi

echo "=============================================="
echo "  AI Market Research Assistant"
echo "  Starting all services..."
echo "=============================================="
echo ""
echo "Services:"
echo "  Frontend (React)     : http://172.168.1.95:3063"
echo "  API Gateway (Node)   : http://172.168.1.95:4063"
echo "  Django API           : http://172.168.1.95:8063"
echo "  A2A Orchestrator     : http://172.168.1.95:7063"
echo "  MCP Server           : http://172.168.1.95:9063"
echo "  PostgreSQL           : localhost:5463"
echo "  Redis                : localhost:6479"
echo ""

# Build and start
docker compose up --build -d

echo ""
echo "=============================================="
echo "  All services started successfully!"
echo "  Access the app at: http://172.168.1.95:3063"
echo ""
echo "  Default admin credentials:"
echo "    Email: admin@amr.local"
echo "    Password: admin123456"
echo "=============================================="
