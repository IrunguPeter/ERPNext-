# Quickstart

Spin up a full ERPNext + HRMS + **Kenya HR + Procurement + Fleet** stack in
about 10-15 minutes.

## Prerequisites

- Linux (Ubuntu 24.04 / Debian 13 tested) or macOS
- Docker Engine 23+ with **Compose v2**
- `git`, `jq` (`sudo apt install git jq`)

## Steps

```bash
# 1. Preview what the script will do
./scripts/deploy-docker.sh --help

# 2. Deploy (builds images; the first build downloads ~1GB)
./scripts/deploy-docker.sh

# 3. The script prints the URL and credentials.
#    For the default site name add a hosts entry:
#    echo "127.0.0.1 erp.localhost" | sudo tee -a /etc/hosts
```

Open **http://erp.localhost:8080** and log in with `Administrator` / `admin`.

## What you get

| App | Provides |
| --- | --- |
| `erpnext` | Full ERP: accounts, buying, selling, stock, projects |
| `hrms` | Employees, Leave Application, Payroll, Attendance |
| `kenya_hr` | Kenya employee ID fields, statutory leave types, Staff Promotion workflow, Kenya HR Settings |
| `kenya_procurement` | E-GP procurement: Supplier Onboarding, Tender mirroring, bids, Kenya EGP Settings |
| `kenya_fleet` | Fleet Management: Vehicle, Driver, Vehicle Assignment, Fuel Log, Maintenance, Insurance, Accidents, Disposal, GVMS Settings |

The `kenya_hr` app is installed *automatically*; its `after_install` creates:

- Custom Fields on Employee: `custom_national_id`, `custom_kra_pin`,
  `custom_nhif_number`, `custom_nssf_number`, `custom_upn_number`, `custom_grade`
- Leave Types: Annual Leave, Sick Leave, Maternity Leave, Paternity Leave,
  Compassionate Leave, Study Leave
- Roles: `Kenya HR Manager`, `Kenya Department Head`, `Senior HR Approver`, `HR Officer`

The `kenya_procurement` app is installed too; its `after_install` creates the
`Procurement Manager` and `Procurement Officer` roles and a `Kenya EGP Settings`
single. The E-GP connector stays **off** until you enable it (see
[Procurement & E-GP](11-procurement-egp.md)).

The `kenya_fleet` app is installed too; its `after_install` creates the
`Fleet Manager` and `Driver` roles and a `GVMS Settings` single. The GVMS
connector stays **off** until you enable it (see
[Fleet Management](10-fleet-management-reference.md)).

## Try the HR features

1. **Create an employee** — HR → Employee → New; note the Kenya section
   (National ID, KRA PIN, NHIF, NSSF, UPN).
2. **Apply for leave** — HR → Leave and Attendance → Leave Application.
3. **Start a promotion** — Kenya HR → Staff Promotion → New
   (`Draft` → `Submitted` → `Approved by Department Head` →
   `Approved by Director` → `Effective`).
4. **Configure the app** — Kenya HR → Kenya HR Settings.

## Try the procurement features

1. **Onboard a supplier** — Kenya Procurement → Supplier Onboarding → New
   (BRS registration no., KRA PIN, AGPO, E-GP status).
2. **Mirror a tender** — Kenya Procurement → Tender → New (or enable the
   connector in Kenya EGP Settings to pull tenders automatically).
3. **Add bids** — open a tender → Tender Bids child table.
4. **Review the pipeline** — Kenya Procurement → Reports → Tender Pipeline.

## Try the fleet features

1. **Register a vehicle** — Fleet Management → Vehicle → New (registration
   `GK A123B`, category **Official**, then Save).
2. **Allocate it** — Fleet Management → Vehicle Assignment → New (the Vehicle
   flips to **Assigned**; overlapping allocations are blocked).
3. **Log fuel** — Fleet Management → Fuel Log → New, then **Submit** (unit
   price derives; the Vehicle odometer advances).
4. **Add cover** — Fleet Management → Insurance Policy → New (auto-expires).
5. **Compliance** — Fleet Management → Reports → Fleet Compliance (insurance,
   licenses and scheduled maintenance due in 30 days).

## Stop / remove

```bash
./scripts/teardown-docker.sh          # stops, keeps data
./scripts/teardown-docker.sh --volumes  # stops and deletes everything
```

## Next steps

- [Deployment options](02-docker-deployment.md) — production, domains, SSL
- [Manual (non-Docker) install](03-manual-install.md)
- [HR configuration guide](04-hr-configuration.md)
- [How the Kenya HR app works](05-kenya-hr-app.md)
- [HRIS-K integration](06-hris-k-integration.md)
- [Roles & permissions](07-roles-permissions.md)
- [Backup & restore](08-backup-restore.md)
- [Architecture](09-architecture.md)
- [Fleet Management](10-fleet-management-reference.md)
- [Procurement & E-GP](11-procurement-egp.md)