// Staff Promotion - client-side form script.
//
// The approval lifecycle is enforced server-side (see staff_promotion.py);
// this script only delegates to it. All transition buttons come from the
// `actions` block in staff_promotion.json.

frappe.ui.form.on("Staff Promotion", {
    refresh(frm) {
        if (frm.doc.approval_status === "Effective" && frm.doc.employee) {
            frm.add_custom_button(__("Employee Record"), function () {
                frappe.set_route("Form", "Employee", frm.doc.employee);
            });
        }
    },
});