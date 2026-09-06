// Tender - form script. Kept deliberately light: tenders may also be
// synchronised automatically from the E-GP gateway (opt-in).
frappe.ui.form.on("Tender", {
    refresh(frm) {
        if (frm.doc.egp_url) {
            frm.add_custom_button(__("Open on E-GP"), function () {
                window.open(frm.doc.egp_url, "_blank");
            });
        }
    },
});