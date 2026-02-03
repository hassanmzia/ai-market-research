#!/usr/bin/env bash
# =============================================================================
# AI Market Research Assistant - Stop Script
# =============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "Stopping all services..."
docker compose down

echo "All services stopped."
