# The Kenya HR App (self-documenting walkthrough)

`apps/kenya_hr` is a standard Frappe **app** you can install with
`bench install-app kenya_hr`. It extends ERPNext/HRMS without patching them.

## Layout

```
apps/kenya_hr/
├── __init__.py                     app version
├── hooks.py                        framework wiring (installs, events, scheduler)
├── modules.txt                     adds the "Kenya HR" module
├── setup.py / requirements.txt     packaging
└── kenya_hr/
    ├── __init__.py                 package docstring (map of modules)
    ├── config/                     desk + docs metadata
    ├── install.py                  install-time customisation (fields, leave types, roles)
    ├── overrides.py                doc_events on Employee / Leave Application
    ├── api.py                      @frappe.whitelist() helper endpoints
    ├── hris_k_sync.py              optional HRIS-K integration client
    ├── doctype/
    │   ├── kenya_hr_settings/      single configuration document
    │   └── staff_promotion/        the promotion workflow document
    └── report/
        └── staff_promotion_log/    promotion status report
```

## What each piece does

### `install.py` — runs at install time (idempotent)

1. **Custom Fields on Employee** — `create_custom_fields` adds the Kenya
   identity fields. Field names start with `custom_` so they can never clash
   with future standard fields. This is the upgrade-safe alternative to
   `export-fixtures`.
2. **Statutory Leave Types** — created only if missing. Tuning values are kept
   in the `KENYA_LEAVE_TYPES` list at the top of the file.
3. **Roles** — `Kenya HR Manager`, `Kenya Department Head`,
   `Senior HR Approver`, `HR Officer`.

### `staff_promotion/` — controller-backed state machine

The `Staff Promotion` doctype JSON declares fields + permissions; the
controller (`staff_promotion.py`) enforces:

- ordered stages and the legal transitions between them,
- which role may advance/reject a promotion,
- side-effect on the Employee when a promotion is marked `Effective`.

All the rules live in small, named constants (`PROMOTION_STAGES`,
`ALLOWED_TRANSITIONS`, `TRANSITION_ROLES`) so the workflow is readable as data.

### `kenya_hr_settings/` — one configuration document

Company, default annual-leave type, promotion toggles, and the HRIS-K
integration block (base URL, API key, org code). Only `Kenya HR Manager` can
edit it (declared in the doctype JSON permissions).

### `overrides.py` — documented hooks into standard doctypes

`hooks.py` registers `doc_events`; each handler delegates to `hris_k_sync`
(which is a **no-op unless enabled**) and posts audit ToDos/Comments. No
downstream code is patched.

### `api.py` — whitelisted endpoints

`get_employee_kenya_details`, `get_leave_balance`, `eligible_for_leave`,
`mark_promotion_effective`. Callable from the desk, scripts, or REST.

### `hris_k_sync.py` — optional integration

See [HRIS-K integration](06-hris-k-integration.md). Disabled by default; the
payloads are collected in one place so adapting to the official API contract is
a small, reviewable change.

## Developing against this app

```bash
# deploy with live reload of the app source
./scripts/deploy-docker.sh --dev

# after editing python code, restart + migrate
docker compose -f docker-compose.generated.yml restart backend
docker compose -f docker-compose.generated.yml exec backend bench --site erp.localhost migrate
```

For a manual bench, `bench get-app` this directory directly.

## Testing conventions

Script reports and controllers are written to read as specification. Add unit
tests under `kenya_hr/tests/` (Frappe runs them with
`bench --site <site> run-tests --app kenya_hr`) — e.g. test each promotion
transition with `frappe.get_doc` and assert the resulting `approval_status`.