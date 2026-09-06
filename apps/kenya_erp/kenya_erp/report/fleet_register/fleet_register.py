# fleet_register.py - the fleet register: every vehicle with insurance overlay.
from __future__ import annotations

import frappe
from frappe import _


def execute(filters=None):
    filters = filters or {}

    # Build WHERE clauses simply below (avoids SQL injection via filters).
    conditions = []
    for key in ("vehicle_category", "status", "department"):
        if filters.get(key):
            conditions.append(f"v.{key} = %({key})s")
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    rows = frappe.db.sql(
        f"""
        SELECT
            v.name,
            v.registration_number,
            v.vehicle_category,
            v.make,
            v.model,
            v.year,
            v.fuel_type,
            v.department,
            v.odometer_reading,
            v.status,
            v.tracking_device_id,
            (SELECT MAX(ip.end_date) FROM `tabInsurance Policy` ip
              WHERE ip.vehicle = v.name) AS insurance_end_date
        FROM `tabVehicle` v
        {where}
        ORDER BY v.vehicle_category ASC, v.registration_number ASC
        """,
        filters,
        as_dict=True,
    )
    today = frappe.utils.today()
    for row in rows:
        if row["insurance_end_date"]:
            row["insurance_state"] = (
                "Expired"
                if str(row["insurance_end_date"]) < today
                else "Active"
            )
        else:
            row["insurance_state"] = "No Policy"
    return get_columns(), rows


def get_columns():
    return [
        {"fieldname": "registration_number", "label": _("Registration Number"), "fieldtype": "Data", "width": 150},
        {"fieldname": "vehicle_category", "label": _("Category"), "fieldtype": "Data", "width": 130},
        {"fieldname": "make", "label": _("Make"), "fieldtype": "Data", "width": 120},
        {"fieldname": "model", "label": _("Model"), "fieldtype": "Data", "width": 120},
        {"fieldname": "year", "label": _("Year"), "fieldtype": "Int", "width": 70},
        {"fieldname": "fuel_type", "label": _("Fuel"), "fieldtype": "Data", "width": 90},
        {"fieldname": "department", "label": _("Department"), "fieldtype": "Link", "options": "Department", "width": 160},
        {"fieldname": "odometer_reading", "label": _("Odometer (km)"), "fieldtype": "Float", "width": 110},
        {"fieldname": "status", "label": _("Status"), "fieldtype": "Data", "width": 140},
        {"fieldname": "insurance_end_date", "label": _("Insurance Till"), "fieldtype": "Date", "width": 110},
        {"fieldname": "insurance_state", "label": _("Insurance"), "fieldtype": "Data", "width": 100},
        {"fieldname": "tracking_device_id", "label": _("Tracking Device"), "fieldtype": "Data", "width": 130},
    ]