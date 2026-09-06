# fleet_compliance.py - single view of everything due: insurance, licenses and
# scheduled maintenance (next-service date / odometer overdue).
from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import add_days, flt, today


LOOK_AHEAD_DAYS = 30


def execute(filters=None):
    data = _insurance_rows() + _license_rows() + _maintenance_rows()
    return get_columns(), data


def get_columns():
    return [
        {"fieldname": "compliance_type", "label": _("Area"), "fieldtype": "Data", "width": 120},
        {"fieldname": "reference", "label": _("Reference"), "fieldtype": "Data", "width": 200},
        {"fieldname": "detail", "label": _("Detail"), "fieldtype": "Data", "width": 220},
        {"fieldname": "due_date", "label": _("Due"), "fieldtype": "Date", "width": 110},
        {"fieldname": "odometer_due", "label": _("Odometer Due (km)"), "fieldtype": "Float", "width": 140},
        {"fieldname": "state", "label": _("State"), "fieldtype": "Data", "width": 100},
    ]


def _state(due_date):
    return "Expired" if due_date and str(due_date) < today() else "Expiring"


def _insurance_rows():
    rows = []
    policies = frappe.db.sql(
        """
        SELECT ip.name, ip.vehicle, ip.policy_number, ip.insurance_company,
               ip.end_date, ip.status
        FROM `tabInsurance Policy` ip
        WHERE ip.status IN ('Active', 'Expired')
          AND ip.end_date IS NOT NULL
        ORDER BY ip.end_date ASC
        """,
        as_dict=True,
    )
    cutoff = str(add_days(today(), LOOK_AHEAD_DAYS))
    for p in policies:
        if p["end_date"] and str(p["end_date"]) <= cutoff:
            rows.append(
                {
                    "compliance_type": _("Insurance"),
                    "reference": p["vehicle"],
                    "detail": f"{p.get('policy_number')} - {p.get('insurance_company')}",
                    "due_date": p["end_date"],
                    "odometer_due": None,
                    "state": _state(p["end_date"]),
                }
            )
    return rows


def _license_rows():
    rows = []
    drivers = frappe.get_all(
        "Driver",
        filters={"license_expiry": ["is", "set"]},
        fields=["name", "employee", "license_number", "license_expiry"],
    )
    cutoff = str(add_days(today(), LOOK_AHEAD_DAYS))
    for d in drivers:
        if str(d["license_expiry"]) <= cutoff:
            rows.append(
                {
                    "compliance_type": _("License"),
                    "reference": d["name"],
                    "detail": f"{d.get('employee') or d.get('name')} ({d.get('license_number')})",
                    "due_date": d["license_expiry"],
                    "odometer_due": None,
                    "state": _state(d["license_expiry"]),
                }
            )
    return rows


def _maintenance_rows():
    rows = []
    # Latest submitted maintenance record per vehicle that schedules a service.
    due = frappe.db.sql(
        """
        SELECT m.vehicle, m.next_service_date, m.next_service_odometer, m.date
        FROM `tabMaintenance Record` m
        JOIN (
            SELECT vehicle, MAX(date) AS max_date
            FROM `tabMaintenance Record`
            WHERE docstatus = 1 AND next_service_date IS NOT NULL
            GROUP BY vehicle
        ) latest ON latest.vehicle = m.vehicle AND latest.max_date = m.date
        WHERE m.docstatus = 1
        ORDER BY m.next_service_date ASC
        """,
        as_dict=True,
    )
    cutoff = str(today())
    for m in due:
        odometer_due = None
        if m["next_service_odometer"]:
            current = flt(
                frappe.db.get_value("Vehicle", m["vehicle"], "odometer_reading") or 0
            )
            if current >= m["next_service_odometer"]:
                odometer_due = m["next_service_odometer"]
        if m["next_service_date"] and str(m["next_service_date"]) <= cutoff:
            rows.append(
                {
                    "compliance_type": _("Maintenance"),
                    "reference": m["vehicle"],
                    "detail": _("Scheduled service due (set {0}).").format(m.get("date")),
                    "due_date": m["next_service_date"],
                    "odometer_due": odometer_due,
                    "state": "Expired",
                }
            )
        elif odometer_due:
            rows.append(
                {
                    "compliance_type": _("Maintenance"),
                    "reference": m["vehicle"],
                    "detail": _("Odometer-based service due."),
                    "due_date": None,
                    "odometer_due": odometer_due,
                    "state": _("Expired"),
                }
            )
    return rows