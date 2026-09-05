# install.py - idempotent, self-documenting setup for the Kenya Fleet app.
#
# Design note (same as kenya_hr / kenya_procurement): roles and defaults are
# created *programmatically* (not via fixtures) so they can be diffed, upgraded
# safely, and re-run after a partial failure. Every function is safe to call
# again.
from __future__ import annotations

import frappe

# ---------------------------------------------------------------------------
# Public constants - the single source of truth for the app's defaults.
# ---------------------------------------------------------------------------

# Roles created on install. Used by the doctype permissions blocks in the JSON
# files; they must exist before the first `bench migrate`.
FLEET_ROLES = (
    "Fleet Manager",  # full control of fleet records + the GVMS connector
    "Driver",         # drivers: fuel logs, accident reports (read for the rest)
)

# GoK Transport Policy 2024 user classes the Vehicle category maps to.
VEHICLE_CATEGORIES = (
    "Executive",
    "Official",
    "General Purpose",
    "Utility",
    "Security",
    "Ambulance",
    "Specialized",
)

VEHICLE_STATUS_OPTIONS = ("Available", "Assigned", "Under Maintenance", "Retired")

MAINTENANCE_TYPE_OPTIONS = ("Service", "Repair", "Inspection")

POLICY_TYPE_OPTIONS = ("Comprehensive", "Third Party", "Fire and Theft", "Specialized")

# Disposal criteria per the Transport Policy 2024 (age 7-10 years by class).
DISPOSAL_REASON_OPTIONS = (
    "Age Based",
    "Condition Based",
    "Beyond Economical Repair",
    "Funding/Duration Closure",
    "Other",
)

# GVMS portal root. The connector overrides this via GVMS Settings.
GVMS_PORTAL_URL = "https://gvms.go.ke"


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------
def after_install():
    """Run after this app is installed on a site (idempotent)."""
    create_fleet_roles()
    create_default_gvms_settings()


def after_app_uninstall():
    """Best-effort cleanup. Keeps ERPNext/HRMS masters untouched on purpose."""
    frappe.clear_cache()


# ---------------------------------------------------------------------------
# Setup helpers
# ---------------------------------------------------------------------------
def create_fleet_roles():
    """Create the fleet roles if they do not already exist."""
    for role in FLEET_ROLES:
        if not frappe.db.exists("Role", role):
            frappe.get_doc({"doctype": "Role", "role_name": role}).insert(ignore_permissions=True)


def create_default_gvms_settings():
    """Ensure a `GVMS Settings` single exists with portal defaults."""
    settings = frappe.get_single("GVMS Settings")
    if not settings.base_url:
        settings.base_url = GVMS_PORTAL_URL
    settings.flags.ignore_permissions = True
    settings.save()