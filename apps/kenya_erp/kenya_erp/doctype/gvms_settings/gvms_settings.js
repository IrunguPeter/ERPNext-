# GVMS Settings - application level settings single.
#
# `enabled` is the master switch for the GVMS connector. When off, all the
# app's doctypes simply act as manual records you keep by hand.
frappe.ui.form.on("GVMS Settings", {
    refresh() {
        // Connector documentation lives in docs/10-fleet-management-reference.md.
    },
});