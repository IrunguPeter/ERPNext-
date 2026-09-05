# Accident Report - a road traffic incident involving a fleet vehicle.
from __future__ import annotations

import frappe
from frappe.model.document import Document


class AccidentReport(Document):
    def validate(self):
        """A closed accident must carry its reference numbers."""
        if self.status == "Closed":
            if not (self.police_report_number or self.insurance_claim_number):
                frappe.throw(
                    frappe._(
                        "Provide at least one of Police Report Number or "
                        "Insurance Claim Number before closing an accident."
                    )
                )