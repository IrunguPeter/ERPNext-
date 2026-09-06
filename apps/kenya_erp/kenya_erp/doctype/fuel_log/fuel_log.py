# Fuel Log - a fuel purchase for a vehicle. Submittable so the GVMS connector
# only receives audited records (submit hook) and odometer rollback stays
# impossible after submission.
from __future__ import annotations

import frappe
from frappe.model.document import Document


class FuelLog(Document):
    def before_save(self):
        if self.fuel_quantity:
            self.unit_price = frappe.utils.flt(self.fuel_cost / self.fuel_quantity, 2)

    def validate(self):
        if frappe.utils.flt(self.fuel_quantity) <= 0:
            frappe.throw(frappe._("Fuel quantity must be greater than zero."))
        if frappe.utils.flt(self.odometer_reading) < 0:
            frappe.throw(frappe._("Odometer reading cannot be negative."))

    def on_submit(self):
        # Keep the vehicle's current odometer at the highest reading we know.
        vehicle = frappe.get_doc("Vehicle", self.vehicle)
        current = frappe.utils.flt(vehicle.odometer_reading)
        if self.odometer_reading > current:
            vehicle.db_set("odometer_reading", self.odometer_reading)