"""
DocType event handlers (doc_events) for the Kenya ERP app.

Registered in ``hooks.py`` on:

    Employee           -> after_insert / on_update          (HR + HRIS-K)
    Leave Application  -> on_submit / on_cancel             (HR + HRIS-K)
    Supplier           -> after_insert / on_update          (Procurement + EGP)
    Vehicle            -> on_update                         (Fleet + GVMS)
    Fuel Log           -> on_submit                         (Fleet + GVMS)
    Maintenance Record -> on_submit                         (Fleet + GVMS)

Each handler is deliberately small: it delegates to the relevant connector
only when that integration is enabled in its Settings single, otherwise it is
a no-op.
"""

from __future__ import annotations

import frappe
from frappe import _

from . import egp_sync, gvms_sync

MIN_PROMOTION_DAYS_AT_DESIGNATION = 1  # tunable business rule


# ---------------------------------------------------------------------------
# HR: Employee / Leave Application handlers
# ---------------------------------------------------------------------------
def on_employee_after_insert(employee_doc, method=None):
    """Called after an Employee record is created."""
    _notify_hr(employee_doc, "created")
    _sync_employee_to_hris_k(employee_doc)


def on_employee_update(employee_doc, method=None):
    """Called every time an Employee record changes."""
    if employee_doc.flags.in_insert:
        return  # after_insert already fired
    _sync_employee_to_hris_k(employee_doc)


def on_leave_application_submit(doc, method=None):
    """Called when a Leave Application is submitted."""
    _sync_leave_to_hris_k(doc)
    _annotate_leave_balance(doc)


def on_leave_application_cancel(doc, method=None):
    """Best-effort: notify HRIS-K that a leave was cancelled."""
    settings = _hris_settings()
    if not settings or not settings.enable_hris_k_sync:
        return
    try:
        from kenya_erp.hris_k_sync import cancel_leave_in_hris

        cancel_leave_in_hris(doc)
    except Exception:
        frappe.log_error(
            frappe.get_traceback(), "Kenya ERP: failed to cancel leave in HRIS-K"
        )


# ---------------------------------------------------------------------------
# Procurement: Supplier handlers
# ---------------------------------------------------------------------------
def _egp_registration_ready(supplier_doc) -> bool:
    """Heuristic: does the linked Supplier Onboarding carry a BRS number yet?"""
    brs_no = frappe.db.get_value(
        "Supplier Onboarding",
        {"supplier": supplier_doc.name},
        "business_registration_no",
    )
    return bool(brs_no)


def on_supplier_after_insert(supplier_doc, method=None):
    """Nothing to do for the E-GP connector at creation time."""
    return


def on_supplier_update(supplier_doc, method=None):
    """Annotate the Supplier name with E-GP status when the connector is on."""
    if not egp_sync.is_enabled():
        return
    if not _egp_registration_ready(supplier_doc):
        return
    status = frappe.db.get_value(
        "Supplier Onboarding",
        {"supplier": supplier_doc.name},
        "egp_status",
    )
    if status and status not in ("Not Registered",):
        prefix = f"[EGP {status}] "
        if not (supplier_doc.supplier_name or "").startswith(prefix):
            supplier_doc.db_set(
                "supplier_name", f"{prefix}{supplier_doc.supplier_name}", commit=True
            )


# ---------------------------------------------------------------------------
# Fleet: Vehicle / Fuel Log / Maintenance Record handlers
# ---------------------------------------------------------------------------
def on_vehicle_saved(vehicle_doc, method=None):
    """Push vehicle changes to GVMS when the connector is on."""
    gvms_sync.sync_vehicle_to_gvms(vehicle_doc.name)


def on_fuel_log_submit(fuel_log_doc, method=None):
    """Push submitted fuel logs to GVMS when the connector is on."""
    gvms_sync.sync_fuel_log_to_gvms(fuel_log_doc.name)


def on_maintenance_submit(maintenance_doc, method=None):
    """Push submitted maintenance records to GVMS when the connector is on."""
    gvms_sync.sync_maintenance_to_gvms(maintenance_doc.name)


# ---------------------------------------------------------------------------
# Private HR helpers
# ---------------------------------------------------------------------------
def _hris_settings():
    """Return the Kenya HR Settings single, or None if not initialised."""
    try:
        return frappe.get_single("Kenya HR Settings")
    except frappe.DoesNotExistError:
        return None


def _sync_employee_to_hris_k(employee_doc):
    """Sync an Employee to HRIS-K, but only when the integration is enabled."""
    settings = _hris_settings()
    if not settings or not settings.enable_hris_k_sync:
        return
    try:
        from kenya_erp.hris_k_sync import sync_employee_to_hris

        sync_employee_to_hris(employee_doc.name)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Kenya ERP: employee HRIS-K sync failed")


def _sync_leave_to_hris_k(doc):
    """Sync a submitted Leave Application to HRIS-K (opt-in)."""
    settings = _hris_settings()
    if not settings or not settings.enable_hris_k_sync:
        return
    try:
        from kenya_erp.hris_k_sync import sync_leave_to_hris

        sync_leave_to_hris(doc.name)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Kenya ERP: leave HRIS-K sync failed")


def _notify_hr(employee_doc, action):
    """Push a ToDo to the HR managers when HR data changes."""
    hr_managers = frappe.get_all(
        "Has Role",
        filters={"role": "Kenya HR Manager"},
        pluck="parent",
    )
    # Skip in fixtures / setup runs to avoid noise.
    if not hr_managers or frappe.flags.in_install:
        return
    frappe.get_doc(
        {
            "doctype": "ToDo",
            "owner": hr_managers[0],
            "description": _(
                "Employee {0} was {1}. Review the Kenya HR fields (National ID, "
                "KRA PIN, NHIF, NSSF, UPN)."
            ).format(employee_doc.name, action),
            "reference_type": "Employee",
            "reference_name": employee_doc.name,
            "role": "Kenya HR Manager",
        }
    ).insert(ignore_permissions=True)


def _annotate_leave_balance(doc):
    """Post an audit comment with the employee's remaining leave balance."""
    balance = frappe.db.sql(
        """
        SELECT leave_type, total_allocated_leaves, balance_leaves
        FROM `tabLeave Ledger Entry`
        WHERE employee = %s
          AND leave_type = %s
          AND from_date <= %s
          AND to_date >= %s
        ORDER BY from_date DESC
        LIMIT 1
        """,
        (doc.employee, doc.leave_type, doc.from_date, doc.from_date),
        as_dict=True,
    )
    if not balance:
        return
    frappe.get_doc(
        {
            "doctype": "Comment",
            "comment_type": "Info",
            "reference_doctype": "Leave Application",
            "reference_name": doc.name,
            "content": _(
                "Remaining {0} balance at time of application: {1} days."
            ).format(balance[0].leave_type, balance[0].balance_leaves),
        }
    ).insert(ignore_permissions=True)
