# ERPNext- · Kenya HR, Procurement & Fleet

An **ERPNext v16** deployment pre-configured for Human Resources, procurement
and fleet management for the Kenyan public sector, with three custom apps:

- **Kenya HR** — statutory leave, national identity fields, multi-stage promotions
- **Kenya Procurement** — E-GP (Electronic Government Procurement) mirror:
  supplier onboarding, tender tracking, and an opt-in gateway connector
- **Kenya Fleet** — government-aligned fleet management: vehicles, drivers,
  fuel, maintenance, insurance, accident reporting, disposal, and an opt-in
  GVMS connector

> Self-documenting project: every script, doc, and module in this repository
> explains itself. Start at [Quickstart](docs/01-quickstart.md).

```
┌──────────────────────────────────────────────────────────────┐
│  ERPNext v16  +  HRMS  +  kenya_hr + kenya_procurement        │
│                                +  kenya_fleet                 │
│                                                              │
│  HR · Promotions · HRIS-K · Procurement · E-GP · Fleet · GVMS │
└──────────────────────────────────────────────────────────────┘
```

## What's in here

| Path | Purpose |
| --- | --- |
| [`apps/kenya_hr/`](apps/kenya_hr/) | Custom Frappe app: Kenya employee fields, statutory leave types, Staff Promotion workflow, Kenya HR Settings, HRIS-K client |
| [`apps/kenya_procurement/`](apps/kenya_procurement/) | Custom Frappe app: E-GP procurement - Supplier Onboarding, Tender/Bid mirroring, Kenya EGP Settings, opt-in connector |
| [`apps/kenya_fleet/`](apps/kenya_fleet/) | Custom Frappe app: Fleet Management - Vehicle, Driver, Fuel Log, Maintenance, Insurance, Accidents, Disposal, GVMS Settings, opt-in connector |
| [`docker/`](docker/) | Image build files (`apps.json`, `Containerfile.kenya_hr`) and env template |
| [`scripts/`](scripts/) | Repeatable ops: deploy, teardown, bench, backup, restore |
| [`docs/`](docs/) | Full documentation (all guides) |

## Quick start (Docker, ~10 min)

```bash
# requirements: docker + compose v2 + git + jq
./scripts/deploy-docker.sh
```

Then open **http://erp.localhost:8080** — `Administrator` / `admin`
(add `127.0.0.1 erp.localhost` to `/etc/hosts`).

The deploy script builds a custom image with ERPNext + HRMS, layers all three
custom apps on top, and creates a site with all five apps installed. See
[Deployment](docs/02-docker-deployment.md) for production options (domains,
passwords, ports, SSL, updates).

## HR features (from the custom app)

- **Employees** — National ID, KRA PIN, NHIF, NSSF, UPN fields on the Employee master
- **Leave** — statutory Kenya leave types (Annual 21, Sick 7, Maternity 90,
  Paternity 14, Compassionate 7, Study 30), allocations/policies, balance annotation
- **Promotions** — `Staff Promotion` with a guarded state machine:
  `Draft → Submitted → Dept Head → Director → Effective` (+ Reject), audit trail,
  auto-update of the Employee designation/grade on effectiveness
- **Optional HRIS-K sync** — opt-in client in `kenya_hr/hris_k_sync.py`

See the [HR configuration guide](docs/04-hr-configuration.md) and the
[app walkthrough](docs/05-kenya-hr-app.md).

## Procurement features (from the custom app)

- **Supplier Onboarding** — E-GP profile: BRS registration no., KRA PIN,
  authorised rep / ID, business categories, AGPO (youth/women/PWD), E-GP status
- **Tender mirroring** — `Tender` records keyed on E-GP Tender ID
  (reference no., procuring entity, method, start/end datetimes), embedded bid table
- **Kenya EGP Settings** — master switch + API gateway endpoint/token (Password)
- **Optional E-GP connector** — opt-in `egp_sync.py`: daily pull of tenders and
  supplier status via a gateway endpoint (the public portal has no REST API)
- **Tender Pipeline report** — status breakdown chart + deadlines table

See [Procurement & E-GP integration](docs/11-procurement-egp.md).

## Fleet features (from the custom app)

- **Vehicle register** — GVMS-style master: registration, Transport Policy 2024
  categories, stock/ops facts, status, tracking device + GPS telemetry
- **Drivers & allocations** — NTSA licence data (classes A-D), certifications,
  Vehicle Assignment with overlap guard (one active allocation per vehicle)
- **Fuel & maintenance** — submittable Fuel Logs (derived unit price, advanced
  odometer) and Maintenance Records (next-service planning)
- **Insurance & accidents** — per-vehicle cover that auto-expires, incident
  reports with police/insurance references
- **Disposal** — age-based retirement (7-10 yrs) that retires the Vehicle
- **Optional GVMS connector** — opt-in `gvms_sync.py`: real-time fuel/
  maintenance push on submit, daily registry sync, hourly GPS pull
- **Reports** — Fuel Consumption, Fleet Register, Fleet Compliance

See [Fleet Management](docs/10-fleet-management-reference.md).

## Documentation index

| Topic | Doc |
| --- | --- |
| Fastest start | [01-quickstart.md](docs/01-quickstart.md) |
| Docker deployment (prod) | [02-docker-deployment.md](docs/02-docker-deployment.md) |
| Manual (bare-metal) install | [03-manual-install.md](docs/03-manual-install.md) |
| HR configuration guide | [04-hr-configuration.md](docs/04-hr-configuration.md) |
| Kenya HR app internals | [05-kenya-hr-app.md](docs/05-kenya-hr-app.md) |
| HRIS-K integration | [06-hris-k-integration.md](docs/06-hris-k-integration.md) |
| Roles & permissions | [07-roles-permissions.md](docs/07-roles-permissions.md) |
| Backup & restore | [08-backup-restore.md](docs/08-backup-restore.md) |
| Architecture | [09-architecture.md](docs/09-architecture.md) |
| Fleet management | [10-fleet-management-reference.md](docs/10-fleet-management-reference.md) |
| Procurement & E-GP | [11-procurement-egp.md](docs/11-procurement-egp.md) |

Root-level `*.md` guides (`erpnext-setup-guide.md`, `erpnext-customization-guide.md`,
`erpnext-fleet-management-guide.md`) are the original planning material that
this project was built on; keep them for reference.

## Repository layout

```
.
├── apps/kenya_hr/            # custom HR app (installable via bench)
├── apps/kenya_procurement/   # custom procurement app (installable via bench)
├── apps/kenya_fleet/         # custom fleet app (installable via bench)
├── docker/                   # image build + env template
├── scripts/                  # deploy / teardown / bench / backup / restore
├── docs/                     # documentation (start here)
├── erpnext-*-guide.md        # original planning guides
├── LICENSE                   # MIT
└── README.md
```

## License

MIT — see [LICENSE](LICENSE).

## Upstream projects

- [Frappe](https://github.com/frappe/frappe) — low-code web framework
- [ERPNext](https://github.com/frappe/erpnext) — open-source ERP
- [Frappe HRMS](https://github.com/frappe/hrms) — HR & payroll
- [frappe_docker](https://github.com/frappe/frappe_docker) — official container setup