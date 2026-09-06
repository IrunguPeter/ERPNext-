# GVMS Settings - single doctype. Kept a dumb data holder; all connector logic
# lives in kenya_erp.gvms_sync so the settings page stays predictable.
from frappe.model.document import Document


class GVMSSettings(Document):
    pass