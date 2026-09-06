"""
Kenya ERP - installation-time setup.

Consolidated installer for the Kenyan public-sector ERPNext extension. Merges
the three former apps (kenya_hr / kenya_procurement / kenya_fleet) into one.

Runs once when the app is installed (or upgraded). Everything here is
idempotent: running it twice is safe, which makes it upgrade-friendly.

What install does
=================
1. Adds Kenya national identity fields to the standard ``Employee`` doctype.
2. Creates the Kenya statutory Leave Types.
3. Creates the HR / EGP / Fleet roles used by the workflows and permissions.
4. Ensures the `Kenya EGP Settings` and `GVMS Settings` singles exist.

Design note: roles and defaults are created *programmatically* (not via
fixtures) so they can be diffed, upgraded safely, and re-run after a partial
failure. Every function is safe to call again.
"""

from __future__ import annotations

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.utils import nowdate


# ---------------------------------------------------------------------------
# HR: Kenya national identity fields on the Employee master
# ---------------------------------------------------------------------------
# These match the identifiers used by Kenya's government HR systems
# (HRIS-K, KRA iTax, NHIF, NSSF). They are added as Custom Fields so the
# standard HRMS Employee doctype stays upgrade-safe.
#
# Field names are prefixed with ``custom_`` to guarantee they never collide
# with standard fields added by ERPNext/HRMS in future releases.
# ---------------------------------------------------------------------------
KENYA_EMPLOYEE_FIELDS = {
    "Employee": [
        dict(
            fieldname="custom_national_id",
            label="National ID Number",
            fieldtype="Data",
            insert_after="gender",
            translatable=0,
            description="Kenya National Identity Card number.",
        ),
        dict(
            fieldname="custom_kra_pin",
            label="KRA PIN",
            fieldtype="Data",
            insert_after="custom_national_id",
            translatable=0,
            description="Kenya Revenue Authority Personal Identification Number.",
        ),
        dict(
            fieldname="custom_nhif_number",
            label="NHIF Number",
            fieldtype="Data",
            insert_after="custom_kra_pin",
            translatable=0,
            description="National Hospital Insurance Fund membership number.",
        ),
        dict(
            fieldname="custom_nssf_number",
            label="NSSF Number",
            fieldtype="Data",
            insert_after="custom_nhif_number",
            translatable=0,
            description="National Social Security Fund membership number.",
        ),
        dict(
            fieldname="custom_upn_number",
            label="Unified Payroll Number (UPN)",
            fieldtype="Data",
            insert_after="custom_nssf_number",
            translatable=0,
            description="Unified Payroll Number assigned by the public payroll system.",
        ),
        dict(
            fieldname="custom_grade",
            label="Grade",
            fieldtype="Data",
            insert_after="designation",
            translatable=0,
            description="Pay grade of the employee (used by the promotion workflow).",
        ),
        dict(
            fieldname="custom_staff_roll",
            label="Staff Roll",
            fieldtype="Data",
            insert_after="employee_number",
            translatable=0,
            description="Official staff serial/roll number.",
        ),
    ]
}

# ---------------------------------------------------------------------------
# HR: Kenya statutory Leave Types
# ---------------------------------------------------------------------------
# Per the Kenya Employment Act 2007 (Cap. 226):
#   - Annual leave       : 21 working days / year
#   - Sick leave         : 7 days (subject to medical certificate)
#   - Maternity leave    : 3 months (90 days)
#   - Paternity leave    : not less than 14 days
#   - Compassionate leave: death of immediate family
# ---------------------------------------------------------------------------
KENYA_LEAVE_TYPES = [
    dict(
        name="Annual Leave",
        leave_type_name="Annual Leave",
        max_days_allowed=21,
        is_carry_forward=1,
        carry_forward="12 Months",  # carry-over period
        max_carry_forward_days=21,
        expire_carry_forward="30th June",  # expiry of accumulated days
        color="#00693E",
        description="Statutory annual leave per the Kenya Employment Act.",
    ),
    dict(
        name="Sick Leave",
        leave_type_name="Sick Leave",
        max_days_allowed=7,
        is_lwp=0,
        color="#B38F00",
        description="Statutory sick leave; medical certificate required.",
    ),
    dict(
        name="Maternity Leave",
        leave_type_name="Maternity Leave",
        max_days_allowed=90,
        is_lwp=0,
        color="#C70039",
        description="Statutory maternity leave (3 months).",
    ),
    dict(
        name="Paternity Leave",
        leave_type_name="Paternity Leave",
        max_days_allowed=14,
        is_lwp=0,
        color="#581845",
        description="Statutory paternity leave (at least 2 weeks).",
    ),
    dict(
        name="Compassionate Leave",
        leave_type_name="Compassionate Leave",
        max_days_allowed=7,
        is_lwp=0,
        color="#900C3F",
        description="Leave on the death of an immediate family member.",
    ),
    dict(
        name="Study Leave",
        leave_type_name="Study Leave",
        max_days_allowed=30,
        is_lwp=0,
        color="#1F618D",
        description="Leave granted to pursue approved studies or examinations.",
    ),
]

# ---------------------------------------------------------------------------
# HR: Kenya HR roles
# ---------------------------------------------------------------------------
KENYA_HR_ROLES = [
    "Kenya HR Manager",
    "Kenya Department Head",
    "Senior HR Approver",
    "HR Officer",
]

# ---------------------------------------------------------------------------
# Procurement: roles + E-GP defaults
# ---------------------------------------------------------------------------
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
AGPO_CATEGORY_OPTIONS = (
    "Youth Enterprise",
    "Women Enterprise",
    "Persons with Disability Enterprise",
)

# EGP portal root. The connector only overrides this via Kenya EGP Settings.
EGP_PORTAL_URL = "https://egpkenya.go.ke"
EGP_SUPPLIER_REGISTRATION_URL = f"{EGP_PORTAL_URL}/supplier/registration"

# ---------------------------------------------------------------------------
# Fleet: roles + defaults
# ---------------------------------------------------------------------------
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
    create_employee_custom_fields()
    create_kenya_leave_types()
    create_kenya_hr_roles()
    create_kenya_egp_roles()
    create_default_egp_settings()
    create_fleet_roles()
    create_default_gvms_settings()
    frappe.clear_cache()


def after_app_uninstall():
    """Best-effort cleanup. Does not delete ERPNext/HRMS master data on purpose."""
    frappe.clear_cache()


# ---------------------------------------------------------------------------
# HR setup helpers
# ---------------------------------------------------------------------------
def create_employee_custom_fields():
    """Add the Kenya national identity fields to the Employee doctype."""
    create_custom_fields(KENYA_EMPLOYEE_FIELDS, update=True)


def create_kenya_leave_types():
    """Create the statutory Leave Type records if they do not exist."""
    for leave_type in KENYA_LEAVE_TYPES:
        if frappe.db.exists("Leave Type", leave_type["name"]):
            continue
        doc = frappe.get_doc({"doctype": "Leave Type", **leave_type})
        doc.insert()
    frappe.db.commit()


def create_kenya_hr_roles():
    """Create the Kenya HR roles (no-op for roles that already exist)."""
    for role in KENYA_HR_ROLES:
        if not frappe.db.exists("Role", role):
            frappe.get_doc(
                {
                    "doctype": "Role",
                    "role_name": role,
                    "desk_access": 1,
                    "role": role,
                }
            ).insert(ignore_permissions=True)
    frappe.db.commit()


def get_statutory_leave_types():
    """Return the list of statutory leave type names handled by this app."""
    return [lt["name"] for lt in KENYA_LEAVE_TYPES]


def ensure_employee_fields_applied():
    """Force-apply the custom fields (used in dev against older sites)."""
    create_employee_custom_fields()
    create_kenya_leave_types()
    create_kenya_hr_roles()


# ---------------------------------------------------------------------------
# Procurement setup helpers
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


# ---------------------------------------------------------------------------
# Fleet setup helpers
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
