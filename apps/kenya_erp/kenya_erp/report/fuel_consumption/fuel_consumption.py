# fuel_consumption.py - litres, cost and average consumption per vehicle.
from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt, get_first_day, get_last_day, today


def execute(filters=None):
    filters = filters or {}
    _defaults(filters)
    columns, data = get_columns(), get_data(filters)
    return columns, data, None, None, get_report_summary(data)


def _defaults(filters: dict):
    """Defaults mirroring the report .json filter definitions."""
    if not filters.get("from_date"):
        filters["from_date"] = get_first_day(today())
    if not filters.get("to_date"):
        filters["to_date"] = get_last_day(today())


def get_columns():
    return [
        {"fieldname": "registration_number", "label": _("Registration"), "fieldtype": "Data", "width": 140},
        {"fieldname": "vehicle", "label": _("Vehicle"), "fieldtype": "Link", "options": "Vehicle", "width": 160},
        {"fieldname": "department", "label": _("Department"), "fieldtype": "Data", "width": 160},
        {"fieldname": "logs", "label": _("Fuel Logs"), "fieldtype": "Int", "width": 90},
        {"fieldname": "total_fuel", "label": _("Fuel (litres)"), "fieldtype": "Float", "width": 110},
        {"fieldname": "total_cost", "label": _("Cost (KSh)"), "fieldtype": "Currency", "width": 120},
        {"fieldname": "mileage", "label": _("Mileage (km)"), "fieldtype": "Float", "width": 120},
        {
            "fieldname": "consumption",
            "label": _("Consumption (litres/100km)"),
            "fieldtype": "Float",
            "width": 150,
        },
    ]


def get_data(filters: dict) -> list[dict]:
    conditions = ["fl.docstatus = 1", "fl.date BETWEEN %(from_date)s AND %(to_date)s"]
    if filters.get("vehicle"):
        conditions.append("fl.vehicle = %(vehicle)s")

    rows = frappe.db.sql(
        f"""
        SELECT
            fl.vehicle,
            v.registration_number,
            v.department,
            COUNT(*) AS logs,
            SUM(fl.fuel_quantity) AS total_fuel,
            SUM(fl.fuel_cost) AS total_cost,
            MAX(fl.odometer_reading) - MIN(fl.odometer_reading) AS mileage
        FROM `tabFuel Log` fl
        JOIN `tabVehicle` v ON v.name = fl.vehicle
        WHERE {' AND '.join(conditions)}
        GROUP BY fl.vehicle, v.registration_number, v.department
        ORDER BY total_cost DESC
        """,
        filters,
        as_dict=True,
    )
    for row in rows:
        row["mileage"] = flt(row["mileage"] or 0)
        row["consumption"] = (
            flt((row["total_fuel"] or 0) / row["mileage"] * 100, 2) if row["mileage"] > 0 else 0
        )
    return rows


def get_report_summary(data):
    fuel = sum(flt(row["total_fuel"] or 0) for row in data)
    cost = sum(flt(row["total_cost"] or 0) for row in data)
    return [
        {"label": _("Vehicles"), "value": len(data), "datatype": "Int"},
        {"label": _("Fuel (litres)"), "value": round(fuel, 2), "datatype": "Float"},
        {"label": _("Cost (KSh)"), "value": round(cost, 2), "datatype": "Currency"},
    ]