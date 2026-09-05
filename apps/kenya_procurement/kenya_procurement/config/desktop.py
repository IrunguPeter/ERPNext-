# config/desktop.py - desk tile metadata.
from frappe import _


def get_data():
    """Return the desk tile entry for the Kenya Procurement module."""
    return [
        {
            "module_name": "Kenya Procurement",
            "color": "#00693E",
            "icon": "octicon octicon-package",
            "type": "module",
            "label": _("Kenya Procurement"),
        }
    ]