# api.py - whitelisted (REST-accessible) helpers for the procurement module.
from __future__ import annotations

import frappe
from frappe import _

from .egp_sync import _api, _mirror_tender, is_enabled


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