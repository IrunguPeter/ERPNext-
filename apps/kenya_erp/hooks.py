#
# Kenya ERP - Frappe app hooks
#
# Every Frappe app exposes a `hooks.py` that tells the framework how to load,
# install, and behave. This app consolidates the three former Kenya extensions
# (kenya_hr / kenya_procurement / kenya_fleet) into one.
#
# Modules owned by this app:
#   kenya_erp.install         - idempotent setup (roles, leave types, fields)
#   kenya_erp.overrides       - doc_events handlers on standard + custom doctypes
#   kenya_erp.api             - whitelisted (REST) helper endpoints
#   kenya_erp.hris_k_sync     - optional HRIS-K integration
#   kenya_erp.egp_sync        - optional E-GP (procurement) connector
#   kenya_erp.gvms_sync       - optional GVMS (fleet) connector
#   kenya_erp.doctype         - custom DocTypes owned by this app
#   kenya_erp.report          - custom reports shipped with this app
#

app_name = "kenya_erp"  # Python package name (used for imports and `bench install-app`)
app_title = "Kenya ERP"  # Human readable title shown in the desk
app_publisher = "IrunguPeter"
app_description = (
    "Kenyan public-sector ERP extension for ERPNext: HR (statutory leave, "
    "national identity fields, promotions with HRIS-K sync), Procurement "
    "(E-GP supplier onboarding, tenders, bids) and Fleet (vehicles, drivers, "
    "fuel, maintenance, insurance, disposal with GVMS sync)."
)
app_email = "irungupeter204@gmail.com"
app_license = "MIT"
app_version = "0.1.0"
app_icon = "octicon octicon-organization"
app_color = "#00693E"  # Kenya green
app_url = "https://github.com/IrunguPeter/ERPNext-"

# ---------------------------------------------------------------------------
# Required apps
# ---------------------------------------------------------------------------
# `bench install-app kenya_erp` will install these first. The HR extension
# builds on HRMS `Employee` / `Leave Application`; procurement on ERPNext
# `Supplier`; fleet on `Supplier`, `Employee` and `Department`.
# ---------------------------------------------------------------------------
required_apps = ("erpnext", "hrms")

# ---------------------------------------------------------------------------
# Install / uninstall lifecycle
# ---------------------------------------------------------------------------
after_install = "kenya_erp.install.after_install"
after_app_install = "kenya_erp.install.after_install"
after_app_uninstall = "kenya_erp.install.after_app_uninstall"

# ---------------------------------------------------------------------------
# DocType events
# ---------------------------------------------------------------------------
# Fired on lifecycle events of standard doctypes (Employee, Leave Application,
# Supplier) and this app's own doctypes (Vehicle, Fuel Log, Maintenance Record)
# so Kenya-specific data is enriched or synchronised without patching upstream.
# ---------------------------------------------------------------------------
doc_events = {
    "Employee": {
        "after_insert": "kenya_erp.overrides.on_employee_after_insert",
        "on_update": "kenya_erp.overrides.on_employee_update",
    },
    "Leave Application": {
        "on_submit": "kenya_erp.overrides.on_leave_application_submit",
        "on_cancel": "kenya_erp.overrides.on_leave_application_cancel",
    },
    "Supplier": {
        "after_insert": "kenya_erp.overrides.on_supplier_after_insert",
        "on_update": "kenya_erp.overrides.on_supplier_update",
    },
    "Vehicle": {
        "on_update": "kenya_erp.overrides.on_vehicle_saved",
    },
    "Fuel Log": {
        "on_submit": "kenya_erp.overrides.on_fuel_log_submit",
    },
    "Maintenance Record": {
        "on_submit": "kenya_erp.overrides.on_maintenance_submit",
    },
}

# ---------------------------------------------------------------------------
# Scheduled tasks
# ---------------------------------------------------------------------------
# All integrations are opt-in and no-op unless their Settings master switch is
# enabled:
#   HR   - daily HRIS-K employee sync
#   EGP  - daily procurement sync (tenders / suppliers)
#   GVMS - hourly GPS pull + daily vehicle registry sync
# Fuel and maintenance are pushed in real time via the submit hooks.
# ---------------------------------------------------------------------------
scheduler_events = {
    "hourly": [
        "kenya_erp.gvms_sync.sync_all_vehicle_locations",
    ],
    "daily": [
        "kenya_erp.hris_k_sync.sync_all_employees_due",
        "kenya_erp.egp_sync.sync_all_due",
        "kenya_erp.gvms_sync.sync_all_due",
    ],
}
