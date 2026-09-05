// Supplier Onboarding - form script.
frappe.ui.form.on("Supplier Onboarding", {
    refresh(frm) {
        // Convenience: open the linked ERPNext Supplier master.
        if (frm.doc.supplier) {
            frm.add_custom_button(__("Open Supplier"), function () {
                frappe.set_route("Form", "Supplier", frm.doc.supplier);
            });
        }
    },
});