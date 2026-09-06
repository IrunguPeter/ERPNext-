# Keycloak SSO

Single sign-on for the Kenya ERP site using **Keycloak** as an OpenID Connect
(OIDC) Identity Provider. This is bundled in-repo; the full manual variant is
in your [erpnext-keycloak-setup](https://github.com/IrunguPeter/erpnext-keycloak-setup) guide.

## How to enable (Docker)

```bash
./scripts/deploy-docker.sh --with-keycloak
```

This:
1. Starts a Keycloak service (host port **18080**, admin `admin` / `admin`).
2. Provisions a realm (`erpnext-realm`), a public client (`erpnext`), and a
   test user (`erpnext-admin` / `admin`).

Then wire the ERPNext login button:

```bash
./scripts/setup-keycloak-sso.sh -- erp.localhost
```

## What it sets up

| Piece | Details |
| --- | --- |
| Keycloak service | `docker/overrides/compose.keycloak.yaml` (image `quay.io/keycloak/keycloak:23.0.4`) |
| Realm/client provisioning | `scripts/setup-keycloak.sh` (Keycloak Admin REST API) |
| ERPNext Social Login Key | `scripts/setup-keycloak-sso.sh` (creates `keycloak` key on the site) |

## Verify

1. Open **http://localhost:18080/** → realm `erpnext-realm` (admin/admin).
2. Open the ERPNext login page → **Keycloak** button →
   login as `erpnext-admin` / `admin`. You are redirected back and logged in.

## Config knobs (`docker/.env`)

| Var | Default |
| --- | --- |
| `KEYCLOAK_VERSION` | `23.0.4` |
| `KEYCLOAK_PUBLISH_PORT` | `18080` |
| `KEYCLOAK_ADMIN` | `admin` |
| `KEYCLOAK_ADMIN_PASSWORD` | `admin` |

## Production notes

- Run behind **HTTPS** and change the Keycloak admin password.
- Use a **confidential** client and a client secret (the scripts default to a
  public client for the local demo).
- The API endpoint must be an absolute URL; the scripts already use
  `http://keycloak:8080/realms/<realm>/...` from inside the compose network.
- Advanced mapping (Keycloak groups → Role Profiles) requires the
  `frappe-oidc-extended` app; see the manual guide.

## Troubleshooting

- **No Keycloak button** → re-run `setup-keycloak-sso.sh`, then clear the Frappe
  cache (`bench --site <site> clear-cache`).
- **Redirect URI mismatch** → the Keycloak client's redirect URIs and the ERPNext
  site's host/port must match exactly.
- **Email not verified** → ensure the user in Keycloak has `emailVerified`.
