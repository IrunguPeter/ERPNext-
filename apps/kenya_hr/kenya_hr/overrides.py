"""
DocType event handlers (doc_events) that enrich standard HRMS doctypes.

Registered in ``hooks.py``:

    Employee         -> after_insert / on_update
    Leave Application -> on_submit / on_cancel

Each handler is deliberately small: it delegates to the HRIS-K client when the
integration is enabled in *Kenya HR Settings*, otherwise it is a no-op.
"""

import frappe
from frappe import _

MIN_PROMOTION_DAYS_AT_DESIGNATION = 1  # tunable business rule


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
        from kenya_hr.hris_k_sync import cancel_leave_in_hris

        cancel_leave_in_hris(doc)
    except Exception:
        frappe.log_error(
            frappe.get_traceback(), "Kenya HR: failed to cancel leave in HRIS-K"
        )


# ---------------------------------------------------------------------------
# Private helpers
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
        from kenya_hr.hris_k_sync import sync_employee_to_hris

        sync_employee_to_hris(employee_doc.name)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Kenya HR: employee HRIS-K sync failed")


def _sync_leave_to_hris_k(doc):
    """Sync a submitted Leave Application to HRIS-K (opt-in)."""
    settings = _hris_settings()
    if not settings or not settings.enable_hris_k_sync:
        return
    try:
        from kenya_hr.hris_k_sync import sync_leave_to_hris

        sync_leave_to_hris(doc.name)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Kenya HR: leave HRIS-K sync failed")


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