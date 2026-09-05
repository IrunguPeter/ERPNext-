#!/usr/bin/env bash
#
# bench.sh - run bench commands inside the ERPNext backend container.
#
# Usage:
#   ./scripts/bench.sh <site> <bench-command...>
#
# Examples:
#   ./scripts/bench.sh erp.localhost list-apps
#   ./scripts/bench.sh erp.localhost --site erp.localhost backup
#   ./scripts/bench.sh erp.localhost console
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

COMPOSE_FILE="docker-compose.generated.yml"
[ -f "$COMPOSE_FILE" ] || { echo "No $COMPOSE_FILE found. Run ./scripts/deploy-docker.sh first."; exit 1; }

SITE="${1:?Usage: ./scripts/bench.sh <site> <command...>}"
shift

docker compose -f "$COMPOSE_FILE" exec backend bench --site "$SITE" "$@"