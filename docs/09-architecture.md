# Architecture

## Overview

```
                    ┌─────────────────────────────────────────┐
                    │               Browser                    │
                    └────────────────────┬────────────────────┘
                                         │ HTTPS / HTTP (:8080 demo)
                    ┌────────────────────▼────────────────────┐
                    │       frontend  (nginx, assets)         │
                    └───────┬──────────────┬──────────────────┘
                            │              │
        ┌───────────────────▼───┐   ┌──────▼────────────────────────┐
        │     backend           │   │  worker-default / short / long│
        │  (Gunicorn, WSGI)     │   │  (Celery job workers)         │
        └───┬───────────────────┘   └──────┬───────────────────────┘
            │                              │
            └─────────────┬────────────────┘
                          │
        ┌─────────────────▼────────────────────────────────────────┐
        │              configurator  (writes supervisor/nginx)     │
        └─────────────────┬────────────────────────────────────────┘
                          │
   ┌───────────┐  ┌───────▼────────┐  ┌─────────────────────────────┐
   │   db       │  │ redis-cache   │  │ redis-queue / socketio      │
   │  MariaDB   │  │ (frappe cache)│  │ (jobs / realtime)           │
   └───────────┘  └────────────────┘  └─────────────────────────────┘
```

All services run under Docker Compose (the `docker-compose.generated.yml`
produced by `deploy-docker.sh`). Persistent state lives in named volumes
(`db-data`, `sites`, ...) — see [Docker deployment](02-docker-deployment.md).

## Application stack

| Layer | Technology |
| --- | --- |
| Framework | Frappe v16 (Python 3.14, Node 24 for assets) |
| Core apps | `erpnext` (ERP), `hrms` (HR & payroll), `payments` (if enabled) |
| Custom app | `kenya_hr` — HR add-on for this project |
| Database | MariaDB 11.8 (utf8mb4) |
| Cache/queue | Redis 7 (3 instances: cache, queue, socketio) |
| Web server | nginx (frontend), Gunicorn (backend) |
| PDF | wkhtmltopdf / Chromium (installed in image) |

## Module responsibilities in `kenya_hr`

```
hooks.py        → declares install/uninstall, doc_events, scheduler, metadata
install.py      → adds Employee custom fields, statutory leave types, roles
staff_promotion → promotion state machine (controller + JSON validation)
kenya_hr_settings → app-level configuration single
overrides.py    → Employee / Leave doc_events (audit + optional sync)
api.py          → whitelisted REST helpers
hris_k_sync.py  → optional HRIS-K client (opt-in)
report/staff_promotion_log → promotions report
```

## Key design decisions

1. **No monkey-patching.** All extension happens through documented hooks
   (`doc_events`, `after_install`, app doctypes). Upgrades of ERPNext/HRMS stay
   clean.
2. **Custom fields are prefixed `custom_`** and created programmatically
   (`create_custom_fields(..., update=True)`), avoiding fixture drift.
3. **The promotion workflow is data-driven.** Stages and allowed transitions
   are constants in `staff_promotion.py`, making the policy readable and
   easy to review in code review.
4. **Integration is opt-in and isolated.** `hris_k_sync.py` has no effect
   unless enabled, and API payloads/credentials are confined to one module.
5. **Deployment wraps the official frappe_docker** rather than vendoring a
   fork, so security fixes flow upstream and this repo documents *how* rather
   than *what* images to run.

## Data model (core entities)

```
User ──user_id──▶ Employee ──has many──▶ Leave Application
                    │                        │ leave_type
                    │                        ▼
                    │                   Leave Type / Allocation
                    │
                    │   has designation / department / grade
                    ▼
              Staff Promotion  (employee → new designation/grade)
```

## Security model

- RBAC via roles (see [Roles & permissions](07-roles-permissions.md)).
- The promotion controller re-checks role membership server-side per transition.
- Secrets (API keys, DB passwords) never enter the repo; use `.env`/docker
  secrets / Password fields.