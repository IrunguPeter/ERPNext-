# egp_sync.py - opt-in connector to the Kenya E-GP (Electronic Government
# Procurement) system.
#
# IMPORTANT: the public E-GP portal (egpkenya.go.ke) does NOT publish a public
# REST API. This module therefore talks to the *gateway endpoint you configure*
# in `Kenya EGP Settings`. When the Treasury opens an official API, this module
# becomes the single place to point at it.
#
# Guards in order of peace-of-mind:
#   1. `Kenya EGP Settings.enabled` must be checked (master switch).
#   2. `sync_tenders` / `sync_suppliers` toggle individual parts.
#   3. Every function logs errors and never raises out of a scheduled run.
import frappe
import requests

from .install import EGP_PORTAL_URL

# ---------------------------------------------------------------------------
# Small, dependency-free accessors (kept here rather than on the doctype so the
# doctype controller stays a dumb data holder).
# ---------------------------------------------------------------------------
def get_settings():
    """Return the Kenya EGP Settings single."""
    return frappe.get_single("Kenya EGP Settings")


def is_enabled() -> bool:
    """Master switch for the whole connector."""
    return frappe.db.get_single_value("Kenya EGP Settings", "enabled") or False


# ---------------------------------------------------------------------------
# HTTP plumbing
# ---------------------------------------------------------------------------
def _headers():
    """Standard headers incl. the bearer token when configured."""
    settings = get_settings()
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if settings.api_token:
        headers["Authorization"] = f"Bearer {settings.api_token}"
    return headers


def _log(level: str, message: str, data=None):
    """Central logger. Errors land in the Frappe Error Log for review."""
    if level == "error":
        frappe.log_error(message=message, title="Kenya EGP Sync", data=data)
    else:
        frappe.logger().info(f"[kenya_egp] {message}")


def _api(method: str, endpoint: str, payload=None, timeout: int = 30):
    """Perform a request against the configured gateway endpoint.

    Returns ``(ok, json_or_text)`` so callers never deal with exceptions.
    """
    settings = get_settings()
    base = (settings.api_endpoint or "").rstrip("/")
    if not base:
        _log("error", "No API endpoint configured in Kenya EGP Settings.")
        return False, None
    url = f"{base}/{endpoint.lstrip('/')}"
    try:
        response = requests.request(
            method,
            url,
            json=payload,
            headers=_headers(),
            timeout=timeout,
        )
    except requests.RequestException as exc:
        _log("error", f"Request to {url} failed: {exc}")
        return False, None
    if response.status_code >= 400:
        _log("error", f"{method} {url} -> {response.status_code}", response.text)
        return False, response.text
    try:
        return True, response.json()
    except ValueError:
        return True, response.text


# ---------------------------------------------------------------------------
# Suppliers
# ---------------------------------------------------------------------------
def fetch_supplier_egp_status(business_registration_no: str) -> dict | None:
    """Query the gateway for a single supplier's E-GP status by BRS number."""
    ok, data = _api("GET", f"suppliers/{business_registration_no}")
    if not ok or not isinstance(data, dict):
        return None
    # Expected shape: {"business_registration_no": "...", "status": "Registered"}
    return data


def sync_supplier_statuses():
    """Refresh `Supplier Onboarding` records with E-GP status from the gateway."""
    if not is_enabled() or not get_settings().sync_suppliers:
        return 0
    updated = 0
    for onboarding in frappe.get_all(
        "Supplier Onboarding",
        filters={"business_registration_no": ["is", "set"]},
        pluck="name",
    ):
        doc = frappe.get_doc("Supplier Onboarding", onboarding)
        data = fetch_supplier_egp_status(doc.business_registration_no)
        if data and data.get("status") and data["status"] != doc.egp_status:
            doc.egp_status = data["status"]
            doc.flags.ignore_permissions = True
            doc.save()
            updated += 1
            _log("info", f"Updated E-GP status of {onboarding} -> {data['status']}")
    return updated


# ---------------------------------------------------------------------------
# Tenders
# ---------------------------------------------------------------------------
def fetch_open_tenders() -> list[dict]:
    """Pull the current tender notices from the gateway.

    Expected payload: ``{"tenders": [{...}, ...]}`` where each tender carries
    the keys mapped below in ``_mirror_tender()``.
    """
    ok, data = _api("GET", "tenders")
    if not ok:
        return []
    if isinstance(data, dict):
        return data.get("tenders", [])
    return data if isinstance(data, list) else []


def _mirror_tender(remote: dict):
    """Upsert a Tender record keyed on the E-GP Tender ID."""
    tender_id = str(remote.get("tender_id") or "").strip()
    if not tender_id:
        _log("info", "Skipping gateway tender without tender_id", remote)
        return
    fields = {
        "tender_reference": remote.get("tender_reference"),
        "title": remote.get("title"),
        "procuring_entity": remote.get("procuring_entity"),
        "procurement_method": remote.get("procurement_method"),
        "start_datetime": remote.get("start_datetime"),
        "closing_datetime": remote.get("closing_datetime"),
        "egp_url": remote.get("egp_url") or EGP_PORTAL_URL,
        "status": remote.get("status") or "Open",
    }
    existing = frappe.db.get_value("Tender", {"tender_id": tender_id}, "name")
    if existing:
        doc = frappe.get_doc("Tender", existing)
        _apply_sync_fields(doc, fields)
    else:
        doc = frappe.new_doc("Tender")
        doc.tender_id = tender_id
        _apply_sync_fields(doc, fields)
    doc.flags.ignore_permissions = True
    doc.flags.ignore_validate = False
    doc.save(ignore_permissions=True)
    _log("info", f"Mirrored tender {tender_id}")


def _apply_sync_fields(doc, fields: dict):
    for key, value in fields.items():
        if getattr(doc, key, None) in (None, "") and value is not None:
            setattr(doc, key, value)


def sync_tenders():
    """Mirror all open tenders from the gateway."""
    if not is_enabled() or not get_settings().sync_tenders:
        return 0
    count = 0
    for remote in fetch_open_tenders():
        _mirror_tender(remote)
        count += 1
    return count


# ---------------------------------------------------------------------------
# Scheduled entry point
# ---------------------------------------------------------------------------
def sync_all_due():
    """Daily scheduled routine (see hooks.py). A no-op unless enabled."""
    if not is_enabled():
        _log("info", "E-GP connector disabled; daily sync skipped.")
        return
    try:
        synced_tenders = sync_tenders()
        updated_suppliers = sync_supplier_statuses()
    except Exception as exc:  # never take the scheduled job down
        _log("error", "Daily E-GP sync failed", exc)
        return
    settings = get_settings()
    settings.last_sync = frappe.utils.now()
    settings.flags.ignore_permissions = True
    settings.save()
    _log(
        "info",
        f"Daily E-GP sync complete: {synced_tenders} tenders, {updated_suppliers} suppliers.",
    )