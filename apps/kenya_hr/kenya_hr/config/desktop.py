# Desktop module definition
#
# The desk layout picks up the modules listed in `modules.txt`. When the app
# is installed, a "Kenya HR" module is available under the list of modules.
#
# Workspaces (the clickable tiles on the desk home) are defined in the UI and
# exported as fixtures, not generated here. See docs/04-hr-configuration.md.
from frappe import _

MODULE_DEFINITION = {
    "module_name": "Kenya HR",
    "category": "Modules",
    "label": _("Kenya HR"),
    "color": "#00693E",
    "icon": "octicon octicon-organization",
    "hidden": 0,
}


def get_data():
    return [
        MODULE_DEFINITION,
    ]