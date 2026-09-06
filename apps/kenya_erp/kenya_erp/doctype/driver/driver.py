# Driver - a licensed driver, linked to an HRMS `Employee`.
from __future__ import annotations

import frappe
from frappe.model.document import Document


class Driver(Document):
    def validate(self):
        """Flag expired licenses early (blocking, not best-effort)."""
        if self.license_expiry and self.license_expiry < frappe.utils.today():
            frappe.msgprint(
                frappe._("This driving license expired on {0}. Renew it before allocation.").format(
                    self.license_expiry
                ),
                indicator="orange",
            )