#!/usr/bin/env bash
#
# setup-keycloak-sso.sh - configure ERPNext's 'keycloak' Social Login Key.
#
# Creates or updates a Social Login Key on the ERPNext site so the login page
# shows a Keycloak button and routes OIDC auth through Keycloak.
#
# Requires a running stack (deploy-docker.sh --with-keycloak) and that
# scripts/setup-keycloak.sh has already provisioned the realm/client.
#
# Usage:
#   ./scripts/setup-keycloak-sso.sh -- SITE [--kc-url URL] [--realm NAME] [--client-id ID]
#
# Examples:
#   ./scripts/setup-keycloak-sso.sh -- erp.localhost
#   ./scripts/setup-keycloak-sso.sh -- erp.localhost --kc-url http://keycloak:8080
#
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

if [ ! -f docker-compose.generated.yml ]; then
  echo "docker-compose.generated.yml not found - run deploy-docker.sh first."; exit 1
fi

# First positional arg after `--` is the site.
SITE=""
ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --) shift; SITE="$1"; shift ;;
    *) ARGS+=("$1"); shift ;;
  esac
done

KC_URL="http://keycloak:8080"
REALM="erpnext-realm"
CLIENT_ID="erpnext"

i=0
while [ $i -lt ${#ARGS[@]} ]; do
  case "${ARGS[$i]}" in
    --kc-url)   KC_URL="${ARGS[$((i+1))]}"; i=$((i+2)) ;;
    --realm)    REALM="${ARGS[$((i+1))]}"; i=$((i+2)) ;;
    --client-id) CLIENT_ID="${ARGS[$((i+1))]}"; i=$((i+2)) ;;
    *) echo "Unknown option: ${ARGS[$i]}"; exit 1 ;;
  esac
done

[ -z "$SITE" ] && { echo "Usage: ./scripts/setup-keycloak-sso.sh -- SITE [opts]"; exit 1; }

RUN() { docker compose -f docker-compose.generated.yml exec -T backend bench --site "$SITE" "$@"; }

echo "==> Writing 'keycloak' Social Login Key on $SITE ..."
RUN execute frappe.core.doctype.social_login_key.social_login_key.set_social_login_key \
  --args "[\"keycloak\"]" >/dev/null 2>&1 || true

RUN console <<PYEOF
import json, frappe
name = "keycloak"
key = frappe.get_doc({
    "doctype": "Social Login Key",
    "name": name,
    "provider": name,
    "enable_social_login": 1,
    "client_id": "$CLIENT_ID",
    "client_secret": "",
    "base_url": "$KC_URL/realms/$REALM",
    "authorize_url": "/protocol/openid-connect/auth",
    "access_token_url": "$KC_URL/realms/$REALM/protocol/openid-connect/token",
    "api_endpoint": "$KC_URL/realms/$REALM/protocol/openid-connect/userinfo",
    "icon": name,
    "auth_url_data": json.dumps({
        "response_type": "code",
        "scope": "openid profile email",
    }),
    "user_id_property": "preferred_username",
})
if frappe.db.exists("Social Login Key", name):
    key = frappe.get_doc("Social Login Key", name)
    for f, v in {
        "enable_social_login": 1,
        "client_id": "$CLIENT_ID",
        "base_url": "$KC_URL/realms/$REALM",
        "authorize_url": "/protocol/openid-connect/auth",
        "access_token_url": "$KC_URL/realms/$REALM/protocol/openid-connect/token",
        "api_endpoint": "$KC_URL/realms/$REALM/protocol/openid-connect/userinfo",
        "auth_url_data": json.dumps({"response_type":"code","scope":"openid profile email"}),
        "user_id_property": "preferred_username",
    }.items():
        key.set(f, v)
key.save(ignore_permissions=True)
frappe.db.commit()
print("Social Login Key 'keycloak' configured.")
PYEOF

echo
echo "Keycloak SSO is configured on $SITE."
echo "  Login page now shows the Keycloak button ->" \
     "http://localhost:\${HTTP_PUBLISH_PORT:-8080}/login"
