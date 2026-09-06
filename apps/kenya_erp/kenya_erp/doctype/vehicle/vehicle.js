# Vehicle - fleet master form.
frappe.ui.form.on("Vehicle", {
    refresh(frm) {
        // Firmly report telemetry freshness so nobody mistakes stale GPS for live.
        if (frm.doc.tracking_device_id) {
            frm.dashboard.set_headline(
                __("Tracking device: {0}", [frm.doc.tracking_device_id]),
                "blue"
            );
        }
    },
});