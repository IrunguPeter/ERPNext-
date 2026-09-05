# Fleet Management (kenya_fleet)

> Status: **implemented**. The **`kenya_fleet`** app installs with every site of
> this project (default image) and provides the government-aligned fleet
> workflows that *erpnext-fleet-management-guide.md* reuses. When the connector
> is off, the app is simply manual fleet records; nothing depends on GVMS.

## What the app adds

| DocType | Purpose | Autoname |
| --- | --- | --- |
| Vehicle | Fleet master: registration, category (Transport Policy 2024 classes), make/model/year, engine/chassis, fuel type, department, status, tracking device + live GPS telemetry (read-only) | `VHC-.YYYY.-.#####` |
| Driver | Licensed drivers linked to HRMS `Employee`: NTSA licence number/class/expiry, certifications (defensive driving, first aid, medical fitness) | `DRV-.YYYY.-.#####` |
| Vehicle Assignment | Allocation of a vehicle to an officer/employee with dates, purpose and approver; one active allocation per vehicle enforced | `VA-.YYYY.-.#####` |
| Fuel Log | Submittable fuel purchase: date, odometer, litres, cost (unit price derived), station, receipt number | `FLG-.YYYY.-.#####` |
| Maintenance Record | Submittable service/repair/inspection: cost, vendor (ERPNext `Supplier`), description, next service date/odometer | `MNT-.YYYY.-.#####` |
| Insurance Policy | Cover per vehicle (comprehensive/third party/fire & theft/specialized) against an ERPNext `Supplier`; auto-expires from its end date | `INS-.YYYY.-.#####` |
| Accident Report | Road traffic incidents with police/insurance references; closed reports require a reference number | `ACC-.YYYY.-.#####` |
| Vehicle Disposal | Retiring vehicles (age 7-10 years per Transport Policy 2024 or condition based); setting it **Completed** marks the Vehicle **Retired** | `DSP-.YYYY.-.#####` |
| GVMS Settings | Single doctype: master switch + connector configuration (see below) | - |

## Roles

Created at install: **Fleet Manager** (full control incl. the connector) and
**Driver** (creates fuel logs and accident reports, reads the rest). Everyone
with the standard **Employee** role can read fleet records. Grant the roles to
users under *Setup > Users*; see docs/07.

## Kenya government rules encoded

- **Vehicle allocation** — Vehicle `status` flips to `Assigned` when an active
  Vehicle Assignment starts; overlapping assignments to different employees
  are blocked.
- **Disposal criteria** — `Vehicle Disposal.disposal_reason` mirrors the
  Transport Policy 2024 age bands (7-10 years by class) and completion retires
  the vehicle.
- **Insurance / licence compliance** — Insurance Policy auto-sets `Expired`;
  expired licenses warn on the Driver record.
- **Preventive maintenance** — `Maintenance Record.next_service_date` /
  `next_service_odometer` feed the compliance report.
- **Audit trails** — Fuel Log and Maintenance Record are submittable (cannot
  be edited/rolled back after submission).

Full operational detail (fuel-station/fuel-card workflows, allocation classes
per user group, maintenance intervals by class): see
`erpnext-fleet-management-guide.md` (kept at repo root) and
`ERP NEXT/fleet-management-system.md`.

## GVMS connector (opt-in)

`GVMS Settings` is the master switch, same pattern as the HRIS-K and E-GP
connectors:

1. Check **Enable GVMS Connector** in *Fleet Management > GVMS Settings*.
2. Set **API Gateway Endpoint** (GVMS has no public REST API today; point the
   connector at a gateway/middleware endpoint, yours or the government's) and
   optionally an **API Key** (sent as `X-GVMS-Key`) and your **Organization
   Code**.
3. Tune which parts sync: vehicles, fuel logs, maintenance, vehicle locations.
   Fuel/maintenance push in real time on **submit**; vehicles push on save and
   on the daily job; locations pull hourly for vehicles with a tracking device
   id.

Expected gateway endpoints (`kenya_fleet/gvms_sync.py`):
`POST /vehicles/sync`, `POST /fuel/sync`, `POST /maintenance/sync`,
`GET /vehicles/{registration_number}`, `GET /tracking/{device_id}` returning
`{"latitude":…, "longitude":…, "at":…}`.

Whitelisted helpers (`kenya_fleet/api.py`): `fleet_summary()` (dashboard
figures), `get_vehicle(vehicle)` (public key facts), `sync_vehicle_now(vehicle)`
(manual push for testing).

## Reports

| Report | Shows |
| --- | --- |
| Fuel Consumption | Litres, cost and consumption (litres/100km) per vehicle for a date range |
| Fleet Register | Every vehicle with category, department, status, odometer and insurance overlay |
| Fleet Compliance | Anything due in 30 days: insurance, driving licenses, scheduled maintenance (date or odometer) |

## Try it

1. After deployment, log in as **Administrator** (docs/01).
2. Give yourself **Fleet Manager** via `scripts/bench.sh -- <site> execute
   frappe.client.get_list` — or simpler, assign the role in *Setup > Users*.
3. *Fleet Management > Vehicle* → **New**: enter registration `GK A123B`,
   category **Official**, than **Save**.
4. Create a **Vehicle Assignment**, then a submitted **Fuel Log**, and open
   **Fleet Register** / **Fuel Consumption** reports.