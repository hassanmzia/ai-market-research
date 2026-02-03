#!/usr/bin/env bash
# =============================================================================
# AI Market Research Assistant - Reset Script (removes all data)
# =============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "WARNING: This will remove all containers, volumes, and data!"
read -p "Are you sure? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker compose down -v --remove-orphans
    echo "All data and containers removed."
else
    echo "Cancelled."
fi
