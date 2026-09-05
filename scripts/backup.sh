#!/usr/bin/env bash
#
# backup.sh - take a site backup (database + files) into ./backups.
#
# Usage: ./scripts/backup.sh <site> [--with-files]
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

COMPOSE_FILE="docker-compose.generated.yml"
[ -f "$COMPOSE_FILE" ] || { echo "No $COMPOSE_FILE found. Run ./scripts/deploy-docker.sh first."; exit 1; }

SITE="${1:?Usage: ./scripts/backup.sh <site> [--with-files]}"
shift || true

mkdir -p backups
docker compose -f "$COMPOSE_FILE" exec backend bench --site "$SITE" backup --backup-path /home/frappe/frappe-bench/backups "$@"

echo "==> Backups produced inside the backend container:"
docker compose -f "$COMPOSE_FILE" exec backend ls -lt /home/frappe/frappe-bench/backups | head -6