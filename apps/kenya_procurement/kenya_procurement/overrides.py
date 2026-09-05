# overrides.py - doc_events hooks on ERPNext standard doctypes.
from __future__ import annotations

import frappe

from . import egp_sync


def _egp_registration_ready(supplier_doc) -> bool:
    """Heuristic: does the linked Supplier Onboarding carry a BRS number yet?"""
    brs_no = frappe.db.get_value(
        "Supplier Onboarding",
        {"supplier": supplier_doc.name},
        "business_registration_no",
    )
    return bool(brs_no)


def on_supplier_after_insert(supplier_doc, method=None):
    """Nothing to do for the E-GP connector at creation time."""
    return


def on_supplier_update(supplier_doc, method=None):
    """Annotate the Supplier name with E-GP status when the connector is on."""
    if not egp_sync.is_enabled():
        return
    if not _egp_registration_ready(supplier_doc):
        return
    status = frappe.db.get_value(
        "Supplier Onboarding",
        {"supplier": supplier_doc.name},
        "egp_status",
    )
    if status and status not in ("Not Registered",):
        prefix = f"[EGP {status}] "
        if not (supplier_doc.supplier_name or "").startswith(prefix):
            supplier_doc.db_set(
                "supplier_name", f"{prefix}{supplier_doc.supplier_name}", commit=True
            )