# Kenya Fleet - Frappe app hooks
#
# This app adds a government-aligned fleet management section to ERPNext
# (per docs/10-fleet-management-reference.md and the GVMS working-group spec in
# erpnext-fleet-management-guide.md):
#
#   * Vehicle              - fleet master incl. categories mapped to the GoK
#                            Transport Policy 2024 user classes
#   * Driver               - licensed drivers (NTSA licence classes A-D)
#   * Vehicle Assignment   - allocation of vehicles to employees/officers
#   * Fuel Log             - fuel purchases (litres, cost, odometer)
#   * Maintenance Record   - services/repairs plus next-service planning
#   * Insurance Policy     - comprehensive/third-party cover per vehicle
#   * Accident Report      - road traffic incident records
#   * Vehicle Disposal     - disposal of aged BOR (age 7-10 years) vehicles
#   * GVMS Settings        - opt-in connector to the Government Vehicle
#                            Management System (GPS / telematics / registry)
#
# The connector is opt-in (same rule as kenya_hr / kenya_procurement): nothing
# runs until `GVMS Settings.enabled` is checked. GVMS does not publish a public
# REST API, so the connector targets a gateway/middleware endpoint you control;
# see docs/10-fleet-management-reference.md.
#

app_name = "kenya_fleet"  # Python package name (used for imports and `bench install-app`)
app_title = "Kenya Fleet"
app_publisher = "IrunguPeter"
app_description = (
    "Government-aligned fleet management for ERPNext - vehicles, drivers, "
    "fuel logs, maintenance, insurance, accident reporting, vehicle disposal "
    "and an opt-in GVMS (Government Vehicle Management System) connector."
)
app_email = "irungupeter204@gmail.com"
app_license = "MIT"
app_version = "0.1.0"
app_icon = "octicon octicon-location"
app_color = "#00693E"  # Kenya green
app_url = "https://github.com/IrunguPeter/ERPNext-"

# ---------------------------------------------------------------------------
# Required apps
# ---------------------------------------------------------------------------
# Uses `Supplier` (insurance companies, maintenance vendors) from ERPNext and
# `Employee` / `Department` from HRMS (drivers and assignment allocations).
# ---------------------------------------------------------------------------
required_apps = ("erpnext", "hrms")

# ---------------------------------------------------------------------------
# Install / uninstall lifecycle
# ---------------------------------------------------------------------------
after_install = "kenya_fleet.install.after_install"
after_app_install = "kenya_fleet.install.after_install"
after_app_uninstall = "kenya_fleet.install.after_app_uninstall"

# ---------------------------------------------------------------------------
# DocType events
# ---------------------------------------------------------------------------
doc_events = {
    "Vehicle": {
        "on_update": "kenya_fleet.overrides.on_vehicle_saved",
    },
    "Fuel Log": {
        "on_submit": "kenya_fleet.overrides.on_fuel_log_submit",
    },
    "Maintenance Record": {
        "on_submit": "kenya_fleet.overrides.on_maintenance_submit",
    },
}

# ---------------------------------------------------------------------------
# Scheduled tasks
# ---------------------------------------------------------------------------
# Opt-in GVMS synchronisation. A no-op unless `GVMS Settings.enabled` is set.
#   hourly - pull GPS locations for vehicles with a tracking device id
#   daily  - push/refresh the vehicle registry
# Fuel and maintenance records are pushed in real time via the submit hooks.
# ---------------------------------------------------------------------------
scheduler_events = {
    "hourly": [
        "kenya_fleet.gvms_sync.sync_all_vehicle_locations",
    ],
    "daily": [
        "kenya_fleet.gvms_sync.sync_all_due",
    ],
}