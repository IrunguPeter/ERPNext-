# ERPNext- · Kenya ERP

An **ERPNext v16** deployment for the **Kenyan public sector** — HR,
procurement and fleet management — all bundled into **one Frappe app**:
`kenya_erp`.

> Self-documenting project. Start at [Quickstart](docs/01-quickstart.md).

```
┌──────────────────────────────────────┐
│  ERPNext v16 + HRMS + kenya_erp      │
│                                      │
│  HR · Procurement · Fleet · SSO-ready│
└──────────────────────────────────────┘
```

## What it does (in brief)

| Module | Features |
| --- | --- |
| **HR** | Kenya statutory leave types, national identity fields (ID, KRA PIN, NHIF, NSSF, UPN), multi-stage Staff Promotion workflow, opt-in HRIS-K sync |
| **Procurement** | E-GP mirror: supplier onboarding, tender/bid tracking, opt-in EGP gateway connector |
| **Fleet** | Vehicles, drivers, fuel, maintenance, insurance, accidents, disposal, opt-in GVMS connector, 3 reports |

Everything lives in [`apps/kenya_erp/`](apps/kenya_erp/). All integrations are
**opt-in** (master switch in their Settings single).

## Quick start (Docker, ~10 min)

```bash
./scripts/deploy-docker.sh
```

Open **http://erp.localhost:8080** — `Administrator` / `admin`
(add `127.0.0.1 erp.localhost` to `/etc/hosts`).

**Want Keycloak SSO too?**

```bash
./scripts/deploy-docker.sh --with-keycloak
./scripts/setup-keycloak-sso.sh -- erp.localhost
```

See [Deployment](docs/02-docker-deployment.md) and
[Keycloak SSO](docs/12-keycloak-sso.md) for production options
(domains, passwords, ports, SSL, updates).

## Repo layout

```
├── apps/kenya_erp/      # the single consolidated Frappe app (installable via bench)
├── docker/              # image build (Containerfile.kenya_erp) + env template
├── scripts/             # deploy / teardown / bench / backup / restore
├── docs/                # documentation (start here)
├── erpnext-*-guide.md   # original planning guides (reference)
├── LICENSE              # MIT
└── README.md
```

> **Legacy:** the previous three apps (`apps/kenya_hr`, `apps/kenya_procurement`,
> `apps/kenya_fleet`) are preserved in the repo but are superseded by
> `kenya_erp`, which merges their functionality.

## Docs

| Topic | Doc |
| --- | --- |
| Fastest start | [01-quickstart.md](docs/01-quickstart.md) |
| Docker deployment (prod) | [02-docker-deployment.md](docs/02-docker-deployment.md) |
| Manual (bare-metal) install | [03-manual-install.md](docs/03-manual-install.md) |
| HR / Procurement / Fleet | [04](docs/04-hr-configuration.md) · [11](docs/11-procurement-egp.md) · [10](docs/10-fleet-management-reference.md) |
| Keycloak SSO | [12-keycloak-sso.md](docs/12-keycloak-sso.md) |
| Roles & permissions | [07-roles-permissions.md](docs/07-roles-permissions.md) |
| Backup & restore | [08-backup-restore.md](docs/08-backup-restore.md) |
| Architecture | [09-architecture.md](docs/09-architecture.md) |

## License

MIT — see [LICENSE](LICENSE).
