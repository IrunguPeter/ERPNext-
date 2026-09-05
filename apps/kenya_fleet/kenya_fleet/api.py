# api.py - whitelisted (REST-accessible) helpers for the fleet module.
from __future__ import annotations

import frappe
from frappe import _

from . import gvms_sync


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