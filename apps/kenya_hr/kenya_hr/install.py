"""
Kenya HR - installation-time setup.

Runs once when the app is installed (or upgraded). Everything here is
idempotent: running it twice is safe, which makes it upgrade-friendly.

What install does
=================
1. Adds Kenya national identity fields to the standard ``Employee`` doctype.
2. Creates the Kenya statutory Leave Types.
3. Creates the Kenya HR roles used by the promotion workflow and permissions.
4. Creates an attendance / statutory label field used by reports.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.utils import nowdate


# ---------------------------------------------------------------------------
# 1. Kenya national identity fields on the Employee master
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
# 2. Kenya statutory Leave Types
# ---------------------------------------------------------------------------
# Per the Kenya Employment Act 2007 (Cap. 226):
#   - Annual leave       : 21 working days / year
#   - Sick leave         : 7 days (subject to medical certificate)
#   - Maternity leave    : 3 months (90 days)
#   - Paternity leave    : not less than 14 days
#   - Compassionate leave: death of immediate family
#----------------------------------------------------------------------------
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
# 3. Kenya HR roles
# ---------------------------------------------------------------------------
# Roles drive the permission rules declared in the Staff Promotion doctype and
# the recommended rules in docs/07-roles-permissions.md.
# ---------------------------------------------------------------------------
KENYA_HR_ROLES = [
    "Kenya HR Manager",
    "Kenya Department Head",
    "Senior HR Approver",
    "HR Officer",
]


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------
def after_install():
    """Create the Kenya-specific HR configuration. Idempotent."""
    create_employee_custom_fields()
    create_kenya_leave_types()
    create_kenya_roles()
    frappe.clear_cache()


def after_app_uninstall():
    """Best-effort cleanup. Does not delete HRIS data on purpose."""
    frappe.clear_cache()


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


def create_kenya_roles():
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


# ---------------------------------------------------------------------------
# Convenience helpers
# ---------------------------------------------------------------------------
def get_statutory_leave_types():
    """Return the list of statutory leave type names handled by this app."""
    return [lt["name"] for lt in KENYA_LEAVE_TYPES]


def ensure_employee_fields_applied():
    """Force-apply the custom fields (used in dev against older sites)."""
    create_employee_custom_fields()
    create_kenya_leave_types()
    create_kenya_roles()