"""
Whitelisted helper endpoints exposed by the Kenya HR app.

All functions here are decorated with ``@frappe.whitelist()`` so they can be
called from forms, scripts, and the REST API (with a valid session/API key).
"""

import frappe
from frappe import _
from frappe.utils import flt

from kenya_hr.install import get_statutory_leave_types


@frappe.whitelist()
def get_employee_kenya_details(employee: str) -> dict:
    """Return the Kenya identity fields for an Employee (used by reports/print)."""
    data = frappe.db.get_value(
        "Employee",
        employee,
        [
            "employee_name",
            "custom_national_id",
            "custom_kra_pin",
            "custom_nhif_number",
            "custom_nssf_number",
            "custom_upn_number",
            "custom_grade",
            "department",
            "designation",
        ],
        as_dict=True,
    )
    if not data:
        frappe.throw(_("Employee {0} not found.").format(employee))
    return data


@frappe.whitelist()
def get_leave_balance(employee: str, leave_type: str | None = None) -> list[dict]:
    """Return the available leave balances for an employee.

    Falls back to all statutory leave types when ``leave_type`` is omitted,
    matching the Kenya statute list from the install module.
    """
    if not leave_type:
        leave_types = get_statutory_leave_types()
    else:
        leave_types = [leave_type]

    result = []
    for lt in leave_types:
        allocated = frappe.db.get_value(
            "Leave Allocation",
            {
                "employee": employee,
                "leave_type": lt,
                "docstatus": 1,
            },
            "total_leaves_allocated",
            order_by="to_date desc",
        )
        consumed = frappe.db.sql(
            """
            SELECT COALESCE(SUM(total_leave_days), 0)
            FROM `tabLeave Application`
            WHERE employee = %s AND leave_type = %s
              AND status = "Approved" AND docstatus = 1
            """,
            (employee, lt),
        )[0][0]
        result.append(
            {
                "leave_type": lt,
                "allocated": flt(allocated),
                "consumed": flt(consumed),
                "balance": flt(allocated or 0) - flt(consumed),
            }
        )
    return result


@frappe.whitelist()
def eligible_for_leave(employee: str, leave_type: str) -> dict:
    """Return whether an employee can apply for the given leave type."""
    service_from = frappe.db.get_value("Employee", employee, "date_of_joining")
    if not service_from:
        return {"eligible": False, "reason": "No Date of Joining on record."}
    return {"eligible": True, "reason": ""}


@frappe.whitelist()
def mark_promotion_effective(promotion: str):
    """Convenience endpoint that finalises a promotion via the controller."""
    doc = frappe.get_doc("Staff Promotion", promotion)
    doc.mark_effective()
    return {"name": doc.name, "approval_status": doc.approval_status}