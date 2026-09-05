# Roles & Permissions

The Kenya HR, Kenya Procurement and Kenya Fleet apps ship with roles but let the
administrator control exactly what each role can do. This page documents the
recommended matrix and how the custom doctypes enforce access.

## Roles created by the apps

| Role | Intended holder | Purpose |
| --- | --- | --- |
| `Kenya HR Manager` | HR head / HR admin | Full control of Kenya HR config, promotions, reports |
| `Kenya Department Head` | Department heads | Create + first-approve department promotions |
| `Senior HR Approver` | Director / senior HR | Second sign-off on promotions |
| `HR Officer` | Regular HR staff | Create promotions, manage day-to-day HR |
| `Procurement Manager` | Procurement head | Full control of procurement, E-GP connector, delete rights |
| `Procurement Officer` | Procurement staff | Daily ops: onboard suppliers, maintain tenders & bids |
| `Fleet Manager` | Fleet/admin officer | Full control of fleet records + the GVMS connector, delete rights |
| `Driver` | Vehicle drivers | File fuel logs & accident reports, read the rest of fleet data |
| `Employee` (standard) | All staff | Self-service: apply for leave, view own record, read tenders & fleet |

## Where permissions live

1. **In code** — the `permissions` blocks inside the doctype JSON, e.g. for
   `Staff Promotion`, `Kenya HR Settings`, `Kenya EGP Settings`, `Tender`,
   `Supplier Onboarding`, `Vehicle`, `Fuel Log`, `GVMS Settings`. These are
   applied by `bench migrate`.
2. **In the controller** — `Staff Promotion` also checks *which role* may
   perform each transition (`TRANSITION_ROLES`), so UI-level permission is
   enforced server-side too. `Vehicle Assignment` blocks overlapping
   allocations and `Vehicle Disposal` retires the vehicle on completion.
3. **In the connector** — `kenya_procurement.egp_sync`, `kenya_fleet.gvms_sync`
   and `hris_k_sync` are no-ops unless their master switch is set in the
   settings single.
4. **In the UI** — HRMS entities (`Employee`, `Leave Application`) use the
   standard "Role Permissions Manager". Configure the matrix below once.

## Recommended matrix (HRMS entities)

### Employee

| Role | Read | Write | Create | Delete |
| --- | --- | --- | --- | --- |
| Kenya HR Manager | ✓ | ✓ | ✓ | ✓ |
| Kenya Department Head | ✓ | ✓ (own department via User Permissions) | ✓ | – |
| Employee | ✓ (own record only via User Permissions) | – | – | – |
| HR Officer | ✓ | ✓ | ✓ | – |

### Leave Application

| Role | Read | Write | Create | Approve |
| --- | --- | --- | --- | --- |
| Employee | own | – | ✓ | – |
| Kenya Department Head | own department | ✓ | – | first level |
| Kenya HR Manager | ✓ | ✓ | ✓ | final |
| HR Officer | ✓ | ✓ | ✓ | – |

## Setting up User Permissions (own-record / department-scoped)

Use **Setup → Permissions → User Permission** so records are filtered by value
(e.g. `User → Department` or `Employee`). This is how "own record only" and
"department only" are enforced.

## Notes on `Staff Promotion` permissions (already in the JSON)

| Role | Read | Write | Create |
| --- | --- | --- | --- |
| Kenya HR Manager | ✓ | ✓ | ✓ |
| Administrator | ✓ | ✓ | ✓ |
| HR Officer | ✓ | ✓ | ✓ |
| Kenya Department Head | ✓ | ✓ | ✓ |
| Senior HR Approver | ✓ | ✓ | – |
| Employee | ✓ | – | – |

`Kenya HR Settings` is editable only by `Kenya HR Manager` (and Administrator).
`Kenya EGP Settings` is editable only by `Procurement Manager` (and Administrator).

## Procurement doctype permissions (already in the JSON)

| Doctype | Procurement Manager | Procurement Officer | Employee |
| --- | --- | --- | --- |
| `Kenya EGP Settings` | read/write/create/delete | – | – |
| `Supplier Onboarding` | read/write/create/delete | read/write/create | – |
| `Tender` | read/write/create/delete | read/write/create | read |
| `Tender Bid` | read/write/create/delete | read/write/create | – |

## Fleet doctype permissions (already in the JSON)

| Doctype | Fleet Manager | Driver | Employee |
| --- | --- | --- | --- |
| `GVMS Settings` | read/write/create/delete | – | – |
| `Vehicle` | read/write/create/delete | read | read |
| `Driver` | read/write/create/delete | read | read |
| `Vehicle Assignment` | read/write/create/delete | read | read |
| `Fuel Log` | read/write/create/delete + submit | read/create/submit (no delete) | read |
| `Maintenance Record` | read/write/create/delete + submit | read | read |
| `Insurance Policy` | read/write/create/delete | read | read |
| `Accident Report` | read/write/create/delete | read/create/write (no delete) | read |
| `Vehicle Disposal` | read/write/create/delete | read | read |

Fleet reports (`Fuel Consumption`, `Fleet Register`, `Fleet Compliance`) are
readable by all three roles. The Fleet Manager may *amend* submitted fuel and
maintenance records; Drivers cannot.