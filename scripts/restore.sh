#!/usr/bin/env bash
#
# restore.sh - restore a site database backup.
#
# Usage: ./scripts/restore.sh <site> <backup-file-inside-container>
#
# The backup file must already be inside the backend container
# (e.g. /home/frappe/frappe-bench/backups/mysite-2026-01-01.sql.gz).
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

COMPOSE_FILE="docker-compose.generated.yml"
[ -f "$COMPOSE_FILE" ] || { echo "No $COMPOSE_FILE found. Run ./scripts/deploy-docker.sh first."; exit 1; }

SITE="${1:?Usage: ./scripts/restore.sh <site> <backup-file>}"
BACKUP="${2:?Usage: ./scripts/restore.sh <site> <backup-file>}"

docker compose -f "$COMPOSE_FILE" exec backend bench --site "$SITE" restore "$BACKUP" --force
echo "==> Restore complete. Clear caches and restart workers:"
echo "    ./scripts/bench.sh $SITE clear-cache"
echo "    docker compose -f $COMPOSE_FILE restart backend schedule worker-default"