# Kenya EGP Settings - application level settings single.
#
# `enabled` is the master switch for the E-GP connector. When off, all the
# app's doctypes simply act as manual records you keep by hand.
frappe.ui.form.on("Kenya EGP Settings", {
    refresh() {
        // Connector documentation lives in docs/11-procurement-egp.md.
    },
});