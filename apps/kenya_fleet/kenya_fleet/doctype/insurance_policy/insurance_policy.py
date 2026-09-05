# Insurance Policy - cover for a vehicle (comprehensive/third-party/etc).
from __future__ import annotations

import frappe
from frappe.model.document import Document


class InsurancePolicy(Document):
    def validate(self):
        self._sane_dates()
        self._auto_status()

    def _sane_dates(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            frappe.throw(frappe._("End date cannot be before the start date."))

    def _auto_status(self):
        today = frappe.utils.today()
        if self.status == "Cancelled":
            return
        if self.end_date and self.end_date < today:
            self.status = "Expired"
        elif not self.status:
            self.status = "Active"