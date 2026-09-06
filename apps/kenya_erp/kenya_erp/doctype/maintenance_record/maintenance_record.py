# Maintenance Record - services/repairs/inspections plus next-service
# planning. Submittable so the GVMS connector only receives audited records.
from __future__ import annotations

import frappe
from frappe.model.document import Document


class MaintenanceRecord(Document):
    def validate(self):
        """The next service milestone must be ahead of the work just done."""
        if (
            self.next_service_odometer
            and self.odometer_reading
            and self.next_service_odometer <= self.odometer_reading
        ):
            frappe.throw(
                frappe._(
                    "Next service odometer ({0} km) must be after the current reading ({1} km)."
                ).format(self.next_service_odometer, self.odometer_reading)
            )