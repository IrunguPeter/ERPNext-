# Vehicle Assignment - allocation of a vehicle to an officer/employee for a
# period. Enforces the "one vehicle, one active allocation" rule and keeps the
# Vehicle's status meaningful.
from __future__ import annotations

import frappe
from frappe.model.document import Document


class VehicleAssignment(Document):
    def validate(self):
        self._sane_dates()
        self._guard_overlap()
        self.status = self._compute_status()

    def on_update(self):
        # A freshly-started allocation marks the vehicle as Assigned; an
        # ended one is left alone so "Under Maintenance" is never clobbered.
        vehicle = frappe.get_doc("Vehicle", self.vehicle)
        if self.status == "Active" and vehicle.status != "Assigned":
            vehicle.db_set("status", "Assigned")

    def _sane_dates(self):
        if self.end_date and self.start_date and self.end_date < self.start_date:
            frappe.throw(frappe._("End date cannot be before the start date."))

    def _compute_status(self):
        today = frappe.utils.today()
        if self.end_date and self.end_date < today:
            return "Ended"
        return "Active"

    def _guard_overlap(self):
        """Never allow two different employees to hold the same vehicle."""
        overlap = frappe.db.sql(
            """
            SELECT name, assigned_to, start_date, end_date
            FROM `tabVehicle Assignment`
            WHERE vehicle = %(vehicle)s
              AND name != %(name)s
              AND IFNULL(end_date, %(today)s) >= %(start)s
              AND %(end)s >= start_date
            """,
            {
                "vehicle": self.vehicle,
                "name": self.name or "",
                "today": frappe.utils.today(),
                "start": self.start_date,
                "end": self.end_date or "9999-12-31",
            },
            as_dict=True,
        )
        if overlap:
            other = overlap[0]
            frappe.throw(
                frappe._(
                    "Vehicle {0} is already assigned to {1} from {2}"
                    " to {3}. End that assignment before creating a new one."
                ).format(
                    self.vehicle,
                    other.get("assigned_to"),
                    other.get("start_date"),
                    other.get("end_date") or "open-ended",
                )
            )