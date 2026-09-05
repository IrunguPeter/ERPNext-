# Fleet Management (reference)

> Scope note: this project's default image **does not** install the fleet app.
> Use this page when the organisation also manages a vehicle pool and wants the
> government-fleet workflows described in *erpnext-fleet-management-guide.md*.

## Quick start

```bash
# manual bench (add to the apps list before install)
bench get-app https://github.com/frappe/fleet_management
bench --site your-site install-app fleet_management
```

Or bake into the image: append the repo URL to `docker/apps.json` and rerun
`./scripts/deploy-docker.sh`.

## Entities to create (if not provided by the app)

| DocType | Key fields |
| --- | --- |
| Vehicle | Registration No, Make/Model, Year, Engine/Chassis No, Fuel Type, Department, Status (Available/Assigned/Under Maintenance/Retired), Insurance Expiry, GPS Tracking Device ID |
| Vehicle Assignment | Vehicle, Driver/Employee, Start/End date, Purpose, Approved By |
| Driver | Employee, License No, License Class, Expiry, Endorsements |
| Fuel Log | Vehicle, Date, Odometer, Quantity, Cost, Station, Receipt No |
| Maintenance Record | Vehicle, Type (Service/Repair/Inspection), Date, Cost, Vendor, Next Service |
| Insurance Policy | Policy No, Company, Vehicle, Type, Start/End, Premium, Status |
| Accident Report | Vehicle, Driver, Date, Location, Injuries, Damage, Police No, Status |

## Kenya government rules encoded in the guide

- **Vehicle allocation** per Transport Policy 2024 (CS, PS, parastatal heads, pool).
- **Disposal criteria** by vehicle class (age-based: 7–10 years depending on class).
- **Authorised fuel stations / fuel card** workflows.
- **Preventive maintenance** intervals per vehicle class.

## Integration option: GVMS

The guide sketches an `erpnext_gvms_integration` app that mirrors the same
opt-in pattern this repo uses for HRIS-K: a settings single + a client module
+ hooks. Follow [Explanation of HRIS-K](06-hris-k-integration.md) as the
template if you build it.

## Reports worth shipping

- Vehicle Register (dept, status, age)
- Fleet Utilization / Idle time
- Cost per vehicle / per km
- Insurance & License compliance (expiry alerts)
- Fuel consumption + anomaly detection

Full detail: see `erpnext-fleet-management-guide.md` (kept at repo root for
reference) and the original project docs.