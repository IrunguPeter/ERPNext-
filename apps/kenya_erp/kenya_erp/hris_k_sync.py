"""
Optional HRIS-K integration client.

The Kenya HR system (HRIS-K - https://uhr.kenya.go.ke/) is the government's
centralised HR platform. This module exposes the synchronisation functions that
the Kenya HR app calls when **HRIS-K Sync** is enabled in *Kenya HR Settings*.

Design decisions
================
- The integration is **opt-in**. Everything degrades gracefully to a no-op
  unless ``enable_hris_k_sync`` is ticked in the settings single.
- The exact HRIS-K API contract is not public. Each function therefore logs
  to ``Log`` documents and raises ``HRISKError`` so that adapting the payloads
  to the official API is a one-line-per-field change.
- No credentials are ever logged. The API key is read from the *Password*
  field via ``get_password``.
"""

import requests

import frappe
from frappe import _


class HRISKError(Exception):
    """Raised when a request to the HRIS-K API fails."""


def get_settings():
    """Return the Kenya HR Settings single record."""
    return frappe.get_single("Kenya HR Settings")


def is_enabled() -> bool:
    """Return True when synchronisation is switched on in Settings."""
    settings = frappe.get_single("Kenya HR Settings")
    return bool(settings.enable_hris_k_sync)


def _headers():
    settings = get_settings()
    return {
        "Authorization": f"Bearer {settings.get_password('hris_k_api_key') or ''}",
        "Content-Type": "application/json",
    }


def _base_url():
    settings = get_settings()
    if not settings.hris_k_base_url:
        frappe.throw(_("Set the HRIS-K Base URL in Kenya HR Settings first."))
    return settings.hris_k_base_url.rstrip("/")


def _log(level: str, message: str):
    frappe.get_doc(
        {
            "doctype": "Log",
            "title": f"HRIS-K {level}",
            "message": message,
        }
    ).insert(ignore_permissions=True)


def _post(endpoint: str, payload: dict):
    """POST ``payload`` to ``_base_url()/endpoint`` with sensible timeouts."""
    try:
        response = requests.post(
            f"{_base_url()}/{endpoint}",
            json=payload,
            headers=_headers(),
            timeout=10,
        )
    except requests.RequestException as exc:
        _log("Error", f"HRIS-K request failed: {exc}")
        raise HRISKError(str(exc)) from exc

    if not response.ok:
        _log("Error", f"HRIS-K {endpoint} returned {response.status_code}: {response.text[:500]}")
        raise HRISKError(f"HRIS-K {endpoint} returned {response.status_code}")
    return response.json()


# ---------------------------------------------------------------------------
# Public synchronisation functions (also listed in kenya_erp/api usage docs)
# ---------------------------------------------------------------------------
def sync_employee_to_hris(employee_name: str) -> dict:
    """Push an Employee record to HRIS-K.

    Payload uses the Kenya identity fields added by this app
    (``custom_national_id``, ``custom_kra_pin``, ...).
    """
    if not is_enabled():
        return {}

    employee = frappe.get_doc("Employee", employee_name)
    payload = {
        "upn_number": employee.custom_upn_number,
        "national_id": employee.custom_national_id,
        "kra_pin": employee.custom_kra_pin,
        "nhif_number": employee.custom_nhif_number,
        "nssf_number": employee.custom_nssf_number,
        "employee_name": employee.employee_name,
        "department": employee.department,
        "designation": employee.designation,
        "employment_type": employee.employment_type,
        "date_of_joining": str(employee.date_of_joining or ""),
        "organization_code": get_settings().hris_k_organization_code,
    }
    result = _post("employees/sync", payload)
    _log("Info", f"Synced employee {employee_name} to HRIS-K.")
    return result


def sync_leave_to_hris(leave_name: str) -> dict:
    """Push a submitted Leave Application to HRIS-K."""
    if not is_enabled():
        return {}

    leave = frappe.get_doc("Leave Application", leave_name)
    employee = frappe.get_doc("Employee", leave.employee)
    payload = {
        "upn_number": employee.custom_upn_number,
        "leave_type": leave.leave_type,
        "from_date": str(leave.from_date),
        "to_date": str(leave.to_date),
        "total_days": leave.total_leave_days,
        "reason": leave.reason,
        "leave_balance": None,
        "organization_code": get_settings().hris_k_organization_code,
    }
    result = _post("leave/sync", payload)
    _log("Info", f"Synced leave {leave_name} to HRIS-K.")
    return result


def cancel_leave_in_hris(leave_name: str) -> dict:
    """Notify HRIS-K that a previously submitted leave was cancelled."""
    if not is_enabled():
        return {}
    leave = frappe.get_doc("Leave Application", leave_name)
    result = _post(
        "leave/cancel",
        {
            "leave_application": leave.name,
            "organization_code": get_settings().hris_k_organization_code,
        },
    )
    _log("Info", f"Cancelled leave {leave_name} in HRIS-K.")
    return result


def sync_all_employees_due():
    """Scheduled job: re-sync employees whose identity fields recently changed.

    Can be wired in ``hooks.py`` scheduler_events when the API contract is known.
    """
    if not is_enabled():
        return
    limit = 50
    employees = frappe.get_all(
        "Employee",
        filters={"status": "Active"},
        pluck="name",
        order_by="modified desc",
        limit_page_length=limit,
    )
    for name in employees:
        try:
            sync_employee_to_hris(name)
        except HRISKError:
            # Individual failures must not block the batch run.
            pass