#!/usr/bin/env bash
#
# teardown-docker.sh - stop and remove the ERPNext stack.
#
# Usage: ./scripts/teardown-docker.sh [--volumes]
#
# By default the database volume is PRESERVED (your data is kept).
# Pass --volumes to also remove the named volumes (irreversible!).
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

COMPOSE_FILE="docker-compose.generated.yml"
[ -f "$COMPOSE_FILE" ] || { echo "No $COMPOSE_FILE found. Run ./scripts/deploy-docker.sh first."; exit 1; }

KEEP_VOLUMES=1
[ "${1:-}" = "--volumes" ] && KEEP_VOLUMES=0

echo "==> Stopping the stack ..."
if [ "$KEEP_VOLUMES" = 1 ]; then
  docker compose -f "$COMPOSE_FILE" down
  echo "    Data volumes preserved. Images are left in place."
else
  docker compose -f "$COMPOSE_FILE" down --volumes --rmi local
  echo "    Volumes and local images removed."
fi