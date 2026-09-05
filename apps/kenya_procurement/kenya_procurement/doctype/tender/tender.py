# Tender - tender notice mirrored from the E-GP portal (or entered manually).
#
# The approved flow keeps tender data in sync with the National Treasury E-GP
# system; this doctype is the ERPNext-side mirror that procurement analytics
# and the pipeline report read from.
from __future__ import annotations

import frappe
from frappe.model.document import Document


class Tender(Document):
    def validate(self):
        """Sane-data guard: closing time must be after opening time."""
        if self.start_datetime and self.closing_datetime:
            if self.closing_datetime <= self.start_datetime:
                frappe.throw(
                    frappe._("Closing date/time must be after the tender start date/time.")
                )

    def before_save(self):
        # Keep the bid count derived rather than hand-maintained.
        self.no_of_bids = len(self.bids or [])