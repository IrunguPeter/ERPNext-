"""Staff Promotion Log - simple status report over the promotion pipeline."""

import frappe
from frappe import _


def execute(filters=None):
    """Build a tabular report of Staff Promotions with optional filters."""
    columns = [
        {"fieldname": "name", "label": _("Promotion"), "fieldtype": "Link", "options": "Staff Promotion", "width": 140},
        {"fieldname": "employee_name", "label": _("Employee"), "fieldtype": "Data", "width": 200},
        {"fieldname": "department", "label": _("Department"), "fieldtype": "Link", "options": "Department", "width": 180},
        {"fieldname": "promotion_type", "label": _("Type"), "fieldtype": "Data", "width": 100},
        {"fieldname": "current_designation", "label": _("Current Designation"), "fieldtype": "Data", "width": 200},
        {"fieldname": "new_designation", "label": _("New Designation"), "fieldtype": "Data", "width": 200},
        {"fieldname": "effective_date", "label": _("Effective Date"), "fieldtype": "Date", "width": 110},
        {"fieldname": "approval_status", "label": _("Status"), "fieldtype": "Data", "width": 210},
    ]

    filters = filters or {}
    conditions = []
    params = {}

    if filters.get("status"):
        conditions.append("approval_status = %(status)s")
        params["status"] = filters["status"]
    if filters.get("department"):
        conditions.append("department = %(department)s")
        params["department"] = filters["department"]
    if filters.get("from_date") and filters.get("to_date"):
        conditions.append("effective_date BETWEEN %(from_date)s AND %(to_date)s")
        params["from_date"] = filters["from_date"]
        params["to_date"] = filters["to_date"]

    where = " AND ".join(conditions)
    if where:
        where = "WHERE " + where

    data = frappe.db.sql(
        f"""
        SELECT name, employee_name, department, promotion_type,
               current_designation, new_designation, effective_date, approval_status
        FROM `tabStaff Promotion`
        {where}
        ORDER BY effective_date DESC, modified DESC
        """,
        params,
        as_dict=True,
    )
    return columns, data