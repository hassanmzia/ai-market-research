#!/usr/bin/env bash
# =============================================================================
# AI Market Research Assistant - View Logs
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

if [ -z "$1" ]; then
    echo "Usage: $0 [service|all]"
    echo ""
    echo "Services:"
    echo "  frontend, gateway, django-api, celery-worker, celery-beat"
    echo "  mcp-server, a2a-orchestrator, postgres, redis"
    echo "  all - show all service logs"
    exit 1
fi

if [ "$1" = "all" ]; then
    docker compose logs -f --tail=100
else
    docker compose logs -f --tail=100 "$1"
fi
