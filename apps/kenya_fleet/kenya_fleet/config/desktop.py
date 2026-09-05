# config/desktop.py - desk tile metadata.
from frappe import _


def get_data():
    """Return the desk tile entry for the Fleet Management module."""
    return [
        {
            "module_name": "Fleet Management",
            "color": "#00693E",
            "icon": "octicon octicon-location",
            "type": "module",
            "label": _("Fleet Management"),
        }
    ]