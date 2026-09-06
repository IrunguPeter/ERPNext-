#!/usr/bin/env bash
#
# setup-keycloak.sh - provision a Keycloak realm + OIDC client for ERPNext SSO.
#
# Automates the manual steps in the original keycloak-sso-setup guide:
#   1. Create the realm
#   2. Create a public OIDC client for ERPNext
#   3. Add a test user
#
# Assumptions:
#   * The 'keycloak' compose service is running (see deploy-docker.sh --with-keycloak).
#   * Keycloak is reachable at the given admin URL (default http://localhost:18080).
#   * `jq` and `curl` are installed.
#
# Usage:
#   ./scripts/setup-keycloak.sh [options]
#
# Options:
#   --kc-url URL        Keycloak base URL (default: http://localhost:18080)
#   --realm NAME        Realm name (default: erpnext-realm)
#   --admin USER:pass   Admin credentials (default: admin:admin)
#   --client-id ID      OIDC client id (default: erpnext)
#   --redirect-uri URI  ERPNext redirect URI (default: http://erp.localhost:8080/*)
#
set -euo pipefail

KC_URL="http://localhost:18080"
REALM="erpnext-realm"
ADMIN_CREDS="admin:admin"
CLIENT_ID="erpnext"
REDIRECT_URI="http://erp.localhost:8080/*"
WEB_ORIGIN="http://erp.localhost:8080"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --kc-url) KC_URL="$2"; shift 2 ;;
    --realm) REALM="$2"; shift 2 ;;
    --admin) ADMIN_CREDS="$2"; shift 2 ;;
    --client-id) CLIENT_ID="$2"; shift 2 ;;
    --redirect-uri) REDIRECT_URI="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

command -v curl >/dev/null 2>&1 || { echo "curl is required"; exit 1; }
command -v jq  >/dev/null 2>&1 || { echo "jq is required (apt install jq)"; exit 1; }

echo "==> Waiting for Keycloak at $KC_URL ..."
for i in $(seq 1 60); do
  if curl -sf "$KC_URL" >/dev/null 2>&1; then
    break
  fi
  sleep 2
  if [ "$i" = 60 ]; then echo "Keycloak did not become ready"; exit 1; fi
done

echo "==> Logging in to Keycloak admin ..."
TOKEN=$(curl -sf -X POST "$KC_URL/realms/master/protocol/openid-connect/token" \
  -d "client_id=admin-cli" \
  -d "username=${ADMIN_CREDS%%:*}" \
  -d "password=${ADMIN_CREDS#*:}" \
  -d "grant_type=password" | jq -r '.access_token') \
  || { echo "Admin login failed - check --admin creds"; exit 1; }

AUTH="Authorization: Bearer $TOKEN"
HDR="Content-Type: application/json"
API="$KC_URL/admin/realms"

echo "==> Creating realm '$REALM' (if missing) ..."
if ! curl -sf -H "$AUTH" "$API/$REALM" >/dev/null 2>&1; then
  curl -sf -H "$AUTH" -H "$HDR" -X POST "$API" \
    -d "{\"realm\":\"$REALM\",\"enabled\":true}" >/dev/null
fi

echo "==> Creating OIDC client '$CLIENT_ID' (if missing) ..."
CLIENT_UUID=$(curl -sf -H "$AUTH" "$API/$REALM/clients?clientId=$CLIENT_ID" \
  | jq -r '.[0].id // empty')
if [ -z "$CLIENT_UUID" ]; then
  CLIENT_UUID=$(curl -sf -H "$AUTH" -H "$HDR" -X POST "$API/$REALM/clients" \
    -d "{
      \"clientId\":\"$CLIENT_ID\",
      \"name\":\"ERPNext\",
      \"protocol\":\"openid-connect\",
      \"publicClient\":true,
      \"standardFlowEnabled\":true,
      \"directAccessGrantsEnabled\":true,
      \"redirectUris\":[\"$REDIRECT_URI\"],
      \"webOrigins\":[\"$WEB_ORIGIN\"]
    }" -D - -o /dev/null | grep -i '^location:' | sed 's|.*clients/||' | tr -d '\r')
fi

echo "==> Adding test user 'erpnext-admin' (if missing) ..."
if ! curl -sf -H "$AUTH" "$API/$REALM/users?username=erpnext-admin" | jq -e 'length > 0' >/dev/null 2>&1; then
  curl -sf -H "$AUTH" -H "$HDR" -X POST "$API/$REALM/users" \
    -d '{
      "username":"erpnext-admin",
      "email":"admin@erp.localhost",
      "emailVerified":true,
      "enabled":true,
      "credentials":[{"type":"password","value":"admin","temporary":false}]
    }' >/dev/null
  echo "    created user: erpnext-admin / admin"
else
  echo "    user already exists (skipped)"
fi

echo
echo "Keycloak SSO provisioned."
echo "  Admin console : $KC_URL/ (realm: $REALM)"
echo "  Realm issuer  : $KC_URL/realms/$REALM"
echo "  Client        : $CLIENT_ID (public)"
echo "  Redirect URIs : $REDIRECT_URI"
echo
echo "Next: point ERPNext's 'keycloak' Social Login Key at this realm. Run:"
echo "  ./scripts/setup-keycloak-sso.sh"
