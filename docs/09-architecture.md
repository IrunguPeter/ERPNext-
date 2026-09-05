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
| Custom apps | `kenya_hr` — HR add-on; `kenya_procurement` — E-GP procurement add-on; `kenya_fleet` — fleet management add-on |
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

## Module responsibilities in `kenya_procurement`

```
hooks.py          → declares required_apps, doc_events on Supplier, daily sync
install.py        → creates Procurement roles + Kenya EGP Settings defaults
supplier_onboarding → E-GP supplier profile (BRS no., KRA PIN, AGPO, categories)
tender            → tender notice mirror + validation (closing > start)
tender_bid        → bid submissions + evaluation result (child of Tender)
kenya_egp_settings → connector single (endpoint, token, toggles)
egp_sync.py       → opt-in gateway connector (no-op unless enabled)
overrides.py      → Supplier doc_events (EGP status annotation)
api.py            → whitelisted REST helpers (open tenders, EGP status)
report/tender_pipeline → tender pipeline report + bar chart
```

## Module responsibilities in `kenya_fleet`

```
hooks.py             → declares doc_events (Vehicle/Fuel Log/Maintenance),
                       hourly + daily scheduler for the connector
install.py           → creates Fleet roles + GVMS Settings defaults
vehicle              → fleet master (category, stock/ops facts, GPS telemetry)
driver               → licensed drivers (NTSA classes, certifications)
vehicle_assignment   → allocation with overlap guard + status flip
fuel_log             → submittable fuel purchase (derived unit price)
maintenance_record   → submittable service/repair/inspection + next service
insurance_policy     → per-vehicle cover, auto-expiry from end date
accident_report      → incident records (police/insurance references)
vehicle_disposal     → age-based retirement (marks Vehicle Retired)
gvms_settings        → connector single (endpoint, key, toggles)
gvms_sync.py         → opt-in gateway connector (no-op unless enabled)
overrides.py         → save/submit doc_events delegating to gvms_sync
api.py               → whitelisted REST helpers (fleet_summary, get_vehicle)
report/fuel_consumption → litres/cost/consumption per vehicle per period
report/fleet_register   → fleet register w/ insurance overlay
report/fleet_compliance → insurance, licenses, scheduled maintenance due
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
4. **Integration is opt-in and isolated.** `hris_k_sync.py`, `egp_sync.py` and
   `gvms_sync.py` have no effect unless enabled, and credentials live in a
   single settings doctype (Password fields).
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

Procurement (Kenya Procurement app):

```
Supplier ──onboarded in──▶ Supplier Onboarding ──has many──▶ business categories
     │                              │
     │                              │ participates in
     │                              ▼
     └──────────────────────▶ Tender ◀──has many── Tender Bids
                                 │ (mirrored from E-GP)
                                 └─► awarded_to (Supplier Onboarding)
```

Fleet (Kenya Fleet app):

```
Vehicle ──has many──▶ Vehicle Assignment ─assigned_to──▶ Employee
  │  ──has many──▶ Fuel Log        (submittable, advances odometer)
  │  ──has many──▶ Maintenance Record (submittable, next service plan)
  │  ──has many──▶ Insurance Policy   (auto-expires)
  │  ──has many──▶ Accident Report    (police/insurance references)
  │
  └──disposed by──▶ Vehicle Disposal ──▶ marks Vehicle Retired
Employee ──licensed as──▶ Driver (NTSA licence classes A-D)
```

## Security model

- RBAC via roles (see [Roles & permissions](07-roles-permissions.md)).
- The promotion controller re-checks role membership server-side per transition;
  submittable fleet docs (Fuel Log, Maintenance Record) cannot be edited once
  submitted and only Fleet Manager can amend them.
- E-GP / HRIS-K / GVMS connectors are no-ops unless their master switch is set;
  tokens are stored in Password fields (GVMS sends `X-GVMS-Key`).
- Secrets (API keys, DB passwords) never enter the repo; use `.env`/docker
  secrets / Password fields.