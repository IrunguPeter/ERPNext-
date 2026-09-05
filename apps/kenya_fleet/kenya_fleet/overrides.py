# overrides.py - doc_events hooks on this app's own doctypes.
#
# These wrappers exist so hooks.py stays declarative and each sync concern can
# call the connector directly with a doctype name (never a full document).
from __future__ import annotations

from . import gvms_sync


def on_vehicle_saved(vehicle_doc, method=None):
    """Push vehicle changes to GVMS when the connector is on."""
    gvms_sync.sync_vehicle_to_gvms(vehicle_doc.name)


def on_fuel_log_submit(fuel_log_doc, method=None):
    """Push submitted fuel logs to GVMS when the connector is on."""
    gvms_sync.sync_fuel_log_to_gvms(fuel_log_doc.name)


def on_maintenance_submit(maintenance_doc, method=None):
    """Push submitted maintenance records to GVMS when the connector is on."""
    gvms_sync.sync_maintenance_to_gvms(maintenance_doc.name)