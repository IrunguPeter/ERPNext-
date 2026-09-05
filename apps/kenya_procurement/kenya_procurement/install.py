# install.py - idempotent, self-documenting setup for the Kenya Procurement app.
#
# Design note (same as kenya_hr): roles and defaults are created *programmatically*
# (not via fixtures) so they can be diffed, upgraded safely, and re-run after a
# partial failure. Every function is safe to call again.
from __future__ import annotations

import frappe

# ---------------------------------------------------------------------------
# Public constants - the single source of truth for the app's defaults.
# ---------------------------------------------------------------------------

# Roles created on install. Used by the doctype permissions blocks in the JSON
# files; they must exist before the first `bench migrate`.
KENYA_EGP_ROLES = (
    "Procurement Manager",  # full control of procurement + EGP connector
    "Procurement Officer",  # daily operations: onboarding suppliers, tenders, bids
)

# Procurement methods recognised by PPRA (PPADA 2015 / PPADR 2020).
PPRA_PROCUREMENT_METHODS = (
    "Open Tender",
    "Restricted Tender",
    "Direct Procurement",
    "Request for Quotation (RFQ)",
    "Request for Proposals (RFP)",
    "Request for Expressions of Interest (REOI)",
)

# AGPO = Access to Government Procurement Opportunities (30% government
# set-aside programme for youth / women / persons-with-disabilities enterprises).
# The same list is hardcoded in the Supplier Onboarding doctype JSON
# (`agpo_category` select); mirror those options if you change it here.
AGPO_CATEGORY_OPTIONS = ("Youth Enterprise", "Women Enterprise", "Persons with Disability Enterprise")

# EGP portal root. The connector only overrides this via Kenya EGP Settings.
EGP_PORTAL_URL = "https://egpkenya.go.ke"
EGP_SUPPLIER_REGISTRATION_URL = f"{EGP_PORTAL_URL}/supplier/registration"


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------
def after_install():
    """Run after this app is installed on a site (idempotent)."""
    create_kenya_egp_roles()
    create_default_egp_settings()


def after_app_uninstall():
    """Best-effort cleanup. Keeps ERPNext `Supplier` records untouched on purpose."""
    frappe.clear_cache()


# ---------------------------------------------------------------------------
# Setup helpers
# ---------------------------------------------------------------------------
def create_kenya_egp_roles():
    """Create the procurement roles if they do not already exist."""
    for role in KENYA_EGP_ROLES:
        if not frappe.db.exists("Role", role):
            frappe.get_doc({"doctype": "Role", "role_name": role}).insert(ignore_permissions=True)


def create_default_egp_settings():
    """Ensure a `Kenya EGP Settings` single exists with portal defaults."""
    settings = frappe.get_single("Kenya EGP Settings")
    if not settings.base_url:
        settings.base_url = EGP_PORTAL_URL
    if not settings.supplier_registration_url:
        settings.supplier_registration_url = EGP_SUPPLIER_REGISTRATION_URL
    settings.flags.ignore_permissions = True
    settings.save()