# Vehicle - fleet master. The local mirror of a vehicle registered in GVMS
# (or kept standalone when the connector is off / never configured).
from __future__ import annotations

import frappe
from frappe.model.document import Document


class Vehicle(Document):
    def validate(self):
        """Sane-data guard: manufacture year must be plausible."""
        if self.year:
            current_year = frappe.utils.now_datetime().year
            if not (1950 <= self.year <= current_year + 1):
                frappe.throw(
                    frappe._("Year of manufacture must be between 1950 and {0}.").format(current_year + 1)
                )