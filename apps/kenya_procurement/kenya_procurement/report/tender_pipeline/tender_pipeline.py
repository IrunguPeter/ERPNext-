# Copyright (c) 2026, IrunguPeter and contributors
# For license information, please see license.txt

# tender_pipeline.py - script report over the Tender doctype.
from __future__ import annotations

import frappe
from frappe import _


def execute(filters=None):
    columns, data = get_columns(), get_data(filters or {})
    chart = get_chart(data)
    return columns, data, None, chart, get_report_summary(data)


def get_columns():
    return [
        {"fieldname": "tender_reference", "label": _("Tender Reference"), "fieldtype": "Data", "width": 180},
        {"fieldname": "title", "label": _("Title"), "fieldtype": "Data", "width": 260},
        {"fieldname": "procuring_entity", "label": _("Procuring Entity"), "fieldtype": "Data", "width": 220},
        {"fieldname": "procurement_method", "label": _("Method"), "fieldtype": "Data", "width": 150},
        {"fieldname": "closing_datetime", "label": _("Closing"), "fieldtype": "Datetime", "width": 150},
        {"fieldname": "status", "label": _("Status"), "fieldtype": "Data", "width": 110},
        {"fieldname": "no_of_bids", "label": _("Bids"), "fieldtype": "Int", "width": 70},
        {"fieldname": "awarded_to", "label": _("Awarded To"), "fieldtype": "Link", "options": "Supplier Onboarding", "width": 200},
    ]


def get_data(filters: dict) -> list[dict]:
    conditions = []
    values = {}
    for key, value in filters.items():
        if value:
            conditions.append(f"`tabTender`.{key} = %({key})s")
            values[key] = value
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    rows = frappe.db.sql(
        f"""
        SELECT
            name, tender_id, tender_reference, title, procuring_entity,
            procurement_method, closing_datetime, status, no_of_bids, awarded_to
        FROM `tabTender`
        {where}
        ORDER BY closing_datetime ASC, status ASC
        """,
        values,
        as_dict=True,
    )
    for row in rows:
        row["awarded_to"] = frappe.get_cached_value(
            "Supplier Onboarding", row["awarded_to"], "supplier"
        ) if row["awarded_to"] else None
    return rows


def get_chart(data):
    labels = ["Open", "Closed", "Evaluation", "Awarded", "Cancelled"]
    counts = [sum(1 for d in data if d["status"] == label) for label in labels]
    return {
        "data": {
            "labels": labels,
            "datasets": [{"name": _("Tenders"), "values": counts}],
        },
        "type": "bar",
        "height": 260,
    }


def get_report_summary(data):
    return [
        {"label": _("Total Tenders"), "value": len(data), "datatype": "Int"},
        {"label": _("Open"), "value": sum(1 for d in data if d["status"] == "Open"), "datatype": "Int"},
        {"label": _("Total Bids"), "value": sum(d.get("no_of_bids") or 0 for d in data), "datatype": "Int"},
    ]