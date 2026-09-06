"""
Whitelisted (REST-accessible) helper endpoints for the Kenya ERP app.

All functions here are decorated with ``@frappe.whitelist()`` so they can be
called from forms, scripts, and the REST API (with a valid session/API key).

Endpoints are grouped by module:
  * HR          - get_employee_kenya_details, get_leave_balance, ...
  * Procurement - get_open_tenders, get_supplier_egp_status, mirror_tender, ...
  * Fleet       - fleet_summary, get_vehicle, sync_vehicle_now, ...
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt

from . import gvms_sync
from .egp_sync import _api, _mirror_tender, is_enabled
from .install import get_statutory_leave_types


# ---------------------------------------------------------------------------
# HR endpoints
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Procurement endpoints
# ---------------------------------------------------------------------------
@frappe.whitelist()
def get_open_tenders():
    """Open tenders, newest deadline first. Read-only convenience endpoint."""
    tenders = frappe.get_all(
        "Tender",
        filters={"status": "Open"},
        fields=[
            "tender_id",
            "tender_reference",
            "title",
            "procuring_entity",
            "procurement_method",
            "closing_datetime",
            "egp_url",
        ],
        order_by="closing_datetime asc",
    )
    return {
        "tenders": tenders,
        "portal_url": frappe.db.get_single_value("Kenya EGP Settings", "base_url"),
    }


@frappe.whitelist()
def get_supplier_egp_status(supplier: str):
    """E-GP status of a supplier's onboarding record, or None if not onboarded."""
    onboarding = frappe.db.get_value(
        "Supplier Onboarding",
        {"supplier": supplier},
        ["name", "egp_status", "business_registration_no", "kra_pin"],
        as_dict=True,
    )
    if not onboarding:
        frappe.throw(_("No Supplier Onboarding record for {0}.").format(supplier))
    return onboarding


@frappe.whitelist()
def mirror_tender(tender_id: str):
    """Manually pull a single tender from the gateway (useful for testing)."""
    if not is_enabled():
        frappe.throw(_("The E-GP connector is disabled in Kenya EGP Settings."))
    ok, data = _api("GET", f"tenders/{tender_id}")
    if not ok or not isinstance(data, dict):
        frappe.throw(_("Tender {0} could not be fetched from the gateway.").format(tender_id))
    _mirror_tender(data)
    return {"status": "ok", "tender_id": tender_id}


# ---------------------------------------------------------------------------
# Fleet endpoints
# ---------------------------------------------------------------------------
@frappe.whitelist()
def fleet_summary():
    """Headline figures for a fleet dashboard (counts by status, fuel spend)."""
    statuses = {s: 0 for s in ("Available", "Assigned", "Under Maintenance", "Retired")}
    for status, count in frappe.get_all("Vehicle", fields=["status"], group_by="status"):
        statuses[status] = count

    fuel = frappe.db.sql(
        """
        SELECT COUNT(*) AS logs, COALESCE(SUM(fuel_quantity), 0) AS litres,
               COALESCE(SUM(fuel_cost), 0) AS cost
        FROM `tabFuel Log`
        WHERE docstatus = 1
        """,
        as_dict=True,
    )[0]

    expiring = frappe.db.count(
        "Insurance Policy",
        filters={"status": "Active", "end_date": ["<=", frappe.utils.add_days(None, 30)]},
    )
    return {
        "total_vehicles": sum(statuses.values()),
        "by_status": statuses,
        "fuel_logs": fuel.logs,
        "fuel_litres": round(fuel.litres, 2),
        "fuel_cost": round(fuel.cost or 0, 2),
        "insurance_expiring_30d": expiring,
    }


@frappe.whitelist()
def get_vehicle(vehicle: str):
    """Public key facts about a single vehicle (for portals/gateways)."""
    doc = frappe.get_doc("Vehicle", vehicle)
    return {
        "name": doc.name,
        "registration_number": doc.registration_number,
        "vehicle_category": doc.vehicle_category,
        "make": doc.make,
        "model": doc.model,
        "fuel_type": doc.fuel_type,
        "department": doc.department,
        "status": doc.status,
        "odometer_reading": doc.odometer_reading,
        "tracking_device_id": doc.tracking_device_id,
    }


@frappe.whitelist()
def sync_vehicle_now(vehicle: str):
    """Manually push a single vehicle to the GVMS gateway (for testing)."""
    if not gvms_sync.is_enabled():
        frappe.throw(_("The GVMS connector is disabled in GVMS Settings."))
    ok = gvms_sync.sync_vehicle_to_gvms(vehicle)
    if not ok:
        frappe.throw(_("Vehicle {0} could not be synced to the gateway. Check the error log.").format(vehicle))
    return {"status": "ok", "vehicle": vehicle}
