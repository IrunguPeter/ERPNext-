#!/usr/bin/env bash
#
# deploy-docker.sh - build and run the ERPNext + HRMS + Kenya ERP stack with Docker.
#
# This is a thin, documented wrapper around the official frappe_docker project:
#   https://github.com/frappe/frappe_docker
#
# It performs the following steps (each one is independently re-runnable):
#   1. Clones frappe_docker (pinned ref) into ./.frappe_docker
#   2. Builds a custom image with ERPNext + HRMS (docker/apps.json)
#   3. Layers the consolidated Kenya ERP app on top
#      (docker/Containerfile.kenya_erp)
#   4. Generates the final compose file
#   5. Starts all containers
#   6. Creates a site and installs erpnext, hrms, kenya_erp
#
# Usage:
#   ./scripts/deploy-docker.sh [options]
#
# Options:
#   -s, --site NAME      Site name (default: erp.localhost)
#   -p, --admin-pass X   Administrator password (default: admin)
#   -d, --db-pass X      MariaDB root password (default: 123)
#   -P, --port N         HTTP publish port (default: 8080)
#   -e, --env FILE       .env file used for the compose pipeline (default: docker/.env)
#   --version TAG        ERPNext image version tag (default: v16.34.1)
#   --dev                Mount the local app source instead of baking it (dev loop)
#   --with-keycloak      Also start Keycloak (SSO) and provision realm/client
#   -h, --help           Show this help
#
# Examples:
#   ./scripts/deploy-docker.sh                          # local demo stack
#   ./scripts/deploy-docker.sh --with-keycloak          # + Keycloak SSO
#   ./scripts/deploy-docker.sh --site erp.example.com --admin-pass s3cret \
#         --db-pass s3cret --port 80                    # production-ish box
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

# ---------------------------------------------------------------------------
# defaults
# ---------------------------------------------------------------------------
SITE="erp.localhost"
ADMIN_PASSWORD="admin"
DB_PASSWORD="123"
HTTP_PUBLISH_PORT="8080"
ERPNEXT_VERSION="v16.34.1"
DEV_MODE=0
WITH_KEYCLOAK=0
DOT_ENV="docker/.env"

usage() { sed -n '2,35p' "$0"; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    -s|--site) SITE="$2"; shift 2 ;;
    -p|--admin-pass) ADMIN_PASSWORD="$2"; shift 2 ;;
    -d|--db-pass) DB_PASSWORD="$2"; shift 2 ;;
    -P|--port) HTTP_PUBLISH_PORT="$2"; shift 2 ;;
    -e|--env) DOT_ENV="$2"; shift 2 ;;
    --version) ERPNEXT_VERSION="$2"; shift 2 ;;
    --dev) DEV_MODE=1; shift ;;
    --with-keycloak) WITH_KEYCLOAK=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1"; usage; exit 1 ;;
  esac
done

# ---------------------------------------------------------------------------
# 0. prerequisites
# ---------------------------------------------------------------------------
command -v docker >/dev/null 2>&1 || { echo "docker is required"; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "docker compose v2 is required"; exit 1; }
command -v jq >/dev/null 2>&1 || { echo "jq is required (apt install jq)"; exit 1; }

FRAPPE_DOCKER_DIR="$REPO_DIR/.frappe_docker"
CUSTOM_IMAGE="kenya-erp-stack:16"

echo "==> Kenya ERP stack deploy script"
echo "    site: $SITE  admin-pass: $ADMIN_PASSWORD  port: $HTTP_PUBLISH_PORT"
echo "    erpnext image tag: $ERPNEXT_VERSION  dev mode: $([ "$DEV_MODE" = 1 ] && echo yes || echo no)"

# ---------------------------------------------------------------------------
# 1. clone/pin frappe_docker
# ---------------------------------------------------------------------------
if [ ! -d "$FRAPPE_DOCKER_DIR/.git" ]; then
  echo "==> Cloning frappe_docker ..."
  git clone --depth 1 https://github.com/frappe/frappe_docker "$FRAPPE_DOCKER_DIR"
else
  echo "==> frappe_docker already present, updating ..."
  git -C "$FRAPPE_DOCKER_DIR" fetch --depth 1 origin
  git -C "$FRAPPE_DOCKER_DIR" reset --hard origin/main
fi
# Pin to a specific ref if one was given (recommended for reproducibility).
if [ "${FRAPPE_DOCKER_REF:-}" ]; then
  git -C "$FRAPPE_DOCKER_DIR" checkout "$FRAPPE_DOCKER_REF"
fi

# ---------------------------------------------------------------------------
# 2. write the app manifest for the layered build
# ---------------------------------------------------------------------------
APPS_JSON="$FRAPPE_DOCKER_DIR/apps.json"
cp "$REPO_DIR/docker/apps.json" "$APPS_JSON"
jq empty "$APPS_JSON" || { echo "apps.json is invalid"; exit 1; }

# ---------------------------------------------------------------------------
# 3. build the two-stage custom image
# ---------------------------------------------------------------------------
echo "==> Building ERPNext + HRMS base image (this can take a while) ..."
pushd "$FRAPPE_DOCKER_DIR" >/dev/null
# The layered Containerfile reads the app list via a BuildKit *secret* (not a
# build-arg) mounted at /opt/frappe/apps.json. Docker 23+ uses BuildKit by
# default, so --secret works out of the box.
docker build \
  --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
  --build-arg=FRAPPE_BRANCH=version-16 \
  --secret=id=apps_json,src="$APPS_JSON" \
  --tag=erpnext-hrms:16 \
  --file=images/layered/Containerfile .
popd >/dev/null

echo "==> Layering Kenya ERP app ..."
docker build \
  -f docker/Containerfile.kenya_erp \
  --build-arg BASE_IMAGE=erpnext-hrms:16 \
  -t "$CUSTOM_IMAGE" .

# ---------------------------------------------------------------------------
# 4. environment file used by the compose pipeline
# ---------------------------------------------------------------------------
if [ ! -f "$DOT_ENV" ]; then
  echo "==> Creating $DOT_ENV"
  cp docker/.env.example "$DOT_ENV"
fi

cat > .env.deploy <<EOF
ERPNEXT_VERSION=$ERPNEXT_VERSION
DB_PASSWORD=$DB_PASSWORD
HTTP_PUBLISH_PORT=$HTTP_PUBLISH_PORT
HTTPS_PUBLISH_PORT=443
CUSTOM_IMAGE=${CUSTOM_IMAGE%:*}
CUSTOM_TAG=${CUSTOM_IMAGE##*:}
PULL_POLICY=never
KEYCLOAK_VERSION=${KEYCLOAK_VERSION:-23.0.4}
KEYCLOAK_PUBLISH_PORT=${KEYCLOAK_PUBLISH_PORT:-18080}
KEYCLOAK_ADMIN=${KEYCLOAK_ADMIN:-admin}
KEYCLOAK_ADMIN_PASSWORD=${KEYCLOAK_ADMIN_PASSWORD:-admin}
EOF

# ---------------------------------------------------------------------------
# 5. generate + start the compose stack
# ---------------------------------------------------------------------------
COMPOSE_OUT="$REPO_DIR/docker-compose.generated.yml"
COMPOSE_FILES=(
  -f "$FRAPPE_DOCKER_DIR/compose.yaml"
  -f "$FRAPPE_DOCKER_DIR/overrides/compose.mariadb.yaml"
  -f "$FRAPPE_DOCKER_DIR/overrides/compose.redis.yaml"
  -f "$FRAPPE_DOCKER_DIR/overrides/compose.noproxy.yaml"
)
if [ "$WITH_KEYCLOAK" = 1 ]; then
  COMPOSE_FILES+=(-f "$REPO_DIR/docker/overrides/compose.keycloak.yaml")
fi

echo "==> Rendering compose file ..."
docker compose --env-file .env.deploy "${COMPOSE_FILES[@]}" config > "$COMPOSE_OUT"

echo "==> Starting containers ..."
docker compose -f "$COMPOSE_OUT" up -d

if [ "$WITH_KEYCLOAK" = 1 ]; then
  echo "==> Provisioning Keycloak realm + client ..."
  "$REPO_DIR/scripts/setup-keycloak.sh" \
    --kc-url "http://localhost:${KEYCLOAK_PUBLISH_PORT:-18080}" \
    --admin "admin:${KEYCLOAK_ADMIN_PASSWORD:-admin}" || \
    echo "WARNING: Keycloak provisioning failed - run scripts/setup-keycloak.sh manually."
fi

# ---------------------------------------------------------------------------
# 6. create site + install apps
# ---------------------------------------------------------------------------
RUN() { docker compose -f "$COMPOSE_OUT" exec backend bench "$@"; }

if docker compose -f "$COMPOSE_OUT" exec backend bash -c "test -f sites/$SITE/site_config.json"; then
  echo "==> Site $SITE already exists, skipping site creation."
else
  echo "==> Creating site $SITE and installing erpnext ..."
  RUN new-site "$SITE" \
    --mariadb-user-host-login-scope=% \
    --db-root-password "$DB_PASSWORD" \
    --admin-password "$ADMIN_PASSWORD" \
    --install-app erpnext
  echo "==> Installing hrms ..."
  RUN --site "$SITE" install-app hrms
  echo "==> Installing kenya_erp ..."
  RUN --site "$SITE" install-app kenya_erp
fi

docker compose -f "$COMPOSE_OUT" exec backend bench --site "$SITE" clear-cache >/dev/null 2>&1 || true

echo
echo "Deployment complete."
echo "  UI   : http://localhost:$HTTP_PUBLISH_PORT  (if your site is '$SITE', add:"
echo "         '127.0.0.1 $SITE' to /etc/hosts and browse http://$SITE:$HTTP_PUBLISH_PORT)"
echo "  Admin: Administrator / $ADMIN_PASSWORD"
if [ "$WITH_KEYCLOAK" = 1 ]; then
  echo "  Keycloak : http://localhost:${KEYCLOAK_PUBLISH_PORT:-18080}/ (admin/admin)"
  echo "  Next     : ./scripts/setup-keycloak-sso.sh -- $SITE  to wire the login button"
fi
echo
echo "Helpers:"
echo "  ./scripts/bench.sh -- $SITE <cmd>       run bench commands"
echo "  ./scripts/backup.sh -- $SITE            take a site backup"
echo "  ./scripts/teardown-docker.sh            stop and remove the stack"
echo "  compose file: docker-compose.generated.yml"