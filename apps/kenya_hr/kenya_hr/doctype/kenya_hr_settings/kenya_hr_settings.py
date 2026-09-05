"""Kenya HR Settings - runtime configuration for the Kenya HR app."""

import frappe
from frappe.model.document import Document


class KenyaHRSettings(Document):
    """Holds app-level configuration entered via the desk.

    Only reachable by users with the ``Kenya HR Manager`` role (see the
    ``permissions`` block in the doctype JSON).
    """

    @staticmethod
    def get_settings() -> "KenyaHRSettings":
        """Return the cached single record (creates a blank one on demand)."""
        return frappe.get_single("Kenya HR Settings")