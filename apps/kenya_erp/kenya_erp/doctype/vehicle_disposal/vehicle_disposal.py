# Vehicle Disposal - retiring a vehicle from the fleet (age 7-10 years per the
# Transport Policy 2024, or condition/duration based). Completing a disposal
# flips the Vehicle's status to Retired.
from __future__ import annotations

import frappe
from frappe.model.document import Document


class VehicleDisposal(Document):
    def on_update(self):
        if self.status == "Completed":
            vehicle = frappe.get_doc("Vehicle", self.vehicle)
            if vehicle.status != "Retired":
                vehicle.db_set("status", "Retired")