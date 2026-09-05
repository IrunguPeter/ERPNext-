#
# Kenya HR - Frappe app hooks
#
# Every Frappe app exposes a `hooks.py` that tells the framework how to load,
# install, and behave. See the docstring fields below for what each hook does.
#
# This file is intentionally heavily commented so the project is self-documenting.
#

app_name = "kenya_hr"  # Python package name (used for imports and `bench install-app`)
app_title = "Kenya HR"  # Human readable title shown in the desk
app_publisher = "IrunguPeter"
app_description = (
    "Kenya-specific Human Resources extension for ERPNext. Adds statutory leave "
    "types, national identity fields on Employee, and a multi-stage Staff "
    "Promotion workflow with optional HRIS-K synchronisation."
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
# `bench install-app kenya_hr` will install these first. The Kenya HR app
# extends the standard HRMS `Employee` and `Leave Application` doctypes, so
# those apps must be present before our `after_install` runs.
# ---------------------------------------------------------------------------
required_apps = ("erpnext", "hrms")

# ---------------------------------------------------------------------------
# Install / uninstall lifecycle
# ---------------------------------------------------------------------------
after_install = "kenya_hr.install.after_install"
after_app_install = "kenya_hr.install.after_install"
after_app_uninstall = "kenya_hr.install.after_app_uninstall"

# ---------------------------------------------------------------------------
# Document satellite hooks
# ---------------------------------------------------------------------------
# The apps front-end includes (a JS bundle) shipped by this app. We keep the
# app backend-only, so nothing to include:
# app_include_css = "/assets/kenya_hr/css/kenya_hr.css"
# app_include_js  = "/assets/kenya_hr/js/kenya_hr.js"

# ---------------------------------------------------------------------------
# DocType events
# ---------------------------------------------------------------------------
# Fired on lifecycle events of standard HRMS doctypes so the Kenya HR app can
# enrich or synchronise data without patching the HRMS codebase.
# ---------------------------------------------------------------------------
doc_events = {
    "Employee": {
        "after_insert": "kenya_hr.overrides.on_employee_after_insert",
        "on_update": "kenya_hr.overrides.on_employee_update",
    },
    "Leave Application": {
        "on_submit": "kenya_hr.overrides.on_leave_application_submit",
        "on_cancel": "kenya_hr.overrides.on_leave_application_cancel",
    },
}

# ---------------------------------------------------------------------------
# Scheduled tasks
# ---------------------------------------------------------------------------
# Jobs that run on an interval. Used by the (optional, opt-in) HRIS-K
# synchronisation. Empty by default - see docs/06-hris-k-integration.md.
# ---------------------------------------------------------------------------
scheduler_events = {
    "daily": [
        "kenya_hr.hris_k_sync.sync_all_employees_due",
    ]
}

# ---------------------------------------------------------------------------
# Whitelisted API methods
# ---------------------------------------------------------------------------
# Methods exposed over the REST API / whitelisted endpoints. These live in
# kenya_hr/api.py and are decorated with @frappe.whitelist().
# ---------------------------------------------------------------------------
# override_whitelisted_methods = {}

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
# Configuration records that are exported as JSON and auto-synced on migrate.
# Data created by kenya_hr.install is intentionally *programmatic* so it can
# be diffed and upgraded safely; see docs/05-kenya-hr-app.md for the trade-off.
# ---------------------------------------------------------------------------
# fixtures = [...]

# ---------------------------------------------------------------------------
# Permissions
# ---------------------------------------------------------------------------
# `fixtures` above can include "Custom DocPerm" or "Role" so permission rules
# survive `bench migrate`. Kenya-specific roles are created in install.py.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Jinja filters / print formats / web hooks
# ---------------------------------------------------------------------------
# jenv = {}
# developer_mode_only = []
# web_include_js = []