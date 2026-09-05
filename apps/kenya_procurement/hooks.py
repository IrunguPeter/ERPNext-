# Kenya Procurement - Frappe app hooks
#
# This app adds a public-procurement section that mirrors the Kenyan E-GP
# (Electronic Government Procurement) system operated by the National Treasury:
#
#   * Supplier Onboarding  - E-GP registration data (BRS no., KRA PIN, AGPO, etc.)
#   * Tender               - tender notices mirrored from the E-GP portal
#   * Tender Bid           - bid submissions and their evaluation status
#   * Kenya EGP Settings   - opt-in connector configuration
#
# The connector is opt-in (mirrors docs/06-hris-k-integration.md): nothing runs
# until `Kenya EGP Settings.enabled` is checked. E-GP itself does not publish a
# public REST API, so sync targets a gateway/middleware endpoint you control;
# see docs/11-procurement-egp.md.
#

app_name = "kenya_procurement"  # Python package name (used for imports and `bench install-app`)
app_title = "Kenya Procurement"
app_publisher = "IrunguPeter"
app_description = (
    "Kenya public-procurement extension for ERPNext integrated with the E-GP "
    "(Electronic Government Procurement) system - supplier onboarding, tender "
    "mirroring, bid tracking and an opt-in EGP connector."
)
app_email = "irungupeter204@gmail.com"
app_license = "MIT"
app_version = "0.1.0"
app_icon = "octicon octicon-package"
app_color = "#00693E"  # Kenya green
app_url = "https://github.com/IrunguPeter/ERPNext-"

# ---------------------------------------------------------------------------
# Required apps
# ---------------------------------------------------------------------------
# Uses the standard ERPNext `Supplier` master and purchase transactions.
# ---------------------------------------------------------------------------
required_apps = ("erpnext",)

# ---------------------------------------------------------------------------
# Install / uninstall lifecycle
# ---------------------------------------------------------------------------
after_install = "kenya_procurement.install.after_install"
after_app_install = "kenya_procurement.install.after_install"
after_app_uninstall = "kenya_procurement.install.after_app_uninstall"

# ---------------------------------------------------------------------------
# DocType events
# ---------------------------------------------------------------------------
doc_events = {
    "Supplier": {
        "after_insert": "kenya_procurement.overrides.on_supplier_after_insert",
        "on_update": "kenya_procurement.overrides.on_supplier_update",
    },
}

# ---------------------------------------------------------------------------
# Scheduled tasks
# ---------------------------------------------------------------------------
# Opt-in EGP synchronisation. A no-op unless `Kenya EGP Settings.enabled` is set.
# ---------------------------------------------------------------------------
scheduler_events = {
    "daily": [
        "kenya_procurement.egp_sync.sync_all_due",
    ]
}