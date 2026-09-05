# gvms_sync.py - opt-in connector to the Government Vehicle Management System
# (GVMS), the Kenyan Government's single source of truth for fleet data
# (registry, insurance, GPS/telematics, maintenance).
#
# IMPORTANT: GVMS does NOT publish a public REST API today. This module
# therefore talks to the *gateway endpoint you configure* in `GVMS Settings`.
# When the government opens an official API, this module is the single place
# to point at it (same approach as kenya_procurement's egp_sync.py).
#
# Guards in order of peace-of-mind:
#   1. `GVMS Settings.enabled` must be checked (master switch).
#   2. `sync_vehicles` / `sync_fuel_logs` / `sync_maintenance` /
#      `sync_vehicle_locations` toggle individual parts.
#   3. Every function logs errors and never raises out of a scheduled run.
from __future__ import annotations

import frappe
import requests

from .install import GVMS_PORTAL_URL

# ---------------------------------------------------------------------------
# Small, dependency-free accessors (kept here rather than on the doctype so the
# doctype controller stays a dumb data holder).
# ---------------------------------------------------------------------------
def get_settings():
    """Return the GVMS Settings single."""
    return frappe.get_single("GVMS Settings")


def is_enabled() -> bool:
    """Master switch for the whole connector."""
    return frappe.db.get_single_value("GVMS Settings", "enabled") or False


# ---------------------------------------------------------------------------
# HTTP plumbing
# ---------------------------------------------------------------------------
def _headers():
    """Standard headers incl. the API key when configured."""
    settings = get_settings()
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if settings.api_key:
        headers["X-GVMS-Key"] = settings.get_password("api_key", raise_exception=False) or settings.api_key
    return headers


def _log(level: str, message: str, data=None):
    """Central logger. Errors land in the Frappe Error Log for review."""
    if level == "error":
        frappe.log_error(message=message, title="GVMS Sync", data=data)
    else:
        frappe.logger().info(f"[kenya_fleet] {message}")


def _api(method: str, endpoint: str, payload=None, timeout: int = 30):
    """Perform a request against the configured gateway endpoint.

    Returns ``(ok, json_or_text)`` so callers never deal with exceptions.
    """
    settings = get_settings()
    base = (settings.api_endpoint or "").rstrip("/")
    if not base:
        _log("error", "No API endpoint configured in GVMS Settings.")
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
# Remote payload mapping
# ---------------------------------------------------------------------------
def _vehicle_payload(vehicle) -> dict:
    return {
        "vehicle_id": vehicle.name,
        "registration_number": vehicle.registration_number,
        "category": vehicle.vehicle_category,
        "make": vehicle.make,
        "model": vehicle.model,
        "year": vehicle.year,
        "color": vehicle.color,
        "fuel_type": vehicle.fuel_type,
        "engine_number": vehicle.engine_number,
        "chassis_number": vehicle.chassis_number,
        "department": vehicle.department,
        "status": vehicle.status,
        "odometer_reading": vehicle.odometer_reading,
        "tracking_device_id": vehicle.tracking_device_id,
    }


def _fuel_payload(fuel_log) -> dict:
    registration_number = frappe.db.get_value("Vehicle", fuel_log.vehicle, "registration_number")
    return {
        "fuel_log_id": fuel_log.name,
        "vehicle": fuel_log.vehicle,
        "registration_number": registration_number,
        "date": fuel_log.date,
        "odometer_reading": fuel_log.odometer_reading,
        "fuel_quantity": fuel_log.fuel_quantity,
        "fuel_cost": fuel_log.fuel_cost,
        "unit_price": fuel_log.unit_price,
        "station": fuel_log.station,
        "receipt_number": fuel_log.receipt_number,
    }


def _maintenance_payload(maintenance) -> dict:
    registration_number = frappe.db.get_value("Vehicle", maintenance.vehicle, "registration_number")
    return {
        "maintenance_id": maintenance.name,
        "vehicle": maintenance.vehicle,
        "registration_number": registration_number,
        "maintenance_type": maintenance.maintenance_type,
        "date": maintenance.date,
        "description": maintenance.description,
        "cost": maintenance.cost,
        "vendor": maintenance.vendor,
        "next_service_date": maintenance.next_service_date,
        "next_service_odometer": maintenance.next_service_odometer,
    }


def _apply_sync_fields(doc, fields: dict):
    for key, value in fields.items():
        if getattr(doc, key, None) in (None, "") and value is not None:
            setattr(doc, key, value)
    doc.flags.ignore_permissions = True
    doc.save(ignore_permissions=True)


# ---------------------------------------------------------------------------
# Vehicle registry
# ---------------------------------------------------------------------------
def sync_vehicle_to_gvms(vehicle: str):
    """Push a single vehicle to the gateway."""
    if not is_enabled() or not get_settings().sync_vehicles:
        return False
    ok, _ = _api("POST", "vehicles/sync", _vehicle_payload(frappe.get_doc("Vehicle", vehicle)))
    if ok:
        _log("info", f"Synced vehicle {vehicle} to GVMS")
    return ok


def fetch_vehicle_from_gvms(registration_number: str) -> dict | None:
    """Pull a vehicle's GVMS record and update the local Vehicle if present."""
    ok, data = _api("GET", f"vehicles/{registration_number}")
    if not ok or not isinstance(data, dict):
        return None
    vehicle_id = data.get("vehicle_id")
    if not frappe.db.exists("Vehicle", vehicle_id):
        doc = frappe.new_doc("Vehicle")
        doc.registration_number = registration_number
    else:
        doc = frappe.get_doc("Vehicle", vehicle_id)
    _apply_sync_fields(
        doc,
        {
            "make": data.get("make"),
            "model": data.get("model"),
            "year": data.get("year"),
            "fuel_type": data.get("fuel_type"),
            "tracking_device_id": data.get("tracking_device_id"),
            "status": data.get("status"),
        },
    )
    return data


def sync_all_vehicles():
    """Push every locally-registered vehicle (daily catch-up)."""
    if not is_enabled() or not get_settings().sync_vehicles:
        return 0
    count = 0
    for vehicle in frappe.get_all("Vehicle", pluck="name"):
        if sync_vehicle_to_gvms(vehicle):
            count += 1
    return count


# ---------------------------------------------------------------------------
# Fuel and maintenance (pushed on submit via hooks)
# ---------------------------------------------------------------------------
def sync_fuel_log_to_gvms(fuel_log: str) -> bool:
    """Push a submitted fuel log to the gateway."""
    if not is_enabled() or not get_settings().sync_fuel_logs:
        return False
    doc = frappe.get_doc("Fuel Log", fuel_log)
    if doc.docstatus != 1:
        _log("warning", f"Fuel log {fuel_log} not submitted; skipping GVMS sync.")
        return False
    ok, _ = _api("POST", "fuel/sync", _fuel_payload(doc))
    if ok:
        _log("info", f"Synced fuel log {fuel_log} to GVMS")
    return ok


def sync_maintenance_to_gvms(maintenance: str) -> bool:
    """Push a submitted maintenance record to the gateway."""
    if not is_enabled() or not get_settings().sync_maintenance:
        return False
    doc = frappe.get_doc("Maintenance Record", maintenance)
    if doc.docstatus != 1:
        _log("warning", f"Maintenance record {maintenance} not submitted; skipping GVMS sync.")
        return False
    ok, _ = _api("POST", "maintenance/sync", _maintenance_payload(doc))
    if ok:
        _log("info", f"Synced maintenance record {maintenance} to GVMS")
    return ok


# ---------------------------------------------------------------------------
# GPS / telematics (hourly pull)
# ---------------------------------------------------------------------------
def sync_all_vehicle_locations():
    """Pull live GPS positions for every vehicle with a tracking device id."""
    if not is_enabled() or not get_settings().sync_vehicle_locations:
        return 0
    updated = 0
    for vehicle in frappe.get_all(
        "Vehicle",
        filters={"tracking_device_id": ["is", "set"]},
        fields=["name", "tracking_device_id"],
    ):
        ok, data = _api("GET", f"tracking/{vehicle.tracking_device_id}")
        if not ok or not isinstance(data, dict):
            continue
        doc = frappe.get_doc("Vehicle", vehicle.name)
        doc.db_set(
            {
                "current_latitude": data.get("latitude"),
                "current_longitude": data.get("longitude"),
                "last_tracking_update": data.get("at") or frappe.utils.now(),
            }
        )
        updated += 1
    settings = get_settings()
    if updated or not settings.last_location_sync:
        settings.last_location_sync = frappe.utils.now()
        settings.flags.ignore_permissions = True
        settings.save()
    _log("info", f"GVMS location sync complete: {updated} vehicles updated.")
    return updated


# ---------------------------------------------------------------------------
# Scheduled entry point
# ---------------------------------------------------------------------------
def sync_all_due():
    """Daily scheduled routine (see hooks.py). A no-op unless enabled."""
    if not is_enabled():
        _log("info", "GVMS connector disabled; daily sync skipped.")
        return
    try:
        synced_vehicles = sync_all_vehicles()
    except Exception as exc:  # never take the scheduled job down
        _log("error", "Daily GVMS sync failed", exc)
        return
    settings = get_settings()
    settings.last_sync = frappe.utils.now()
    settings.flags.ignore_permissions = True
    settings.save()
    _log("info", f"Daily GVMS sync complete: {synced_vehicles} vehicles.")